import pandas as pd
from firecloud.case_integrity import PASS, FAIL, WARN, build_analysis_integrity_audit


def _result():
    spectral = pd.DataFrame({
        "wavelength_nm": [550,575,600,650,700,750],
        "tau_gas": [0.1]*6,
        "tau_aerosol": [0.02]*6,
        "missing_components": [""]*6,
    })
    return {
        "route_points": pd.DataFrame({"distance_km":[0,5]}),
        "hourly_raw": pd.DataFrame({"time":[1]}),
        "gfs_native_request_audit": pd.DataFrame({"status":["OK"]}),
        "gfs_grib_message_inventory": pd.DataFrame({"short_name":["CLWMR","ICMR"]}),
        "gfs_native_field_completeness": pd.DataFrame({"field":["CLWMR","ICMR"]}),
        "native_cloud_voxel_matrix": pd.DataFrame({"distance_km":[0]}),
        "cams_request_audit": pd.DataFrame({"role":["O3_PRESSURE_LEVEL","SPECTRAL_AOD"], "status":["OK","OK"]}),
        "ozone_profile_route_snapshots": pd.DataFrame({"o3_mole_fraction":[1e-8,2e-8], "o3_quality":["CAMS_O3_PROFILE","CAMS_O3_PROFILE"]}),
        "gas_profile_route_snapshots": pd.DataFrame({"temperature_k":[290,280],"h2o_mole_fraction":[.01,.005],"o2_mole_fraction":[.20946,.20946],"o3_quality":["CAMS_O3_PROFILE"]*2,"gas_profile_source":["GFS+CAMS_O3"]*2}),
        "aerosol_spectral_route_snapshots": pd.DataFrame({"aod550":[.1,.2],"aod600":[.09,.18],"aod650":[.08,.16],"aod700":[.07,.14],"aod750":[.06,.12]}),
        "v1_canvas_candidates": pd.DataFrame({"canvas_id":["c1"]}),
        "v1_spectral_optical_paths": spectral,
        "v1_formation": pd.DataFrame({"solar_altitude_deg":[0]}),
        "v1_viewing_summary": pd.DataFrame({"status":["READY"]}),
        "performance_diagnostics": pd.DataFrame({"stage":["TOTAL"]}),
        "details": {0:{"native_provider_metadata":{"native_status":"FULL_NATIVE_MICROPHYSICS"}}},
    }


def status(audit, cid):
    return audit.loc[audit.check_id.eq(cid), "status"].iloc[0]


def test_good_payloads_pass():
    a=build_analysis_integrity_audit(_result())
    assert status(a,"CAMS_REQUEST_AUDIT_PRESENT") == PASS
    assert status(a,"CAMS_O3_ROUTE_PAYLOAD_VALIDITY") == PASS
    assert status(a,"CAMS_AEROSOL_SPECTRAL_PAYLOAD_VALIDITY") == PASS
    assert status(a,"GAS_CORE_PAYLOAD_VALIDITY") == PASS
    assert status(a,"ANALYSIS_INTEGRITY_OVERALL") == PASS


def test_o3_table_present_but_all_numeric_payload_missing_is_hard_fail():
    r=_result(); r["ozone_profile_route_snapshots"] = pd.DataFrame({"o3_mole_fraction":[None,None],"o3_number_density_m3":[None,None],"o3_quality":["CAMS_O3_MISSING"]*2})
    r["gas_profile_route_snapshots"]["o3_quality"]="CAMS_O3_MISSING"; r["gas_profile_route_snapshots"]["gas_profile_source"]="GFS+O3_MISSING+HITRAN"
    a=build_analysis_integrity_audit(r)
    assert status(a,"CAMS_O3_ROUTE_HANDOFF") == PASS
    assert status(a,"CAMS_O3_ROUTE_PAYLOAD_VALIDITY") == FAIL
    assert status(a,"CAMS_O3_QUALITY_MISSING_FRACTION") == FAIL
    assert status(a,"ANALYSIS_INTEGRITY_OVERALL") == FAIL


def test_blank_cams_request_audit_cannot_silently_coexist_with_missing_o3_payload():
    r=_result(); r["cams_request_audit"] = pd.DataFrame(); r["ozone_profile_route_snapshots"] = pd.DataFrame({"o3_mole_fraction":[None],"o3_quality":["CAMS_O3_MISSING"]}); r["gas_profile_route_snapshots"]["o3_quality"]="CAMS_O3_MISSING"; r["gas_profile_route_snapshots"]["gas_profile_source"]="GFS+O3_MISSING"
    a=build_analysis_integrity_audit(r)
    assert status(a,"CAMS_REQUEST_AUDIT_PRESENT") == FAIL
    assert status(a,"ANALYSIS_INTEGRITY_OVERALL") == FAIL


def test_empty_aerosol_payload_with_aerosol_missing_on_all_target_paths_is_hard_fail():
    r=_result(); r["aerosol_spectral_route_snapshots"] = pd.DataFrame(); r["v1_spectral_optical_paths"]["tau_aerosol"] = None; r["v1_spectral_optical_paths"]["missing_components"] = "AEROSOL"
    a=build_analysis_integrity_audit(r)
    assert status(a,"CAMS_AEROSOL_SPECTRAL_PAYLOAD_VALIDITY") == FAIL
    assert status(a,"ANALYSIS_INTEGRITY_OVERALL") == FAIL


def test_partial_o3_payload_warns_but_is_not_all_missing_hard_failure():
    r=_result(); r["ozone_profile_route_snapshots"] = pd.DataFrame({"o3_mole_fraction":[1e-8,None],"o3_quality":["CAMS_O3_PROFILE","CAMS_O3_MISSING"]})
    a=build_analysis_integrity_audit(r)
    assert status(a,"CAMS_O3_ROUTE_PAYLOAD_VALIDITY") == WARN
