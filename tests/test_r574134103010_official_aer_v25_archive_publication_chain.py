from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)

EXPECTED_STATE = "PASS_FAIL_CLOSED_FU96_PRIMARY_0P700UM_BOUNDARY_AND_BAND24_NONASSOCIATIVE_REAVERAGING_BARRIER_QUALIFIED_EXACT_RRTM_BAND24_25_REALIZATION_UNRECOVERED"


def test_step3q10_official_aer_v25_archive_filename_and_web_build_chain_are_pinned():
    e = build_fu96_rrtmg_band_weighting_provenance_evidence().set_index("check_id")
    assert e.loc["AER_OFFICIAL_RRTM_SW_V25_SOURCE_ARCHIVE_FILENAME_PUBLISHED", "status"] == "PASS_PINNED"
    assert "aer_rrtm_sw_v2.5.tar.gz" in e.loc["AER_OFFICIAL_RRTM_SW_V25_SOURCE_ARCHIVE_FILENAME_PUBLISHED", "observed"]
    assert e.loc["AER_OFFICIAL_RRTM_SW_WEB_TAR_BUILD_PROCEDURE", "status"] == "PASS_PINNED"
    assert "script_build_rrtm_sw.pl" in e.loc["AER_OFFICIAL_RRTM_SW_WEB_TAR_BUILD_PROCEDURE", "observed"]


def test_step3q10_publication_chain_does_not_promote_original_tarball_byte_identity_or_generator():
    e = build_fu96_rrtmg_band_weighting_provenance_evidence()
    g = build_fu96_rrtmg_band_weighting_provenance_gate(e).iloc[0]
    assert bool(g["RRTM_SW_V25_OFFICIAL_ARCHIVE_PUBLICATION_CHAIN_QUALIFIED"]) is True
    assert bool(g["AER_OFFICIAL_RRTM_SW_V25_ARCHIVE_BYTES_RECOVERED"]) is False
    assert bool(g["AER_OFFICIAL_RRTM_SW_V25_ARCHIVE_HASH_RECOVERED"]) is False
    assert bool(g["RRTM_SW_V25_EXTERNAL_MIRROR_ORIGINAL_AER_TARBALL_BYTE_IDENTITY_PROVEN"]) is False
    assert bool(g["RRTM_SW_PREAVERAGING_GENERATOR_RECOVERED"]) is False
    assert bool(g["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"]) is False
    assert bool(g["TAU_ICE_PRODUCTION_ALLOWED"]) is False


def test_step3q10_contract_identity_and_fail_closed_state():
    p = fu96_rrtmg_band_weighting_provenance_contract_payload()
    assert p["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_18"
    assert p["step_version"] == "R5.7.41.3.4.10.30.18"
    assert p["qualification_state"] == EXPECTED_STATE
    assert p["sources"]["aer_rrtm_sw_v25_source_archive_filename"] == "aer_rrtm_sw_v2.5.tar.gz"
    assert p["qualified_weighting_semantic_class"]["v25_original_aer_archive_hash_recovered"] is False
