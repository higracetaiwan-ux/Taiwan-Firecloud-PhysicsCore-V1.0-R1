from pathlib import Path
import pandas as pd

import firecloud
from firecloud.case_integrity import build_analysis_integrity_audit, build_archive_integrity_audit, PASS
from firecloud.ice_microphysics_wyser_psd_geometry_contract import (
    SCIENCE_BASELINE,
    STEP3E_VERSION,
    build_wyser_psd_geometry_evidence,
    build_wyser_psd_geometry_gate,
    wyser_psd_geometry_contract_payload,
)

EVIDENCE = "ice_microphysics_wyser_psd_geometry_evidence.csv"
GATE = "ice_microphysics_wyser_psd_geometry_gate.csv"
CONTRACT = "ice_microphysics_wyser_psd_geometry_contract.json"


def test_release_identity_and_frozen_mode():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.30.18.2"
    assert STEP3E_VERSION == "R5.7.41.3.4.10.18"
    assert SCIENCE_BASELINE == "R5.7.41.2_SHADOW_COT_AB_FROZEN"


def test_absolute_psd_normalization_is_pinned_from_primary_wyser_contract():
    ev = build_wyser_psd_geometry_evidence().set_index("evidence_id")
    assert ev.loc["WYSER_PSD_AMPLITUDE_IWC_NORMALIZATION", "pin_status"] == "PINNED_PRIMARY_EQUATIONS_7_8"
    assert "A=IWC/integral" in ev.loc["WYSER_PSD_AMPLITUDE_IWC_NORMALIZATION", "value"]
    assert ev.loc["WYSER_MIXED_PSD_SHAPE_FUNCTION", "pin_status"] == "PINNED_PIECEWISE_SHAPE"
    assert ev.loc["WYSER_MIXED_BRANCH_CONTINUITY_FACTOR", "pin_status"] == "PINNED_ANALYTIC_FROM_CONTINUITY"


def test_geometry_and_l_to_dmax_remain_fail_closed():
    g = build_wyser_psd_geometry_gate().iloc[0]
    assert bool(g["WYSER_IWC_AMPLITUDE_NORMALIZATION_RULE_PINNED"]) is True
    assert bool(g["WYSER_EXACT_COLUMN_WIDTH_LAW_PINNED"]) is False
    assert bool(g["WYSER_L_TO_YANG_DMAX_COORDINATE_VALIDATED"]) is False
    assert bool(g["BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE"]) is False
    assert bool(g["PRODUCTION_ICE_OPTICS_READY"]) is False
    assert bool(g["physics_promotion_allowed"]) is False
    assert g["qualification_state"] == "WYSER_NORMALIZATION_RULE_PINNED_EXECUTION_GEOMETRY_BLOCKED"


def test_contract_rejects_secondary_geometry_substitution_and_direct_l_equals_dmax():
    c = wyser_psd_geometry_contract_payload(physicscore_version=firecloud.__version__)
    assert c["contract_version"] == "FIRECLOUD_ICE_WYSER_PSD_GEOMETRY_QUALIFICATION_V1"
    assert c["wyser_iwc_amplitude_normalization_rule_pinned"] is True
    assert c["absolute_psd_reconstruction_executable"] is False
    assert c["wyser_exact_column_width_law_pinned"] is False
    assert c["wyser_L_to_yang_dmax_coordinate_validated"] is False
    forbidden = set(c["forbidden_shortcuts"])
    assert "secondary_column_width_law_substituted_for_Wyser_equation_5" in forbidden
    assert "Wyser_L_silently_equal_to_Yang_Bi_Dmax" in forbidden
    assert "PSD_amplitude_selected_without_IWC_mass_closure" in forbidden


def _analysis_result():
    ev = build_wyser_psd_geometry_evidence()
    gate = build_wyser_psd_geometry_gate(ev)
    return {
        "ice_microphysics_wyser_psd_geometry_required": True,
        "v1_ice_microphysics_wyser_psd_geometry_evidence": ev,
        "v1_ice_microphysics_wyser_psd_geometry_gate": gate,
        "ice_microphysics_wyser_psd_geometry_contract": wyser_psd_geometry_contract_payload(
            physicscore_version=firecloud.__version__
        ),
    }


def test_analysis_integrity_step3e_gates_pass_and_fail_closed():
    audit = build_analysis_integrity_audit(_analysis_result()).set_index("check_id")
    for check in (
        "ICE_MICROPHYSICS_WYSER_PSD_GEOMETRY_EVIDENCE_PRESENT",
        "ICE_MICROPHYSICS_WYSER_PSD_GEOMETRY_CONTRACT_FREEZE",
        "ICE_MICROPHYSICS_WYSER_PSD_GEOMETRY_FAIL_CLOSED",
    ):
        assert audit.loc[check, "status"] == PASS


def test_case_archive_requires_nonempty_step3e_artifacts():
    manifest = pd.DataFrame([
        {"artifact": EVIDENCE, "row_count": 12, "byte_size": 6000},
        {"artifact": GATE, "row_count": 1, "byte_size": 1200},
        {"artifact": CONTRACT, "row_count": float("nan"), "byte_size": 1800},
    ])
    audit = build_archive_integrity_audit(manifest, pd.DataFrame()).set_index("check_id")
    assert audit.loc["ARCHIVE_CONTENT::ICE_MICROPHYSICS_WYSER_PSD_GEOMETRY_EVIDENCE_NONEMPTY", "status"] == PASS
    assert audit.loc["ARCHIVE_CONTENT::ICE_MICROPHYSICS_WYSER_PSD_GEOMETRY_GATE_NONEMPTY", "status"] == PASS
    assert audit.loc["ARCHIVE_CONTENT::ICE_MICROPHYSICS_WYSER_PSD_GEOMETRY_CONTRACT_NONEMPTY", "status"] == PASS


def test_app_rebuilds_step3e_static_evidence_for_case_export():
    app = Path(__file__).resolve().parents[1].joinpath("app.py").read_text(encoding="utf-8")
    assert "_case_wyser_psd_geometry_evidence = build_wyser_psd_geometry_evidence()" in app
    assert "_case_wyser_psd_geometry_gate = build_wyser_psd_geometry_gate(" in app
    assert "_case_wyser_psd_geometry_contract = wyser_psd_geometry_contract_payload(" in app
    assert f'("{EVIDENCE}", _case_wyser_psd_geometry_evidence)' in app
    assert f'("{GATE}", _case_wyser_psd_geometry_gate)' in app
    assert f'("{CONTRACT}", _case_wyser_psd_geometry_contract)' in app
