from pathlib import Path


def test_step3q_model_handoff_present():
    text = Path("firecloud/model.py").read_text(encoding="utf-8")
    assert "build_ice_microphysics_fu96_rrtmg_band_weighting_provenance_evidence" in text
    assert '"v1_ice_microphysics_fu96_rrtmg_band_weighting_provenance_evidence"' in text
    assert '"ice_microphysics_fu96_rrtmg_band_weighting_provenance_required": True' in text


def test_step3q_app_case_archive_handoff_present():
    text = Path("app.py").read_text(encoding="utf-8")
    assert "ice_microphysics_fu96_rrtmg_band_weighting_provenance_evidence.csv" in text
    assert "ice_microphysics_fu96_rrtmg_band_weighting_provenance_gate.csv" in text
    assert "ice_microphysics_fu96_rrtmg_band_weighting_provenance_contract.json" in text
    assert "serialize_fu96_rrtmg_band_weighting_provenance_contract_json_bytes" in text


def test_step3q_integrity_handoff_present():
    text = Path("firecloud/case_integrity.py").read_text(encoding="utf-8")
    assert "ICE_MICROPHYSICS_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_EVIDENCE_PRESENT" in text
    assert "ICE_MICROPHYSICS_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_FAIL_CLOSED" in text
    assert "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_15" in text
    assert "PASS_FAIL_CLOSED_AER_RRTM_SW_TO_RRTMG_SW_FU96_FINAL_TABLE_CONTINUITY_QUALIFIED_ORIGINAL_TARBALL_BYTES_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED" in text
    assert "PASS_FAIL_CLOSED_EXACT_WEIGHTING_PROVENANCE_UNRESOLVED" not in text
