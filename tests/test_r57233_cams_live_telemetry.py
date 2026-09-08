from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from firecloud.providers import cams_native


def _points():
    return [{"point_id":"p0","lat":25.0,"lon":121.0,"distance_km":0.0,"direction_offset_deg":0.0}]


def test_decoded_cache_lookup_is_visible_before_cache_hit(monkeypatch, tmp_path):
    events=[]
    cached={
        "status":"CACHE_HIT",
        "df":pd.DataFrame([{"point_id":"p0","aod550":0.1}]),
        "meta":{},
        "inventory":[],
        "error":"",
    }
    monkeypatch.setattr(cams_native, "_load_decoded_role_cache", lambda *a, **k: dict(cached))
    res=cams_native._run_cams_role_isolated(
        "SPECTRAL_COLUMN_AOD", _points(), datetime(2026,9,8,9,tzinfo=timezone.utc),
        cache_dir=tmp_path, deadline_seconds=1.0,
        heartbeat_callback=lambda role,status,elapsed: events.append((role,str(status).upper(),float(elapsed))),
    )
    assert res["status"] == "CACHE_HIT"
    assert events[0][0] == "DECODED_ROUTE_CACHE_LOOKUP"
    assert events[0][1] == "RUNNING"
    assert any(r == "DECODED_ROUTE_CACHE_LOOKUP" and s == "CACHE_HIT" for r,s,_ in events)
    assert any(r == "SPECTRAL_COLUMN_AOD" and s == "CACHE_HIT" for r,s,_ in events)


def test_single_flight_callback_repaints_ui_immediately():
    src=(Path(__file__).resolve().parents[1]/"firecloud"/"model.py").read_text(encoding="utf-8")
    assert 'if _cams_parallel_workers == 1:' in src
    assert '_render_cams_prefetch_progress(int(_cams_completed_visible.get("count", 0)))' in src
    assert '"DECODED_ROUTE_CACHE_LOOKUP": "解碼快取查找"' in src
    assert '"CAMS_WORKER_STARTUP": "worker啟動"' in src


def test_release_version_is_r57233():
    import firecloud
    assert firecloud.__version__ == "1.0.0-R5.7.23.4"
