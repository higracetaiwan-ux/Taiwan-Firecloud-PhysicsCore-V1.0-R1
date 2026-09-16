from pathlib import Path
import pandas as pd
import firecloud

from firecloud.case_integrity import build_archive_integrity_audit, PASS, FAIL
from firecloud.ice_microphysics_gfsv16_scheme_pin import (
    build_gfsv16_scheme_pin_evidence,
    build_gfsv16_scheme_pin_gate,
    gfsv16_scheme_pin_contract_payload,
)


EVIDENCE = "ice_microphysics_gfsv16_scheme_pin_evidence.csv"
GATE = "ice_microphysics_gfsv16_scheme_pin_gate.csv"
CONTRACT = "ice_microphysics_gfsv16_scheme_pin_contract.json"


def _manifest(evidence_rows=8, gate_rows=1, contract_bytes=1024):
    return pd.DataFrame([
        {"artifact": EVIDENCE, "row_count": evidence_rows, "byte_size": 4096},
        {"artifact": GATE, "row_count": gate_rows, "byte_size": 1024},
        {"artifact": CONTRACT, "row_count": float("nan"), "byte_size": contract_bytes},
    ])


def test_release_version_and_static_step3b_payload_are_nonempty():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.16"
    evidence = build_gfsv16_scheme_pin_evidence()
    gate = build_gfsv16_scheme_pin_gate(evidence)
    contract = gfsv16_scheme_pin_contract_payload(physicscore_version=firecloud.__version__)
    assert len(evidence) >= 8
    assert len(gate) >= 1
    assert contract["contract_version"] == "FIRECLOUD_ICE_GFSV16_SCHEME_PIN_V1"
    assert contract["physicscore_version"] == firecloud.__version__


def test_archive_content_gate_rejects_exact_tws100_failure_shape():
    audit = build_archive_integrity_audit(
        _manifest(evidence_rows=0, gate_rows=0, contract_bytes=2),
        pd.DataFrame(),
    ).set_index("check_id")
    assert audit.loc[
        "ARCHIVE_CONTENT::ICE_MICROPHYSICS_GFSV16_SCHEME_PIN_EVIDENCE_NONEMPTY", "status"
    ] == FAIL
    assert audit.loc[
        "ARCHIVE_CONTENT::ICE_MICROPHYSICS_GFSV16_SCHEME_PIN_GATE_NONEMPTY", "status"
    ] == FAIL
    assert audit.loc[
        "ARCHIVE_CONTENT::ICE_MICROPHYSICS_GFSV16_SCHEME_PIN_CONTRACT_NONEMPTY", "status"
    ] == FAIL
    # Presence-only checks would have passed in .10.15; the new content layer must not.
    assert audit.loc[f"ARCHIVE_MEMBER::{EVIDENCE}", "status"] == PASS
    assert audit.loc[f"ARCHIVE_MEMBER::{GATE}", "status"] == PASS
    assert audit.loc[f"ARCHIVE_MEMBER::{CONTRACT}", "status"] == PASS


def test_archive_content_gate_accepts_nonempty_step3b_payload():
    audit = build_archive_integrity_audit(_manifest(), pd.DataFrame()).set_index("check_id")
    assert audit.loc[
        "ARCHIVE_CONTENT::ICE_MICROPHYSICS_GFSV16_SCHEME_PIN_EVIDENCE_NONEMPTY", "status"
    ] == PASS
    assert audit.loc[
        "ARCHIVE_CONTENT::ICE_MICROPHYSICS_GFSV16_SCHEME_PIN_GATE_NONEMPTY", "status"
    ] == PASS
    assert audit.loc[
        "ARCHIVE_CONTENT::ICE_MICROPHYSICS_GFSV16_SCHEME_PIN_CONTRACT_NONEMPTY", "status"
    ] == PASS


def test_app_case_export_rebuilds_step3b_static_evidence_from_running_release():
    app = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
    assert "_case_gfsv16_scheme_pin_evidence = build_gfsv16_scheme_pin_evidence()" in app
    assert "_case_gfsv16_scheme_pin_gate = build_gfsv16_scheme_pin_gate(" in app
    assert "_case_gfsv16_scheme_pin_contract = gfsv16_scheme_pin_contract_payload(" in app
    assert '("ice_microphysics_gfsv16_scheme_pin_evidence.csv", _case_gfsv16_scheme_pin_evidence)' in app
    assert '("ice_microphysics_gfsv16_scheme_pin_gate.csv", _case_gfsv16_scheme_pin_gate)' in app
    assert '("ice_microphysics_gfsv16_scheme_pin_contract.json", _case_gfsv16_scheme_pin_contract)' in app
