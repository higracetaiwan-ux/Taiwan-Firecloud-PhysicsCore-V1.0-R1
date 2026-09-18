from pathlib import Path


def test_step3p_model_handoff_present():
    text = Path("firecloud/model.py").read_text(encoding="utf-8")
    assert "build_ice_microphysics_yang_full_spectral_source_qualification_evidence" in text
    assert '"v1_ice_microphysics_yang_full_spectral_source_qualification_evidence"' in text
    assert '"ice_microphysics_yang_full_spectral_source_qualification_required": True' in text


def test_step3p_app_case_archive_handoff_present():
    text = Path("app.py").read_text(encoding="utf-8")
    assert "ice_microphysics_yang_full_spectral_source_qualification_evidence.csv" in text
    assert "ice_microphysics_yang_full_spectral_source_qualification_gate.csv" in text
    assert "ice_microphysics_yang_full_spectral_source_qualification_contract.json" in text
    assert "serialize_yang_full_spectral_source_qualification_contract_json_bytes" in text


def test_step3p_integrity_handoff_present():
    text = Path("firecloud/case_integrity.py").read_text(encoding="utf-8")
    assert "ICE_MICROPHYSICS_YANG_FULL_SPECTRAL_SOURCE_QUALIFICATION_EVIDENCE_PRESENT" in text
    assert "ICE_MICROPHYSICS_YANG_FULL_SPECTRAL_SOURCE_QUALIFICATION_FAIL_CLOSED" in text
    assert "ARCHIVE_CONTENT::ICE_MICROPHYSICS_YANG_FULL_SPECTRAL_SOURCE_QUALIFICATION_CONTRACT_NONEMPTY" in text
