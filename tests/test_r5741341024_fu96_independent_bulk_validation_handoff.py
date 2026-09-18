from pathlib import Path

import pandas as pd

from firecloud.case_integrity import build_analysis_integrity_audit, build_archive_integrity_audit, PASS
from firecloud.ice_microphysics_fu96_independent_bulk_validation import (
    build_fu96_independent_bulk_validation_evidence,
    build_fu96_independent_bulk_validation_gate,
    fu96_independent_bulk_validation_contract_payload,
)

EVIDENCE = "ice_microphysics_fu96_independent_bulk_validation_evidence.csv"
GATE = "ice_microphysics_fu96_independent_bulk_validation_gate.csv"
CONTRACT = "ice_microphysics_fu96_independent_bulk_validation_contract.json"


def _analysis_result():
    evidence = build_fu96_independent_bulk_validation_evidence()
    gate = build_fu96_independent_bulk_validation_gate(evidence)
    return {
        "ice_microphysics_fu96_independent_bulk_validation_required": True,
        "v1_ice_microphysics_fu96_independent_bulk_validation_evidence": evidence,
        "v1_ice_microphysics_fu96_independent_bulk_validation_gate": gate,
        "ice_microphysics_fu96_independent_bulk_validation_contract": fu96_independent_bulk_validation_contract_payload(
            physicscore_version="1.0.0-R5.7.41.3.4.10.28.1"
        ),
    }


def test_analysis_integrity_step3k_presence_contract_and_fail_closed_gates_pass():
    audit = build_analysis_integrity_audit(_analysis_result()).set_index("check_id")
    for check_id in (
        "ICE_MICROPHYSICS_FU96_INDEPENDENT_BULK_VALIDATION_EVIDENCE_PRESENT",
        "ICE_MICROPHYSICS_FU96_INDEPENDENT_BULK_VALIDATION_CONTRACT_FREEZE",
        "ICE_MICROPHYSICS_FU96_INDEPENDENT_BULK_VALIDATION_FAIL_CLOSED",
    ):
        assert audit.loc[check_id, "status"] == PASS


def test_archive_content_integrity_requires_nonempty_step3k_artifacts():
    manifest = pd.DataFrame([
        {"artifact": EVIDENCE, "row_count": 11, "byte_size": 8000},
        {"artifact": GATE, "row_count": 1, "byte_size": 1800},
        {"artifact": CONTRACT, "row_count": float("nan"), "byte_size": 3500},
    ])
    audit = build_archive_integrity_audit(manifest, pd.DataFrame()).set_index("check_id")
    assert audit.loc["ARCHIVE_CONTENT::ICE_MICROPHYSICS_FU96_INDEPENDENT_BULK_VALIDATION_EVIDENCE_NONEMPTY", "status"] == PASS
    assert audit.loc["ARCHIVE_CONTENT::ICE_MICROPHYSICS_FU96_INDEPENDENT_BULK_VALIDATION_GATE_NONEMPTY", "status"] == PASS
    assert audit.loc["ARCHIVE_CONTENT::ICE_MICROPHYSICS_FU96_INDEPENDENT_BULK_VALIDATION_CONTRACT_NONEMPTY", "status"] == PASS


def test_model_and_app_wire_step3k_evidence_gate_contract_into_case_export():
    root = Path(__file__).resolve().parents[1]
    model = root.joinpath("firecloud", "model.py").read_text(encoding="utf-8")
    app = root.joinpath("app.py").read_text(encoding="utf-8")

    assert "build_ice_microphysics_fu96_independent_bulk_validation_evidence" in model
    assert '"ice_microphysics_fu96_independent_bulk_validation_required": True' in model
    assert '"v1_ice_microphysics_fu96_independent_bulk_validation_evidence"' in model
    assert '"v1_ice_microphysics_fu96_independent_bulk_validation_gate"' in model
    assert '"ice_microphysics_fu96_independent_bulk_validation_contract"' in model

    assert "_case_fu96_independent_bulk_validation_evidence = build_fu96_independent_bulk_validation_evidence()" in app
    assert "_case_fu96_independent_bulk_validation_gate = build_fu96_independent_bulk_validation_gate(" in app
    assert "_case_fu96_independent_bulk_validation_contract = fu96_independent_bulk_validation_contract_payload(" in app
    assert f'("{EVIDENCE}", _case_fu96_independent_bulk_validation_evidence)' in app
    assert f'("{GATE}", _case_fu96_independent_bulk_validation_gate)' in app
    assert f'("{CONTRACT}", _case_fu96_independent_bulk_validation_contract)' in app
