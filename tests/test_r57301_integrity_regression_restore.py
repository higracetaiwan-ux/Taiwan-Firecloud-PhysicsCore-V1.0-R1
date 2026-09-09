import pandas as pd

from firecloud.case_integrity import build_analysis_integrity_audit


def _geometry():
    return pd.DataFrame([
        {"time":"t0","solar_altitude_deg":-1.0,"canvas_id":"c1","cloud_layer_id":"l1","photographic_target_eligible":True},
        {"time":"t0","solar_altitude_deg":-1.0,"canvas_id":"c2","cloud_layer_id":"l2","photographic_target_eligible":True},
    ])


def _native_ready():
    return pd.DataFrame({"field":["RWMR","SNMR","GRLE"],"status":["READY","READY","READY"]})


def test_partial_precipitation_target_coverage_cannot_pass_integrity():
    audit = build_analysis_integrity_audit({
        "gfs_native_field_completeness": _native_ready(),
        "v1_viewing_path_geometry": _geometry(),
        "v1_viewing_precipitation_evidence": pd.DataFrame([
            {"time":"t0","solar_altitude_deg":-1.0,"canvas_id":"c1","view_precipitation_status":"VIEW_PRECIPITATION_OPTICS_RESOLVED"}
        ]),
    })
    status = audit.set_index("check_id")["status"].to_dict()
    assert status["VIEWING_PRECIPITATION_TARGET_COVERAGE"] == "FAIL"
    assert status["VIEWING_NATIVE_HYDROMETEOR_HANDOFF"] == "FAIL"


def test_volume_unresolved_cannot_pass_when_native_hydrometeors_ready():
    audit = build_analysis_integrity_audit({
        "gfs_native_field_completeness": _native_ready(),
        "v1_viewing_path_geometry": _geometry(),
        "v1_viewing_precipitation_evidence": pd.DataFrame([
            {"time":"t0","solar_altitude_deg":-1.0,"canvas_id":"c1","view_precipitation_status":"VIEW_PRECIPITATION_OPTICS_RESOLVED"},
            {"time":"t0","solar_altitude_deg":-1.0,"canvas_id":"c2","view_precipitation_status":"VIEW_PRECIPITATION_VOLUME_UNRESOLVED"},
        ]),
    })
    status = audit.set_index("check_id")["status"].to_dict()
    assert status["VIEWING_PRECIPITATION_TARGET_COVERAGE"] == "PASS"
    assert status["VIEWING_NATIVE_HYDROMETEOR_HANDOFF"] == "FAIL"
