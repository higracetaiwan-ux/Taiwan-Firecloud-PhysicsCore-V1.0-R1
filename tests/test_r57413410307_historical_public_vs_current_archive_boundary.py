from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)


def test_historical_public_release_existence_is_separate_from_current_availability():
    e = build_fu96_rrtmg_band_weighting_provenance_evidence().set_index("check_id")
    assert e.loc["RRTMG_SW_CURRENT_PRE_V5_PUBLIC_RELEASE_AVAILABILITY", "status"] == "PASS_QUALIFIED"
    assert e.loc["RRTM_SW_V24_HISTORICALLY_PUBLIC_2002", "status"] == "PASS_PINNED"
    assert e.loc["RRTM_SW_V25_HISTORICAL_USE_2006", "status"] == "PASS_PINNED"


def test_current_unavailability_does_not_erase_historical_publication_or_unlock_generator():
    e = build_fu96_rrtmg_band_weighting_provenance_evidence()
    g = build_fu96_rrtmg_band_weighting_provenance_gate(e).iloc[0]
    assert g["qualification_state"] == "PASS_FAIL_CLOSED_V25_EXTERNAL_DISTRIBUTION_LINEAGE_QUALIFIED_PREAVERAGING_GENERATOR_UNRECOVERED"
    assert bool(g["RRTMG_SW_PRE_V5_CURRENT_PUBLIC_RELEASES_AVAILABLE"]) is False
    assert bool(g["RRTM_SW_V24_HISTORICALLY_PUBLIC_2002"]) is True
    assert bool(g["RRTM_SW_V25_HISTORICAL_USE_2006"]) is True
    assert bool(g["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"]) is False
    assert bool(g["PRODUCTION_ICE_OPTICS_READY"]) is False


def test_step3q7_contract_version_and_semantics():
    p = fu96_rrtmg_band_weighting_provenance_contract_payload()
    assert p["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_8"
    assert p["step_version"] == "R5.7.41.3.4.10.30.8"
    q = p["qualified_weighting_semantic_class"]
    assert q["rrtmg_sw_pre_v5_current_public_releases_available"] is False
    assert q["rrtm_sw_v24_historically_public_2002"] is True
    assert q["rrtm_sw_v25_historical_use_2006"] is True
    assert q["rrtm_sw_preaveraging_generator_recovered"] is False
