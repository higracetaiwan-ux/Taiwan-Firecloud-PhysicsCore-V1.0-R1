from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)


def test_step3q6_public_archive_boundary_fail_closed():
    e = build_fu96_rrtmg_band_weighting_provenance_evidence().set_index("check_id")
    assert e.loc["RRTMG_SW_CURRENT_PRE_V5_PUBLIC_RELEASE_AVAILABILITY", "status"] == "PASS_QUALIFIED"
    assert e.loc["PUBLIC_RUNTIME_ARCHIVE_SUFFICIENT_FOR_EXACT_HISTORICAL_GENERATOR", "status"] == "PASS_FAIL_CLOSED"
    g = build_fu96_rrtmg_band_weighting_provenance_gate(e.reset_index()).iloc[0]
    assert g["qualification_state"] == "PASS_FAIL_CLOSED_V25_EXTERNAL_DISTRIBUTION_LINEAGE_QUALIFIED_PREAVERAGING_GENERATOR_UNRECOVERED"
    assert bool(g["RRTMG_SW_PUBLIC_RELEASE_AVAILABILITY_BOUNDARY_QUALIFIED"]) is True
    assert bool(g["RRTMG_SW_PRE_V5_CURRENT_PUBLIC_RELEASES_AVAILABLE"]) is False
    assert bool(g["PUBLIC_RUNTIME_ARCHIVE_SUFFICIENT_FOR_EXACT_HISTORICAL_GENERATOR"]) is False
    assert bool(g["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"]) is False
    assert bool(g["PRODUCTION_ICE_OPTICS_READY"]) is False


def test_step3q6_contract_records_archive_availability_without_inference():
    p = fu96_rrtmg_band_weighting_provenance_contract_payload()
    assert p["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_8"
    assert p["step_version"] == "R5.7.41.3.4.10.30.8"
    assert p["qualified_weighting_semantic_class"]["rrtmg_sw_pre_v5_current_public_releases_available"] is False
    assert p["qualified_weighting_semantic_class"]["public_runtime_archive_sufficient_for_exact_historical_generator"] is False
    assert "treating_public_release_absence_as_generator_identity_evidence" in p["forbidden_substitutes"]
