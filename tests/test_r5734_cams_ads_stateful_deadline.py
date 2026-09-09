from __future__ import annotations

import json
from pathlib import Path

import pytest

from firecloud.providers.cams_ads_stateful import (
    AdsStatefulTimeout,
    canonical_request_fingerprint,
    request_journal_path,
    retrieve_with_stateful_deadline,
)


class Clock:
    def __init__(self):
        self.t = 0.0
    def monotonic(self):
        return self.t
    def sleep(self, seconds):
        self.t += float(seconds)


class Remote:
    def __init__(self, client, request_id):
        self.client = client
        self.request_id = request_id
    @property
    def status(self):
        return self.client.status
    def download(self, target):
        Path(target).write_bytes(b"x" * 2048)
        self.client.downloads += 1


class FakeClient:
    def __init__(self, status="accepted"):
        self.status = status
        self.submits = 0
        self.gets = 0
        self.downloads = 0
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


def test_queue_timeout_preserves_request_id_for_recovery(tmp_path):
    clock = Clock(); client = FakeClient("accepted")
    request = {"date": "2026-09-09", "variable": ["x"]}
    with pytest.raises(AdsStatefulTimeout) as ei:
        retrieve_with_stateful_deadline(
            client=client, dataset="cams", request=request, target=tmp_path/"out.grib",
            role="NATIVE_AEROSOL", cache_dir=tmp_path,
            queue_grace_seconds=3, running_grace_seconds=10, total_deadline_seconds=20,
            poll_seconds=1, monotonic=clock.monotonic, sleep=clock.sleep,
        )
    exc = ei.value
    assert exc.reason == "CAMS_ADS_QUEUE_GRACE_EXCEEDED"
    assert exc.request_id == "rid-1"
    assert exc.audit_fields["ads_request_recovery_eligible"] is True
    assert client.submits == 1
    fp = canonical_request_fingerprint("cams", request)
    journal = json.loads(request_journal_path(tmp_path, "NATIVE_AEROSOL", fp).read_text())
    assert journal["request_id"] == "rid-1"
    assert journal["local_wait_deferred_reason"] == "CAMS_ADS_QUEUE_GRACE_EXCEEDED"


def test_second_invocation_reattaches_same_request_id_without_duplicate_submit(tmp_path):
    clock = Clock(); client = FakeClient("accepted")
    request = {"date": "2026-09-09", "variable": ["x"]}
    with pytest.raises(AdsStatefulTimeout):
        retrieve_with_stateful_deadline(
            client=client, dataset="cams", request=request, target=tmp_path/"first.grib",
            role="SPECTRAL_COLUMN_AOD", cache_dir=tmp_path,
            queue_grace_seconds=2, running_grace_seconds=10, total_deadline_seconds=20,
            poll_seconds=1, monotonic=clock.monotonic, sleep=clock.sleep,
        )
    assert client.submits == 1
    client.status = "successful"
    clock2 = Clock()
    out = tmp_path/"second.grib"
    meta = retrieve_with_stateful_deadline(
        client=client, dataset="cams", request=request, target=out,
        role="SPECTRAL_COLUMN_AOD", cache_dir=tmp_path,
        queue_grace_seconds=2, running_grace_seconds=10, total_deadline_seconds=20,
        poll_seconds=1, monotonic=clock2.monotonic, sleep=clock2.sleep,
    )
    assert client.submits == 1
    assert meta["ads_request_id"] == "rid-1"
    assert meta["ads_request_reattached"] is True
    assert out.stat().st_size == 2048


def test_running_grace_is_separate_from_queue_grace(tmp_path):
    clock = Clock(); client = FakeClient("running")
    request = {"date": "2026-09-09", "variable": ["x"]}
    with pytest.raises(AdsStatefulTimeout) as ei:
        retrieve_with_stateful_deadline(
            client=client, dataset="cams", request=request, target=tmp_path/"out.grib",
            role="O3", cache_dir=tmp_path,
            queue_grace_seconds=1, running_grace_seconds=4, total_deadline_seconds=20,
            poll_seconds=1, monotonic=clock.monotonic, sleep=clock.sleep,
        )
    assert ei.value.reason == "CAMS_ADS_RUNNING_GRACE_EXCEEDED"
    assert ei.value.running_elapsed_seconds >= 4


def test_request_fingerprint_prevents_cross_request_reattach(tmp_path):
    clock = Clock(); client = FakeClient("accepted")
    req1 = {"date": "2026-09-09", "variable": ["x"]}
    with pytest.raises(AdsStatefulTimeout):
        retrieve_with_stateful_deadline(
            client=client, dataset="cams", request=req1, target=tmp_path/"x",
            role="A", cache_dir=tmp_path, queue_grace_seconds=1,
            running_grace_seconds=5, total_deadline_seconds=10, poll_seconds=1,
            monotonic=clock.monotonic, sleep=clock.sleep,
        )
    req2 = {"date": "2026-09-09", "variable": ["y"]}
    clock2 = Clock()
    with pytest.raises(AdsStatefulTimeout):
        retrieve_with_stateful_deadline(
            client=client, dataset="cams", request=req2, target=tmp_path/"y",
            role="A", cache_dir=tmp_path, queue_grace_seconds=1,
            running_grace_seconds=5, total_deadline_seconds=10, poll_seconds=1,
            monotonic=clock2.monotonic, sleep=clock2.sleep,
        )
    assert client.submits == 2
