"""Ice Optics Phase 2 Step 3D — Wyser PSD + Yang/Bi bulk-integration qualification.

Evidence/contract only.  This module pins the parts of the Wyser (1998)
particle population that are explicitly recoverable from primary/public sources
and defines the mathematical form of a future Yang/Bi PSD integration.  It does
not reconstruct a runtime PSD, select a Yang/Bi habit/roughness state, synthesize
Dmax, or promote Ice Optics into Formation.
"""
from __future__ import annotations

from typing import Any
import pandas as pd

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
STEP3D_VERSION = "R5.7.41.3.4.10.17"
STEP3D_MODE = "WYSER_PSD_YANG_BI_HABIT_BULK_INTEGRATION_QUALIFICATION_ONLY"
PHYSICS_PROMOTION_ALLOWED = False
EVIDENCE_AS_OF = "2026-09-17"
WAVELENGTHS_NM = [550, 575, 600, 650, 700, 750]

EVIDENCE_COLUMNS = [
    "step3d_version", "science_baseline", "step3d_mode", "evidence_id",
    "evidence_type", "pin_status", "value", "semantic_role",
    "authoritative_for_runtime_mapping", "source_reference", "source_path",
    "source_sha", "notes",
]

_EVIDENCE: tuple[dict[str, Any], ...] = (
    {
        "evidence_id": "WYSER_MIXED_PSD_STRUCTURE",
        "evidence_type": "PEER_REVIEWED_PSD_STRUCTURE",
        "pin_status": "PINNED_MIXED_GAMMA_POWERLAW",
        "value": "Gamma small-particle branch through 20 um; power-law branch above 20 um; continuity enforced at 20 um",
        "semantic_role": "WYSER_MIXED_POPULATION_STRUCTURE",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://doi.org/10.1175/1520-0442(1998)011%3C1793:TERIIC%3E2.0.CO;2",
        "source_path": "Wyser (1998), mixed distribution section",
        "source_sha": "",
        "notes": "The article explicitly selects the mixed spectrum for the remainder of the work. This pins the branch structure, not the full absolute normalization needed for runtime reconstruction.",
    },
    {
        "evidence_id": "WYSER_SMALL_PARTICLE_GAMMA_PARAMETERS",
        "evidence_type": "PEER_REVIEWED_PSD_PARAMETERS",
        "pin_status": "PINNED_NU3_LAMBDA0P3_SWITCH20UM",
        "value": "nu=3; lambda=0.3 um^-1; small-particle branch L<=20 um",
        "semantic_role": "SMALL_CRYSTAL_GAMMA_SHAPE_PARAMETERS",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://doi.org/10.1175/1520-0442(1998)011%3C1793:TERIIC%3E2.0.CO;2",
        "source_path": "Wyser (1998), mixed distribution",
        "source_sha": "",
        "notes": "These constants are explicit in the article text. They constrain shape of the small-particle spectrum but do not determine the complete number-density normalization.",
    },
    {
        "evidence_id": "WYSER_DEFAULT_INTEGRATION_LIMITS",
        "evidence_type": "PEER_REVIEWED_INTEGRATION_DOMAIN",
        "pin_status": "PINNED_L10_L1000_UM",
        "value": "Lmin=10 um; Lmax=1000 um unless stated otherwise",
        "semantic_role": "WYSER_PARTICLE_LENGTH_INTEGRATION_DOMAIN",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://doi.org/10.1175/1520-0442(1998)011%3C1793:TERIIC%3E2.0.CO;2",
        "source_path": "Wyser (1998), section 5 Integration limits",
        "source_sha": "",
        "notes": "The article also reports sensitivity to both limits. L is retained as Wyser crystal length; it is not silently relabeled Yang/Bi maximum dimension.",
    },
    {
        "evidence_id": "WYSER_POWERLAW_B_T_IWC_FORMULA",
        "evidence_type": "PUBLIC_SOURCE_PARAMETERIZATION",
        "pin_status": "PINNED_GFSV16_SOURCE_EQUIVALENT",
        "value": "B=-2 + 1e-3*log10(IWC/IWC0)*max(0,Tice-T)^1.5 with IWC0=50 g m^-3 (unit-equivalent to source rho0=50e-3 kg m^-3)",
        "semantic_role": "GFSV16_WYSER_POWERLAW_SLOPE_CONTROL",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://github.com/ufs-community/ccpp-physics/blob/ufs/dev/physics/MP/GFDL/v1_2019/gfdl_cloud_microphys_mod.F90",
        "source_path": "cloud_diagnosis :: reiflag=2 :: bw",
        "source_sha": "ad0304074e17a7b83be2f0fe016345b7f11be4ef",
        "notes": "The public GFDL v1 source exposes the numerical B expression used before the cubic rei fit. This pins the slope-control formula on the public reproduction path, not the full production PSD normalization.",
    },
    {
        "evidence_id": "WYSER_GAMMA_POWERLAW_CONTINUITY_RULE",
        "evidence_type": "PEER_REVIEWED_PSD_JOIN_RULE",
        "pin_status": "PINNED_CONTINUITY_AT_20UM",
        "value": "alpha selected so n(L) is continuous at L=20 um",
        "semantic_role": "PSD_BRANCH_JOIN_CONSTRAINT",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://doi.org/10.1175/1520-0442(1998)011%3C1793:TERIIC%3E2.0.CO;2",
        "source_path": "Wyser (1998), mixed distribution",
        "source_sha": "",
        "notes": "Continuity is pinned, but the exact absolute amplitude/normalization of n(L) still requires a complete reproducible contract.",
    },
    {
        "evidence_id": "WYSER_ABSOLUTE_PSD_NORMALIZATION",
        "evidence_type": "PSD_RECONSTRUCTION_REQUIREMENT",
        "pin_status": "UNRESOLVED",
        "value": "NO_COMPLETE_REPRODUCIBLE_NUMBER_DENSITY_NORMALIZATION_CONTRACT",
        "semantic_role": "ABSOLUTE_N_OF_L_REQUIRED_FOR_BULK_OPTICS",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://doi.org/10.1175/1520-0442(1998)011%3C1793:TERIIC%3E2.0.CO;2",
        "source_path": "Wyser (1998), equations 13-15 and associated amplitude definitions",
        "source_sha": "",
        "notes": "The accessible primary text pins the mixed structure and join rule, but this audit does not yet claim a fully independently reproduced absolute n(L) normalization across the operational domain.",
    },
    {
        "evidence_id": "WYSER_HEX_COLUMN_GEOMETRY_FAMILY",
        "evidence_type": "PEER_REVIEWED_GEOMETRY",
        "pin_status": "PINNED_HEXAGONAL_COLUMNS_SIZE_DEPENDENT_ASPECT_RATIO",
        "value": "all crystals assumed hexagonal columns; aspect ratio depends on particle size",
        "semantic_role": "WYSER_PARTICLE_GEOMETRY_FAMILY",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://doi.org/10.1175/1520-0442(1998)011%3C1793:TERIIC%3E2.0.CO;2",
        "source_path": "Wyser (1998), abstract/microphysical geometry",
        "source_sha": "",
        "notes": "Geometry family is pinned; exact size-dependent width/length law remains a separate requirement.",
    },
    {
        "evidence_id": "WYSER_HEX_COLUMN_ASPECT_RATIO_LAW",
        "evidence_type": "GEOMETRY_RECONSTRUCTION_REQUIREMENT",
        "pin_status": "UNRESOLVED_PRIMARY_CONTRACT",
        "value": "EXACT_WIDTH_LENGTH_LAW_NOT_YET_PRIMARY_PINNED_IN_THIS_RELEASE",
        "semantic_role": "L_TO_PARTICLE_GEOMETRY_AND_DMAX_COORDINATE",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://doi.org/10.1175/1520-0442(1998)011%3C1793:TERIIC%3E2.0.CO;2",
        "source_path": "Wyser (1998) + Wyser/Yang geometry lineage",
        "source_sha": "",
        "notes": "Secondary literature exposes candidate column size relations, but this release does not promote them without a primary-source geometry contract tied to the exact population used by the GFS-v16 rei branch.",
    },
    {
        "evidence_id": "YANG_BI_DMAX_DOMAIN",
        "evidence_type": "AUTHORITATIVE_OPTICAL_DOMAIN",
        "pin_status": "PINNED_DMAX_2_TO_10000_UM",
        "value": "maximum dimension D spans 2 to 10000 um",
        "semantic_role": "YANG_BI_SINGLE_PARTICLE_DMAX_DOMAIN",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://doi.org/10.1175/JAS-D-12-039.1",
        "source_path": "Yang et al. (2013) single-scattering library",
        "source_sha": "",
        "notes": "The optical library domain covers the nominal Wyser length range numerically, but numerical range overlap is not proof that Wyser L equals Yang/Bi Dmax.",
    },
    {
        "evidence_id": "YANG_BI_SOLID_COLUMN_HABIT_CANDIDATE",
        "evidence_type": "HABIT_BRIDGE_CANDIDATE",
        "pin_status": "IDENTIFIED_NOT_VALIDATED",
        "value": "solid_column",
        "semantic_role": "HEXAGONAL_COLUMN_FAMILY_CANDIDATE",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://doi.org/10.1175/JAS-D-12-039.1",
        "source_path": "Yang et al. (2013) habit library",
        "source_sha": "",
        "notes": "Yang/Bi includes a solid hexagonal column habit, which is the nearest family-level candidate to Wyser's hexagonal columns. Exact aspect-ratio/volume/projected-area compatibility is not yet validated.",
    },
    {
        "evidence_id": "YANG_BI_ROUGHNESS_STATES",
        "evidence_type": "AUTHORITATIVE_ROUGHNESS_DOMAIN",
        "pin_status": "PINNED_THREE_STATES",
        "value": "smooth|moderate|severe",
        "semantic_role": "YANG_BI_SURFACE_ROUGHNESS_AXIS",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://doi.org/10.1175/JAS-D-12-039.1",
        "source_path": "Yang et al. (2013) library",
        "source_sha": "",
        "notes": "The library exposes three roughness conditions, while the GFS-v16/Wyser state contains no corresponding runtime roughness variable.",
    },
    {
        "evidence_id": "ROUGHNESS_UNCERTAINTY_ENSEMBLE",
        "evidence_type": "UNCERTAINTY_TREATMENT_CANDIDATE",
        "pin_status": "IDENTIFIED_NOT_VALIDATED",
        "value": "evaluate smooth/moderate/severe as a diagnostic uncertainty ensemble",
        "semantic_role": "NO_SILENT_SINGLE_ROUGHNESS_DEFAULT",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://doi.org/10.1175/JAS-D-12-039.1",
        "source_path": "Step 3D candidate uncertainty treatment",
        "source_sha": "",
        "notes": "An ensemble is safer than silently fixing one roughness state, but sensitivity thresholds and production policy are not yet validated.",
    },
    {
        "evidence_id": "BULK_INTEGRATION_NORMALIZATION",
        "evidence_type": "MATHEMATICAL_CONTRACT",
        "pin_status": "PINNED_MATHEMATICAL_CONTRACT",
        "value": "beta_ext=integral[n(D) Cext(D,lambda)dD]; beta_sca=integral[n(D) Csca(D,lambda)dD]; omega=beta_sca/beta_ext; g=integral[n Csca g dD]/beta_sca; k_ext=beta_ext/IWC; tau=IWP*k_ext",
        "semantic_role": "PSD_WEIGHTED_BULK_SINGLE_SCATTERING_NORMALIZATION",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2018MS001398",
        "source_path": "Yang-library single-particle A/Qext/omega/g to bulk optical integration contract",
        "source_sha": "",
        "notes": "Mathematics is pinned as a future contract only. It is not executed until PSD coordinate, normalization, habit, roughness, and validation gates pass.",
    },
    {
        "evidence_id": "SIX_BAND_BULK_OUTPUT_CONTRACT",
        "evidence_type": "FROZEN_SPECTRAL_CONTRACT",
        "pin_status": "PINNED_550_575_600_650_700_750_NM",
        "value": "550|575|600|650|700|750 nm",
        "semantic_role": "FROZEN_SIX_BAND_BULK_OUTPUT",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "",
        "source_path": "PhysicsCore frozen science baseline",
        "source_sha": "",
        "notes": "Any future bulk integration must preserve all six bands end-to-end; no pre-merge is allowed.",
    },
    {
        "evidence_id": "WYSER_L_TO_YANG_DMAX_COORDINATE_BRIDGE",
        "evidence_type": "COORDINATE_BRIDGE_REQUIREMENT",
        "pin_status": "UNRESOLVED",
        "value": "NUMERICAL_DOMAIN_OVERLAP_ONLY_NOT_SEMANTIC_EQUIVALENCE",
        "semantic_role": "PARTICLE_LENGTH_TO_MAXIMUM_DIMENSION_MAPPING",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://doi.org/10.1175/1520-0442(1998)011%3C1793:TERIIC%3E2.0.CO;2|https://doi.org/10.1175/JAS-D-12-039.1",
        "source_path": "Step 3D geometry/coordinate comparison",
        "source_sha": "",
        "notes": "Wyser uses crystal length L and size-dependent aspect ratio. Yang/Bi indexes by maximum dimension D. Exact geometry must prove how L maps to D for every integrated particle size.",
    },
    {
        "evidence_id": "INDEPENDENT_BULK_INTEGRATION_VALIDATION",
        "evidence_type": "VALIDATION_REQUIREMENT",
        "pin_status": "UNRESOLVED",
        "value": "NOT_PERFORMED",
        "semantic_role": "REFERENCE_BULK_OPTICS_COMPARISON_GATE",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://www.sciencedirect.com/science/article/abs/pii/S0169809598000830",
        "source_path": "Future comparison against published Wyser/Yang bulk shortwave behavior and/or an independent RT implementation",
        "source_sha": "",
        "notes": "No production promotion until the integrated six-band results are compared against an independent reference with explicit tolerances.",
    },
)


def build_wyser_yang_bulk_evidence() -> pd.DataFrame:
    rows = [
        {
            "step3d_version": STEP3D_VERSION,
            "science_baseline": SCIENCE_BASELINE,
            "step3d_mode": STEP3D_MODE,
            **item,
        }
        for item in _EVIDENCE
    ]
    return pd.DataFrame(rows, columns=EVIDENCE_COLUMNS)


def build_wyser_yang_bulk_gate(evidence: pd.DataFrame | None = None) -> pd.DataFrame:
    df = evidence if isinstance(evidence, pd.DataFrame) else build_wyser_yang_bulk_evidence()
    status = {str(r.get("evidence_id")): str(r.get("pin_status")) for _, r in df.iterrows()} if not df.empty else {}

    psd_core = status.get("WYSER_MIXED_PSD_STRUCTURE") == "PINNED_MIXED_GAMMA_POWERLAW"
    gamma = status.get("WYSER_SMALL_PARTICLE_GAMMA_PARAMETERS") == "PINNED_NU3_LAMBDA0P3_SWITCH20UM"
    limits = status.get("WYSER_DEFAULT_INTEGRATION_LIMITS") == "PINNED_L10_L1000_UM"
    b_formula = status.get("WYSER_POWERLAW_B_T_IWC_FORMULA") == "PINNED_GFSV16_SOURCE_EQUIVALENT"
    normalization = status.get("WYSER_ABSOLUTE_PSD_NORMALIZATION") != "UNRESOLVED"
    geometry = status.get("WYSER_HEX_COLUMN_ASPECT_RATIO_LAW") not in {"UNRESOLVED", "UNRESOLVED_PRIMARY_CONTRACT"}
    habit_candidate = status.get("YANG_BI_SOLID_COLUMN_HABIT_CANDIDATE") == "IDENTIFIED_NOT_VALIDATED"
    habit_valid = False
    roughness_valid = False
    bulk_math = status.get("BULK_INTEGRATION_NORMALIZATION") == "PINNED_MATHEMATICAL_CONTRACT"
    six_band = status.get("SIX_BAND_BULK_OUTPUT_CONTRACT") == "PINNED_550_575_600_650_700_750_NM"
    coordinate_valid = status.get("WYSER_L_TO_YANG_DMAX_COORDINATE_BRIDGE") != "UNRESOLVED"
    independent_valid = status.get("INDEPENDENT_BULK_INTEGRATION_VALIDATION") != "UNRESOLVED"

    eligible = bool(
        psd_core and gamma and limits and b_formula and normalization and geometry
        and habit_valid and roughness_valid and bulk_math and six_band
        and coordinate_valid and independent_valid
    )
    blockers = []
    if not normalization: blockers.append("WYSER_ABSOLUTE_PSD_NORMALIZATION_UNRESOLVED")
    if not geometry: blockers.append("WYSER_COLUMN_ASPECT_RATIO_LAW_UNRESOLVED")
    if not coordinate_valid: blockers.append("WYSER_L_TO_YANG_DMAX_COORDINATE_UNRESOLVED")
    if not habit_valid: blockers.append("YANG_BI_SOLID_COLUMN_HABIT_BRIDGE_NOT_VALIDATED")
    if not roughness_valid: blockers.append("YANG_BI_ROUGHNESS_POLICY_NOT_VALIDATED")
    if not independent_valid: blockers.append("NO_INDEPENDENT_BULK_INTEGRATION_VALIDATION")

    return pd.DataFrame([{
        "step3d_version": STEP3D_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "step3d_mode": STEP3D_MODE,
        "WYSER_PSD_CORE_STRUCTURE_PINNED": psd_core,
        "WYSER_SMALL_PARTICLE_GAMMA_PINNED": gamma,
        "WYSER_INTEGRATION_LIMITS_PINNED": limits,
        "WYSER_POWERLAW_B_FORMULA_PINNED": b_formula,
        "WYSER_ABSOLUTE_PSD_NORMALIZATION_PINNED": normalization,
        "WYSER_COLUMN_GEOMETRY_PINNED": geometry,
        "YANG_BI_SOLID_COLUMN_CANDIDATE_IDENTIFIED": habit_candidate,
        "YANG_BI_HABIT_BRIDGE_VALIDATED": habit_valid,
        "YANG_BI_ROUGHNESS_BRIDGE_VALIDATED": roughness_valid,
        "BULK_INTEGRATION_NORMALIZATION_PINNED": bulk_math,
        "SIX_BAND_BULK_OUTPUT_CONTRACT_PINNED": six_band,
        "WYSER_L_TO_YANG_DMAX_COORDINATE_VALIDATED": coordinate_valid,
        "INDEPENDENT_BULK_INTEGRATION_VALIDATION_PASS": independent_valid,
        "BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE": eligible,
        "GFSV16_DMAX_MAPPING_ELIGIBLE": False,
        "PRODUCTION_ICE_OPTICS_READY": False,
        "physics_promotion_allowed": False,
        "evidence_row_count": int(len(df)),
        "qualification_state": "WYSER_PSD_CORE_PINNED_GEOMETRY_HABIT_ROUGHNESS_BLOCKED",
        "qualification_blockers": "|".join(blockers),
        "detail": "Core Wyser mixed-PSD structure and future bulk-integration math are pinned, but exact normalization/geometry/Dmax-coordinate/habit/roughness/independent-validation gates remain closed.",
    }])


def wyser_yang_bulk_contract_payload(*, physicscore_version: str | None = None) -> dict[str, Any]:
    return {
        "contract_version": "FIRECLOUD_ICE_WYSER_YANG_BULK_INTEGRATION_QUALIFICATION_V1",
        "physicscore_version": physicscore_version or "",
        "step3d_version": STEP3D_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "mode": STEP3D_MODE,
        "source_population": "Wyser_1998_mixed_hexagonal_column_population_candidate",
        "authoritative_single_particle_optics": "Yang_Bi_V2_Zenodo_5348402",
        "authoritative_size_axis": "maximum_dimension_um",
        "wavelengths_nm": list(WAVELENGTHS_NM),
        "wyser_psd_core_structure_pinned": True,
        "wyser_absolute_psd_normalization_pinned": False,
        "wyser_column_geometry_pinned": False,
        "wyser_L_to_yang_dmax_coordinate_validated": False,
        "yang_bi_solid_column_candidate_identified": True,
        "yang_bi_habit_bridge_validated": False,
        "yang_bi_roughness_bridge_validated": False,
        "bulk_integration_math_pinned": True,
        "bulk_yang_bi_psd_integration_eligible": False,
        "gfsv16_dmax_mapping_eligible": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "bulk_integration_equations": {
            "C_ext": "Q_ext(D,lambda) * A_proj(D)",
            "C_sca": "omega0(D,lambda) * C_ext(D,lambda)",
            "beta_ext": "integral n(D) * C_ext(D,lambda) dD",
            "beta_sca": "integral n(D) * C_sca(D,lambda) dD",
            "omega_bulk": "beta_sca / beta_ext",
            "g_bulk": "integral n(D) * C_sca(D,lambda) * g(D,lambda) dD / beta_sca",
            "k_ext": "beta_ext / IWC",
            "tau_ice": "IWP * k_ext",
        },
        "candidate_roughness_policy": "diagnostic_three_state_ensemble_smooth_moderate_severe_not_yet_validated",
        "forbidden_shortcuts": [
            "Wyser_length_L_silently_treated_as_Yang_Bi_Dmax",
            "Wyser_hex_column_silently_treated_as_Yang_Bi_solid_column",
            "PSD_amplitude_invented_from_IWC_without_exact_contract",
            "single_roughness_state_silently_selected",
            "bulk_tau_synthesized_before_independent_validation",
            "GFDL_rei_treated_as_Yang_Bi_Dmax",
            "Dmax_equal_2_times_rei",
            "production_promotion_before_bulk_integration_qualification",
        ],
        "qualification_requirements": [
            "pin_complete_Wyser_absolute_PSD_normalization",
            "pin_primary_source_size_dependent_hex_column_geometry",
            "validate_Wyser_L_to_Yang_Bi_maximum_dimension_coordinate",
            "validate_Wyser_geometry_against_Yang_Bi_solid_column_area_volume_aspect_ratio",
            "validate_roughness_uncertainty_policy_or_obtain_runtime_roughness_state",
            "implement_diagnostic_only_six_band_bulk_integrator",
            "validate_mass_conservation_and_IWC_normalization",
            "independent_bulk_shortwave_optics_validation",
            "separate_production_promotion_gate",
        ],
        "frozen_science_unchanged": True,
    }
