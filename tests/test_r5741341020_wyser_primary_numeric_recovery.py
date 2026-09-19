from pathlib import Path
import math
import pandas as pd

import firecloud
from firecloud.case_integrity import build_analysis_integrity_audit, build_archive_integrity_audit, PASS
from firecloud.ice_microphysics_wyser_primary_numeric_recovery import (
    SCIENCE_BASELINE,
    STEP3G_VERSION,
    build_wyser_primary_numeric_recovery_evidence,
    build_wyser_primary_numeric_recovery_gate,
    diagnostic_mass_closure,
    wyser_primary_numeric_recovery_contract_payload,
)

EVIDENCE = "ice_microphysics_wyser_primary_numeric_recovery_evidence.csv"
GATE = "ice_microphysics_wyser_primary_numeric_recovery_gate.csv"
CONTRACT = "ice_microphysics_wyser_primary_numeric_recovery_contract.json"


def test_release_identity_and_frozen_mode():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.30.12"
    assert STEP3G_VERSION == "R5.7.41.3.4.10.20.1"
    assert SCIENCE_BASELINE == "R5.7.41.2_SHADOW_COT_AB_FROZEN"


def test_primary_numeric_recovery_is_not_overclaimed():
    ev = build_wyser_primary_numeric_recovery_evidence().set_index("evidence_id")
    assert ev.loc["WYSER_YANG_1998_GEOMETRY_LINEAGE", "pin_status"] == "SEPARATE_REFERENCE_NOT_WYSER_1998_EQ5"
    assert "D=2.5*L^0.6" in ev.loc["WYSER_YANG_1998_GEOMETRY_LINEAGE", "value"]
    assert ev.loc["WYSER_EQ5_PRIMARY_MACHINE_NUMERIC_RECOVERY", "pin_status"] == "PINNED_PRIMARY_NUMERIC_WITH_INDEPENDENT_TRANSCRIPTION"
    assert ev.loc["WYSER_EQ6_PRIMARY_MACHINE_NUMERIC_RECOVERY", "pin_status"] == "PINNED_PRIMARY_NUMERIC_INDEX_RECOVERY"
    assert bool(ev.loc["WYSER_EQ6_PRIMARY_MACHINE_NUMERIC_RECOVERY", "authoritative_for_runtime_mapping"]) is False


def test_dual_source_gate_keeps_scientific_mass_closure_fail_closed():
    g = build_wyser_primary_numeric_recovery_gate().iloc[0]
    assert bool(g["WYSER_EQ5_PRIMARY_MACHINE_NUMERIC_RECOVERED"]) is True
    assert bool(g["WYSER_EQ6_PRIMARY_MACHINE_NUMERIC_RECOVERED"]) is True
    assert bool(g["INDEPENDENT_EQ5_TRANSCRIPTION_PASS"]) is True
    assert bool(g["INDEPENDENT_EQ6_EXTERNAL_NUMERIC_CORROBORATION_PASS"]) is False
    assert bool(g["INDEPENDENT_TRANSCRIPTION_REPRODUCTION_PASS"]) is False
    assert bool(g["EQ5_EQ6_UNIT_CONSISTENCY_PASS"]) is True
    assert bool(g["DIAGNOSTIC_MASS_CLOSURE_HARNESS_READY"]) is True
    assert bool(g["SCIENTIFIC_MASS_CLOSURE_EXECUTED"]) is False
    assert bool(g["ABSOLUTE_PSD_RECONSTRUCTION_EXECUTABLE"]) is False
    assert bool(g["PSD_MASS_CLOSURE_VALIDATION_PASS"]) is False
    assert bool(g["PRODUCTION_ICE_OPTICS_READY"]) is False
    assert bool(g["physics_promotion_allowed"]) is False
    assert g["qualification_state"] == "WYSER_PRIMARY_EQ5_EQ6_NUMERIC_RECOVERED_DIAGNOSTIC_MASS_CLOSURE_PASS_EXTERNAL_EQ6_CORROBORATION_BLOCKED"


def test_diagnostic_mass_closure_harness_closes_only_synthetic_inputs():
    result = diagnostic_mass_closure(
        length_um=[10.0, 20.0, 30.0, 40.0],
        shape_weights=[1.0, 2.0, 1.5, 0.5],
        mass_g=[1e-9, 3e-9, 8e-9, 1.5e-8],
        iwc_g_m3=0.02,
    )
    assert result["diagnostic_only"] is True
    assert result["input_contract"] == "SYNTHETIC_GENERIC_NOT_WYSER_SCIENTIFIC_VALIDATION"
    assert math.isfinite(result["amplitude"])
    assert result["amplitude"] > 0
    assert math.isclose(result["reconstructed_iwc_g_m3"], 0.02, rel_tol=1e-12, abs_tol=1e-15)
    assert result["relative_error"] <= 1e-12
    assert result["scientific_mass_closure_pass"] is False


def test_contract_requires_dual_source_promotion_and_forbids_ocr_or_substitution_shortcuts():
    c = wyser_primary_numeric_recovery_contract_payload(physicscore_version=firecloud.__version__)
    assert c["contract_version"] == "FIRECLOUD_ICE_WYSER_PRIMARY_NUMERIC_RECOVERY_V3"
    assert c["wyser_eq5_primary_machine_numeric_recovered"] is True
    assert c["wyser_eq6_primary_machine_numeric_recovered"] is True
    assert c["independent_eq5_transcription_pass"] is True
    assert c["independent_eq6_external_numeric_corroboration_pass"] is False
    assert c["diagnostic_mass_closure_harness_ready"] is True
    assert c["scientific_mass_closure_executed"] is False
    assert c["absolute_psd_reconstruction_executable"] is False
    forbidden = set(c["forbidden_shortcuts"])
    assert "Wyser_Yang_1998_D_2p5_L_0p6_substituted_for_single_author_Wyser_1998_equation_5" in forbidden
    assert "indexed_equation_6_parse_treated_as_independent_external_corroboration" in forbidden
    assert "unrelated_mass_size_law_substituted_for_Wyser_equation_6" in forbidden
    assert "synthetic_harness_pass_treated_as_scientific_Wyser_mass_closure" in forbidden


def _analysis_result():
    ev = build_wyser_primary_numeric_recovery_evidence()
    gate = build_wyser_primary_numeric_recovery_gate(ev)
    return {
        "ice_microphysics_wyser_primary_numeric_recovery_required": True,
        "v1_ice_microphysics_wyser_primary_numeric_recovery_evidence": ev,
        "v1_ice_microphysics_wyser_primary_numeric_recovery_gate": gate,
        "ice_microphysics_wyser_primary_numeric_recovery_contract": wyser_primary_numeric_recovery_contract_payload(
            physicscore_version=firecloud.__version__
        ),
    }


def test_analysis_integrity_step3g_gates_pass_and_fail_closed():
    audit = build_analysis_integrity_audit(_analysis_result()).set_index("check_id")
    for check in (
        "ICE_MICROPHYSICS_WYSER_PRIMARY_NUMERIC_RECOVERY_EVIDENCE_PRESENT",
        "ICE_MICROPHYSICS_WYSER_PRIMARY_NUMERIC_RECOVERY_CONTRACT_FREEZE",
        "ICE_MICROPHYSICS_WYSER_PRIMARY_NUMERIC_RECOVERY_FAIL_CLOSED",
    ):
        assert audit.loc[check, "status"] == PASS


def test_case_archive_and_app_require_nonempty_step3g_artifacts():
    manifest = pd.DataFrame([
        {"artifact": EVIDENCE, "row_count": 12, "byte_size": 6500},
        {"artifact": GATE, "row_count": 1, "byte_size": 1400},
        {"artifact": CONTRACT, "row_count": float("nan"), "byte_size": 2200},
    ])
    audit = build_archive_integrity_audit(manifest, pd.DataFrame()).set_index("check_id")
    assert audit.loc["ARCHIVE_CONTENT::ICE_MICROPHYSICS_WYSER_PRIMARY_NUMERIC_RECOVERY_EVIDENCE_NONEMPTY", "status"] == PASS
    assert audit.loc["ARCHIVE_CONTENT::ICE_MICROPHYSICS_WYSER_PRIMARY_NUMERIC_RECOVERY_GATE_NONEMPTY", "status"] == PASS
    assert audit.loc["ARCHIVE_CONTENT::ICE_MICROPHYSICS_WYSER_PRIMARY_NUMERIC_RECOVERY_CONTRACT_NONEMPTY", "status"] == PASS

    app = Path(__file__).resolve().parents[1].joinpath("app.py").read_text(encoding="utf-8")
    assert "_case_wyser_primary_numeric_recovery_evidence = build_wyser_primary_numeric_recovery_evidence()" in app
    assert "_case_wyser_primary_numeric_recovery_gate = build_wyser_primary_numeric_recovery_gate(" in app
    assert "_case_wyser_primary_numeric_recovery_contract = wyser_primary_numeric_recovery_contract_payload(" in app
    assert f'(\"{EVIDENCE}\", _case_wyser_primary_numeric_recovery_evidence)' in app
    assert f'(\"{GATE}\", _case_wyser_primary_numeric_recovery_gate)' in app
    assert f'(\"{CONTRACT}\", _case_wyser_primary_numeric_recovery_contract)' in app
