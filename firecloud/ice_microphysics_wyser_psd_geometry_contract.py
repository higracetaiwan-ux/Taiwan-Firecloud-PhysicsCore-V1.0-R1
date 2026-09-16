"""Ice Optics Phase 2 Step 3E — Wyser PSD normalization + geometry qualification.

Evidence/contract only.  This module pins the primary-source IWC amplitude
normalization rule for Wyser's mixed particle-size distribution while keeping
numerical PSD reconstruction, exact column geometry, the Wyser-L -> Yang/Bi
Dmax coordinate bridge, habit, roughness, bulk tau synthesis, and production
promotion fail-closed.
"""
from __future__ import annotations

from typing import Any
import pandas as pd

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
STEP3E_VERSION = "R5.7.41.3.4.10.18"
STEP3E_MODE = "WYSER_PSD_NORMALIZATION_GEOMETRY_COORDINATE_QUALIFICATION_ONLY"
PHYSICS_PROMOTION_ALLOWED = False
EVIDENCE_AS_OF = "2026-09-17"
WAVELENGTHS_NM = [550, 575, 600, 650, 700, 750]

EVIDENCE_COLUMNS = [
    "step3e_version", "science_baseline", "step3e_mode", "evidence_id",
    "evidence_type", "pin_status", "value", "semantic_role",
    "authoritative_for_runtime_mapping", "source_reference", "source_path",
    "source_sha", "notes",
]

_WYSER_DOI = "https://doi.org/10.1175/1520-0442(1998)011%3C1793:TERIIC%3E2.0.CO;2"
_YANG_REF = "https://www.giss.nasa.gov/pubs/abs/ya07100h.html"
_GFDL_REF = "https://github.com/ufs-community/ccpp-physics/blob/ufs/dev/physics/MP/GFDL/v1_2019/gfdl_cloud_microphys_mod.F90"

_EVIDENCE: tuple[dict[str, Any], ...] = (
    {
        "evidence_id": "WYSER_PSD_AMPLITUDE_IWC_NORMALIZATION",
        "evidence_type": "PRIMARY_PSD_NORMALIZATION_RULE",
        "pin_status": "PINNED_PRIMARY_EQUATIONS_7_8",
        "value": "n(L)=A*n_x(L); A=IWC/integral[m(L)*n_x(L)dL] over the selected Wyser size domain",
        "semantic_role": "IWC_CONSTRAINED_PSD_AMPLITUDE",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_DOI,
        "source_path": "Wyser (1998), section 3, equations 7-8",
        "source_sha": "",
        "notes": "Primary text explicitly links the free PSD amplitude to IWC and inverts the mass integral. The rule is pinned; numerical execution remains blocked until the same-population mass/geometry contract is pinned.",
    },
    {
        "evidence_id": "WYSER_MIXED_PSD_SHAPE_FUNCTION",
        "evidence_type": "PRIMARY_PSD_SHAPE",
        "pin_status": "PINNED_PIECEWISE_SHAPE",
        "value": "phi(L)=L^nu*exp(-lambda*L) for L<=20 um; phi(L)=alpha*L^B for L>20 um; nu=3; lambda=0.3 um^-1",
        "semantic_role": "UNNORMALIZED_MIXED_PSD_SHAPE",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_DOI,
        "source_path": "Wyser (1998), mixed distribution section/equation 15 lineage",
        "source_sha": "",
        "notes": "The mixed Gamma + power-law structure and small-particle Gamma parameters are primary-source supported. This row deliberately uses phi(L) for the unnormalized shape to separate shape from IWC amplitude.",
    },
    {
        "evidence_id": "WYSER_MIXED_BRANCH_CONTINUITY_FACTOR",
        "evidence_type": "ANALYTIC_JOIN_CONTRACT",
        "pin_status": "PINNED_ANALYTIC_FROM_CONTINUITY",
        "value": "alpha=20^(nu-B)*exp(-lambda*20) when both branches use one common amplitude A and continuity is imposed at L=20 um",
        "semantic_role": "GAMMA_POWERLAW_CONTINUITY_FACTOR",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_DOI,
        "source_path": "Wyser (1998), continuity requirement at 20 um + algebraic consequence",
        "source_sha": "",
        "notes": "This is an algebraic consequence of the pinned piecewise forms and primary continuity requirement; it does not introduce an empirical coefficient.",
    },
    {
        "evidence_id": "WYSER_POWERLAW_B_GFSV16_SOURCE",
        "evidence_type": "PUBLIC_SOURCE_PARAMETERIZATION",
        "pin_status": "PINNED_GFSV16_SOURCE_EQUIVALENT",
        "value": "B=-2 + 1e-3*log10(IWC/IWC0)*max(0,Tice-T)^1.5; IWC0=50 g m^-3",
        "semantic_role": "POWERLAW_SLOPE_CONTROL",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _GFDL_REF,
        "source_path": "cloud_diagnosis :: reiflag=2 :: bw",
        "source_sha": "ad0304074e17a7b83be2f0fe016345b7f11be4ef",
        "notes": "Public GFDL v1 reproduction source pins the operational-family B(T,IWC) numerical expression used before the rei fit.",
    },
    {
        "evidence_id": "WYSER_NUMERIC_MASS_SIZE_CONTRACT",
        "evidence_type": "NUMERIC_RECONSTRUCTION_REQUIREMENT",
        "pin_status": "UNRESOLVED_EXACT_NUMERIC_EQUATION_6",
        "value": "PRIMARY_TEXT_CONFIRMS_MASS_FROM_SIZE_DEPENDENT_DENSITY_AND_VOLUME_BUT_MACHINE_EXTRACTED_NUMERIC_COEFFICIENTS_NOT_ACCEPTED",
        "semantic_role": "MASS_CLOSURE_INTEGRAND_M_OF_L",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_DOI,
        "source_path": "Wyser (1998), equation 6",
        "source_sha": "",
        "notes": "The amplitude rule is known, but PhysicsCore does not numerically evaluate A until equation-6 coefficients/units are independently pinned from a primary-quality representation.",
    },
    {
        "evidence_id": "WYSER_ABSOLUTE_PSD_RECONSTRUCTION_EXECUTABLE",
        "evidence_type": "EXECUTION_GATE",
        "pin_status": "BLOCKED",
        "value": "false",
        "semantic_role": "NO_NUMERIC_N_OF_L_YET",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_DOI,
        "source_path": "Step 3E separation of normalization rule from executable reconstruction",
        "source_sha": "",
        "notes": "Do not confuse a pinned normalization equation with a production-ready numeric PSD. Exact m(L)/geometry remains required.",
    },
    {
        "evidence_id": "WYSER_EXACT_COLUMN_WIDTH_LAW",
        "evidence_type": "PRIMARY_GEOMETRY_REQUIREMENT",
        "pin_status": "UNRESOLVED_PRIMARY_EQUATION_5",
        "value": "PRIMARY_TEXT_CONFIRMS_CONTINUOUS_SIZE_DEPENDENT_L_TO_WIDTH_RELATION_BUT_EXACT_EQUATION_IMAGE_NOT_PROMOTED",
        "semantic_role": "WYSER_L_TO_COLUMN_WIDTH",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_DOI,
        "source_path": "Wyser (1998), equation 5",
        "source_sha": "",
        "notes": "Primary text says Eq.5 is continuous and close to Ebert-Curry. PhysicsCore refuses to replace it with a later/secondary D=0.7L / D=6.96sqrt(L) relation without exact lineage proof.",
    },
    {
        "evidence_id": "SECONDARY_COLUMN_WIDTH_LAW_CANDIDATE",
        "evidence_type": "SECONDARY_GEOMETRY_REFERENCE",
        "pin_status": "REFERENCE_ONLY_NOT_SUBSTITUTABLE",
        "value": "D=0.7L for L<100 um; D=6.96*sqrt(L) for L>=100 um appears in later column-model literature",
        "semantic_role": "GEOMETRY_CANDIDATE_FOR_LINEAGE_CHECK_ONLY",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://journals.ametsoc.org/view/journals/atsc/76/9/jas-d-19-0031.1.xml",
        "source_path": "Later Yang-lineage hexagonal-column aspect-ratio definition",
        "source_sha": "",
        "notes": "Useful for lineage comparison only. It must not be silently substituted for Wyser Eq.5.",
    },
    {
        "evidence_id": "HEX_COLUMN_MAXIMUM_DIMENSION_GEOMETRY",
        "evidence_type": "COORDINATE_GEOMETRY_REQUIREMENT",
        "pin_status": "GEOMETRIC_FORM_IDENTIFIED_NOT_WYSER_BRIDGED",
        "value": "for a prism described by axial length L and basal span D, particle maximum dimension depends on both dimensions (not L alone)",
        "semantic_role": "WHY_L_IS_NOT_AUTOMATICALLY_DMAX",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://www.giss.nasa.gov/pubs/abs/ya07100h.html",
        "source_path": "Yang/Bi maximum-dimension optical coordinate + hexagonal-prism geometry",
        "source_sha": "",
        "notes": "The Yang/Bi axis is maximum dimension. Until exact Wyser D(L) and the Yang solid-column geometry convention are matched, L cannot be used as Dmax.",
    },
    {
        "evidence_id": "WYSER_L_TO_YANG_DMAX_COORDINATE_BRIDGE",
        "evidence_type": "COORDINATE_BRIDGE_REQUIREMENT",
        "pin_status": "UNRESOLVED",
        "value": "false",
        "semantic_role": "NO_L_TO_DMAX_RUNTIME_COORDINATE",
        "authoritative_for_runtime_mapping": False,
        "source_reference": f"{_WYSER_DOI}|{_YANG_REF}",
        "source_path": "Step 3E coordinate audit",
        "source_sha": "",
        "notes": "Numerical domain overlap is insufficient. Exact geometry and Yang/Bi solid-column coordinate semantics must be demonstrated.",
    },
    {
        "evidence_id": "PSD_MASS_CLOSURE_VALIDATION_REQUIREMENT",
        "evidence_type": "VALIDATION_REQUIREMENT",
        "pin_status": "IDENTIFIED_NOT_EXECUTED",
        "value": "integral[m(L)*n(L)dL] must reproduce requested IWC within explicit numerical tolerance over the supported T/IWC domain",
        "semantic_role": "ABSOLUTE_PSD_RECONSTRUCTION_VALIDATION",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_DOI,
        "source_path": "Equations 7-8 mass closure",
        "source_sha": "",
        "notes": "This must be a numerical test before any diagnostic bulk integrator is enabled.",
    },
    {
        "evidence_id": "STEP3E_PRODUCTION_PROMOTION",
        "evidence_type": "PROMOTION_GATE",
        "pin_status": "BLOCKED",
        "value": "false",
        "semantic_role": "DIAGNOSTIC_EVIDENCE_ONLY",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "",
        "source_path": "PhysicsCore frozen promotion policy",
        "source_sha": "",
        "notes": "No Dmax synthesis, PSD runtime reconstruction, Yang/Bi bulk tau synthesis, or Formation promotion in Step 3E.",
    },
)


def build_wyser_psd_geometry_evidence() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "step3e_version": STEP3E_VERSION,
            "science_baseline": SCIENCE_BASELINE,
            "step3e_mode": STEP3E_MODE,
            **item,
        }
        for item in _EVIDENCE
    ], columns=EVIDENCE_COLUMNS)


def build_wyser_psd_geometry_gate(evidence: pd.DataFrame | None = None) -> pd.DataFrame:
    df = evidence if isinstance(evidence, pd.DataFrame) else build_wyser_psd_geometry_evidence()
    status = {str(r.get("evidence_id")): str(r.get("pin_status")) for _, r in df.iterrows()} if not df.empty else {}

    normalization_rule = status.get("WYSER_PSD_AMPLITUDE_IWC_NORMALIZATION") == "PINNED_PRIMARY_EQUATIONS_7_8"
    shape = status.get("WYSER_MIXED_PSD_SHAPE_FUNCTION") == "PINNED_PIECEWISE_SHAPE"
    continuity = status.get("WYSER_MIXED_BRANCH_CONTINUITY_FACTOR") == "PINNED_ANALYTIC_FROM_CONTINUITY"
    b_formula = status.get("WYSER_POWERLAW_B_GFSV16_SOURCE") == "PINNED_GFSV16_SOURCE_EQUIVALENT"
    mass_numeric = status.get("WYSER_NUMERIC_MASS_SIZE_CONTRACT") not in {"UNRESOLVED", "UNRESOLVED_EXACT_NUMERIC_EQUATION_6"}
    psd_executable = status.get("WYSER_ABSOLUTE_PSD_RECONSTRUCTION_EXECUTABLE") not in {"BLOCKED", "UNRESOLVED"}
    geometry = status.get("WYSER_EXACT_COLUMN_WIDTH_LAW") not in {"UNRESOLVED", "UNRESOLVED_PRIMARY_EQUATION_5"}
    coordinate = status.get("WYSER_L_TO_YANG_DMAX_COORDINATE_BRIDGE") not in {"UNRESOLVED", "BLOCKED"}
    mass_validation = status.get("PSD_MASS_CLOSURE_VALIDATION_REQUIREMENT") not in {"IDENTIFIED_NOT_EXECUTED", "UNRESOLVED"}

    eligible = bool(normalization_rule and shape and continuity and b_formula and mass_numeric and psd_executable and geometry and coordinate and mass_validation)
    blockers: list[str] = []
    if not mass_numeric: blockers.append("WYSER_NUMERIC_MASS_SIZE_CONTRACT_UNRESOLVED")
    if not psd_executable: blockers.append("ABSOLUTE_PSD_RECONSTRUCTION_NOT_EXECUTABLE")
    if not geometry: blockers.append("WYSER_EXACT_COLUMN_WIDTH_LAW_UNRESOLVED")
    if not coordinate: blockers.append("WYSER_L_TO_YANG_DMAX_COORDINATE_UNRESOLVED")
    if not mass_validation: blockers.append("PSD_MASS_CLOSURE_VALIDATION_NOT_RUN")
    blockers.extend(["YANG_BI_HABIT_BRIDGE_NOT_VALIDATED", "YANG_BI_ROUGHNESS_POLICY_NOT_VALIDATED", "NO_INDEPENDENT_BULK_OPTICS_VALIDATION"])

    return pd.DataFrame([{
        "step3e_version": STEP3E_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "step3e_mode": STEP3E_MODE,
        "WYSER_IWC_AMPLITUDE_NORMALIZATION_RULE_PINNED": normalization_rule,
        "WYSER_MIXED_PSD_SHAPE_PINNED": shape,
        "WYSER_MIXED_BRANCH_CONTINUITY_PINNED": continuity,
        "WYSER_POWERLAW_B_FORMULA_PINNED": b_formula,
        "WYSER_NUMERIC_MASS_SIZE_CONTRACT_PINNED": mass_numeric,
        "ABSOLUTE_PSD_RECONSTRUCTION_EXECUTABLE": psd_executable,
        "WYSER_EXACT_COLUMN_WIDTH_LAW_PINNED": geometry,
        "WYSER_L_TO_YANG_DMAX_COORDINATE_VALIDATED": coordinate,
        "PSD_MASS_CLOSURE_VALIDATION_PASS": mass_validation,
        "BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE": eligible,
        "GFSV16_DMAX_MAPPING_ELIGIBLE": False,
        "PRODUCTION_ICE_OPTICS_READY": False,
        "physics_promotion_allowed": False,
        "evidence_row_count": int(len(df)),
        "qualification_state": "WYSER_NORMALIZATION_RULE_PINNED_EXECUTION_GEOMETRY_BLOCKED",
        "qualification_blockers": "|".join(blockers),
        "detail": "Primary Wyser IWC-amplitude normalization rule and mixed PSD shape are pinned, but numeric m(L), exact Eq.5 geometry, L->Dmax coordinate and validation remain fail-closed.",
    }])


def wyser_psd_geometry_contract_payload(*, physicscore_version: str | None = None) -> dict[str, Any]:
    return {
        "contract_version": "FIRECLOUD_ICE_WYSER_PSD_GEOMETRY_QUALIFICATION_V1",
        "physicscore_version": physicscore_version or "",
        "step3e_version": STEP3E_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "mode": STEP3E_MODE,
        "wavelengths_nm": list(WAVELENGTHS_NM),
        "wyser_iwc_amplitude_normalization_rule_pinned": True,
        "wyser_mixed_psd_shape_pinned": True,
        "wyser_mixed_branch_continuity_pinned": True,
        "wyser_powerlaw_B_formula_pinned": True,
        "wyser_numeric_mass_size_contract_pinned": False,
        "absolute_psd_reconstruction_executable": False,
        "wyser_exact_column_width_law_pinned": False,
        "wyser_L_to_yang_dmax_coordinate_validated": False,
        "psd_mass_closure_validation_pass": False,
        "yang_bi_habit_bridge_validated": False,
        "yang_bi_roughness_bridge_validated": False,
        "bulk_yang_bi_psd_integration_eligible": False,
        "gfsv16_dmax_mapping_eligible": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "normalization_contract": {
            "shape_symbol": "phi(L;T,IWC)",
            "number_distribution": "n(L)=A(T,IWC)*phi(L;T,IWC)",
            "amplitude": "A=IWC/integral[m(L)*phi(L;T,IWC)dL]",
            "small_branch": "phi=L^3*exp(-0.3*L), L<=20 um",
            "large_branch": "phi=alpha*L^B, L>20 um",
            "continuity_factor": "alpha=20^(3-B)*exp(-0.3*20)",
            "B": "-2 + 1e-3*log10(IWC/50[g m^-3])*max(0,273.16-T[K])^1.5",
            "nominal_L_domain_um": [10.0, 1000.0],
            "execution_status": "BLOCKED_UNTIL_EXACT_M_OF_L_AND_GEOMETRY_PINNED",
        },
        "forbidden_shortcuts": [
            "secondary_column_width_law_substituted_for_Wyser_equation_5",
            "Wyser_L_silently_equal_to_Yang_Bi_Dmax",
            "PSD_amplitude_selected_without_IWC_mass_closure",
            "machine_garbled_equation_6_coefficients_used_as_runtime_mass_law",
            "absolute_PSD_reconstruction_before_exact_mass_size_contract",
            "Yang_Bi_habit_selected_before_geometry_bridge_validation",
            "single_roughness_state_silently_selected",
            "bulk_tau_synthesized_before_independent_validation",
            "production_promotion_before_step3e_and_later_gates_pass",
        ],
        "qualification_requirements": [
            "pin_exact_primary_quality_Wyser_equation_6_mass_size_density_contract",
            "pin_exact_primary_quality_Wyser_equation_5_column_width_law",
            "validate_Wyser_L_to_Yang_Bi_maximum_dimension_coordinate",
            "numerically_reproduce_IWC_mass_closure_over_supported_T_IWC_domain",
            "validate_Yang_Bi_habit_geometry_bridge",
            "validate_roughness_uncertainty_policy",
            "independent_bulk_shortwave_optics_validation",
            "separate_production_promotion_gate",
        ],
        "frozen_science_unchanged": True,
    }
