from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import os
import pickle
import time

import pandas as pd

from firecloud import analysis_worker
from firecloud.runtime_hardening import (
    CACHE_MODE_COLD,
    atomic_write_bytes,
    cache_provenance,
    stamp_cache_artifact,
)


def test_atomic_cache_stamp_tracks_current_job(tmp_path, monkeypatch):
    monkeypatch.setenv("FIRECLOUD_JOB_ID", "job-current")
    monkeypatch.setenv("FIRECLOUD_ANALYSIS_RUN_MODE", CACHE_MODE_COLD)
    monkeypatch.setenv("FIRECLOUD_ANALYSIS_STARTED_AT_UTC", datetime.now(timezone.utc).isoformat())
    p = tmp_path / "provider.grib"
    atomic_write_bytes(p, b"GRIB" + b"x" * 2048)
    stamp_cache_artifact(p, provider="TEST", role="RAW", schema="V1", qc_state="CACHE_READY")
    prov = cache_provenance(p, provider="TEST", role="RAW", cache_status="CACHE_HIT")
    assert prov["cache_relation"] == "CURRENT_RUN_CACHE"
    assert prov["cache_source_job_id"] == "job-current"
    assert prov["cache_qc_state"] == "CACHE_READY"
    assert prov["cache_predates_current_job"] is False


def test_unstamped_old_cache_is_prior_run(tmp_path, monkeypatch):
    monkeypatch.setenv("FIRECLOUD_JOB_ID", "job-new")
    started = datetime.now(timezone.utc)
    monkeypatch.setenv("FIRECLOUD_ANALYSIS_STARTED_AT_UTC", started.isoformat())
    p = tmp_path / "old.json"
    p.write_text("{}", encoding="utf-8")
    old = (started - timedelta(hours=2)).timestamp()
    os.utime(p, (old, old))
    prov = cache_provenance(p, provider="TEST", cache_status="CACHE_HIT")
    assert prov["cache_relation"] == "PRIOR_RUN_PERSISTENT_CACHE"
    assert prov["cache_predates_current_job"] is True
    assert prov["stamp_present"] is False


def test_analysis_worker_emits_heartbeat_stage_trace_and_resources(tmp_path, monkeypatch):
    monkeypatch.setenv("FIRECLOUD_JOB_ID", "job-heartbeat")
    monkeypatch.setenv("FIRECLOUD_ANALYSIS_RUN_MODE", CACHE_MODE_COLD)
    monkeypatch.setenv("FIRECLOUD_RUNTIME_HEARTBEAT_SECONDS", "0.05")

    def fake_analyze(lat, lon, day, event, tz_name, progress_callback, timezone_mode):
        progress_callback(0.2, "太陽高度角 -3.0°（7/13）：重建 0.5 km 垂直雲柱…")
        time.sleep(0.13)
        progress_callback(0.7, "太陽高度角 -5.5°（12/13）：建立氣體狀態…")
        time.sleep(0.13)
        return {"summary": pd.DataFrame([{"ok": 1}])}

    monkeypatch.setattr(analysis_worker, "analyze_event", fake_analyze)
    req = tmp_path / "request.json"
    result = tmp_path / "result.pkl"
    progress = tmp_path / "progress.json"
    req.write_text(json.dumps({
        "lat": 23.5, "lon": 121.0, "day": "2026-09-08", "event": "sunset",
        "tz_name": "Asia/Taipei", "tz_mode": "AUTO_COORDINATE",
    }), encoding="utf-8")

    rc = analysis_worker.main([str(req), str(result), str(progress)])
    assert rc == 0
    with result.open("rb") as fh:
        payload = pickle.load(fh)
    trace = payload["runtime_stage_trace"]
    resource = payload["runtime_resource_telemetry"]
    contract = payload["runtime_execution_contract"]
    assert not trace.empty
    assert "HEARTBEAT" in set(trace["status"].astype(str))
    assert trace["last_message"].astype(str).str.contains("-3.0°").any()
    assert trace["last_message"].astype(str).str.contains("-5.5°").any()
    assert not resource.empty
    assert "rss_mb" in resource.columns
    assert bool(contract.iloc[0]["cold_cache_isolated"]) is True
    pstate = json.loads(progress.read_text(encoding="utf-8"))
    assert pstate["status"] == "COMPLETED"
    assert pstate["job_id"] == "job-heartbeat"
    assert (tmp_path / "runtime_stage_trace.csv").is_file()
    assert (tmp_path / "runtime_resource_telemetry.csv").is_file()


def test_r5723_model_defaults_cams_to_global_ads_single_flight():
    src = (Path(__file__).resolve().parents[1] / "firecloud" / "model.py").read_text(encoding="utf-8")
    assert 'FIRECLOUD_CAMS_PREFETCH_WORKERS", "1"' in src
    assert "FIRECLOUD_CAMS_ALLOW_PARALLEL_TIME_BUNDLES" in src
    assert "GLOBAL_ADS_SINGLE_FLIGHT" in src
    assert "PREFETCH_GLOBAL_ADS_SINGLE_FLIGHT" in src


def test_app_exposes_isolated_cache_namespace_and_runtime_case_evidence():
    src = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
    for token in (
        "COLD_ISOLATED_TEST",
        "RESUME_SAME_JOB",
        "FIRECLOUD_GFS_CACHE_DIR",
        "FIRECLOUD_CAMS_CACHE_DIR",
        "FIRECLOUD_OPENMETEO_CACHE_DIR",
        "FIRECLOUD_DWD_ICON_CACHE_DIR",
        "runtime_execution_contract.csv",
        "runtime_cache_provenance.csv",
        "runtime_stage_trace.csv",
        "runtime_resource_telemetry.csv",
    ):
        assert token in src


def test_r57231_cold_cams_skips_decoded_route_cache_write(tmp_path, monkeypatch):
    from firecloud.providers import cams_native
    monkeypatch.setenv("FIRECLOUD_ANALYSIS_RUN_MODE", "COLD_ISOLATED_TEST")
    pts=[{"point_id":"p0","lat":23.5,"lon":121.0,"distance_km":0.0,"direction_offset_deg":0.0}]
    t=datetime(2026,9,8,9,tzinfo=timezone.utc)
    result={"status":"OK","df":pd.DataFrame([{"point_id":"p0","cams_ozone_kgkg_500":1e-6}]),"meta":{}}
    audit=cams_native._save_decoded_role_cache("O3_PRESSURE_LEVEL",pts,t,result,tmp_path)
    assert audit["status"] == "SKIPPED_COLD_ISOLATED_TEST"
    assert not list(tmp_path.rglob("cams_decoded_*.pkl"))


def test_r57231_cams_post_worker_progress_is_explicit():
    src = (Path(__file__).resolve().parents[1] / "firecloud" / "providers" / "cams_native.py").read_text(encoding="utf-8")
    assert 'heartbeat_callback("DECODED_ROUTE_CACHE_WRITE", "RUNNING"' in src
    assert 'progress_callback("CAMS_BUNDLE_POSTPROCESS", "RUNNING"' in src
    model = (Path(__file__).resolve().parents[1] / "firecloud" / "model.py").read_text(encoding="utf-8")
    assert '"DECODED_ROUTE_CACHE_WRITE": "解碼快取落盤"' in model
    assert '"CAMS_BUNDLE_POSTPROCESS": "時次後處理"' in model


def test_r57231_streamlit_rerun_auto_reattaches_live_worker():
    src = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
    assert "_active_detached_job" in src
    assert "已自動重新連線監看" in src
    assert "resume_run = bool(_active_detached_job)" in src
    assert '_reattach_request = dict(_old_job.get("request") or _request)' in src
