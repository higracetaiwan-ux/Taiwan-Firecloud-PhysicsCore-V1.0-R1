import math
import pandas as pd

from firecloud.case_integrity import PASS, _cams_role_success, build_analysis_integrity_audit


def _base_result(cams_audit: pd.DataFrame):
    return {
        "route_points": pd.DataFrame({
            "distance_km": [0.0, 20.0],
            "direction_offset_deg": [0.0, 0.0],
            "bearing_deg": [270.0, 270.0],
        }),
        "route_reference_contract": pd.DataFrame({
            "reference_azimuth_deg": [270.0],
            "route_domain_max_km": [20.0],
            "route_invariant_to_runtime_angle_set": [True],
        }),
        "hourly_raw": pd.DataFrame({"time": [1]}),
        "gfs_native_request_audit": pd.DataFrame({"status": ["OK_DOWNLOADED"]}),
        "gfs_grib_message_inventory": pd.DataFrame({"short_name": ["CLWMR", "ICMR"]}),
        "gfs_native_field_completeness": pd.DataFrame({"field": ["CLWMR", "ICMR"], "status": ["READY", "READY"]}),
        "native_cloud_voxel_matrix": pd.DataFrame({"distance_km": [0.0], "clwmr": [0.0], "icmr": [0.0]}),
        "gas_profile_route_snapshots": pd.DataFrame({"pressure_hpa": [1000.0]}),
        "ozone_profile_route_snapshots": pd.DataFrame({"o3_mole_fraction": [1e-8], "o3_quality": ["OK"]}),
        "cams_request_audit": cams_audit,
        "aerosol_spectral_route_snapshots": pd.DataFrame(),
        "v1_formation": pd.DataFrame({"solar_altitude_deg": [0.0]}),
        "v1_viewing_summary": pd.DataFrame({"status": ["VIEWING_CLEAR"]}),
        "performance_diagnostics": pd.DataFrame({"stage": ["TOTAL_ANALYSIS_CORE"]}),
        "v1_canvas_candidates": pd.DataFrame(),
        "v1_spectral_optical_paths": pd.DataFrame(),
        "details": {0.0: {"native_provider_metadata": {"native_status": "FULL_NATIVE_MICROPHYSICS"}}},
    }


def test_cams_role_success_accepts_mixed_float_nan_role_fields():
    audit = pd.DataFrame({
        "role": ["O3_PRESSURE_LEVEL", "SPECTRAL_COLUMN_AOD"],
        "variable": [575.0, math.nan],
        "product": [math.nan, 550.0],
        "status": ["OK", "OK"],
    })
    assert _cams_role_success(audit, ["O3", "OZONE"]) is True


def test_cams_role_timeout_is_incomplete_not_success_even_with_other_time_ok():
    audit = pd.DataFrame({
        "role": ["O3_PRESSURE_LEVEL", "O3_PRESSURE_LEVEL"],
        "variable": [575.0, 575.0],
        "status": ["OK", "CAMS_ADS_TIMEOUT"],
        "error": [math.nan, "CAMS_ADS_WALLCLOCK_DEADLINE_EXCEEDED_90S"],
    })
    assert _cams_role_success(audit, ["O3", "OZONE"]) is False


def test_analysis_integrity_survives_mixed_type_cams_audit_with_aerosol_timeout():
    cams = pd.DataFrame({
        "role": ["O3_PRESSURE_LEVEL", "NATIVE_AEROSOL_532NM_PRESSURE_LEVEL"],
        "variable": [575.0, 532.0],
        "pressure_level": [1000.0, math.nan],
        "status": ["OK", "CAMS_ADS_TIMEOUT"],
        "error": [math.nan, "CAMS_ADS_WALLCLOCK_DEADLINE_EXCEEDED_90S"],
    })
    out = build_analysis_integrity_audit(_base_result(cams))
    assert not out.empty
    timeout_row = out.loc[out["check_id"].eq("CAMS_PROVIDER_TIMEOUT_VISIBLE")].iloc[0]
    assert timeout_row["status"] == "WARN"
    assert int(timeout_row["observed"]) == 1
    overall = out.loc[out["check_id"].eq("ANALYSIS_INTEGRITY_OVERALL"), "status"].iloc[0]
    assert overall == PASS
