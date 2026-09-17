from pathlib import Path

import pandas as pd
import firecloud

from firecloud.case_integrity import build_analysis_integrity_audit, build_archive_integrity_audit, PASS, FAIL
from firecloud.ice_microphysics_wyser_yang_bulk_contract import (
    SCIENCE_BASELINE,
    STEP3D_MODE,
    build_wyser_yang_bulk_evidence,
    build_wyser_yang_bulk_gate,
    wyser_yang_bulk_contract_payload,
)

EVIDENCE = "ice_microphysics_wyser_yang_bulk_evidence.csv"
GATE = "ice_microphysics_wyser_yang_bulk_gate.csv"
CONTRACT = "ice_microphysics_wyser_yang_bulk_contract.json"


def test_release_and_step3d_mode():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.21"
    assert SCIENCE_BASELINE == "R5.7.41.2_SHADOW_COT_AB_FROZEN"
    assert STEP3D_MODE == "WYSER_PSD_YANG_BI_HABIT_BULK_INTEGRATION_QUALIFICATION_ONLY"


def test_step3d_evidence_pins_only_what_sources_support():
    ev = build_wyser_yang_bulk_evidence().set_index("evidence_id")
    assert ev.loc["WYSER_MIXED_PSD_STRUCTURE", "pin_status"] == "PINNED_MIXED_GAMMA_POWERLAW"
    assert ev.loc["WYSER_SMALL_PARTICLE_GAMMA_PARAMETERS", "pin_status"] == "PINNED_NU3_LAMBDA0P3_SWITCH20UM"
    assert ev.loc["WYSER_DEFAULT_INTEGRATION_LIMITS", "pin_status"] == "PINNED_L10_L1000_UM"
    assert ev.loc["WYSER_POWERLAW_B_T_IWC_FORMULA", "pin_status"] == "PINNED_GFSV16_SOURCE_EQUIVALENT"
    assert ev.loc["WYSER_ABSOLUTE_PSD_NORMALIZATION", "pin_status"] == "UNRESOLVED"
    assert ev.loc["WYSER_HEX_COLUMN_ASPECT_RATIO_LAW", "pin_status"] == "UNRESOLVED_PRIMARY_CONTRACT"
    assert ev.loc["YANG_BI_SOLID_COLUMN_HABIT_CANDIDATE", "pin_status"] == "IDENTIFIED_NOT_VALIDATED"
    assert ev.loc["YANG_BI_DMAX_DOMAIN", "pin_status"] == "PINNED_DMAX_2_TO_10000_UM"
    assert ev.loc["BULK_INTEGRATION_NORMALIZATION", "pin_status"] == "PINNED_MATHEMATICAL_CONTRACT"
    assert ev.loc["ROUGHNESS_UNCERTAINTY_ENSEMBLE", "pin_status"] == "IDENTIFIED_NOT_VALIDATED"


def test_step3d_gate_keeps_bulk_integration_fail_closed():
    g = build_wyser_yang_bulk_gate().iloc[0]
    assert bool(g["WYSER_PSD_CORE_STRUCTURE_PINNED"])
    assert bool(g["WYSER_SMALL_PARTICLE_GAMMA_PINNED"])
    assert bool(g["WYSER_INTEGRATION_LIMITS_PINNED"])
    assert bool(g["WYSER_POWERLAW_B_FORMULA_PINNED"])
    assert not bool(g["WYSER_ABSOLUTE_PSD_NORMALIZATION_PINNED"])
    assert not bool(g["WYSER_COLUMN_GEOMETRY_PINNED"])
    assert bool(g["YANG_BI_SOLID_COLUMN_CANDIDATE_IDENTIFIED"])
    assert not bool(g["YANG_BI_HABIT_BRIDGE_VALIDATED"])
    assert not bool(g["YANG_BI_ROUGHNESS_BRIDGE_VALIDATED"])
    assert bool(g["BULK_INTEGRATION_NORMALIZATION_PINNED"])
    assert bool(g["SIX_BAND_BULK_OUTPUT_CONTRACT_PINNED"])
    assert not bool(g["BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE"])
    assert not bool(g["PRODUCTION_ICE_OPTICS_READY"])
    assert not bool(g["physics_promotion_allowed"])
    assert g["qualification_state"] == "WYSER_PSD_CORE_PINNED_GEOMETRY_HABIT_ROUGHNESS_BLOCKED"


def test_contract_defines_bulk_math_but_forbids_runtime_synthesis():
    c = wyser_yang_bulk_contract_payload(physicscore_version=firecloud.__version__)
    assert c["contract_version"] == "FIRECLOUD_ICE_WYSER_YANG_BULK_INTEGRATION_QUALIFICATION_V1"
    assert c["bulk_integration_math_pinned"] is True
    assert c["bulk_yang_bi_psd_integration_eligible"] is False
    assert c["production_ice_optics_ready"] is False
    assert c["physics_promotion_allowed"] is False
    assert c["wavelengths_nm"] == [550, 575, 600, 650, 700, 750]
    forbidden = set(c["forbidden_shortcuts"])
    assert {
        "Wyser_length_L_silently_treated_as_Yang_Bi_Dmax",
        "Wyser_hex_column_silently_treated_as_Yang_Bi_solid_column",
        "PSD_amplitude_invented_from_IWC_without_exact_contract",
        "single_roughness_state_silently_selected",
        "bulk_tau_synthesized_before_independent_validation",
    }.issubset(forbidden)
    math = c["bulk_integration_equations"]
    assert "beta_ext" in math and "beta_sca" in math and "g_bulk" in math and "k_ext" in math and "tau_ice" in math


def _result():
    ev = build_wyser_yang_bulk_evidence()
    gate = build_wyser_yang_bulk_gate(ev)
    return {
        "ice_microphysics_wyser_yang_bulk_required": True,
        "v1_ice_microphysics_wyser_yang_bulk_evidence": ev,
        "v1_ice_microphysics_wyser_yang_bulk_gate": gate,
        "ice_microphysics_wyser_yang_bulk_contract": wyser_yang_bulk_contract_payload(
            physicscore_version=firecloud.__version__
        ),
    }


def test_analysis_integrity_enforces_step3d_contract_and_fail_close():
    a = build_analysis_integrity_audit(_result()).set_index("check_id")
    ids = [
        "ICE_MICROPHYSICS_WYSER_YANG_BULK_EVIDENCE_PRESENT",
        "ICE_MICROPHYSICS_WYSER_YANG_BULK_CONTRACT_FREEZE",
        "ICE_MICROPHYSICS_WYSER_YANG_BULK_FAIL_CLOSED",
    ]
    assert all(a.loc[i, "status"] == PASS for i in ids)

    broken = _result()
    broken["ice_microphysics_wyser_yang_bulk_contract"] = {}
    b = build_analysis_integrity_audit(broken).set_index("check_id")
    assert b.loc[ids[0], "status"] == FAIL


def test_archive_requires_step3d_members_and_nonempty_content():
    manifest = pd.DataFrame([
        {"artifact": EVIDENCE, "row_count": 16, "byte_size": 7000},
        {"artifact": GATE, "row_count": 1, "byte_size": 1500},
        {"artifact": CONTRACT, "row_count": float("nan"), "byte_size": 2500},
    ])
    a = build_archive_integrity_audit(manifest, pd.DataFrame()).set_index("check_id")
    for name in (EVIDENCE, GATE, CONTRACT):
        assert a.loc[f"ARCHIVE_MEMBER::{name}", "status"] == PASS
    assert a.loc["ARCHIVE_CONTENT::ICE_MICROPHYSICS_WYSER_YANG_BULK_EVIDENCE_NONEMPTY", "status"] == PASS
    assert a.loc["ARCHIVE_CONTENT::ICE_MICROPHYSICS_WYSER_YANG_BULK_GATE_NONEMPTY", "status"] == PASS
    assert a.loc["ARCHIVE_CONTENT::ICE_MICROPHYSICS_WYSER_YANG_BULK_CONTRACT_NONEMPTY", "status"] == PASS


def test_app_case_export_rebuilds_step3d_static_evidence_from_running_release():
    app = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
    assert "_case_wyser_yang_bulk_evidence = build_wyser_yang_bulk_evidence()" in app
    assert "_case_wyser_yang_bulk_gate = build_wyser_yang_bulk_gate(" in app
    assert "_case_wyser_yang_bulk_contract = wyser_yang_bulk_contract_payload(" in app
    assert f'("{EVIDENCE}", _case_wyser_yang_bulk_evidence)' in app
    assert f'("{GATE}", _case_wyser_yang_bulk_gate)' in app
    assert f'("{CONTRACT}", _case_wyser_yang_bulk_contract)' in app
