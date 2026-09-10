from __future__ import annotations

import json
from pathlib import Path
from urllib.error import HTTPError

import pytest

import firecloud.providers.cams_ads_stateful as mod
from firecloud.providers.cams_ads_stateful import (
    AdsStatefulFailure,
    canonical_request_fingerprint,
    request_journal_path,
    retrieve_with_stateful_deadline,
)


class Clock:
    def __init__(self):
        self.t = 0.0
        self.sleeps: list[float] = []

    def monotonic(self):
        return self.t

    def sleep(self, seconds):
        seconds = float(seconds)
        self.sleeps.append(seconds)
        self.t += seconds


class Results:
    def __init__(self, location="https://download.invalid/signed-result"):
        self.location = location


class Remote:
    def __init__(self, client, request_id):
        self.client = client
        self.request_id = request_id

    @property
    def status(self):
        return self.client.status

    def download(self, target):
        self.client.native_downloads += 1
        Path(target).write_bytes(b"n" * 2048)


class Client:
    def __init__(self):
        self.status = "successful"
        self.submits = 0
        self.gets = 0
        self.result_gets = 0
        self.native_downloads = 0
        self.remote = None

    def submit(self, dataset, request):
        self.submits += 1
        self.remote = Remote(self, f"rid-{self.submits}")
        return self.remote

    def get_remote(self, request_id):
        self.gets += 1
        if self.remote is None or self.remote.request_id != request_id:
            self.remote = Remote(self, request_id)
        return self.remote

    def get_results(self, request_id):
        self.result_gets += 1
        assert request_id.startswith("rid-")
        return Results(f"https://download.invalid/result-{self.result_gets}")


def _call(tmp_path, client, clock, role="SPECTRAL_COLUMN_AOD"):
    return retrieve_with_stateful_deadline(
        client=client,
        dataset="cams",
        request={"date": "2026-09-10", "variable": ["aod"]},
        target=tmp_path / "out.grib",
        role=role,
        cache_dir=tmp_path,
        queue_grace_seconds=3,
        running_grace_seconds=3,
        total_deadline_seconds=10,
        poll_seconds=1,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )


def test_transient_502_retries_same_successful_request_without_resubmit(tmp_path, monkeypatch):
    client = Client()
    clock = Clock()
    attempts = {"n": 0}

    def fake_download(location, target, timeout_seconds):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise HTTPError(location, 502, "Bad Gateway", {}, None)
        target.write_bytes(b"x" * 2048)
        return 2048

    monkeypatch.setattr(mod, "_download_url_once", fake_download)
    meta = _call(tmp_path, client, clock)

    assert client.submits == 1
    assert client.result_gets == 2
    assert client.native_downloads == 0
    assert meta["ads_request_id"] == "rid-1"
    assert meta["ads_download_attempts"] == 2
    assert meta["ads_download_retry_count"] == 1
    assert meta["ads_download_url_refresh_count"] == 2
    assert meta["ads_download_backoff_seconds"] == 2.0
    assert meta["ads_download_strategy"] == "DIRECT_RESULTS_LOCATION_BOUNDED_RETRY_V1"
    assert (tmp_path / "out.grib").stat().st_size == 2048

    fp = canonical_request_fingerprint("cams", {"date": "2026-09-10", "variable": ["aod"]})
    journal = json.loads(request_journal_path(tmp_path, "SPECTRAL_COLUMN_AOD", fp).read_text())
    text = json.dumps(journal)
    assert "https://" not in text
    assert journal["ads_download_retry_count"] == 1


def test_exhausted_download_is_recovery_eligible_and_next_invocation_reattaches(tmp_path, monkeypatch):
    client = Client()
    clock = Clock()

    def always_502(location, target, timeout_seconds):
        raise HTTPError(location, 502, "Bad Gateway", {}, None)

    monkeypatch.setattr(mod, "_download_url_once", always_502)
    with pytest.raises(AdsStatefulFailure) as ei:
        _call(tmp_path, client, clock, role="O3_PRESSURE_LEVEL")
    assert client.submits == 1
    assert ei.value.audit_fields["ads_request_id"] == "rid-1"
    assert ei.value.audit_fields["ads_request_recovery_eligible"] is True
    assert ei.value.audit_fields["ads_download_recovery_eligible"] is True
    assert ei.value.audit_fields["ads_download_attempts"] == 4

    def succeed(location, target, timeout_seconds):
        target.write_bytes(b"z" * 2048)
        return 2048

    monkeypatch.setattr(mod, "_download_url_once", succeed)
    clock2 = Clock()
    meta = _call(tmp_path, client, clock2, role="O3_PRESSURE_LEVEL")
    assert client.submits == 1  # no duplicate remote job
    assert meta["ads_request_id"] == "rid-1"
    assert meta["ads_request_reattached"] is True
    assert meta["ads_download_attempts"] == 1


def test_non_retryable_http_404_fails_immediately(tmp_path, monkeypatch):
    client = Client()
    clock = Clock()

    def fail404(location, target, timeout_seconds):
        raise HTTPError(location, 404, "Not Found", {}, None)

    monkeypatch.setattr(mod, "_download_url_once", fail404)
    with pytest.raises(AdsStatefulFailure) as ei:
        _call(tmp_path, client, clock)
    assert client.submits == 1
    assert client.result_gets == 1
    assert ei.value.audit_fields["ads_download_attempts"] == 1
    assert ei.value.audit_fields["ads_download_retry_count"] == 0
    assert clock.sleeps == []


def test_retry_after_120_seconds_is_bounded_by_download_backoff_cap(tmp_path, monkeypatch):
    client = Client()
    clock = Clock()
    attempts = {"n": 0}

    class Headers(dict):
        pass

    def fail_once(location, target, timeout_seconds):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise HTTPError(location, 502, "Bad Gateway", Headers({"Retry-After": "120"}), None)
        target.write_bytes(b"y" * 2048)
        return 2048

    monkeypatch.setattr(mod, "_download_url_once", fail_once)
    monkeypatch.setenv("FIRECLOUD_CAMS_DOWNLOAD_MAX_BACKOFF_SECONDS", "12")
    meta = _call(tmp_path, client, clock)
    assert clock.sleeps == [12.0]
    assert meta["ads_download_backoff_seconds"] == 12.0


def test_results_location_path_is_preferred_over_native_remote_download(tmp_path, monkeypatch):
    client = Client()
    clock = Clock()

    def succeed(location, target, timeout_seconds):
        assert location.startswith("https://download.invalid/")
        target.write_bytes(b"d" * 2048)
        return 2048

    monkeypatch.setattr(mod, "_download_url_once", succeed)
    meta = _call(tmp_path, client, clock)
    assert client.native_downloads == 0
    assert meta["ads_download_strategy"] == "DIRECT_RESULTS_LOCATION_BOUNDED_RETRY_V1"


def _download_integrity_status(cams_rows):
    import pandas as pd
    from firecloud.case_integrity import build_analysis_integrity_audit

    audit = build_analysis_integrity_audit({
        "cams_request_audit": pd.DataFrame(cams_rows),
        "cams_post_success_download_recovery_required": True,
    })
    row = audit.loc[audit["check_id"].eq("CAMS_POST_SUCCESS_DOWNLOAD_RECOVERY_TELEMETRY")].iloc[0]
    return row


def test_integrity_requires_r5738_download_telemetry_for_fresh_success():
    row = _download_integrity_status([{
        "request_role": "SPECTRAL_COLUMN_AOD",
        "ads_remote_status": "successful",
        "ads_request_id": "rid-1",
        "cache_hit": False,
        "ads_download_recovery_contract": "R5.7.38_POST_SUCCESS_SAME_REQUEST_ID_BOUNDED_DOWNLOAD_RETRY_V1",
        "ads_download_attempts": 2,
        "ads_download_retry_count": 1,
        "ads_download_url_refresh_count": 2,
        "ads_download_elapsed_seconds": 2.5,
        "ads_download_strategy": "DIRECT_RESULTS_LOCATION_BOUNDED_RETRY_V1",
    }])
    assert row["status"] == "PASS"
    assert "retry_rows=1" in str(row["observed"])


def test_integrity_fails_fresh_success_without_r5738_download_telemetry():
    row = _download_integrity_status([{
        "request_role": "SPECTRAL_COLUMN_AOD",
        "ads_remote_status": "successful",
        "ads_request_id": "rid-1",
        "cache_hit": False,
    }])
    assert row["status"] == "FAIL"


def test_integrity_cache_only_run_does_not_fake_field_proof():
    row = _download_integrity_status([{
        "request_role": "SPECTRAL_COLUMN_AOD",
        "ads_remote_status": "",
        "ads_request_id": "",
        "cache_hit": True,
        "status": "CACHE_HIT",
    }])
    assert row["status"] == "WARN"


def test_signed_download_url_is_redacted_even_when_exception_message_contains_it(tmp_path, monkeypatch):
    client = Client()
    clock = Clock()

    def leak_url(location, target, timeout_seconds):
        raise OSError(f"temporary download failed at {location}?token=SUPERSECRET")

    monkeypatch.setattr(mod, "_download_url_once", leak_url)
    with pytest.raises(AdsStatefulFailure) as ei:
        _call(tmp_path, client, clock)
    fields = ei.value.audit_fields
    assert "https://" not in fields["ads_download_last_error"]
    assert "SUPERSECRET" not in fields["ads_download_last_error"]

    fp = canonical_request_fingerprint("cams", {"date": "2026-09-10", "variable": ["aod"]})
    journal_text = request_journal_path(tmp_path, "SPECTRAL_COLUMN_AOD", fp).read_text()
    assert "https://" not in journal_text
    assert "SUPERSECRET" not in journal_text
