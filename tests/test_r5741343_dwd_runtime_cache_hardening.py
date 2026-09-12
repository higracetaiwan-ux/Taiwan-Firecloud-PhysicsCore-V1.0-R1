from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from firecloud.providers import dwd_icon_native as icon


def _points(ps=1008.0):
    return [{
        "point_id": "p0",
        "distance_km": 20.0,
        "direction_offset_deg": 0.0,
        "lat": 24.25,
        "lon": 121.75,
        "surface_pressure_hpa": ps,
        "surface_elevation_m": 12.0,
    }]


def _clear_runtime_caches():
    icon._FIELD_VALUE_CACHE.clear()
    icon._NEGATIVE_RUN_LEAD_CACHE.clear()
    icon._RUNTIME_CACHE.clear()
    icon._ROUTE_SOURCE_MAP_CACHE.clear()


def test_decoded_field_cache_ignores_surface_anchor_but_preserves_route_geometry(monkeypatch, tmp_path):
    _clear_runtime_caches()
    run = datetime(2026, 9, 12, 0, tzinfo=timezone.utc)
    source_map = {"p0": {"source_index": 0, "dst_address": 1, "target_grid_lat": 24.25, "target_grid_lon": 121.75}}
    grib = tmp_path / "field.grib2"
    grib.write_bytes(b"x")
    calls = {"download": 0, "decode": 0}

    def fake_download(url, timeout_s=20.0):
        calls["download"] += 1
        return grib, {"url": url, "status": "DOWNLOADED", "bytes": 1}

    def fake_decode(path, points, source_map=None):
        calls["decode"] += 1
        return pd.DataFrame([{
            "point_id": "p0", "distance_km": 20.0, "direction_offset_deg": 0.0,
            "lat": 24.25, "lon": 121.75, "grid_lat": 24.25, "grid_lon": 121.75,
            "icon_source_index": 0, "dwd_target_grid_address": 1, "value": 1.5e-5,
            "model_level": 80, "short_name": "qc", "units": "kg kg-1",
        }]), {"short_name": "qc", "level": 80, "units": "kg kg-1", "grid_size": 1}

    monkeypatch.setattr(icon, "_download_decompress", fake_download)
    monkeypatch.setattr(icon, "_decode_nearest", fake_decode)

    df1, m1 = icon._fetch_field(run, 3, 80, "QC", _points(1008.0), 1.0, source_map)
    df2, m2 = icon._fetch_field(run, 3, 80, "QC", _points(998.0), 1.0, source_map)

    assert not df1.empty and not df2.empty
    assert calls == {"download": 1, "decode": 1}
    assert m1["status"].startswith("OK_")
    assert m2["status"] == "DECODED_FIELD_CACHE_HIT"
    assert m2["network_requested"] is False


def test_all_404_condensate_probe_writes_negative_run_lead_cache_and_second_angle_skips(monkeypatch):
    _clear_runtime_caches()
    monkeypatch.setattr(icon, "network_enabled", lambda: True)
    monkeypatch.setattr(icon, "decoder_available", lambda: True)
    monkeypatch.setattr(icon, "remap_reader_available", lambda: True)
    monkeypatch.setattr(icon, "_model_levels", lambda: [55, 56])
    monkeypatch.setattr(icon, "_route_source_index_map", lambda points, timeout_s=30.0: (
        {"p0": {"source_index": 0, "dst_address": 1, "target_grid_lat": 24.25, "target_grid_lon": 121.75}},
        {"stage": "GRID_MAPPING", "status": "GRID_MAPPING_READY"},
    ))
    calls = {"field": 0}

    def fake_fetch(run, lead, level, var, points, timeout_s, source_map):
        calls["field"] += 1
        return pd.DataFrame(), {
            "stage": "FIELD_FETCH", "status": "HTTP_404", "variable": var,
            "model_level": level, "run": run, "lead_hours": lead, "network_requested": True,
        }

    monkeypatch.setattr(icon, "_fetch_field", fake_fetch)
    t = datetime(2026, 9, 4, 21, tzinfo=timezone.utc)

    _, meta1, audit1 = icon.fetch_icon_route_profiles(_points(1008.0), t)
    first_calls = calls["field"]
    _, meta2, audit2 = icon.fetch_icon_route_profiles(_points(998.0), t)

    assert first_calls == 4
    assert calls["field"] == 4
    assert meta1["status"] == "RUN_LEAD_UNAVAILABLE_ALL_QC_QI_HTTP_404"
    assert meta1["negative_run_lead_cache_status"] == "MISS_WRITE"
    assert meta2["status"] == "RUN_LEAD_UNAVAILABLE_CACHED"
    assert meta2["negative_run_lead_cache_status"] == "HIT"
    assert "NEGATIVE_RUN_LEAD_CACHE_WRITE" in set(audit1["status"].astype(str))
    assert set(audit2["status"].astype(str)) == {"NEGATIVE_RUN_LEAD_CACHE_HIT"}


def test_mixed_condensate_failures_do_not_create_negative_availability_cache(monkeypatch):
    _clear_runtime_caches()
    monkeypatch.setattr(icon, "network_enabled", lambda: True)
    monkeypatch.setattr(icon, "decoder_available", lambda: True)
    monkeypatch.setattr(icon, "remap_reader_available", lambda: True)
    monkeypatch.setattr(icon, "_model_levels", lambda: [55])
    monkeypatch.setattr(icon, "_route_source_index_map", lambda points, timeout_s=30.0: (
        {"p0": {"source_index": 0, "dst_address": 1, "target_grid_lat": 24.25, "target_grid_lon": 121.75}},
        {"stage": "GRID_MAPPING", "status": "GRID_MAPPING_READY"},
    ))
    statuses = iter(["HTTP_404", "HTTP_500", "HTTP_404", "HTTP_500"])

    def fake_fetch(run, lead, level, var, points, timeout_s, source_map):
        return pd.DataFrame(), {
            "stage": "FIELD_FETCH", "status": next(statuses), "variable": var,
            "model_level": level, "run": run, "lead_hours": lead, "network_requested": True,
        }

    monkeypatch.setattr(icon, "_fetch_field", fake_fetch)
    t = datetime(2026, 9, 4, 21, tzinfo=timezone.utc)
    _, meta1, _ = icon.fetch_icon_route_profiles(_points(), t)
    _, meta2, _ = icon.fetch_icon_route_profiles(_points(998.0), t)

    assert meta1["status"] == "NATIVE_MICROPHYSICS_UNRESOLVED"
    assert meta2["status"] == "NATIVE_MICROPHYSICS_UNRESOLVED"
    assert not icon._NEGATIVE_RUN_LEAD_CACHE
