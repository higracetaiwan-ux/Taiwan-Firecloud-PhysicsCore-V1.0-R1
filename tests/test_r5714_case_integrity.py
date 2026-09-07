import pandas as pd

from firecloud.case_integrity import (
    PASS, FAIL, ALLOWED_EMPTY,
    build_analysis_integrity_audit,
    build_archive_integrity_audit,
)


def _base_result():
    return {
        "route_points": pd.DataFrame({"distance_km": [0, 20], "direction_offset_deg": [0.0, 0.0], "bearing_deg": [270.0, 270.0]}),
        "route_reference_contract": pd.DataFrame({"reference_azimuth_deg": [270.0], "route_domain_max_km": [20.0], "route_invariant_to_runtime_angle_set": [True]}),
        "hourly_raw": pd.DataFrame({"time": [1]}),
        "gfs_native_request_audit": pd.DataFrame({"status": ["OK_DOWNLOADED"]}),
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


def _status(audit, check_id):
    return audit.loc[audit["check_id"].eq(check_id), "status"].iloc[0]


def test_valid_no_canvas_case_passes_and_target_rt_empty_is_allowed():
    audit = build_analysis_integrity_audit(_base_result())
    assert _status(audit, "GFS_INVENTORY_HANDOFF") == PASS
    assert _status(audit, "GFS_COMPLETENESS_HANDOFF") == PASS
    assert _status(audit, "CAMS_O3_ROUTE_HANDOFF") == PASS
    assert _status(audit, "TARGET_DEPENDENT_SPECTRAL_EMPTY") == ALLOWED_EMPTY
    assert _status(audit, "ANALYSIS_INTEGRITY_OVERALL") == PASS


def test_successful_gfs_request_with_empty_inventory_is_hard_fail():
    result = _base_result()
    result["gfs_grib_message_inventory"] = pd.DataFrame()
    audit = build_analysis_integrity_audit(result)
    assert _status(audit, "GFS_INVENTORY_HANDOFF") == FAIL
    assert _status(audit, "ANALYSIS_INTEGRITY_OVERALL") == FAIL


def test_successful_gfs_request_with_empty_completeness_is_hard_fail():
    result = _base_result()
    result["gfs_native_field_completeness"] = pd.DataFrame()
    audit = build_analysis_integrity_audit(result)
    assert _status(audit, "GFS_COMPLETENESS_HANDOFF") == FAIL
    assert _status(audit, "ANALYSIS_INTEGRITY_OVERALL") == FAIL


def test_successful_cams_o3_request_with_missing_route_evidence_is_hard_fail():
    result = _base_result()
    result["ozone_profile_route_snapshots"] = pd.DataFrame()
    audit = build_analysis_integrity_audit(result)
    assert _status(audit, "CAMS_O3_ROUTE_HANDOFF") == FAIL
    assert _status(audit, "ANALYSIS_INTEGRITY_OVERALL") == FAIL


def test_archive_integrity_propagates_analysis_failure_and_checks_required_members():
    result = _base_result()
    result["gfs_grib_message_inventory"] = pd.DataFrame()
    analysis = build_analysis_integrity_audit(result)
    names = [
        "summary.csv", "route_reference_contract.csv", "route_points.csv", "forecast_raw.csv", "performance_diagnostics.csv",
        "gfs_native_request_audit.csv", "gfs_grib_message_inventory.csv", "gfs_native_field_completeness.csv",
        "v1_formation.csv", "v1_viewing_summary.csv", "analysis_integrity_audit.csv",
    ]
    manifest = pd.DataFrame({"artifact": names, "row_count": [1] * len(names), "byte_size": [10] * len(names), "sha256": ["x"] * len(names)})
    case = build_archive_integrity_audit(manifest, analysis)
    assert _status(case, "ANALYSIS_INTEGRITY_PROPAGATED") == FAIL
    assert _status(case, "CASE_ARCHIVE_INTEGRITY_OVERALL") == FAIL
