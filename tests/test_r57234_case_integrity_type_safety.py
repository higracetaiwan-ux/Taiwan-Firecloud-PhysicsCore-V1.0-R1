import math
import pandas as pd

from firecloud.case_integrity import build_analysis_integrity_audit


def _minimal_result(cams_req: pd.DataFrame):
    return {
        "route_points": pd.DataFrame({"bearing_deg": [0.0], "direction_offset_deg": [0.0], "distance_km": [0.0]}),
        "route_reference_contract": pd.DataFrame({
            "route_invariant_to_runtime_angle_set": [True],
            "reference_azimuth_deg": [0.0],
            "route_domain_max_km": [0.0],
        }),
        "hourly_raw": pd.DataFrame({"time": ["2026-09-08T00:00:00Z"]}),
        "gfs_native_request_audit": pd.DataFrame({"status": ["OK"]}),
        "gfs_grib_message_inventory": pd.DataFrame({"message": [1]}),
        "gfs_native_field_completeness": pd.DataFrame({"field": ["CLWMR", "ICMR"]}),
        "native_cloud_voxel_matrix": pd.DataFrame({"x": [1]}),
        "cams_request_audit": cams_req,
        "ozone_profile_route_snapshots": pd.DataFrame(),
        "aerosol_spectral_route_snapshots": pd.DataFrame(),
        "gas_profile_route_snapshots": pd.DataFrame(),
        "v1_formation": pd.DataFrame({"state": ["MISSING"]}),
        "v1_viewing_summary": pd.DataFrame(),
        "performance_diagnostics": pd.DataFrame({"stage": ["x"]}),
        "v1_canvas_candidates": pd.DataFrame(),
        "v1_spectral_optical_paths": pd.DataFrame(),
        "details": {"0.0": {}},
    }


def test_cams_role_success_tolerates_float_and_nan_role_cells():
    cams = pd.DataFrame({
        "role": ["O3_PRESSURE_LEVEL", math.nan, 532.0],
        "variable": [math.nan, "ozone", 532.0],
        "status": ["OK", "CAMS_ADS_TIMEOUT", "CAMS_ADS_TIMEOUT"],
    })
    audit = build_analysis_integrity_audit(_minimal_result(cams))
    assert not audit.empty
    assert "ANALYSIS_INTEGRITY_OVERALL" in set(audit["check_id"])


def test_cams_timeout_is_audited_not_raised_with_numeric_optional_fields():
    cams = pd.DataFrame({
        "role": ["NATIVE_AEROSOL_532NM_PRESSURE_LEVEL"],
        "chain": [math.nan],
        "dataset_role": [532.0],
        "status": ["CAMS_ADS_TIMEOUT"],
        "elapsed_s": [90.0],
    })
    audit = build_analysis_integrity_audit(_minimal_result(cams))
    assert len(audit) > 0
    # The integrity builder may WARN/FAIL evidence handoff, but must return a table.
    assert audit["status"].isin(["PASS", "FAIL", "WARN", "ALLOWED_EMPTY", "NOT_APPLICABLE"]).all()


def test_gfs_completeness_text_join_tolerates_numeric_and_nan_cells():
    r = _minimal_result(pd.DataFrame({"role": ["O3_PRESSURE_LEVEL"], "status": ["OK"]}))
    r["gfs_native_field_completeness"] = pd.DataFrame({
        "field": ["CLWMR", math.nan],
        "variable": [1.0, "ICMR"],
        "parameter": [math.nan, 2.0],
    })
    audit = build_analysis_integrity_audit(r)
    checks = set(audit["check_id"])
    assert "GFS_CLWMR_COMPLETENESS_ROW" in checks
    assert "GFS_ICMR_COMPLETENESS_ROW" in checks
