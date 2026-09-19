from pathlib import Path

from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)
from tools.verify_rrtm_sw_v25_scientific_source_semantics import (
    SCIENTIFIC_SOURCE_PATHS,
    compare_trees,
)

EXPECTED_STATE = "PASS_FAIL_CLOSED_V25_PRE2020_CROSS_REPOSITORY_CRITICAL_FU96_RAW_BLOB_REPLICATION_QUALIFIED_ORIGINAL_TARBALL_BYTES_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED"


def test_step3q13_scientific_source_set_and_operational_deltas_are_pinned():
    e = build_fu96_rrtmg_band_weighting_provenance_evidence().set_index("check_id")
    assert e.loc["AER_OFFICIAL_RRTM_SW_V25_SCIENTIFIC_SOURCE_SET_MANIFEST_PINNED", "status"] == "PASS_PINNED"
    assert "26 Fortran" in e.loc["AER_OFFICIAL_RRTM_SW_V25_SCIENTIFIC_SOURCE_SET_MANIFEST_PINNED", "observed"]
    assert e.loc["RRTM_SW_V25_SCIENTIFIC_SOURCE_SET_CVS_NORMALIZED_FULL_FILE_MATCH", "status"] == "PASS_QUALIFIED"
    assert "24 of 26" in e.loc["RRTM_SW_V25_SCIENTIFIC_SOURCE_SET_CVS_NORMALIZED_FULL_FILE_MATCH", "observed"]
    assert e.loc["RRTM_SW_V25_RRTATM_OPERATIONAL_ONLY_DELTA_QUALIFIED", "status"] == "PASS_QUALIFIED"
    assert "three" in e.loc["RRTM_SW_V25_RRTATM_OPERATIONAL_ONLY_DELTA_QUALIFIED", "observed"]
    assert e.loc["RRTM_SW_V25_RRTM_INPUT_FILENAME_OPERATIONAL_ONLY_DELTA_QUALIFIED", "status"] == "PASS_QUALIFIED"
    assert "INPUT_RRTM" in e.loc["RRTM_SW_V25_RRTM_INPUT_FILENAME_OPERATIONAL_ONLY_DELTA_QUALIFIED", "observed"]
    assert e.loc["RRTM_SW_V25_SCIENTIFIC_SOURCE_SEMANTIC_EQUIVALENCE", "status"] == "PASS_QUALIFIED"


def test_step3q13_semantic_equivalence_promotes_lineage_only_and_stays_fail_closed():
    g = build_fu96_rrtmg_band_weighting_provenance_gate().iloc[0]
    assert bool(g["AER_OFFICIAL_RRTM_SW_V25_SCIENTIFIC_SOURCE_SET_MANIFEST_PINNED"]) is True
    assert bool(g["RRTM_SW_V25_SCIENTIFIC_SOURCE_SET_CVS_NORMALIZED_FULL_FILE_MATCH_24_OF_26_QUALIFIED"]) is True
    assert bool(g["RRTM_SW_V25_RRTATM_OPERATIONAL_ONLY_DELTA_QUALIFIED"]) is True
    assert bool(g["RRTM_SW_V25_RRTM_INPUT_FILENAME_OPERATIONAL_ONLY_DELTA_QUALIFIED"]) is True
    assert bool(g["RRTM_SW_V25_SCIENTIFIC_SOURCE_SEMANTIC_EQUIVALENCE_QUALIFIED"]) is True
    assert bool(g["RRTM_SW_V25_SCIENTIFIC_SOURCE_SEMANTIC_EQUIVALENCE_IS_FULL_RAW_BYTE_IDENTITY"]) is False
    assert bool(g["AER_OFFICIAL_RRTM_SW_V25_ARCHIVE_BYTES_RECOVERED"]) is False
    assert bool(g["AER_OFFICIAL_RRTM_SW_V25_ARCHIVE_HASH_RECOVERED"]) is False
    assert bool(g["RRTM_SW_PREAVERAGING_GENERATOR_RECOVERED"]) is False
    assert bool(g["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"]) is False
    assert bool(g["PRODUCTION_ICE_OPTICS_READY"]) is False
    p = fu96_rrtmg_band_weighting_provenance_contract_payload()
    assert p["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_14"
    assert p["step_version"] == "R5.7.41.3.4.10.30.14"
    assert p["qualification_state"] == EXPECTED_STATE
    assert p["qualified_weighting_semantic_class"]["v25_scientific_source_semantic_equivalence_qualified"] is True
    assert p["qualified_weighting_semantic_class"]["v25_scientific_source_semantic_equivalence_is_full_raw_byte_identity"] is False


def test_step3q13_semantic_verifier_accepts_only_documented_operational_deltas(tmp_path: Path):
    official = tmp_path / "official"
    mirror = tmp_path / "mirror"
    for rel in SCIENTIFIC_SOURCE_PATHS:
        (official / rel).parent.mkdir(parents=True, exist_ok=True)
        (mirror / rel).parent.mkdir(parents=True, exist_ok=True)
        base = "C     $Revision$\n      X = 1\n"
        (official / rel).write_text(base, encoding="utf-8")
        (mirror / rel).write_text("C     $Revision: 2.5 $\n      X = 1\n", encoding="utf-8")

    (official / "src/rrtatm.f").write_text(
        "C $Revision$\n      CALL LBLDAT(HDATE)\n      CALL FTIME (HTIME)\n      WRITE (IPR,900) HDATE,HTIME\n",
        encoding="utf-8",
    )
    (mirror / "src/rrtatm.f").write_text(
        "C $Revision: 2.5 $\n!      CALL LBLDAT(HDATE)\n!      CALL FTIME (HTIME)\n!      WRITE (IPR,900) HDATE,HTIME\n",
        encoding="utf-8",
    )
    (official / "src/rrtm.f").write_text(
        "C $Revision$\n      OPEN (IRD,FILE='INPUT_RRTM',FORM='FORMATTED')\n",
        encoding="utf-8",
    )
    (mirror / "src/rrtm.f").write_text(
        "C $Revision: 2.5 $\n      OPEN (IRD,FILE='input_rrtm_MLS',FORM='FORMATTED')\n",
        encoding="utf-8",
    )

    r = compare_trees(official, mirror)
    assert r["scientific_source_file_count"] == 26
    assert r["cvs_normalized_full_file_match_count"] == 24
    assert r["allowed_operational_delta_file_count"] == 2
    assert r["allowed_operational_delta_line_count"] == 4
    assert r["unexpected_delta_files"] == []
    assert r["scientific_source_semantic_equivalence_qualified"] is True
    assert r["whole_repository_equality_proven"] is False
    assert r["original_tarball_byte_identity_proven"] is False
