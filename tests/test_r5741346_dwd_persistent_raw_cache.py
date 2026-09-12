from datetime import datetime, timezone
from pathlib import Path
import bz2

import pandas as pd

from firecloud.model import _summarize_dwd_api_efficiency
from firecloud.providers import dwd_icon_native as icon


class _Resp:
    def __init__(self, status_code=200, content=b""):
        self.status_code = status_code
        self.content = content


def _identity(run, lead=3, level=80, var="QC"):
    url = icon._url(run, lead, level, var)
    return url, icon._raw_cache_identity(run, lead, level, var, url)


def test_persistent_raw_cache_exact_identity_sha256_guard(monkeypatch, tmp_path):
    monkeypatch.setenv("FIRECLOUD_DWD_ICON_CACHE_DIR", str(tmp_path))
    run = datetime(2026, 9, 12, 6, tzinfo=timezone.utc)
    url, identity = _identity(run)
    payload = b"GRIB2-EXACT-FIELD-PAYLOAD"
    calls = []

    def fake_get(request_url, timeout=20.0):
        calls.append(request_url)
        return _Resp(200, bz2.compress(payload))

    monkeypatch.setattr(icon.requests, "get", fake_get)

    p1, m1 = icon._download_decompress(url, timeout_s=1.0, cache_identity=identity)
    assert p1 is not None and p1.read_bytes() == payload
    assert m1["status"] == "DOWNLOADED"
    assert m1["network_requested"] is True
    assert m1["network_success"] is True
    assert m1["raw_cache_hit"] is False
    assert len(calls) == 1

    p2, m2 = icon._download_decompress(url, timeout_s=1.0, cache_identity=identity)
    assert p2 == p1
    assert p2.read_bytes() == payload
    assert m2["status"] == "CACHE_HIT"
    assert m2["transfer_status"] == "PERSISTENT_RAW_CACHE_HIT"
    assert m2["network_requested"] is False
    assert m2["raw_cache_hit"] is True
    assert m2["network_bytes"] == 0
    assert m2["raw_cache_validation_status"] == "EXACT_IDENTITY_SHA256_READY"
    assert len(calls) == 1

    # Same source URL with a different forecast identity must not alias the cache.
    changed = dict(identity)
    changed["forecast_lead_hours"] = 6
    p3, m3 = icon._download_decompress(url, timeout_s=1.0, cache_identity=changed)
    assert p3 is not None and p3 != p1
    assert m3["status"] == "DOWNLOADED"
    assert len(calls) == 2


def test_persistent_raw_cache_corruption_fails_closed_and_redownloads(monkeypatch, tmp_path):
    monkeypatch.setenv("FIRECLOUD_DWD_ICON_CACHE_DIR", str(tmp_path))
    run = datetime(2026, 9, 12, 6, tzinfo=timezone.utc)
    url, identity = _identity(run, level=81, var="QI")
    payload = b"ORIGINAL-DWD-GRIB"
    calls = []

    def fake_get(request_url, timeout=20.0):
        calls.append(request_url)
        return _Resp(200, bz2.compress(payload))

    monkeypatch.setattr(icon.requests, "get", fake_get)
    p1, _ = icon._download_decompress(url, timeout_s=1.0, cache_identity=identity)
    assert p1 is not None
    p1.write_bytes(b"CORRUPTED")

    p2, m2 = icon._download_decompress(url, timeout_s=1.0, cache_identity=identity)
    assert p2 == p1
    assert p2.read_bytes() == payload
    assert m2["status"] == "DOWNLOADED"
    assert m2["network_requested"] is True
    assert m2["raw_cache_hit"] is False
    assert m2["raw_cache_validation_status"] in {"BYTE_SIZE_MISMATCH", "SHA256_MISMATCH"}
    assert len(calls) == 2



def test_fetch_field_new_worker_reuses_persistent_raw_bytes_exactly(monkeypatch, tmp_path):
    monkeypatch.setenv("FIRECLOUD_DWD_ICON_CACHE_DIR", str(tmp_path))
    run = datetime(2026, 9, 12, 6, tzinfo=timezone.utc)
    payload = b"PERSISTENT-RAW-GRIB"
    calls = {"network": 0, "decode": 0}

    def fake_get(request_url, timeout=20.0):
        calls["network"] += 1
        return _Resp(200, bz2.compress(payload))

    def fake_decode(path, points, source_map=None):
        calls["decode"] += 1
        assert Path(path).read_bytes() == payload
        return pd.DataFrame([{
            "point_id": "p0", "distance_km": 20.0, "direction_offset_deg": 0.0,
            "lat": 24.25, "lon": 121.75, "grid_lat": 24.25, "grid_lon": 121.75,
            "icon_source_index": 0, "dwd_target_grid_address": 1, "value": 2.5e-5,
            "model_level": 80, "short_name": "qc", "units": "kg kg-1",
        }]), {"short_name": "qc", "level": 80, "units": "kg kg-1", "grid_size": 1}

    monkeypatch.setattr(icon.requests, "get", fake_get)
    monkeypatch.setattr(icon, "_decode_nearest", fake_decode)
    icon._FIELD_VALUE_CACHE.clear()
    source_map = {"p0": {"source_index": 0, "dst_address": 1, "target_grid_lat": 24.25, "target_grid_lon": 121.75}}
    points = [{
        "point_id": "p0", "distance_km": 20.0, "direction_offset_deg": 0.0,
        "lat": 24.25, "lon": 121.75, "surface_pressure_hpa": 1008.0, "surface_elevation_m": 12.0,
    }]

    first, m1 = icon._fetch_field(run, 3, 80, "QC", points, 1.0, source_map)
    icon._FIELD_VALUE_CACHE.clear()  # simulate a fresh analysis worker
    second, m2 = icon._fetch_field(run, 3, 80, "QC", points, 1.0, source_map)

    pd.testing.assert_frame_equal(first, second, check_exact=True)
    assert calls == {"network": 1, "decode": 2}
    assert m1["status"] == "OK_DOWNLOADED"
    assert m2["status"] == "OK_CACHE_HIT"
    assert m2["raw_cache_hit"] is True
    assert m2["network_requested"] is False

def test_dwd_api_efficiency_uses_explicit_transfer_flags_not_final_ok_status():
    audit = pd.DataFrame([
        {
            "stage": "FIELD_FETCH", "status": "OK_DOWNLOADED",
            "network_requested": True, "network_success": True, "network_failure": False,
            "network_bytes": 1234, "raw_cache_hit": False, "decoded_field_cache_hit": False,
        },
        {
            "stage": "FIELD_FETCH", "status": "OK_CACHE_HIT",
            "network_requested": False, "network_success": False, "network_failure": False,
            "network_bytes": 0, "raw_cache_hit": True, "decoded_field_cache_hit": False,
        },
        {
            "stage": "FIELD_FETCH", "status": "DECODED_FIELD_CACHE_HIT",
            "network_requested": False, "network_success": False, "network_failure": False,
            "network_bytes": 0, "raw_cache_hit": False, "decoded_field_cache_hit": True,
        },
        {
            "stage": "FIELD_FETCH", "status": "HTTP_404",
            "network_requested": True, "network_success": False, "network_failure": True,
            "network_bytes": 50, "raw_cache_hit": False, "decoded_field_cache_hit": False,
        },
        {
            "stage": "RUN_LEAD_AVAILABILITY", "status": "NEGATIVE_RUN_LEAD_CACHE_HIT",
            "network_requested": False,
        },
    ])
    row = _summarize_dwd_api_efficiency(audit)
    assert row is not None
    assert row["network_requests"] == 2
    assert row["network_attempts"] == 2
    assert row["network_successes"] == 1
    assert row["network_failures"] == 1
    assert row["network_bytes"] == 1284
    assert row["raw_cache_hits"] == 1
    assert row["decoded_field_cache_hits"] == 1
    assert row["negative_availability_cache_hits"] == 1
    assert row["failure_rows"] == 1
