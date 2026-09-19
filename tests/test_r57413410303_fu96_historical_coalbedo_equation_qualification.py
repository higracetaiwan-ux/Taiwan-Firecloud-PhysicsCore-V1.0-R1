from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)

def test_step3q3_historical_equation_family_is_pinned_but_h_is_fail_closed():
    e=build_fu96_rrtmg_band_weighting_provenance_evidence()
    status=dict(zip(e.check_id,e.status))
    assert status["FU96_LINEAGE_LINEAR_COALBEDO_EQUATION"] == "PASS_QUALIFIED"
    assert status["FU96_LINEAGE_LOG_COALBEDO_EQUATION"] == "PASS_QUALIFIED"
    assert status["FU96_LINEAGE_MIXED_COALBEDO_EQUATION"] == "PASS_QUALIFIED"
    assert status["FU96_LINEAGE_H_EMPIRICAL_SELECTION"] == "PASS_QUALIFIED"
    assert status["FU96_RRTMG_BAND24_25_H_VALUES"] == "BLOCKED_NOT_RECOVERED"
    g=build_fu96_rrtmg_band_weighting_provenance_gate(e).iloc[0]
    assert g["qualification_state"] == "PASS_FAIL_CLOSED_V25_OFFICIAL_SOURCE_TREE_CVS_NORMALIZED_EQUIVALENCE_QUALIFIED_ORIGINAL_TARBALL_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED"
    assert bool(g["FU96_HISTORICAL_COALBEDO_EQUATION_FAMILY_QUALIFIED"]) is True
    assert bool(g["FU96_HISTORICAL_BAND24_25_H_VALUES_RECOVERED"]) is False
    assert bool(g["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"]) is False
    p=fu96_rrtmg_band_weighting_provenance_contract_payload(evidence=e, gate=build_fu96_rrtmg_band_weighting_provenance_gate(e))
    assert p["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_11"
    q=p["qualified_weighting_semantic_class"]
    assert q["historical_fu96_band24_25_h_values_recovered"] is False
    assert q["historical_fu96_alpha_linear"].startswith("sum(alpha_lambda")
    assert q["historical_fu96_h_semantic"].startswith("empirical flux-calibration")
