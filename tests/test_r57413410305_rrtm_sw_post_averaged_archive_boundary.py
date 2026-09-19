from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)


def test_step3q5_post_averaged_archive_boundary_is_pinned_and_fail_closed():
    e = build_fu96_rrtmg_band_weighting_provenance_evidence().set_index("check_id")
    assert e.loc["RRTM_SW_FU96_POST_AVERAGED_ARCHIVE_PINNED", "status"] == "PASS_QUALIFIED"
    assert e.loc["RRTM_SW_FU96_46_NODE_DGE_RUNTIME_GRID", "status"] == "PASS_QUALIFIED"
    assert e.loc["RRTM_SW_PREAVERAGING_FU96_GENERATOR_PRESENT_IN_PINNED_ARCHIVE", "status"] == "BLOCKED_NOT_PRESENT"
    assert e.loc["FINAL_TABLE_INVERSE_IDENTIFICATION_OF_H_OR_WEIGHTS", "status"] == "PASS_FORBIDDEN"
    g = build_fu96_rrtmg_band_weighting_provenance_gate(e.reset_index()).iloc[0]
    assert g["qualification_state"] == "PASS_FAIL_CLOSED_FU96_PRIMARY_0P700UM_BOUNDARY_AND_BAND24_NONASSOCIATIVE_REAVERAGING_BARRIER_QUALIFIED_EXACT_RRTM_BAND24_25_REALIZATION_UNRECOVERED"
    assert bool(g["RRTM_SW_POST_AVERAGED_ARCHIVE_BOUNDARY_QUALIFIED"]) is True
    assert bool(g["RRTM_SW_PREAVERAGING_GENERATOR_RECOVERED"]) is False
    assert bool(g["FINAL_TABLE_INVERSE_IDENTIFICATION_ALLOWED"]) is False
    assert bool(g["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"]) is False
    assert bool(g["TAU_ICE_PRODUCTION_ALLOWED"]) is False


def test_step3q5_contract_records_pinned_aer_archive_boundary():
    p = fu96_rrtmg_band_weighting_provenance_contract_payload()
    assert p["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_18"
    assert p["step_version"] == "R5.7.41.3.4.10.30.18"
    assert p["sources"]["aer_rrtm_sw_cldprop_blob_sha"] == "8632f7d1940285665b62fdbb30c69861924251da"
    q = p["qualified_weighting_semantic_class"]
    assert q["rrtm_sw_preaveraging_generator_recovered"] is False
    assert q["final_table_inverse_identification_allowed"] is False
    assert "inverse_identification_of_unique_h_or_weights_from_final_rrtm_tables" in p["forbidden_substitutes"]
