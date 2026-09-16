"""Ice Optics Phase 2 Step 3G — primary Wyser numeric recovery audit.

Evidence/contract plus a strictly synthetic diagnostic closure harness.  This
step does *not* recover or promote machine-readable primary Eq.(5)/(6), does
not reconstruct the Wyser PSD, and does not enable Dmax, bulk ice optics or
production promotion.  The diagnostic closure harness only proves that the
normalization algebra/code path closes for caller-supplied synthetic arrays.
"""
from __future__ import annotations

from typing import Any, Iterable
import math
import numpy as np
import pandas as pd

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
STEP3G_VERSION = "R5.7.41.3.4.10.20"
STEP3G_MODE = "WYSER_PRIMARY_NUMERIC_RECOVERY_AND_SYNTHETIC_CLOSURE_HARNESS_ONLY"
PHYSICS_PROMOTION_ALLOWED = False
EVIDENCE_AS_OF = "2026-09-17"
WAVELENGTHS_NM = [550, 575, 600, 650, 700, 750]

_WYSER_PRIMARY = "https://doi.org/10.1175/1520-0442(1998)011%3C1793:TERIIC%3E2.0.CO;2"
_YOST_2010 = "https://doi.org/10.1029/2009JD013313"
_ACP_LINEAGE = "https://acp.copernicus.org/preprints/9/24361/2009/acpd-9-24361-2009-print.pdf"
_YANG_REF = "https://www.giss.nasa.gov/pubs/abs/ya07100h.html"

EVIDENCE_COLUMNS = [
    "step3g_version", "science_baseline", "step3g_mode", "evidence_id",
    "evidence_type", "pin_status", "value", "semantic_role",
    "authoritative_for_runtime_mapping", "source_reference", "source_path",
    "source_sha", "notes",
]

_EVIDENCE: tuple[dict[str, Any], ...] = (
    {
        "evidence_id": "WYSER_PRIMARY_EQ5_ROLE",
        "evidence_type": "PRIMARY_GEOMETRY_SEMANTIC",
        "pin_status": "PINNED_PRIMARY_SEMANTIC_ONLY",
        "value": "Eq.(5) is the continuous length-width relation for solid hexagonal columns with size-dependent aspect ratio",
        "semantic_role": "PRIMARY_EQ5_ROLE",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Wyser (1998), Eq.(5) surrounding primary text",
        "source_sha": "",
        "notes": "Primary prose pins the equation role, not a machine-verifiable numeric transcription.",
    },
    {
        "evidence_id": "WYSER_EQ5_MULTI_SOURCE_NUMERIC_LINEAGE",
        "evidence_type": "NONPRIMARY_NUMERIC_LINEAGE",
        "pin_status": "CORROBORATED_NONPRIMARY_NUMERIC_LINEAGE",
        "value": "D=2.5*L^0.6",
        "semantic_role": "EQ5_NUMERIC_RECOVERY_CANDIDATE_NOT_PRIMARY",
        "authoritative_for_runtime_mapping": False,
        "source_reference": f"{_YOST_2010}|{_ACP_LINEAGE}",
        "source_path": "Later literature explicitly attributes D=2.5 L^0.6 to Wyser/Wyser-Yang",
        "source_sha": "",
        "notes": "Multiple-source corroboration is retained as lineage evidence only and cannot satisfy the primary-equation promotion gate.",
    },
    {
        "evidence_id": "WYSER_EQ5_PRIMARY_MACHINE_NUMERIC_RECOVERY",
        "evidence_type": "PRIMARY_NUMERIC_RECOVERY_GATE",
        "pin_status": "UNRESOLVED_PRIMARY_EQUATION_IMAGE",
        "value": "false",
        "semantic_role": "PRIMARY_EQ5_NUMERIC_RECOVERY_REQUIRED",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Wyser (1998), Eq.(5) equation image",
        "source_sha": "",
        "notes": "No machine-verifiable primary-quality numeric representation has been obtained; do not promote the secondary lineage.",
    },
    {
        "evidence_id": "WYSER_PRIMARY_EQ6_ROLE_UNITS",
        "evidence_type": "PRIMARY_MASS_SIZE_SEMANTIC",
        "pin_status": "PINNED_PRIMARY_SEMANTIC_ONLY",
        "value": "m(L)=rho(L)*V(L); m in grams; L in microns; cold solid columns with L/D>2",
        "semantic_role": "PRIMARY_EQ6_ROLE_AND_UNITS",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Wyser (1998), Eq.(6) surrounding primary text",
        "source_sha": "",
        "notes": "Primary prose pins variables/units/regime but not a safe numeric mass-size transcription.",
    },
    {
        "evidence_id": "WYSER_EQ6_CORRUPT_FLAT_EXTRACTION",
        "evidence_type": "MACHINE_EXTRACTION_REJECTION",
        "pin_status": "REJECTED_AS_NUMERIC_SOURCE",
        "value": "machine-flat extraction is incomplete/corrupt and cannot be parsed into coefficients/exponents",
        "semantic_role": "DO_NOT_USE_CORRUPT_EQ6_TEXT",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Wyser (1998), Eq.(6) image / flattened equation text",
        "source_sha": "",
        "notes": "Corrupt flattened/OCR equation text is explicitly non-authoritative for numeric recovery.",
    },
    {
        "evidence_id": "WYSER_EQ6_PRIMARY_MACHINE_NUMERIC_RECOVERY",
        "evidence_type": "PRIMARY_NUMERIC_RECOVERY_GATE",
        "pin_status": "UNRESOLVED_CORRUPT_MACHINE_EXTRACTION",
        "value": "false",
        "semantic_role": "PRIMARY_EQ6_NUMERIC_RECOVERY_REQUIRED",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Wyser (1998), Eq.(6) equation image",
        "source_sha": "",
        "notes": "Exact primary-quality coefficients/exponents and unit conversion remain unresolved.",
    },
    {
        "evidence_id": "DUAL_SOURCE_NUMERIC_PROMOTION_POLICY",
        "evidence_type": "PROMOTION_POLICY",
        "pin_status": "PINNED_FAIL_CLOSED_POLICY",
        "value": "primary numeric Eq.(5)+Eq.(6) AND independent transcription/reproduction AND unit-consistency must all pass before scientific closure execution",
        "semantic_role": "NUMERIC_RECOVERY_PROMOTION_GATE",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "",
        "source_path": "PhysicsCore Step 3G qualification policy",
        "source_sha": "",
        "notes": "Secondary lineage, OCR, or a single transcription source is insufficient.",
    },
    {
        "evidence_id": "DIAGNOSTIC_MASS_CLOSURE_HARNESS",
        "evidence_type": "SOFTWARE_READINESS",
        "pin_status": "READY_SYNTHETIC_ONLY",
        "value": "A=IWC/integral[m(L)*phi(L)dL]; reconstruct integral[m*A*phi dL]",
        "semantic_role": "GENERIC_SYNTHETIC_CLOSURE_HARNESS",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Wyser Eq.(7)/(8) algebra + PhysicsCore diagnostic utility",
        "source_sha": "",
        "notes": "Harness readiness validates code algebra only. Synthetic closure is not scientific Wyser validation.",
    },
    {
        "evidence_id": "SCIENTIFIC_MASS_CLOSURE_EXECUTED",
        "evidence_type": "SCIENTIFIC_VALIDATION_GATE",
        "pin_status": "BLOCKED_PRIMARY_NUMERIC_INPUTS_UNRESOLVED",
        "value": "false",
        "semantic_role": "NO_WYSER_SCIENTIFIC_CLOSURE_YET",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Step 3G dual-source promotion policy",
        "source_sha": "",
        "notes": "Scientific mass-closure grid is not executed until exact Eq.(5)/(6) numeric inputs and units pass promotion.",
    },
    {
        "evidence_id": "ABSOLUTE_PSD_RECONSTRUCTION_EXECUTABLE",
        "evidence_type": "EXECUTION_GATE",
        "pin_status": "BLOCKED",
        "value": "false",
        "semantic_role": "NO_ABSOLUTE_WYSER_PSD_EXECUTION",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Step 3G primary numeric recovery gate",
        "source_sha": "",
        "notes": "Synthetic harness readiness does not unlock absolute n(L).",
    },
    {
        "evidence_id": "WYSER_L_TO_YANG_DMAX_COORDINATE",
        "evidence_type": "COORDINATE_BRIDGE_GATE",
        "pin_status": "UNRESOLVED",
        "value": "false",
        "semantic_role": "NO_L_TO_DMAX_RUNTIME_COORDINATE",
        "authoritative_for_runtime_mapping": False,
        "source_reference": f"{_WYSER_PRIMARY}|{_YANG_REF}",
        "source_path": "Wyser primary geometry versus Yang/Bi maximum-dimension convention",
        "source_sha": "",
        "notes": "Coordinate bridge remains blocked until primary geometry and exact convention matching are verified.",
    },
    {
        "evidence_id": "STEP3G_PRODUCTION_PROMOTION",
        "evidence_type": "PROMOTION_GATE",
        "pin_status": "BLOCKED",
        "value": "false",
        "semantic_role": "EVIDENCE_AND_HARNESS_ONLY_NO_OPTICAL_PROMOTION",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "",
        "source_path": "PhysicsCore frozen promotion policy",
        "source_sha": "",
        "notes": "No PSD runtime reconstruction, Dmax synthesis, habit/roughness selection, bulk tau synthesis or Formation promotion in Step 3G.",
    },
)


def build_wyser_primary_numeric_recovery_evidence() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "step3g_version": STEP3G_VERSION,
            "science_baseline": SCIENCE_BASELINE,
            "step3g_mode": STEP3G_MODE,
            **item,
        }
        for item in _EVIDENCE
    ], columns=EVIDENCE_COLUMNS)


def build_wyser_primary_numeric_recovery_gate(evidence: pd.DataFrame | None = None) -> pd.DataFrame:
    df = evidence.copy() if isinstance(evidence, pd.DataFrame) else build_wyser_primary_numeric_recovery_evidence()
    status = dict(zip(df["evidence_id"].astype(str), df["pin_status"].astype(str)))
    eq5 = status.get("WYSER_EQ5_PRIMARY_MACHINE_NUMERIC_RECOVERY") not in {"UNRESOLVED_PRIMARY_EQUATION_IMAGE", "UNRESOLVED"}
    eq6 = status.get("WYSER_EQ6_PRIMARY_MACHINE_NUMERIC_RECOVERY") not in {"UNRESOLVED_CORRUPT_MACHINE_EXTRACTION", "UNRESOLVED"}
    harness = status.get("DIAGNOSTIC_MASS_CLOSURE_HARNESS") == "READY_SYNTHETIC_ONLY"
    scientific = status.get("SCIENTIFIC_MASS_CLOSURE_EXECUTED") not in {"BLOCKED_PRIMARY_NUMERIC_INPUTS_UNRESOLVED", "UNRESOLVED"}
    blockers = [
        "WYSER_EQ5_PRIMARY_MACHINE_NUMERIC_UNRESOLVED",
        "WYSER_EQ6_PRIMARY_MACHINE_NUMERIC_UNRESOLVED",
        "INDEPENDENT_TRANSCRIPTION_REPRODUCTION_NOT_PASSED",
        "EQ5_EQ6_UNIT_CONSISTENCY_NOT_PASSED",
        "SCIENTIFIC_MASS_CLOSURE_NOT_EXECUTED",
        "ABSOLUTE_PSD_RECONSTRUCTION_BLOCKED",
        "WYSER_L_TO_YANG_DMAX_COORDINATE_UNRESOLVED",
        "YANG_BI_HABIT_BRIDGE_NOT_VALIDATED",
        "YANG_BI_ROUGHNESS_POLICY_NOT_VALIDATED",
        "NO_INDEPENDENT_BULK_OPTICS_VALIDATION",
    ]
    return pd.DataFrame([{
        "step3g_version": STEP3G_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "step3g_mode": STEP3G_MODE,
        "WYSER_EQ5_PRIMARY_MACHINE_NUMERIC_RECOVERED": bool(eq5),
        "WYSER_EQ6_PRIMARY_MACHINE_NUMERIC_RECOVERED": bool(eq6),
        "INDEPENDENT_TRANSCRIPTION_REPRODUCTION_PASS": False,
        "EQ5_EQ6_UNIT_CONSISTENCY_PASS": False,
        "DIAGNOSTIC_MASS_CLOSURE_HARNESS_READY": bool(harness),
        "SCIENTIFIC_MASS_CLOSURE_EXECUTED": bool(scientific),
        "ABSOLUTE_PSD_RECONSTRUCTION_EXECUTABLE": False,
        "PSD_MASS_CLOSURE_VALIDATION_PASS": False,
        "WYSER_L_TO_YANG_DMAX_COORDINATE_VALIDATED": False,
        "BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE": False,
        "GFSV16_DMAX_MAPPING_ELIGIBLE": False,
        "PRODUCTION_ICE_OPTICS_READY": False,
        "physics_promotion_allowed": False,
        "evidence_row_count": int(len(df)),
        "qualification_state": "WYSER_PRIMARY_NUMERIC_RECOVERY_UNRESOLVED_CLOSURE_HARNESS_READY",
        "qualification_blockers": "|".join(blockers),
        "detail": "Primary Eq.5/Eq.6 machine-readable numeric recovery remains unresolved. A synthetic-only closure harness is ready, but scientific mass closure, absolute PSD execution, L->Dmax and production promotion remain blocked.",
    }])


def diagnostic_mass_closure(
    *,
    length_um: Iterable[float],
    shape_weights: Iterable[float],
    mass_g: Iterable[float],
    iwc_g_m3: float,
) -> dict[str, Any]:
    """Generic synthetic normalization closure harness.

    The input arrays are caller supplied and are deliberately *not* interpreted
    as Wyser Eq.(5)/(6).  Passing this calculation cannot satisfy a scientific
    Wyser mass-closure gate.
    """
    L = np.asarray(list(length_um), dtype=float)
    phi = np.asarray(list(shape_weights), dtype=float)
    mass = np.asarray(list(mass_g), dtype=float)
    iwc = float(iwc_g_m3)
    if L.ndim != 1 or phi.ndim != 1 or mass.ndim != 1 or not (len(L) == len(phi) == len(mass)):
        raise ValueError("length_um, shape_weights and mass_g must be equal-length 1-D arrays")
    if len(L) < 2:
        raise ValueError("at least two size points are required")
    if not np.all(np.isfinite(L)) or not np.all(np.isfinite(phi)) or not np.all(np.isfinite(mass)) or not math.isfinite(iwc):
        raise ValueError("all inputs must be finite")
    if np.any(L <= 0) or np.any(np.diff(L) <= 0):
        raise ValueError("length_um must be strictly increasing and positive")
    if np.any(phi < 0) or np.any(mass <= 0) or iwc <= 0:
        raise ValueError("shape_weights must be nonnegative; mass_g and iwc_g_m3 must be positive")
    denom = float(np.trapezoid(mass * phi, L))
    if not math.isfinite(denom) or denom <= 0:
        raise ValueError("normalization denominator must be positive and finite")
    amplitude = iwc / denom
    reconstructed = float(np.trapezoid(mass * amplitude * phi, L))
    relative_error = abs(reconstructed - iwc) / iwc
    return {
        "diagnostic_only": True,
        "input_contract": "SYNTHETIC_GENERIC_NOT_WYSER_SCIENTIFIC_VALIDATION",
        "integration_coordinate": "caller_supplied_length_um",
        "amplitude": float(amplitude),
        "normalization_denominator": denom,
        "target_iwc_g_m3": iwc,
        "reconstructed_iwc_g_m3": reconstructed,
        "relative_error": float(relative_error),
        "numeric_closure_pass": bool(relative_error <= 1e-12),
        "scientific_mass_closure_pass": False,
    }


def wyser_primary_numeric_recovery_contract_payload(*, physicscore_version: str | None = None) -> dict[str, Any]:
    return {
        "contract_version": "FIRECLOUD_ICE_WYSER_PRIMARY_NUMERIC_RECOVERY_V1",
        "physicscore_version": physicscore_version or "",
        "step3g_version": STEP3G_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "mode": STEP3G_MODE,
        "wavelengths_nm": list(WAVELENGTHS_NM),
        "wyser_eq5_multi_source_numeric_lineage": "D=2.5*L^0.6",
        "wyser_eq5_primary_machine_numeric_recovered": False,
        "wyser_eq6_primary_machine_numeric_recovered": False,
        "independent_transcription_reproduction_pass": False,
        "eq5_eq6_unit_consistency_pass": False,
        "diagnostic_mass_closure_harness_ready": True,
        "diagnostic_harness_scope": "SYNTHETIC_GENERIC_ONLY_NOT_WYSER_SCIENTIFIC_VALIDATION",
        "scientific_mass_closure_executed": False,
        "absolute_psd_reconstruction_executable": False,
        "psd_mass_closure_validation_pass": False,
        "wyser_L_to_yang_dmax_coordinate_validated": False,
        "yang_bi_habit_bridge_validated": False,
        "yang_bi_roughness_bridge_validated": False,
        "bulk_yang_bi_psd_integration_eligible": False,
        "gfsv16_dmax_mapping_eligible": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "numeric_promotion_policy": {
            "requires_primary_eq5_machine_numeric": True,
            "requires_primary_eq6_machine_numeric": True,
            "requires_independent_transcription_reproduction": True,
            "requires_unit_consistency": True,
            "synthetic_harness_cannot_satisfy_scientific_gate": True,
        },
        "forbidden_shortcuts": [
            "secondary_D_2p5_L_0p6_promoted_as_primary_Wyser_equation_5",
            "corrupt_equation_6_flat_extraction_parsed_into_coefficients",
            "unrelated_mass_size_law_substituted_for_Wyser_equation_6",
            "synthetic_harness_pass_treated_as_scientific_Wyser_mass_closure",
            "scientific_mass_closure_claimed_before_dual_source_numeric_promotion",
            "absolute_PSD_reconstruction_before_primary_eq5_eq6_numeric_recovery",
            "Wyser_L_silently_equal_to_Yang_Bi_Dmax",
            "Yang_Bi_habit_selected_before_geometry_coordinate_validation",
            "single_roughness_state_silently_selected",
            "bulk_tau_synthesized_before_independent_validation",
            "production_promotion_before_step3g_and_later_gates_pass",
        ],
        "qualification_requirements": [
            "obtain_machine_verifiable_primary_quality_Wyser_equation_5",
            "obtain_machine_verifiable_primary_quality_Wyser_equation_6",
            "independently_transcribe_and_reproduce_both_equations",
            "verify_coefficients_exponents_units_and_coordinate_conventions",
            "execute_scientific_IWC_mass_closure_grid_over_supported_domain",
            "validate_Wyser_L_to_Yang_Bi_maximum_dimension_coordinate",
            "validate_Yang_Bi_habit_geometry_bridge",
            "validate_roughness_uncertainty_policy",
            "independent_bulk_shortwave_optics_validation",
            "separate_production_promotion_gate",
        ],
        "frozen_science_unchanged": True,
    }
