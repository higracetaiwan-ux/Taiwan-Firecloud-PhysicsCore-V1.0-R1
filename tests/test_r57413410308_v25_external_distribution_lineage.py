from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)


def test_v25_external_distribution_lineage_is_pinned_without_promoting_original_tarball_identity():
    e = build_fu96_rrtmg_band_weighting_provenance_evidence().set_index("check_id")
    assert e.loc["RRTM_SW_V25_EXTERNAL_DISTRIBUTION_MIRROR_PINNED", "status"] == "PASS_PINNED"
    assert e.loc["RRTM_SW_V25_UPDATE_NOTE_IDENTITY", "status"] == "PASS_PINNED"
    assert e.loc["RRTM_SW_V25_MAKEFILE_VERSION_IDENTITY", "status"] == "PASS_PINNED"
    assert e.loc["RRTM_SW_V25_CLDPROP_CVS_PROVENANCE", "status"] == "PASS_PINNED"
    assert e.loc["RRTM_SW_V25_CLDPROP_SCIENCE_CONTENT_EQUIVALENCE_TO_AER_ARCHIVE", "status"] == "PASS_QUALIFIED"
    assert e.loc["RRTM_SW_V25_EXTERNAL_MIRROR_ORIGINAL_AER_TARBALL_BYTE_IDENTITY", "status"] == "BLOCKED_NOT_PROVEN"


def test_v25_runtime_kurucz_low_high_resolution_distinction_is_fail_closed():
    e = build_fu96_rrtmg_band_weighting_provenance_evidence().set_index("check_id")
    assert e.loc["RRTM_SW_V25_RUNTIME_KURUCZ_LOW_HIGH_RESOLUTION_DISTINCTION", "status"] == "PASS_QUALIFIED"
    assert e.loc["RRTM_SW_V25_EXTERNAL_DISTRIBUTION_PREAVERAGING_GENERATOR_RECOVERY", "status"] == "BLOCKED_NOT_PRESENT"


def test_step3q8_gate_remains_closed():
    g = build_fu96_rrtmg_band_weighting_provenance_gate().iloc[0]
    assert g["qualification_state"] == "PASS_FAIL_CLOSED_AER_RRTM_SW_TO_RRTMG_SW_FU96_FINAL_TABLE_CONTINUITY_QUALIFIED_ORIGINAL_TARBALL_BYTES_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED"
    assert bool(g["RRTM_SW_V25_EXTERNAL_DISTRIBUTION_MIRROR_PINNED"]) is True
    assert bool(g["RRTM_SW_V25_CLDPROP_CVS_PROVENANCE_PINNED"]) is True
    assert bool(g["RRTM_SW_V25_CLDPROP_SCIENCE_CONTENT_EQUIVALENCE_QUALIFIED"]) is True
    assert bool(g["RRTM_SW_V25_RUNTIME_KURUCZ_LOW_HIGH_RESOLUTION_DISTINCTION_QUALIFIED"]) is True
    assert bool(g["RRTM_SW_V25_EXTERNAL_DISTRIBUTION_CONTAINS_PREAVERAGING_GENERATOR"]) is False
    assert bool(g["RRTM_SW_V25_EXTERNAL_MIRROR_ORIGINAL_AER_TARBALL_BYTE_IDENTITY_PROVEN"]) is False
    assert bool(g["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"]) is False
    assert bool(g["PRODUCTION_ICE_OPTICS_READY"]) is False


def test_step3q8_contract_forbids_runtime_sfluxref_substitution():
    p = fu96_rrtmg_band_weighting_provenance_contract_payload()
    assert p["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_15"
    assert p["step_version"] == "R5.7.41.3.4.10.30.15"
    q = p["qualified_weighting_semantic_class"]
    assert q["v25_external_distribution_lineage_qualified"] is True
    assert q["v25_external_mirror_original_aer_tarball_byte_identity_proven"] is False
    assert q["v25_runtime_kurucz_low_high_resolution_distinction_qualified"] is True
    assert q["v25_runtime_sfluxref_equated_to_cloud_table_high_resolution_weights"] is False
    assert "treating_v25_runtime_low_resolution_kurucz_sfluxref_as_exact_cloud_table_high_resolution_weights" in p["forbidden_substitutes"]
