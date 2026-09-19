import json
from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)

EXPECTED_STATE = "PASS_FAIL_CLOSED_FU96_PRIMARY_BAND_FORWARD_RECONSTRUCTION_INPUTS_QUALIFIED_RRTMG_FINE_GRID_AND_EXACT_BAND24_25_REALIZATION_UNRECOVERED"

def test_step3q16_evidence_scope_is_pinned_and_narrow():
    e=build_fu96_rrtmg_band_weighting_provenance_evidence().set_index("check_id")
    assert e.loc["AER_RRTM_BAND_GEN_IMPORTED_SVN_HISTORY_PINNED","status"] == "PASS_PINNED"
    assert e.loc["AER_RRTM_BAND_GEN_INITIAL_ORIGINAL_RRTM_WORK_COMMIT_PINNED","status"] == "PASS_PINNED"
    assert e.loc["AER_HISTORICAL_RRTM_MOLECULAR_BAND_GENERATION_PIPELINE_SCOPE","status"] == "PASS_QUALIFIED"
    assert e.loc["AER_HISTORICAL_RRTM_BAND_GENERATION_PIPELINE_IS_FU96_CLOUD_PREAVERAGING_GENERATOR","status"] == "PASS_FORBIDDEN"

def test_step3q16_gate_recovers_molecular_pipeline_but_not_fu96_cloud_generator():
    g=build_fu96_rrtmg_band_weighting_provenance_gate().iloc[0]
    assert g["qualification_state"] == EXPECTED_STATE
    assert bool(g["AER_HISTORICAL_RRTM_MOLECULAR_BAND_GENERATION_PIPELINE_RECOVERED"]) is True
    assert bool(g["AER_HISTORICAL_RRTM_BAND_GENERATION_PIPELINE_IS_FU96_CLOUD_PREAVERAGING_GENERATOR"]) is False
    assert bool(g["FU96_CLOUD_PREAVERAGING_GENERATOR_RECOVERED"]) is False
    assert bool(g["RRTM_SW_PREAVERAGING_GENERATOR_RECOVERED"]) is False
    assert bool(g["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"]) is False
    assert bool(g["PRODUCTION_ICE_OPTICS_READY"]) is False

def test_step3q16_contract_identity_and_fail_closed_scope():
    p=fu96_rrtmg_band_weighting_provenance_contract_payload()
    assert p["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_21"
    assert p["step_version"] == "R5.7.41.3.4.10.30.21"
    assert p["qualification_state"] == EXPECTED_STATE
    assert p["production_guards"]["physics_promotion_allowed"] is False
    blob=json.dumps(p,sort_keys=True)
    assert "rrtmgp-band-generation" in blob
    assert "FU96_CLOUD_PREAVERAGING_GENERATOR_RECOVERED" in blob
