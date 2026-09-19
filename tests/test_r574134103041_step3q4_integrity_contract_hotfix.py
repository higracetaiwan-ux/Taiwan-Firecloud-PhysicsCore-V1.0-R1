from firecloud.case_integrity import build_analysis_integrity_audit
from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)

def test_step3q4_v14_contract_and_current_state_are_accepted_by_integrity_gate():
    evidence = build_fu96_rrtmg_band_weighting_provenance_evidence()
    gate = build_fu96_rrtmg_band_weighting_provenance_gate(evidence)
    contract = fu96_rrtmg_band_weighting_provenance_contract_payload(evidence=evidence, gate=gate)
    assert contract["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_13"
    result = {
        "ice_microphysics_fu96_rrtmg_band_weighting_provenance_required": True,
        "v1_ice_microphysics_fu96_rrtmg_band_weighting_provenance_evidence": evidence,
        "v1_ice_microphysics_fu96_rrtmg_band_weighting_provenance_gate": gate,
        "ice_microphysics_fu96_rrtmg_band_weighting_provenance_contract": contract,
    }
    audit = build_analysis_integrity_audit(result).set_index("check_id")
    contract_row = audit.loc["ICE_MICROPHYSICS_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_CONTRACT_FREEZE"]
    state_row = audit.loc["ICE_MICROPHYSICS_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_FAIL_CLOSED"]
    assert contract_row["status"] == "PASS"
    assert state_row["status"] == "PASS"
    assert "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_13" in contract_row["observed"]
    assert "PASS_FAIL_CLOSED_V25_OFFICIAL_SCIENTIFIC_SOURCE_SEMANTIC_EQUIVALENCE_QUALIFIED_ORIGINAL_TARBALL_BYTES_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED" in state_row["observed"]
