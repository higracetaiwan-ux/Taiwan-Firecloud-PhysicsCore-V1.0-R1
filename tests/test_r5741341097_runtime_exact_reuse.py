from datetime import datetime, timezone
import warnings

import numpy as np
import pandas as pd
from pandas.errors import PerformanceWarning

from firecloud.providers import cams_native, gfs_native


def _points():
    return [
        {"point_id": "p0", "distance_km": 0.0, "direction_offset_deg": 0.0, "lat": 24.25, "lon": 120.5},
        {"point_id": "p1", "distance_km": 20.0, "direction_offset_deg": 0.0, "lat": 24.25, "lon": 120.3},
    ]


def _role_result(role, *, complete_scattering=True):
    rows=[]
    for p in _points():
        row={k:p[k] for k in ("point_id","distance_km","direction_offset_deg","lat","lon")}
        if role == "O3_PRESSURE_LEVEL":
            row["cams_ozone_kgkg_100"] = 1e-6
        elif role == "O3_NEAR_SURFACE_MODEL_LEVEL_137":
            row["cams_ozone_ml137_kgkg"] = 8e-8
        elif role == "NATIVE_AEROSOL_532NM_PRESSURE_LEVEL":
            row["cams_aerext532_m1_100"] = 1e-5
        elif role == "AEROSOL_SCATTERING_COLUMN_PROPERTIES":
            row.update({
                "aod532":0.11,"aod550":0.10,"aod645":0.08,"aod670":0.075,
                "ssa550":0.97,"ssa645":0.97,"ssa670":0.97,"ssa800":0.97,
                "asymmetry550":0.72,"asymmetry645":0.72,"asymmetry670":0.72,"asymmetry800":0.72,
            })
            if complete_scattering:
                row["aod800"] = 0.05
        elif role == "SPECTRAL_COLUMN_AOD":
            row.update({"aod550":0.10,"aod645":0.08,"aod670":0.075,"aod800":0.05})
        rows.append(row)
    return {
        "role": role,
        "status": "OK",
        "df": pd.DataFrame(rows),
        "meta": {"request_audit": {"request_role": role, "status": "OK"}},
        "inventory": [],
        "error": "",
        "elapsed_seconds": 0.01,
    }


def test_cams_scattering_exactly_handoffs_spectral_aod_without_second_ads_job(monkeypatch):
    calls=[]
    def fake(role, points, valid_time, cache_dir=None, deadline_seconds=90.0, heartbeat_callback=None):
        calls.append(role)
        return _role_result(role, complete_scattering=True)
    monkeypatch.setattr(cams_native, "_run_cams_role_isolated", fake)
    monkeypatch.setattr(cams_native.time, "sleep", lambda *_: None)
    df, meta = cams_native.fetch_route_native_aerosol_bundle_timed(
        _points(), datetime(2026,9,14,10,0,tzinfo=timezone.utc), deadline_seconds=1.0
    )
    assert calls == [
        "O3_PRESSURE_LEVEL",
        "O3_NEAR_SURFACE_MODEL_LEVEL_137",
        "NATIVE_AEROSOL_532NM_PRESSURE_LEVEL",
        "AEROSOL_SCATTERING_COLUMN_PROPERTIES",
    ]
    assert meta["cams_spectral_aod_status"] == "OK"
    assert meta["cams_spectral_aod_exact_reuse"] is True
    assert meta["cams_spectral_aod_exact_reuse_source"] == "AEROSOL_SCATTERING_COLUMN_PROPERTIES"
    spectral = [x for x in meta["cams_request_audit"] if x.get("request_role") == "SPECTRAL_COLUMN_AOD"]
    assert len(spectral) == 1
    assert spectral[0]["final_status"] == "EXACT_SOURCE_REUSE"
    assert spectral[0]["exact_source_reuse"] is True
    assert float(df.loc[df.point_id.eq("p0"), "aod800"].iloc[0]) == 0.05
    # Four network/worker requests, not five.
    assert meta["cams_tile_count"] == 4


def test_cams_spectral_request_falls_back_when_scattering_aod_is_incomplete(monkeypatch):
    calls=[]
    def fake(role, points, valid_time, cache_dir=None, deadline_seconds=90.0, heartbeat_callback=None):
        calls.append(role)
        return _role_result(role, complete_scattering=False if role == "AEROSOL_SCATTERING_COLUMN_PROPERTIES" else True)
    monkeypatch.setattr(cams_native, "_run_cams_role_isolated", fake)
    monkeypatch.setattr(cams_native.time, "sleep", lambda *_: None)
    _, meta = cams_native.fetch_route_native_aerosol_bundle_timed(
        _points(), datetime(2026,9,14,10,0,tzinfo=timezone.utc), deadline_seconds=1.0
    )
    assert "SPECTRAL_COLUMN_AOD" in calls
    assert meta["cams_spectral_aod_exact_reuse"] is False
    assert meta["cams_tile_count"] == 5


def test_gfs_native_merge_batches_missing_canonical_columns_without_fragmentation_warning():
    snapshot = pd.DataFrame({
        "point_id": ["p0", "p1"],
        # Existing provider value must win over the GFS fallback.
        "temperature_1000hPa": [299.0, np.nan],
    })
    native = pd.DataFrame({"point_id":["p0","p1"], "distance_km":[0.0,20.0]})
    for p in gfs_native.DEFAULT_PRESSURE_LEVELS_HPA:
        native[f"temperature_k_{p}hPa"] = [280.0 + p/1000.0, 281.0 + p/1000.0]
        native[f"relative_humidity_pct_{p}hPa"] = [70.0, 80.0]
        native[f"geopotential_height_m_{p}hPa"] = [100.0, 120.0]
        native[f"cloud_fraction_{p}hPa"] = [0.25, 0.50]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", PerformanceWarning)
        out = gfs_native.merge_native_into_snapshot(snapshot, native)
    assert not [w for w in caught if issubclass(w.category, PerformanceWarning)]
    assert out.loc[0, "temperature_1000hPa"] == 299.0
    assert out.loc[1, "temperature_1000hPa"] == 282.0
    p0 = gfs_native.DEFAULT_PRESSURE_LEVELS_HPA[-1]
    assert out.loc[0, f"cloud_cover_{p0}hPa"] == 25.0
    assert out.loc[1, f"cloud_cover_{p0}hPa"] == 50.0
    assert set(out["pressure_profile_primary_source"]) == {gfs_native.NATIVE_PROVIDER_NAME}


def test_analysis_integrity_accepts_explicit_cams_spectral_exact_reuse_provenance():
    from firecloud.case_integrity import build_analysis_integrity_audit
    cams = pd.DataFrame([
        {
            "request_role":"SPECTRAL_COLUMN_AOD",
            "final_status":"EXACT_SOURCE_REUSE",
            "exact_source_reuse":True,
            "exact_source_role":"AEROSOL_SCATTERING_COLUMN_PROPERTIES",
            "elapsed_seconds":0.0,
        }
    ])
    audit = build_analysis_integrity_audit({"cams_request_audit":cams})
    row = audit.loc[audit["check_id"].eq("CAMS_SPECTRAL_AOD_EXACT_REUSE_PROVENANCE")]
    assert len(row) == 1
    assert row.iloc[0]["status"] == "PASS"
