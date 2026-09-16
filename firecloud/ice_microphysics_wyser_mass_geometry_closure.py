"""Ice Optics Phase 2 Step 3F — Wyser Eq.(5)/(6) geometry/mass-size qualification.

Evidence/contract only. This step records the strong secondary lineage for the
Wyser/Wyser-Yang column relation D=2.5*L^0.6 while explicitly refusing to
promote that lineage to an exact machine-readable primary Eq.(5). Primary
Eq.(6) mass-size coefficients remain unresolved, so absolute PSD execution,
mass closure, L->Yang/Bi Dmax, bulk tau synthesis and production promotion all
remain fail-closed.
"""
from __future__ import annotations

from typing import Any
import pandas as pd

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
STEP3F_VERSION = "R5.7.41.3.4.10.19"
STEP3F_MODE = "WYSER_EQ5_EQ6_MASS_GEOMETRY_CLOSURE_QUALIFICATION_ONLY"
PHYSICS_PROMOTION_ALLOWED = False
EVIDENCE_AS_OF = "2026-09-17"
WAVELENGTHS_NM = [550, 575, 600, 650, 700, 750]

EVIDENCE_COLUMNS = [
    "step3f_version", "science_baseline", "step3f_mode", "evidence_id",
    "evidence_type", "pin_status", "value", "semantic_role",
    "authoritative_for_runtime_mapping", "source_reference", "source_path",
    "source_sha", "notes",
]

_WYSER_PRIMARY = "https://doi.org/10.1175/1520-0442(1998)011%3C1793:TERIIC%3E2.0.CO;2"
_WYSER_YANG = "https://doi.org/10.1016/S0169-8095(98)00083-0"
_YOST_2010 = "https://doi.org/10.1029/2009JD013313"
_ACP_LINEAGE = "https://acp.copernicus.org/preprints/9/24361/2009/acpd-9-24361-2009-print.pdf"
_YANG_REF = "https://www.giss.nasa.gov/pubs/abs/ya07100h.html"

_EVIDENCE: tuple[dict[str, Any], ...] = (
    {
        "evidence_id": "WYSER_EQ5_PRIMARY_SEMANTIC",
        "evidence_type": "PRIMARY_GEOMETRY_SEMANTIC",
        "pin_status": "PINNED_PRIMARY_SEMANTIC_ONLY",
        "value": "Eq.(5) defines a continuous relationship between solid-column length L and width D; all crystals are treated as hexagonal columns with size-dependent aspect ratio",
        "semantic_role": "PRIMARY_COLUMN_GEOMETRY_SEMANTIC",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Wyser (1998), section 2, equation 5 surrounding text",
        "source_sha": "",
        "notes": "Primary HTML text pins the role and continuity of Eq.(5), but the numerical equation is rendered as an image and is not promoted from OCR inference.",
    },
    {
        "evidence_id": "WYSER_EQ5_GEOMETRY_LINEAGE",
        "evidence_type": "SECONDARY_GEOMETRY_LINEAGE",
        "pin_status": "CORROBORATED_SECONDARY_LINEAGE",
        "value": "D=2.5*L^0.6 for hexagonal columns",
        "semantic_role": "WYSER_WYSER_YANG_COLUMN_GEOMETRY_CANDIDATE",
        "authoritative_for_runtime_mapping": False,
        "source_reference": f"{_YOST_2010}|{_ACP_LINEAGE}",
        "source_path": "Yost et al. (2010) section 3.2 explicitly attributes D=2.5 L^0.6 to Wyser and Yang (1998); ACP lineage independently repeats attribution",
        "source_sha": "",
        "notes": "Strong corroborating lineage. This is not equivalent to extracting the numeric primary Eq.(5) from Wyser (1998), so it remains non-authoritative for runtime mapping.",
    },
    {
        "evidence_id": "WYSER_EQ5_PRIMARY_NUMERIC_EQUATION",
        "evidence_type": "PRIMARY_NUMERIC_GEOMETRY_REQUIREMENT",
        "pin_status": "UNRESOLVED_PRIMARY_EQUATION_IMAGE",
        "value": "false",
        "semantic_role": "NO_PRIMARY_NUMERIC_EQ5_PROMOTION",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Wyser (1998), equation 5 image",
        "source_sha": "",
        "notes": "PhysicsCore does not promote the secondary D=2.5*L^0.6 lineage as the exact primary Eq.(5) until a primary-quality machine-verifiable equation representation is obtained.",
    },
    {
        "evidence_id": "WYSER_EQ6_PRIMARY_MASS_SEMANTIC",
        "evidence_type": "PRIMARY_MASS_SIZE_SEMANTIC",
        "pin_status": "PINNED_PRIMARY_SEMANTIC_ONLY",
        "value": "m(L)=rho(L)*V(L); density and volume are parameterized as functions of L for cold solid columns with L/D>2; m in grams and L in microns",
        "semantic_role": "PRIMARY_MASS_SIZE_SEMANTIC",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Wyser (1998), equation 6 surrounding text",
        "source_sha": "",
        "notes": "Primary prose pins variables, units, and particle regime, but the machine-extracted equation is corrupt and cannot serve as a numerical mass-size law.",
    },
    {
        "evidence_id": "WYSER_EQ6_MASS_SIZE_PRIMARY_NUMERIC",
        "evidence_type": "PRIMARY_NUMERIC_MASS_SIZE_REQUIREMENT",
        "pin_status": "UNRESOLVED_CORRUPT_MACHINE_EXTRACTION",
        "value": "false",
        "semantic_role": "M_OF_L_NUMERIC_CONTRACT_BLOCKER",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Wyser (1998), equation 6 image / corrupt text extraction",
        "source_sha": "",
        "notes": "Do not reconstruct coefficients or exponents from the corrupt OCR string. Exact primary-quality numeric m(L) remains required before execution.",
    },
    {
        "evidence_id": "WYSER_IWC_AMPLITUDE_NORMALIZATION_CARRY_FORWARD",
        "evidence_type": "PRIMARY_NORMALIZATION_RULE",
        "pin_status": "PINNED_PRIMARY_EQUATIONS_7_8",
        "value": "A=IWC/integral[m(L)*phi(L)dL]",
        "semantic_role": "ABSOLUTE_PSD_AMPLITUDE_RULE",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Wyser (1998), equations 7-8",
        "source_sha": "",
        "notes": "Normalization rule is valid structurally but cannot be numerically executed until exact m(L) is pinned.",
    },
    {
        "evidence_id": "ABSOLUTE_PSD_RECONSTRUCTION_EXECUTABLE",
        "evidence_type": "EXECUTION_GATE",
        "pin_status": "BLOCKED",
        "value": "false",
        "semantic_role": "NO_NUMERIC_N_OF_L_YET",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Step 3F exact-mass requirement",
        "source_sha": "",
        "notes": "A corroborated geometry lineage is not sufficient to execute absolute n(L) without exact primary m(L).",
    },
    {
        "evidence_id": "PSD_MASS_CLOSURE_VALIDATION",
        "evidence_type": "NUMERICAL_VALIDATION_GATE",
        "pin_status": "NOT_EXECUTABLE_WITHOUT_EXACT_M_OF_L",
        "value": "integral[m(L)*n(L)dL]=IWC must pass explicit tolerance across supported T/IWC domain",
        "semantic_role": "MASS_CLOSURE_VALIDATION",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Wyser equations 7-8 + PhysicsCore numerical validation contract",
        "source_sha": "",
        "notes": "Mass closure cannot be claimed before exact numeric Eq.(6) and unit conversion are pinned.",
    },
    {
        "evidence_id": "WYSER_L_TO_YANG_DMAX_COORDINATE",
        "evidence_type": "COORDINATE_BRIDGE_GATE",
        "pin_status": "UNRESOLVED",
        "value": "false",
        "semantic_role": "NO_L_TO_DMAX_RUNTIME_COORDINATE",
        "authoritative_for_runtime_mapping": False,
        "source_reference": f"{_WYSER_PRIMARY}|{_YANG_REF}",
        "source_path": "Wyser column geometry versus Yang/Bi maximum-dimension coordinate",
        "source_sha": "",
        "notes": "Even if D=2.5*L^0.6 lineage is correct, exact convention matching to Yang/Bi maximum_dimension_um must be independently demonstrated.",
    },
    {
        "evidence_id": "STEP3F_PRODUCTION_PROMOTION",
        "evidence_type": "PROMOTION_GATE",
        "pin_status": "BLOCKED",
        "value": "false",
        "semantic_role": "EVIDENCE_ONLY_NO_OPTICAL_PROMOTION",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "",
        "source_path": "PhysicsCore frozen promotion policy",
        "source_sha": "",
        "notes": "No PSD runtime reconstruction, Dmax synthesis, Yang/Bi habit/roughness selection, bulk tau synthesis, or Formation promotion in Step 3F.",
    },
)


def build_wyser_mass_geometry_evidence() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "step3f_version": STEP3F_VERSION,
            "science_baseline": SCIENCE_BASELINE,
            "step3f_mode": STEP3F_MODE,
            **item,
        }
        for item in _EVIDENCE
    ], columns=EVIDENCE_COLUMNS)


def build_wyser_mass_geometry_gate(evidence: pd.DataFrame | None = None) -> pd.DataFrame:
    df = evidence.copy() if isinstance(evidence, pd.DataFrame) else build_wyser_mass_geometry_evidence()
    status = dict(zip(df.get("evidence_id", pd.Series(dtype=str)).astype(str), df.get("pin_status", pd.Series(dtype=str)).astype(str)))
    lineage = status.get("WYSER_EQ5_GEOMETRY_LINEAGE") == "CORROBORATED_SECONDARY_LINEAGE"
    eq5_primary = status.get("WYSER_EQ5_PRIMARY_NUMERIC_EQUATION") not in {"UNRESOLVED_PRIMARY_EQUATION_IMAGE", "UNRESOLVED"}
    eq6_primary = status.get("WYSER_EQ6_MASS_SIZE_PRIMARY_NUMERIC") not in {"UNRESOLVED_CORRUPT_MACHINE_EXTRACTION", "UNRESOLVED"}
    psd_exec = status.get("ABSOLUTE_PSD_RECONSTRUCTION_EXECUTABLE") not in {"BLOCKED", "UNRESOLVED"}
    mass_closure = status.get("PSD_MASS_CLOSURE_VALIDATION") not in {"NOT_EXECUTABLE_WITHOUT_EXACT_M_OF_L", "UNRESOLVED"}
    coord = status.get("WYSER_L_TO_YANG_DMAX_COORDINATE") not in {"UNRESOLVED", "BLOCKED"}
    blockers = []
    if not eq5_primary: blockers.append("WYSER_EQ5_PRIMARY_NUMERIC_EQUATION_UNRESOLVED")
    if not eq6_primary: blockers.append("WYSER_EQ6_MASS_SIZE_PRIMARY_NUMERIC_UNRESOLVED")
    if not psd_exec: blockers.append("ABSOLUTE_PSD_RECONSTRUCTION_NOT_EXECUTABLE")
    if not mass_closure: blockers.append("PSD_MASS_CLOSURE_NOT_VALIDATED")
    if not coord: blockers.append("WYSER_L_TO_YANG_DMAX_COORDINATE_UNRESOLVED")
    blockers.extend(["YANG_BI_HABIT_BRIDGE_NOT_VALIDATED", "YANG_BI_ROUGHNESS_POLICY_NOT_VALIDATED", "NO_INDEPENDENT_BULK_OPTICS_VALIDATION"])
    return pd.DataFrame([{
        "step3f_version": STEP3F_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "step3f_mode": STEP3F_MODE,
        "WYSER_EQ5_GEOMETRY_LINEAGE_CORROBORATED": lineage,
        "WYSER_EQ5_PRIMARY_NUMERIC_EQUATION_PINNED": eq5_primary,
        "WYSER_EQ6_MASS_SIZE_PRIMARY_NUMERIC_PINNED": eq6_primary,
        "ABSOLUTE_PSD_RECONSTRUCTION_EXECUTABLE": psd_exec,
        "PSD_MASS_CLOSURE_VALIDATION_PASS": mass_closure,
        "WYSER_L_TO_YANG_DMAX_COORDINATE_VALIDATED": coord,
        "BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE": False,
        "GFSV16_DMAX_MAPPING_ELIGIBLE": False,
        "PRODUCTION_ICE_OPTICS_READY": False,
        "physics_promotion_allowed": False,
        "evidence_row_count": int(len(df)),
        "qualification_state": "WYSER_GEOMETRY_LINEAGE_CORROBORATED_PRIMARY_MASS_SIZE_CLOSURE_BLOCKED",
        "qualification_blockers": "|".join(blockers),
        "detail": "D=2.5*L^0.6 is strongly corroborated in Wyser/Wyser-Yang lineage, but exact primary Eq.5 and Eq.6 numeric contracts, mass closure, L->Dmax, habit/roughness and production promotion remain blocked.",
    }])


def wyser_mass_geometry_contract_payload(*, physicscore_version: str | None = None) -> dict[str, Any]:
    return {
        "contract_version": "FIRECLOUD_ICE_WYSER_MASS_GEOMETRY_CLOSURE_QUALIFICATION_V1",
        "physicscore_version": physicscore_version or "",
        "step3f_version": STEP3F_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "mode": STEP3F_MODE,
        "wavelengths_nm": list(WAVELENGTHS_NM),
        "wyser_eq5_geometry_lineage_corroborated": True,
        "wyser_eq5_geometry_lineage_candidate": "D=2.5*L^0.6",
        "wyser_eq5_primary_numeric_equation_pinned": False,
        "wyser_eq6_mass_size_primary_numeric_pinned": False,
        "absolute_psd_reconstruction_executable": False,
        "psd_mass_closure_validation_pass": False,
        "wyser_L_to_yang_dmax_coordinate_validated": False,
        "yang_bi_habit_bridge_validated": False,
        "yang_bi_roughness_bridge_validated": False,
        "bulk_yang_bi_psd_integration_eligible": False,
        "gfsv16_dmax_mapping_eligible": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "mass_closure_contract": {
            "required_identity": "integral[m(L)*n(L)dL]=IWC",
            "amplitude_rule": "A=IWC/integral[m(L)*phi(L)dL]",
            "execution_status": "BLOCKED_UNTIL_EXACT_PRIMARY_NUMERIC_M_OF_L_AND_UNITS_PINNED",
        },
        "geometry_lineage": {
            "candidate": "D=2.5*L^0.6",
            "evidence_level": "CORROBORATED_SECONDARY_LINEAGE",
            "primary_numeric_equation_status": "UNRESOLVED_EQUATION_IMAGE",
            "runtime_authoritative": False,
        },
        "forbidden_shortcuts": [
            "secondary_D_2p5_L_0p6_promoted_as_primary_Wyser_equation_5",
            "corrupt_equation_6_OCR_used_as_numeric_mass_size_contract",
            "mass_closure_claimed_without_exact_primary_m_of_L",
            "Wyser_L_silently_equal_to_Yang_Bi_Dmax",
            "absolute_PSD_reconstruction_before_exact_primary_mass_size_contract",
            "Yang_Bi_habit_selected_before_geometry_coordinate_validation",
            "single_roughness_state_silently_selected",
            "bulk_tau_synthesized_before_independent_validation",
            "production_promotion_before_step3f_and_later_gates_pass",
        ],
        "qualification_requirements": [
            "obtain_machine_verifiable_primary_quality_Wyser_equation_5",
            "obtain_machine_verifiable_primary_quality_Wyser_equation_6_mass_size_coefficients_exponents_units",
            "independently_reproduce_m_of_L_and_unit_conversions",
            "run_IWC_mass_closure_grid_over_supported_T_IWC_domain",
            "validate_Wyser_L_to_Yang_Bi_maximum_dimension_coordinate",
            "validate_Yang_Bi_habit_geometry_bridge",
            "validate_roughness_uncertainty_policy",
            "independent_bulk_shortwave_optics_validation",
            "separate_production_promotion_gate",
        ],
        "frozen_science_unchanged": True,
    }
