from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)

EXPECTED_STATE = "PASS_FAIL_CLOSED_V25_OFFICIAL_SCIENTIFIC_SOURCE_SEMANTIC_EQUIVALENCE_QUALIFIED_ORIGINAL_TARBALL_BYTES_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED"


def test_step3q11_official_2004_history_and_cvs_normalized_equivalence_are_pinned():
    e = build_fu96_rrtmg_band_weighting_provenance_evidence().set_index("check_id")
    assert e.loc["AER_OFFICIAL_RRTM_SW_V25_CLDPROP_2004_HISTORY_PINNED", "status"] == "PASS_PINNED"
    assert "2004-04-15T18:42:10Z" in e.loc["AER_OFFICIAL_RRTM_SW_V25_CLDPROP_2004_HISTORY_PINNED", "observed"]
    assert e.loc["AER_OFFICIAL_RRTM_SW_V25_TAUMOLDIS_2004_HISTORY_PINNED", "status"] == "PASS_PINNED"
    assert "2004-04-15T18:50:57Z" in e.loc["AER_OFFICIAL_RRTM_SW_V25_TAUMOLDIS_2004_HISTORY_PINNED", "observed"]
    assert e.loc["RRTM_SW_V25_CLDPROP_CVS_NORMALIZED_OFFICIAL_MIRROR_EQUIVALENCE", "status"] == "PASS_QUALIFIED"
    assert "2080" in e.loc["RRTM_SW_V25_CLDPROP_CVS_NORMALIZED_OFFICIAL_MIRROR_EQUIVALENCE", "observed"]
    assert e.loc["RRTM_SW_V25_TAUMOLDIS_CVS_NORMALIZED_OFFICIAL_MIRROR_EQUIVALENCE", "status"] == "PASS_QUALIFIED"
    assert "2054" in e.loc["RRTM_SW_V25_TAUMOLDIS_CVS_NORMALIZED_OFFICIAL_MIRROR_EQUIVALENCE", "observed"]


def test_step3q11_source_tree_equivalence_promotes_lineage_only_not_archive_or_physics():
    e = build_fu96_rrtmg_band_weighting_provenance_evidence()
    g = build_fu96_rrtmg_band_weighting_provenance_gate(e).iloc[0]
    assert bool(g["RRTM_SW_V25_OFFICIAL_SOURCE_TREE_CVS_NORMALIZED_EQUIVALENCE_QUALIFIED"]) is True
    assert bool(g["RRTM_SW_V25_CLDPROP_CVS_NORMALIZED_OFFICIAL_MIRROR_EQUIVALENCE_QUALIFIED"]) is True
    assert bool(g["RRTM_SW_V25_TAUMOLDIS_CVS_NORMALIZED_OFFICIAL_MIRROR_EQUIVALENCE_QUALIFIED"]) is True
    assert bool(g["AER_OFFICIAL_RRTM_SW_V25_ARCHIVE_BYTES_RECOVERED"]) is False
    assert bool(g["AER_OFFICIAL_RRTM_SW_V25_ARCHIVE_HASH_RECOVERED"]) is False
    assert bool(g["RRTM_SW_V25_EXTERNAL_MIRROR_ORIGINAL_AER_TARBALL_BYTE_IDENTITY_PROVEN"]) is False
    assert bool(g["RRTM_SW_PREAVERAGING_GENERATOR_RECOVERED"]) is False
    assert bool(g["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"]) is False
    assert bool(g["PRODUCTION_ICE_OPTICS_READY"]) is False


def test_step3q11_contract_identity_and_fail_closed_state():
    p = fu96_rrtmg_band_weighting_provenance_contract_payload()
    assert p["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_13"
    assert p["step_version"] == "R5.7.41.3.4.10.30.13"
    assert p["qualification_state"] == EXPECTED_STATE
    assert p["qualified_weighting_semantic_class"]["v25_official_source_tree_cvs_normalized_equivalence_qualified"] is True
    assert p["qualified_weighting_semantic_class"]["v25_official_source_tree_equivalence_is_original_tarball_byte_identity"] is False
    assert p["production_guards"]["tau_ice_production_allowed"] is False
