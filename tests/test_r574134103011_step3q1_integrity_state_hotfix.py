from firecloud.case_integrity import build_analysis_integrity_audit
from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)


def test_step3q1_current_fail_closed_state_is_accepted_by_integrity_gate():
    evidence = build_fu96_rrtmg_band_weighting_provenance_evidence()
    gate = build_fu96_rrtmg_band_weighting_provenance_gate(evidence)
    contract = fu96_rrtmg_band_weighting_provenance_contract_payload(evidence=evidence, gate=gate)
    result = {
        "ice_microphysics_fu96_rrtmg_band_weighting_provenance_required": True,
        "v1_ice_microphysics_fu96_rrtmg_band_weighting_provenance_evidence": evidence,
        "v1_ice_microphysics_fu96_rrtmg_band_weighting_provenance_gate": gate,
        "ice_microphysics_fu96_rrtmg_band_weighting_provenance_contract": contract,
    }
    audit = build_analysis_integrity_audit(result).set_index("check_id")
    row = audit.loc["ICE_MICROPHYSICS_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_FAIL_CLOSED"]
    assert row["status"] == "PASS"
    assert "PASS_FAIL_CLOSED_V25_OFFICIAL_SCIENTIFIC_SOURCE_SEMANTIC_EQUIVALENCE_QUALIFIED_ORIGINAL_TARBALL_BYTES_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED" in row["observed"]
