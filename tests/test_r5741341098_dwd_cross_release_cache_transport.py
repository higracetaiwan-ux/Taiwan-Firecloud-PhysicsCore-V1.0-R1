from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import threading

import pandas as pd

import firecloud
from firecloud.providers import dwd_icon_native as icon


def test_1098_version():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.11"


def test_shared_cache_root_is_explicit_and_independent_of_cwd(monkeypatch, tmp_path):
    shared = tmp_path / "shared-provider-cache"
    monkeypatch.setenv("FIRECLOUD_DWD_ICON_SHARED_CACHE_DIR", str(shared))
    monkeypatch.delenv("FIRECLOUD_DWD_ICON_RAW_CACHE_DIR", raising=False)
    monkeypatch.delenv("FIRECLOUD_DWD_ICON_CACHE_DIR", raising=False)

    cwd_a = tmp_path / "release-a"
    cwd_b = tmp_path / "release-b"
    cwd_a.mkdir(); cwd_b.mkdir()

    monkeypatch.chdir(cwd_a)
    raw_a = icon._persistent_raw_cache_dir()
    optics_a = icon._persistent_optics_cache_path(
        datetime(2026, 9, 14, 0, tzinfo=timezone.utc), 4,
        [{"point_id":"P0","lat":23.5,"lon":121.0,"surface_pressure_hpa":1000.0,"surface_elevation_m":10.0}],
    )
    monkeypatch.chdir(cwd_b)
    raw_b = icon._persistent_raw_cache_dir()
    optics_b = icon._persistent_optics_cache_path(
        datetime(2026, 9, 14, 0, tzinfo=timezone.utc), 4,
        [{"point_id":"P0","lat":23.5,"lon":121.0,"surface_pressure_hpa":1000.0,"surface_elevation_m":10.0}],
    )

    assert raw_a == raw_b == shared / "raw_grib"
    assert optics_a == optics_b
    assert optics_a.parent == shared / "decoded_secondary_optics"


def test_thread_local_http_session_reuses_within_thread_but_not_across_threads(monkeypatch):
    # Reset the main-thread local slot for deterministic testing.
    icon._HTTP_THREAD_LOCAL = threading.local()
    a = icon._thread_http_session()
    b = icon._thread_http_session()
    assert a is b

    box = []
    def worker():
        box.append(icon._thread_http_session())
        box.append(icon._thread_http_session())
    t = threading.Thread(target=worker)
    t.start(); t.join()
    assert len(box) == 2
    assert box[0] is box[1]
    assert box[0] is not a
    a.close(); box[0].close()


def test_fetch_field_audit_exports_exact_cache_and_connection_reuse(monkeypatch, tmp_path):
    monkeypatch.setenv("FIRECLOUD_DWD_ICON_SHARED_CACHE_DIR", str(tmp_path / "shared"))
    icon._FIELD_VALUE_CACHE.clear()

    raw = tmp_path / "field.grib2"
    raw.write_bytes(b"x")

    def fake_download(url, timeout_s=20.0, *, cache_identity=None):
        return raw, {
            "status":"DOWNLOADED",
            "network_attempted":True,
            "network_success":True,
            "network_failure":False,
            "network_bytes":123,
            "raw_cache_hit":False,
        }

    def fake_decode(path, points, source_map):
        return pd.DataFrame([{
            "point_id":"P0","distance_km":0.0,"direction_offset_deg":0.0,
            "lat":23.5,"lon":121.0,"grid_lat":23.5,"grid_lon":121.0,
            "icon_source_index":0,"dwd_target_grid_address":1,
            "value":1e-6,"model_level":80,"short_name":"qc","units":"kg kg-1",
        }]), {"short_name":"qc","level":80,"units":"kg kg-1"}

    monkeypatch.setattr(icon, "_download_decompress", fake_download)
    monkeypatch.setattr(icon, "_decode_nearest", fake_decode)

    points=[{"point_id":"P0","distance_km":0.0,"direction_offset_deg":0.0,"lat":23.5,"lon":121.0}]
    run=datetime(2026,9,14,0,tzinfo=timezone.utc)
    df, meta = icon._fetch_field(run, 4, 80, "QC", points, 20.0, {"P0":{"source_index":0}})
    assert not df.empty
    assert meta["shared_cache_scope"] == "EXPLICIT_SHARED_CACHE_DIR_EXACT_IDENTITY"
    assert meta["http_connection_reuse"] == "THREAD_LOCAL_REQUESTS_SESSION_POOL"
    assert meta["network_requested"] is True
