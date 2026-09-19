from pathlib import Path
import pandas as pd

import firecloud
from firecloud.case_integrity import build_analysis_integrity_audit, build_archive_integrity_audit, PASS
from firecloud.ice_microphysics_wyser_mass_geometry_closure import (
    SCIENCE_BASELINE,
    STEP3F_VERSION,
    build_wyser_mass_geometry_evidence,
    build_wyser_mass_geometry_gate,
    wyser_mass_geometry_contract_payload,
)

EVIDENCE = "ice_microphysics_wyser_mass_geometry_evidence.csv"
GATE = "ice_microphysics_wyser_mass_geometry_gate.csv"
CONTRACT = "ice_microphysics_wyser_mass_geometry_contract.json"


def test_release_identity_and_frozen_mode():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.30.13"
    assert STEP3F_VERSION == "R5.7.41.3.4.10.19"
    assert SCIENCE_BASELINE == "R5.7.41.2_SHADOW_COT_AB_FROZEN"


def test_geometry_lineage_is_corroborated_but_primary_numeric_eq5_is_not_overclaimed():
    ev = build_wyser_mass_geometry_evidence().set_index("evidence_id")
    assert ev.loc["WYSER_EQ5_GEOMETRY_LINEAGE", "pin_status"] == "CORROBORATED_SECONDARY_LINEAGE"
    assert "D=2.5*L^0.6" in ev.loc["WYSER_EQ5_GEOMETRY_LINEAGE", "value"]
    assert ev.loc["WYSER_EQ5_PRIMARY_NUMERIC_EQUATION", "pin_status"] == "UNRESOLVED_PRIMARY_EQUATION_IMAGE"


def test_eq6_mass_size_and_mass_closure_remain_fail_closed():
    g = build_wyser_mass_geometry_gate().iloc[0]
    assert bool(g["WYSER_EQ5_GEOMETRY_LINEAGE_CORROBORATED"]) is True
    assert bool(g["WYSER_EQ5_PRIMARY_NUMERIC_EQUATION_PINNED"]) is False
    assert bool(g["WYSER_EQ6_MASS_SIZE_PRIMARY_NUMERIC_PINNED"]) is False
    assert bool(g["ABSOLUTE_PSD_RECONSTRUCTION_EXECUTABLE"]) is False
    assert bool(g["PSD_MASS_CLOSURE_VALIDATION_PASS"]) is False
    assert bool(g["WYSER_L_TO_YANG_DMAX_COORDINATE_VALIDATED"]) is False
    assert bool(g["PRODUCTION_ICE_OPTICS_READY"]) is False
    assert bool(g["physics_promotion_allowed"]) is False
    assert g["qualification_state"] == "WYSER_GEOMETRY_LINEAGE_CORROBORATED_PRIMARY_MASS_SIZE_CLOSURE_BLOCKED"


def test_contract_forbids_secondary_lineage_from_becoming_exact_primary_geometry_or_mass_size():
    c = wyser_mass_geometry_contract_payload(physicscore_version=firecloud.__version__)
    assert c["contract_version"] == "FIRECLOUD_ICE_WYSER_MASS_GEOMETRY_CLOSURE_QUALIFICATION_V1"
    assert c["wyser_eq5_geometry_lineage_corroborated"] is True
    assert c["wyser_eq5_primary_numeric_equation_pinned"] is False
    assert c["wyser_eq6_mass_size_primary_numeric_pinned"] is False
    assert c["absolute_psd_reconstruction_executable"] is False
    assert c["psd_mass_closure_validation_pass"] is False
    assert c["wyser_L_to_yang_dmax_coordinate_validated"] is False
    forbidden = set(c["forbidden_shortcuts"])
    assert "secondary_D_2p5_L_0p6_promoted_as_primary_Wyser_equation_5" in forbidden
    assert "corrupt_equation_6_OCR_used_as_numeric_mass_size_contract" in forbidden
    assert "mass_closure_claimed_without_exact_primary_m_of_L" in forbidden


def _analysis_result():
    ev = build_wyser_mass_geometry_evidence()
    gate = build_wyser_mass_geometry_gate(ev)
    return {
        "ice_microphysics_wyser_mass_geometry_required": True,
        "v1_ice_microphysics_wyser_mass_geometry_evidence": ev,
        "v1_ice_microphysics_wyser_mass_geometry_gate": gate,
        "ice_microphysics_wyser_mass_geometry_contract": wyser_mass_geometry_contract_payload(
            physicscore_version=firecloud.__version__
        ),
    }


def test_analysis_integrity_step3f_gates_pass_and_fail_closed():
    audit = build_analysis_integrity_audit(_analysis_result()).set_index("check_id")
    for check in (
        "ICE_MICROPHYSICS_WYSER_MASS_GEOMETRY_EVIDENCE_PRESENT",
        "ICE_MICROPHYSICS_WYSER_MASS_GEOMETRY_CONTRACT_FREEZE",
        "ICE_MICROPHYSICS_WYSER_MASS_GEOMETRY_FAIL_CLOSED",
    ):
        assert audit.loc[check, "status"] == PASS


def test_case_archive_requires_nonempty_step3f_artifacts():
    manifest = pd.DataFrame([
        {"artifact": EVIDENCE, "row_count": 10, "byte_size": 6000},
        {"artifact": GATE, "row_count": 1, "byte_size": 1200},
        {"artifact": CONTRACT, "row_count": float("nan"), "byte_size": 1800},
    ])
    audit = build_archive_integrity_audit(manifest, pd.DataFrame()).set_index("check_id")
    assert audit.loc["ARCHIVE_CONTENT::ICE_MICROPHYSICS_WYSER_MASS_GEOMETRY_EVIDENCE_NONEMPTY", "status"] == PASS
    assert audit.loc["ARCHIVE_CONTENT::ICE_MICROPHYSICS_WYSER_MASS_GEOMETRY_GATE_NONEMPTY", "status"] == PASS
    assert audit.loc["ARCHIVE_CONTENT::ICE_MICROPHYSICS_WYSER_MASS_GEOMETRY_CONTRACT_NONEMPTY", "status"] == PASS


def test_app_rebuilds_step3f_static_evidence_for_case_export():
    app = Path(__file__).resolve().parents[1].joinpath("app.py").read_text(encoding="utf-8")
    assert "_case_wyser_mass_geometry_evidence = build_wyser_mass_geometry_evidence()" in app
    assert "_case_wyser_mass_geometry_gate = build_wyser_mass_geometry_gate(" in app
    assert "_case_wyser_mass_geometry_contract = wyser_mass_geometry_contract_payload(" in app
    assert f'(\"{EVIDENCE}\", _case_wyser_mass_geometry_evidence)' in app
    assert f'(\"{GATE}\", _case_wyser_mass_geometry_gate)' in app
    assert f'(\"{CONTRACT}\", _case_wyser_mass_geometry_contract)' in app
