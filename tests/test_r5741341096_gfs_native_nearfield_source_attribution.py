import pandas as pd

from firecloud.gfs_native_nearfield_source_diagnostic import (
    build_gfs_native_nearfield_source_levels,
    summarize_gfs_native_nearfield_source_levels,
)
from firecloud.case_integrity import build_analysis_integrity_audit


def _snapshot(q=0.0, cf=0.0):
    row = {
        "point_id": "+0.0_0000", "distance_km": 0.0, "direction_offset_deg": 0.0,
        "model_surface_elevation_m": 0.0,
    }
    for p, z in [(1000,100.0),(975,300.0),(950,550.0),(925,800.0),(900,1050.0),(850,1550.0),(800,2050.0),(750,2550.0),(700,3050.0)]:
        row[f"geopotential_height_{p}hPa"] = z
        row[f"cloud_liquid_water_kgkg_{p}hPa"] = q
        row[f"cloud_ice_water_kgkg_{p}hPa"] = 0.0
        row[f"cloud_fraction_{p}hPa"] = cf
        row[f"relative_humidity_{p}hPa"] = 85.0
        row[f"temperature_{p}hPa"] = 290.0
    return pd.DataFrame([row])


def _meta():
    return {
        "gfs_run_utc": "2026-09-14T06:00:00+00:00", "gfs_forecast_hour": 4,
        "gfs_target_time_utc": "2026-09-14T10:00:21+00:00",
        "gfs_valid_time_utc": "2026-09-14T10:00:00+00:00",
        "gfs_valid_time_offset_seconds": -21.0,
        "gfs_forecast_cadence_policy": "HOURLY_F000_F120_THEN_3HOURLY_F123_F384",
        "gfs_file": "gfs.t06z.pgrb2.0p25.f004",
    }


def test_source_attribution_distinguishes_exact_zero_before_voxel_threshold():
    pts = build_gfs_native_nearfield_source_levels(
        _snapshot(q=0.0, cf=0.0), analysis_time="2026-09-14T18:00:21+08:00",
        solar_altitude_deg=0.0, provider_metadata=_meta(), pressure_levels_hpa=(1000,975,950,925,900,850,800,750,700),
    )
    assert not pts.empty
    assert pts.source_condensate_state.eq("SOURCE_CONDENSATE_EXACT_ZERO").all()
    assert pts.source_cloud_fraction_state.eq("SOURCE_CLOUD_FRACTION_EXACT_ZERO").all()
    sm = summarize_gfs_native_nearfield_source_levels(pts)
    assert sm.source_attribution_state.eq("LOW_LAYER_SOURCE_NATIVE_PRESSURE_LEVELS_EXACT_ZERO").all()


def test_source_attribution_distinguishes_below_threshold_from_zero():
    pts = build_gfs_native_nearfield_source_levels(
        _snapshot(q=5e-8, cf=0.1), provider_metadata=_meta(), pressure_levels_hpa=(1000,975,950),
    )
    assert pts.source_condensate_state.eq("SOURCE_CONDENSATE_POSITIVE_BELOW_ENVELOPE_THRESHOLD").all()
    sm = summarize_gfs_native_nearfield_source_levels(pts)
    assert sm.source_attribution_state.eq("LOW_LAYER_SOURCE_CONDENSATE_ONLY_BELOW_ENVELOPE_THRESHOLD").all()


def test_source_diagnostic_integrity_preserves_no_promotion():
    pts = build_gfs_native_nearfield_source_levels(
        _snapshot(q=0.0), provider_metadata=_meta(), pressure_levels_hpa=(1000,975,950),
    )
    sm = summarize_gfs_native_nearfield_source_levels(pts)
    audit = build_analysis_integrity_audit({
        "v1_gfs_native_nearfield_source_levels": pts,
        "v1_gfs_native_nearfield_source_summary": sm,
    })
    by = audit.set_index("check_id")["status"].to_dict()
    assert by["GFS_NATIVE_NEARFIELD_SOURCE_ATTRIBUTION"] == "PASS"
    assert by["GFS_NATIVE_NEARFIELD_SOURCE_ZERO_VS_THRESHOLD_VISIBLE"] == "PASS"
    assert by["GFS_NATIVE_NEARFIELD_SOURCE_SUMMARY"] == "PASS"
