import pandas as pd

import firecloud
from firecloud.case_integrity import build_analysis_integrity_audit, build_archive_integrity_audit, PASS, FAIL
from firecloud.ice_microphysics_capability import phase2_contract_payload


def _eligibility():
    false_cols = [
        "NATIVE_DMAX_AVAILABLE", "CALIBRATED_DMAX_MAPPING_AVAILABLE",
        "NATIVE_PSD_AVAILABLE", "CALIBRATED_PSD_MAPPING_AVAILABLE",
        "ICE_HABIT_RESOLUTION_READY", "ICE_ROUGHNESS_RESOLUTION_READY",
        "MICROPHYSICS_MAPPING_READY", "SINGLE_PARTICLE_LUT_LOOKUP_ELIGIBLE",
        "BULK_PSD_SYNTHESIS_ELIGIBLE", "PRODUCTION_ICE_OPTICS_READY",
        "physics_promotion_allowed",
    ]
    row = {c: False for c in false_cols}
    row.update({
        "eligibility_state": "INSUFFICIENT_MICROPHYSICS",
        "eligibility_blockers": (
            "ICE_DMAX_NATIVE_FIELD_UNAVAILABLE|ICE_DMAX_MAPPING_UNAVAILABLE|"
            "ICE_PSD_INPUT_INCOMPLETE|ICE_HABIT_UNRESOLVED|ICE_ROUGHNESS_UNRESOLVED"
        ),
    })
    return pd.DataFrame([row])


def _analysis_result():
    return {
        "ice_microphysics_phase2_required": True,
        "v1_ice_microphysics_native_input_capability_audit": pd.DataFrame([
            {"field_short_name": "ICMR", "eligibility_state": "NATIVE_INPUT_AVAILABLE_NO_PARTICLE_SIZE_SEMANTICS"}
        ]),
        "v1_ice_microphysics_phase2_mapping_eligibility": _eligibility(),
        "ice_microphysics_phase2_contract": phase2_contract_payload(physicscore_version=firecloud.__version__),
    }


def test_version_hotfix():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.30.5"


def test_phase2_analysis_integrity_gate_passes_fail_closed_contract():
    audit = build_analysis_integrity_audit(_analysis_result())
    phase2 = audit[audit.component.eq("ICE_MICROPHYSICS_PHASE2")]
    assert set(phase2.check_id) == {
        "ICE_MICROPHYSICS_PHASE2_EVIDENCE_PRESENT",
        "ICE_MICROPHYSICS_PHASE2_CONTRACT_FREEZE",
        "ICE_MICROPHYSICS_PHASE2_MAPPING_FAIL_CLOSED",
    }
    assert phase2.status.eq(PASS).all()


def test_phase2_analysis_integrity_gate_fails_when_contract_missing():
    result = _analysis_result()
    result["ice_microphysics_phase2_contract"] = {}
    audit = build_analysis_integrity_audit(result)
    status = audit.set_index("check_id").loc["ICE_MICROPHYSICS_PHASE2_EVIDENCE_PRESENT", "status"]
    assert status == FAIL


def test_case_archive_requires_all_three_phase2_evidence_members():
    required = [
        "ice_microphysics_native_input_capability_audit.csv",
        "ice_microphysics_phase2_mapping_eligibility.csv",
        "ice_microphysics_phase2_contract.json",
    ]
    manifest = pd.DataFrame({"artifact": required})
    audit = build_archive_integrity_audit(manifest, pd.DataFrame())
    indexed = audit.set_index("check_id")
    for name in required:
        assert indexed.loc[f"ARCHIVE_MEMBER::{name}", "status"] == PASS

    manifest_missing = pd.DataFrame({"artifact": required[:-1]})
    audit_missing = build_archive_integrity_audit(manifest_missing, pd.DataFrame()).set_index("check_id")
    assert audit_missing.loc["ARCHIVE_MEMBER::ice_microphysics_phase2_contract.json", "status"] == FAIL
