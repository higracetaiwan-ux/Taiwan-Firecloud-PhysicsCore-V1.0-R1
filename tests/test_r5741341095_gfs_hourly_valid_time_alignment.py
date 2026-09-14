from datetime import datetime, timezone
import pandas as pd

from firecloud.providers.gfs_native import (
    _snap_gfs_0p25_forecast_hour,
    build_nomads_request,
    resolve_run_and_lead,
)
from firecloud.providers.gfs_canvas_optical_probe import build_nomads_request as build_pgrb2b_request
from firecloud.case_integrity import build_analysis_integrity_audit


def dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def test_tws106_event_resolves_06z_f004_not_f003():
    # The frozen analysis clock permits the 06Z cycle. The 10:00 UTC event
    # therefore has an exact f004 state and must not be rounded to f003.
    run, lead = resolve_run_and_lead(
        dt("2026-09-14T10:00:21Z"),
        now_utc=dt("2026-09-14T12:30:00Z"),
    )
    assert run == dt("2026-09-14T06:00:00Z")
    assert lead == 4
    resolved = run + pd.Timedelta(hours=lead)
    assert abs((resolved - dt("2026-09-14T10:00:21Z")).total_seconds()) == 21


def test_tws106_minus6_endpoint_still_uses_nearest_hourly_f004():
    run, lead = resolve_run_and_lead(
        dt("2026-09-14T10:26:48Z"),
        now_utc=dt("2026-09-14T12:30:00Z"),
    )
    assert run == dt("2026-09-14T06:00:00Z")
    assert lead == 4
    assert (run + pd.Timedelta(hours=lead)) == dt("2026-09-14T10:00:00Z")


def test_gfs_0p25_cadence_is_hourly_through_120_then_three_hourly():
    assert _snap_gfs_0p25_forecast_hour(4.01) == 4
    assert _snap_gfs_0p25_forecast_hour(119.4) == 119
    assert _snap_gfs_0p25_forecast_hour(120.0) == 120
    assert _snap_gfs_0p25_forecast_hour(121.6) == 123
    assert _snap_gfs_0p25_forecast_hour(124.4) == 123


def test_primary_and_pgrb2b_request_names_keep_same_hourly_lead():
    run = dt("2026-09-14T06:00:00Z")
    _, primary = build_nomads_request(run, 4, (120.0, 121.0, 23.0, 24.0), (1000, 500))
    _, supplement = build_pgrb2b_request(run, 4, (120.0, 121.0, 23.0, 24.0))
    assert primary["file"] == "gfs.t06z.pgrb2.0p25.f004"
    assert supplement["file"] == "gfs.t06z.pgrb2b.0p25.f004"


def _minimal_integrity_result(offset_seconds: float = -21.0):
    run = pd.Timestamp("2026-09-14T06:00:00Z")
    target = pd.Timestamp("2026-09-14T10:00:21Z")
    valid = pd.Timestamp("2026-09-14T10:00:00Z")
    return {
        "route_points": pd.DataFrame({"distance_km": [0.0], "direction_offset_deg": [0.0], "bearing_deg": [270.0]}),
        "route_reference_contract": pd.DataFrame({"reference_azimuth_deg": [270.0], "route_domain_max_km": [0.0], "route_invariant_to_runtime_angle_set": [True]}),
        "hourly_raw": pd.DataFrame({"time": [target]}),
        "gfs_native_valid_time_alignment_required": True,
        "gfs_native_request_audit": pd.DataFrame([{
            "status": "OK_DOWNLOADED",
            "gfs_run_utc": run.isoformat(),
            "gfs_forecast_hour": 4,
            "gfs_target_time_utc": target.isoformat(),
            "gfs_valid_time_utc": valid.isoformat(),
            "gfs_valid_time_offset_seconds": offset_seconds,
            "gfs_forecast_cadence_policy": "HOURLY_F000_F120_THEN_3HOURLY_F123_F384",
        }]),
        "gfs_grib_message_inventory": pd.DataFrame({"short_name": ["CLWMR", "ICMR"]}),
        "gfs_native_field_completeness": pd.DataFrame({"field": ["CLWMR", "ICMR"], "status": ["READY", "READY"]}),
        "native_cloud_voxel_matrix": pd.DataFrame({"distance_km": [0.0], "clwmr": [0.0], "icmr": [0.0]}),
        "gas_profile_route_snapshots": pd.DataFrame({"pressure_hpa": [1000.0]}),
        "ozone_profile_route_snapshots": pd.DataFrame({"o3_mole_fraction": [1e-8]}),
        "cams_request_audit": pd.DataFrame({"role": ["O3_PRESSURE_LEVEL"], "status": ["OK"]}),
        "v1_formation": pd.DataFrame({"solar_altitude_deg": [0.0]}),
        "v1_viewing_summary": pd.DataFrame({"status": ["VIEWING_CLEAR"]}),
        "performance_diagnostics": pd.DataFrame({"stage": ["TOTAL_ANALYSIS_CORE"]}),
        "v1_canvas_candidates": pd.DataFrame(),
        "v1_spectral_optical_paths": pd.DataFrame(),
        "details": {0.0: {"native_provider_metadata": {"native_status": "FULL_NATIVE_MICROPHYSICS"}}},
    }


def test_valid_time_alignment_integrity_passes_exact_provenance():
    audit = build_analysis_integrity_audit(_minimal_integrity_result())
    row = audit.loc[audit["check_id"].eq("GFS_NATIVE_VALID_TIME_ALIGNMENT")].iloc[0]
    assert row["status"] == "PASS"


def test_valid_time_alignment_integrity_rejects_inconsistent_offset():
    audit = build_analysis_integrity_audit(_minimal_integrity_result(offset_seconds=-3600.0))
    row = audit.loc[audit["check_id"].eq("GFS_NATIVE_VALID_TIME_ALIGNMENT")].iloc[0]
    assert row["status"] == "FAIL"
