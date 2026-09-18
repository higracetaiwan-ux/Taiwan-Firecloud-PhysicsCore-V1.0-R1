from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)


def test_step3q4_h_domain_constraints_narrow_band25_and_keep_band24_fail_closed():
    e = build_fu96_rrtmg_band_weighting_provenance_evidence()
    status = dict(zip(e.check_id, e.status))
    assert status["FU96_LINEAGE_H_DOMAIN_VALUES_CHOU1998"] == "PASS_QUALIFIED"
    assert status["FU96_LINEAGE_H_DOMAIN_VALUES_CHOU2002"] == "PASS_QUALIFIED"
    assert status["RRTMG_BAND25_H_DOMAIN_CONSTRAINT"] == "PASS_QUALIFIED"
    assert status["RRTMG_BAND24_H_DOMAIN_BOUNDARY_CROSSING"] == "PASS_QUALIFIED"
    assert status["RRTMG_BAND25_EXACT_H_FOR_ARCHIVED_TABLE"] == "BLOCKED_NOT_PROVEN"

    g = build_fu96_rrtmg_band_weighting_provenance_gate(e).iloc[0]
    assert g["qualification_state"] == "PASS_FAIL_CLOSED_POST_AVERAGED_ARCHIVE_BOUNDARY_QUALIFIED_EXACT_GENERATOR_UNRECOVERED"
    assert bool(g["FU96_HISTORICAL_H_DOMAIN_CONSTRAINTS_QUALIFIED"]) is True
    assert bool(g["RRTMG_BAND25_FULLY_WITHIN_FU_LINEAGE_H1_DOMAIN"]) is True
    assert bool(g["RRTMG_BAND24_CROSSES_FU_LINEAGE_H_DOMAIN_BOUNDARY"]) is True
    assert bool(g["RRTMG_BAND24_SINGLE_H_ASSIGNMENT_JUSTIFIED"]) is False
    assert bool(g["RRTMG_BAND25_EXACT_ARCHIVED_GENERATOR_H_PROVEN"]) is False
    assert bool(g["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"]) is False

    p = fu96_rrtmg_band_weighting_provenance_contract_payload(evidence=e, gate=build_fu96_rrtmg_band_weighting_provenance_gate(e))
    assert p["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_5"
    q = p["qualified_weighting_semantic_class"]
    assert q["fu_lineage_h_domains"]["0.175_to_0.700_um"] == 1.0
    assert q["fu_lineage_h_domains"]["0.700_to_1.220_um"] == "2/3"
    assert q["rrtmg_band24_single_h_assignment_allowed"] is False
    assert q["rrtmg_band25_exact_archived_generator_h_proven"] is False
