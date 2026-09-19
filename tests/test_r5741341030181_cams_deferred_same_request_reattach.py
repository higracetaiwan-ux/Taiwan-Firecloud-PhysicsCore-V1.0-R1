from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from firecloud.providers import cams_native
from firecloud.providers.cams_ads_stateful import (
    AdsStatefulFailure,
    canonical_request_fingerprint,
    request_journal_path,
    retrieve_with_stateful_deadline,
)


class Remote:
    def __init__(self, request_id: str, status: str = "successful"):
        self.request_id = request_id
        self.status = status
    def download(self, target):
        Path(target).write_bytes(b"x" * 2048)


class ReattachOnlyClient:
    def __init__(self, remote: Remote | None = None):
        self.remote = remote
        self.submits = 0
        self.gets = 0
    def submit(self, dataset, request):
        self.submits += 1
        return Remote(f"new-{self.submits}")
    def get_remote(self, request_id):
        self.gets += 1
        if self.remote is None:
            raise RuntimeError("remote unavailable")
        assert self.remote.request_id == request_id
        return self.remote


def test_reattach_only_without_journal_never_submits(tmp_path):
    client = ReattachOnlyClient()
    with pytest.raises(AdsStatefulFailure) as ei:
        retrieve_with_stateful_deadline(
            client=client,
            dataset="cams",
            request={"date": "2026-09-20", "variable": ["aod"]},
            target=tmp_path / "out.grib",
            role="SPECTRAL_COLUMN_AOD",
            cache_dir=tmp_path,
            reattach_only=True,
        )
    assert "REATTACH_ONLY_NO_RECOVERABLE_REQUEST" in str(ei.value)
    assert client.submits == 0


def test_reattach_only_collects_same_request_id_without_duplicate_submit(tmp_path):
    request = {"date": "2026-09-20", "variable": ["aod"]}
    fp = canonical_request_fingerprint("cams", request)
    journal = request_journal_path(tmp_path, "SPECTRAL_COLUMN_AOD", fp)
    journal.write_text(json.dumps({
        "request_fingerprint": fp,
        "request_id": "rid-existing",
        "remote_status": "running",
        "status_history": [],
    }), encoding="utf-8")
    client = ReattachOnlyClient(Remote("rid-existing", "successful"))
    out = tmp_path / "out.grib"
    meta = retrieve_with_stateful_deadline(
        client=client,
        dataset="cams",
        request=request,
        target=out,
        role="SPECTRAL_COLUMN_AOD",
        cache_dir=tmp_path,
        reattach_only=True,
    )
    assert client.submits == 0
    assert client.gets >= 1
    assert meta["ads_request_id"] == "rid-existing"
    assert meta["ads_request_reattached"] is True
    assert meta["ads_reattach_only"] is True
    assert out.stat().st_size == 2048


def _ok(role: str):
    base = {"point_id":["p0"], "distance_km":[0.0], "direction_offset_deg":[0.0], "lat":[24.25], "lon":[120.5]}
    if role == "O3_PRESSURE_LEVEL":
        base["cams_ozone_kgkg_100"] = [1e-6]
    elif role == "O3_NEAR_SURFACE_MODEL_LEVEL_137":
        base["cams_ozone_ml137_kgkg"] = [8e-8]
    elif role == "SPECTRAL_COLUMN_AOD":
        base.update({"aod550":[0.1], "aod645":[0.08], "aod670":[0.075], "aod800":[0.05]})
    elif role == "AEROSOL_SCATTERING_COLUMN_PROPERTIES":
        base.update({"aod532":[0.11], "aod550":[0.10], "aod645":[0.08], "aod670":[0.075], "aod800":[0.05],
                     "ssa550":[0.97], "ssa645":[0.96], "ssa670":[0.96], "ssa800":[0.95],
                     "asymmetry550":[0.72], "asymmetry645":[0.71], "asymmetry670":[0.70], "asymmetry800":[0.68]})
    else:
        base["cams_aerext532_m1_100"] = [1e-5]
    return {"role":role, "status":"OK", "df":pd.DataFrame(base), "meta":{}, "inventory":[], "error":"", "elapsed_seconds":0.1}


def test_serial_scheduler_same_run_reattaches_timeout_deferred(monkeypatch):
    calls=[]
    timed_out=set()
    def fake_run(role, points, valid_time, cache_dir=None, deadline_seconds=90.0, heartbeat_callback=None, reattach_only=False):
        calls.append((role, bool(reattach_only)))
        if role == "SPECTRAL_COLUMN_AOD" and not reattach_only and role not in timed_out:
            timed_out.add(role)
            return {
                "role": role,
                "status": "TIMEOUT_DEFERRED",
                "df": pd.DataFrame(),
                "meta": {"request_audit": {
                    "ads_request_id": "rid-spectral",
                    "ads_request_recovery_eligible": True,
                    "ads_remote_status": "running",
                }},
                "inventory": [],
                "error": "CAMS_ADS_RUNNING_GRACE_EXCEEDED",
                "elapsed_seconds": 120.0,
            }
        return _ok(role)

    monkeypatch.setattr(cams_native, "_run_cams_role_isolated", fake_run)
    monkeypatch.setattr(cams_native.time, "sleep", lambda *_: None)
    monkeypatch.setenv("FIRECLOUD_CAMS_ROLE_RETRY_COUNT", "0")
    monkeypatch.setenv("FIRECLOUD_CAMS_DEFERRED_REATTACH_COUNT", "1")
    pts=[{"point_id":"p0","distance_km":0.0,"direction_offset_deg":0.0,"lat":24.25,"lon":120.5}]
    _, meta = cams_native._fetch_route_native_aerosol_bundle_single_tile(
        pts, datetime(2026,9,20,0,0,tzinfo=timezone.utc), deadline_seconds=1.0
    )
    assert ("SPECTRAL_COLUMN_AOD", False) in calls
    assert ("SPECTRAL_COLUMN_AOD", True) in calls
    audit=[r for r in meta["cams_request_audit"] if r["request_role"] == "SPECTRAL_COLUMN_AOD"][0]
    assert audit["final_status"] == "OK"
    assert audit["deferred_reattach_attempted"] is True
    assert audit["deferred_reattach_count"] == 1
    assert audit["deferred_initial_status"] == "TIMEOUT_DEFERRED"
    assert audit["deferred_recovery_contract"] == "R5.7.41.3.4.10.30.18.1_SAME_REQUEST_ID_BOUNDED_REATTACH_V1"
