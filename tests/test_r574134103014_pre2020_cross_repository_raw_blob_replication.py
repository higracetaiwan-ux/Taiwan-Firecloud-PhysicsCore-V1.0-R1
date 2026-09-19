from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    PYRRTM_SW_2014_CLDPROP_BLOB_SHA,
    PYRRTM_SW_2014_KGB24_BLOB_SHA,
    PYRRTM_SW_2014_KGB25_BLOB_SHA,
    PYRRTM_SW_2014_TAUMOLDIS_BLOB_SHA,
    RRTM_SW_V25_EXTERNAL_CLDPROP_BLOB_SHA,
    RRTM_SW_V25_EXTERNAL_IMPORT_KGB24_BLOB_SHA,
    RRTM_SW_V25_EXTERNAL_IMPORT_KGB25_BLOB_SHA,
    RRTM_SW_V25_EXTERNAL_IMPORT_TAUMOLDIS_BLOB_SHA,
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)
from tools.verify_rrtm_sw_v25_cross_repository_raw_blobs import (
    CRITICAL_FILENAMES,
    SCIENTIFIC_SOURCE_FILENAMES,
    compare_tree_manifests,
)

EXPECTED_STATE = "PASS_FAIL_CLOSED_V25_PRE2020_CROSS_REPOSITORY_CRITICAL_FU96_RAW_BLOB_REPLICATION_QUALIFIED_ORIGINAL_TARBALL_BYTES_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED"


def test_step3q14_pre2020_history_and_cross_repository_replication_are_qualified():
    e = build_fu96_rrtmg_band_weighting_provenance_evidence().set_index("check_id")
    assert e.loc["PYRRTM_SW_2014_PRE2020_HISTORY_PINNED", "status"] == "PASS_PINNED"
    assert "2014-07-14" in e.loc["PYRRTM_SW_2014_PRE2020_HISTORY_PINNED", "observed"]
    assert e.loc["RRTM_SW_V25_CROSS_REPOSITORY_RAW_BLOB_MATCH_22_OF_26", "status"] == "PASS_QUALIFIED"
    assert "22 of 26" in e.loc["RRTM_SW_V25_CROSS_REPOSITORY_RAW_BLOB_MATCH_22_OF_26", "observed"]
    assert e.loc["RRTM_SW_V25_CRITICAL_FU96_BAND24_25_RAW_BLOB_REPLICATION", "status"] == "PASS_QUALIFIED"
    assert e.loc["RRTM_SW_V25_CROSS_REPOSITORY_RAW_BLOB_REPLICATION_IS_ORIGINAL_AER_TARBALL_IDENTITY", "status"] == "PASS_FORBIDDEN"


def test_step3q14_critical_blobs_are_exactly_replicated_but_production_stays_closed():
    assert PYRRTM_SW_2014_CLDPROP_BLOB_SHA == RRTM_SW_V25_EXTERNAL_CLDPROP_BLOB_SHA
    assert PYRRTM_SW_2014_TAUMOLDIS_BLOB_SHA == RRTM_SW_V25_EXTERNAL_IMPORT_TAUMOLDIS_BLOB_SHA
    assert PYRRTM_SW_2014_KGB24_BLOB_SHA == RRTM_SW_V25_EXTERNAL_IMPORT_KGB24_BLOB_SHA
    assert PYRRTM_SW_2014_KGB25_BLOB_SHA == RRTM_SW_V25_EXTERNAL_IMPORT_KGB25_BLOB_SHA

    g = build_fu96_rrtmg_band_weighting_provenance_gate().iloc[0]
    assert g["qualification_state"] == EXPECTED_STATE
    assert bool(g["PYRRTM_SW_2014_PRE2020_HISTORY_PINNED"]) is True
    assert bool(g["RRTM_SW_V25_CROSS_REPOSITORY_RAW_BLOB_MATCH_22_OF_26_QUALIFIED"]) is True
    assert bool(g["RRTM_SW_V25_CRITICAL_FU96_BAND24_25_RAW_BLOB_REPLICATION_QUALIFIED"]) is True
    assert bool(g["RRTM_SW_V25_CROSS_REPOSITORY_RAW_BLOB_REPLICATION_IS_ORIGINAL_AER_TARBALL_IDENTITY"]) is False
    assert bool(g["AER_OFFICIAL_RRTM_SW_V25_ARCHIVE_BYTES_RECOVERED"]) is False
    assert bool(g["AER_OFFICIAL_RRTM_SW_V25_ARCHIVE_HASH_RECOVERED"]) is False
    assert bool(g["RRTM_SW_PREAVERAGING_GENERATOR_RECOVERED"]) is False
    assert bool(g["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"]) is False
    assert bool(g["PRODUCTION_ICE_OPTICS_READY"]) is False

    p = fu96_rrtmg_band_weighting_provenance_contract_payload()
    assert p["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_14"
    assert p["step_version"] == "R5.7.41.3.4.10.30.14"
    assert p["qualification_state"] == EXPECTED_STATE
    q = p["qualified_weighting_semantic_class"]
    assert q["v25_cross_repository_raw_blob_match_count"] == 22
    assert q["v25_cross_repository_raw_blob_nonmatch_count"] == 4
    assert q["v25_critical_fu96_band24_25_raw_blob_replication_qualified"] is True
    assert q["v25_cross_repository_raw_blob_replication_is_original_aer_tarball_identity"] is False


def test_step3q14_manifest_verifier_counts_22_of_26_and_keeps_archive_identity_false():
    left = []
    right = []
    unequal = {"RDI1MACH.f", "disort.f", "rrtatm.f", "rrtm.f"}
    for i, name in enumerate(SCIENTIFIC_SOURCE_FILENAMES):
        common = f"sha-{i:02d}"
        left.append({"path": f"sw/{name}", "type": "blob", "sha": common})
        right.append({"path": f"SW/src/{name}", "type": "blob", "sha": common if name not in unequal else f"other-{i:02d}"})
    r = compare_tree_manifests(left, right)
    assert r["scientific_source_file_count"] == 26
    assert r["raw_blob_match_count"] == 22
    assert r["raw_blob_nonmatch_count"] == 4
    assert set(r["raw_blob_nonmatch_files"]) == unequal
    assert r["critical_file_count"] == len(CRITICAL_FILENAMES) == 4
    assert r["critical_raw_blob_match_count"] == 4
    assert r["critical_raw_blob_replication_qualified"] is True
    assert r["original_aer_tarball_byte_identity_proven"] is False
    assert r["authoritative_original_archive_hash_recovered"] is False
