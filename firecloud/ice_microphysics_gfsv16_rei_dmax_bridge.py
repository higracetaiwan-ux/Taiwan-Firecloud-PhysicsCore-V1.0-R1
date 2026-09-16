"""Ice Optics Phase 2 Step 3C — GFS v16 rei ↔ Yang/Bi Dmax bridge audit.

This module is evidence/qualification only.  It deliberately rejects a direct
one-to-one conversion between the GFDL-v1 bulk cloud-ice effective radius
(`rei`) and the Yang/Bi single-particle maximum-dimension coordinate (`Dmax`).
It records a more defensible bulk-PSD integration path as *identified but not
qualified*; no Dmax, PSD, habit, roughness, tau, or production promotion is
created here.
"""
from __future__ import annotations

from typing import Any
import pandas as pd

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
STEP3C_VERSION = "R5.7.41.3.4.10.16"
STEP3C_MODE = "GFSV16_REI_DMAX_BRIDGE_FEASIBILITY_AUDIT_ONLY"
PHYSICS_PROMOTION_ALLOWED = False
EVIDENCE_AS_OF = "2026-09-16"

EVIDENCE_COLUMNS = [
    "step3c_version", "science_baseline", "step3c_mode", "evidence_id",
    "evidence_type", "pin_status", "value", "semantic_role",
    "authoritative_for_runtime_mapping", "source_reference", "source_path",
    "source_sha", "notes",
]

_EVIDENCE: tuple[dict[str, Any], ...] = (
    {
        "evidence_id": "GFSV16_REIFLAG2_SOURCE_FORMULA",
        "evidence_type": "PUBLIC_SOURCE_FORMULA",
        "pin_status": "PINNED_WYSER_BULK_REI_FORMULA",
        "value": "reiflag=2 branch computes rei from qmi, air density and temperature; source labels branch Wyser (1998)",
        "semantic_role": "GFDL_V1_BULK_CLOUD_ICE_EFFECTIVE_RADIUS_PARAMETERIZATION",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://github.com/ufs-community/ccpp-physics/blob/ufs/dev/physics/MP/GFDL/v1_2019/gfdl_cloud_microphys_mod.F90",
        "source_path": "physics/MP/GFDL/v1_2019/gfdl_cloud_microphys_mod.F90 :: cloud_diagnosis :: reiflag=2",
        "source_sha": "ad0304074e17a7b83be2f0fe016345b7f11be4ef",
        "notes": "The source branch computes bulk cloud-ice effective radius rei and clamps it to reimin/reimax. It does not output Yang/Bi Dmax.",
    },
    {
        "evidence_id": "REIFLAG2_DOCUMENTATION_SOURCE_LABEL_CONSISTENCY",
        "evidence_type": "PROVENANCE_CONSISTENCY",
        "pin_status": "MISMATCH",
        "value": "parameter-module comment labels reiflag=2 Donner et al. (1997), while v1_2019 source branch labels/formula path Wyser (1998)",
        "semantic_role": "DOCUMENTATION_SOURCE_SEMANTIC_MISMATCH",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://github.com/ufs-community/ccpp-physics/blob/ufs/dev/physics/MP/GFDL/module_gfdlmp_param.F90",
        "source_path": "physics/MP/GFDL/module_gfdlmp_param.F90 + physics/MP/GFDL/v1_2019/gfdl_cloud_microphys_mod.F90",
        "source_sha": "c20e229466a69f5d5e1705bded8a7b20fbd3977e|ad0304074e17a7b83be2f0fe016345b7f11be4ef",
        "notes": "Public-source formula provenance is retained, but this label mismatch is a blocker against claiming an exact production semantic contract without additional authoritative provenance.",
    },
    {
        "evidence_id": "WYSER_REI_BULK_SEMANTIC",
        "evidence_type": "PEER_REVIEWED_SEMANTIC",
        "pin_status": "PINNED_BULK_EFFECTIVE_RADIUS_SEMANTIC",
        "value": "effective radius derives from an ice-crystal population / PSD with hexagonal-column assumptions and size-dependent aspect ratio",
        "semantic_role": "BULK_EFFECTIVE_RADIUS_NOT_SINGLE_PARTICLE_DIMENSION",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://doi.org/10.1175/1520-0442(1998)011%3C1793:TERIIC%3E2.0.CO;2",
        "source_path": "Wyser (1998), The Effective Radius in Ice Clouds",
        "source_sha": "",
        "notes": "For nonspherical ice particles effective radius is not uniquely defined; it characterizes a population and its projected-area/volume moments rather than one particle's maximum dimension.",
    },
    {
        "evidence_id": "WYSER_REI_PARAMETERIZATION_INPUTS",
        "evidence_type": "PEER_REVIEWED_PARAMETERIZATION",
        "pin_status": "PINNED_IWC_T_DEPENDENCE",
        "value": "rei=f(IWC,T) parameterization",
        "semantic_role": "BULK_OPTICAL_SIZE_DIAGNOSTIC",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://doi.org/10.1175/1520-0442(1998)011%3C1793:TERIIC%3E2.0.CO;2",
        "source_path": "Wyser (1998)",
        "source_sha": "",
        "notes": "The parameterized bulk effective radius depends on ice content and temperature; this does not establish a unique particle Dmax.",
    },
    {
        "evidence_id": "YANG_BI_PRIMARY_SIZE_AXIS",
        "evidence_type": "AUTHORITATIVE_OPTICAL_SOURCE_SEMANTIC",
        "pin_status": "PINNED_MAXIMUM_DIMENSION_AXIS",
        "value": "maximum_dimension_um",
        "semantic_role": "SINGLE_PARTICLE_MAXIMUM_DIMENSION_WITH_HABIT_AND_ROUGHNESS",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://www.giss.nasa.gov/pubs/abs/ya07100h.html",
        "source_path": "Yang et al. ice-particle single-scattering database",
        "source_sha": "",
        "notes": "Yang/Bi properties are indexed by per-particle maximum dimension plus habit and roughness. Dmax spans discrete particle geometries; it is not a bulk effective radius.",
    },
    {
        "evidence_id": "DIRECT_REI_TO_DMAX_ONE_TO_ONE_BRIDGE",
        "evidence_type": "BRIDGE_ELIGIBILITY",
        "pin_status": "REJECTED_SEMANTIC_MISMATCH",
        "value": "NO_UNIQUE_ONE_TO_ONE_MAPPING",
        "semantic_role": "BULK_REI_VS_SINGLE_PARTICLE_DMAX_MISMATCH",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://doi.org/10.1175/1520-0442(1998)011%3C1793:TERIIC%3E2.0.CO;2",
        "source_path": "Step 3C semantic comparison",
        "source_sha": "",
        "notes": "Neither rei itself, 2*rei, nor a generalized effective diameter is accepted as Yang/Bi maximum_dimension_um without a same-population geometry/PSD bridge.",
    },
    {
        "evidence_id": "BULK_YANG_BI_PSD_INTEGRATION_PATH",
        "evidence_type": "ALTERNATIVE_BRIDGE_CANDIDATE",
        "pin_status": "IDENTIFIED_NOT_QUALIFIED",
        "value": "reconstruct compatible Wyser PSD/hex-column population and integrate Yang/Bi single-particle optics over Dmax",
        "semantic_role": "BULK_OPTICS_INTEGRATION_CANDIDATE_NOT_DMAX_SUBSTITUTION",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://www.sciencedirect.com/science/article/abs/pii/S0169809598000830",
        "source_path": "Wyser & Yang (1998) bulk single-scattering framework",
        "source_sha": "",
        "notes": "This is more defensible than relabeling rei as Dmax, but exact PSD, integration limits, aspect-ratio law, habit and roughness compatibility must be pinned first.",
    },
    {
        "evidence_id": "WYSER_EXACT_PSD_ASPECT_RATIO_CONTRACT",
        "evidence_type": "PSD_RECONSTRUCTION_REQUIREMENT",
        "pin_status": "UNRESOLVED",
        "value": "NOT_FULLY_PINNED",
        "semantic_role": "EXACT_PSD_COEFFICIENTS_LIMITS_AND_SIZE_DEPENDENT_COLUMN_GEOMETRY",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://doi.org/10.1175/1520-0442(1998)011%3C1793:TERIIC%3E2.0.CO;2",
        "source_path": "Wyser (1998) population model",
        "source_sha": "",
        "notes": "Exact PSD coefficients, branch/bins, integration bounds and size-dependent aspect-ratio law must be reproduced and independently checked before bulk integration is eligible.",
    },
    {
        "evidence_id": "YANG_BI_HABIT_BRIDGE",
        "evidence_type": "HABIT_MAPPING_REQUIREMENT",
        "pin_status": "UNRESOLVED",
        "value": "HEXAGONAL_COLUMN_FAMILY_CANDIDATE_NOT_VALIDATED",
        "semantic_role": "WYSER_GEOMETRY_TO_YANG_BI_HABIT_BRIDGE",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://www.giss.nasa.gov/pubs/abs/ya07100h.html",
        "source_path": "Yang/Bi habit library",
        "source_sha": "",
        "notes": "Wyser assumes hexagonal columns, but a Yang/Bi solid/hollow-column habit must not be silently selected; geometric/aspect-ratio compatibility must be validated.",
    },
    {
        "evidence_id": "YANG_BI_ROUGHNESS_BRIDGE",
        "evidence_type": "ROUGHNESS_MAPPING_REQUIREMENT",
        "pin_status": "UNRESOLVED",
        "value": "NO_FORECAST_ROUGHNESS_STATE",
        "semantic_role": "SURFACE_ROUGHNESS_UNCERTAINTY",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "https://www.giss.nasa.gov/pubs/abs/ya07100h.html",
        "source_path": "Yang/Bi roughness states",
        "source_sha": "",
        "notes": "Yang/Bi supports smooth/moderate/severe roughness; GFS v16/Wyser rei does not provide an equivalent runtime roughness state.",
    },
    {
        "evidence_id": "NCEP_PRODUCTION_BINARY_EXACT_COMMIT",
        "evidence_type": "PRODUCTION_PROVENANCE",
        "pin_status": "UNRESOLVED",
        "value": "NOT_PUBLICLY_PINNED",
        "semantic_role": "EXACT_OPERATIONAL_SOURCE_REVISION",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "",
        "source_path": "",
        "source_sha": "",
        "notes": "The public CCPP GFS_v16 suite is an emulation/reference path and is not proven byte-identical to the NCEP operational production binary.",
    },
    {
        "evidence_id": "BULK_OPTICS_UNCERTAINTY_DOMAIN",
        "evidence_type": "VALIDATION_REQUIREMENT",
        "pin_status": "UNRESOLVED",
        "value": "NO_VALIDATED_DOMAIN_OR_UNCERTAINTY_ENVELOPE",
        "semantic_role": "BULK_BRIDGE_UNCERTAINTY_AND_FAIL_CLOSE_BOUNDARIES",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "",
        "source_path": "",
        "source_sha": "",
        "notes": "No production mapping may be enabled until a domain, uncertainty envelope and fail-close boundaries are validated.",
    },
    {
        "evidence_id": "INDEPENDENT_BULK_OPTICS_VALIDATION",
        "evidence_type": "VALIDATION_REQUIREMENT",
        "pin_status": "UNRESOLVED",
        "value": "NOT_PERFORMED",
        "semantic_role": "INDEPENDENT_VALIDATION_GATE",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "",
        "source_path": "",
        "source_sha": "",
        "notes": "A future bulk-integrated Yang/Bi bridge must be validated independently before any production promotion.",
    },
)


def build_gfsv16_rei_dmax_bridge_evidence() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for item in _EVIDENCE:
        rows.append({
            "step3c_version": STEP3C_VERSION,
            "science_baseline": SCIENCE_BASELINE,
            "step3c_mode": STEP3C_MODE,
            **item,
        })
    return pd.DataFrame(rows, columns=EVIDENCE_COLUMNS)


def build_gfsv16_rei_dmax_bridge_gate(evidence: pd.DataFrame | None = None) -> pd.DataFrame:
    df = evidence if isinstance(evidence, pd.DataFrame) else build_gfsv16_rei_dmax_bridge_evidence()
    status = {str(r.get("evidence_id")): str(r.get("pin_status")) for _, r in df.iterrows()} if not df.empty else {}
    source_formula = status.get("GFSV16_REIFLAG2_SOURCE_FORMULA") == "PINNED_WYSER_BULK_REI_FORMULA"
    doc_consistent = status.get("REIFLAG2_DOCUMENTATION_SOURCE_LABEL_CONSISTENCY") != "MISMATCH"
    bulk_rei = status.get("WYSER_REI_BULK_SEMANTIC") == "PINNED_BULK_EFFECTIVE_RADIUS_SEMANTIC"
    yang_dmax = status.get("YANG_BI_PRIMARY_SIZE_AXIS") == "PINNED_MAXIMUM_DIMENSION_AXIS"
    direct_ok = False
    bulk_path = status.get("BULK_YANG_BI_PSD_INTEGRATION_PATH") == "IDENTIFIED_NOT_QUALIFIED"
    psd_pinned = status.get("WYSER_EXACT_PSD_ASPECT_RATIO_CONTRACT") != "UNRESOLVED"
    habit_valid = status.get("YANG_BI_HABIT_BRIDGE") != "UNRESOLVED"
    rough_valid = status.get("YANG_BI_ROUGHNESS_BRIDGE") != "UNRESOLVED"
    prod_commit = status.get("NCEP_PRODUCTION_BINARY_EXACT_COMMIT") != "UNRESOLVED"
    uncertainty_valid = status.get("BULK_OPTICS_UNCERTAINTY_DOMAIN") != "UNRESOLVED"
    independent_valid = status.get("INDEPENDENT_BULK_OPTICS_VALIDATION") != "UNRESOLVED"
    bulk_eligible = bool(
        bulk_path and psd_pinned and habit_valid and rough_valid and prod_commit
        and uncertainty_valid and independent_valid
    )
    blockers = []
    if not doc_consistent: blockers.append("REIFLAG2_DOCUMENTATION_SOURCE_MISMATCH")
    if not prod_commit: blockers.append("NCEP_PRODUCTION_BINARY_EXACT_COMMIT_UNRESOLVED")
    if not psd_pinned: blockers.append("WYSER_EXACT_PSD_ASPECT_RATIO_CONTRACT_UNRESOLVED")
    if not habit_valid: blockers.append("YANG_BI_HABIT_BRIDGE_UNRESOLVED")
    if not rough_valid: blockers.append("YANG_BI_ROUGHNESS_UNRESOLVED")
    if not uncertainty_valid: blockers.append("BULK_OPTICS_UNCERTAINTY_DOMAIN_UNRESOLVED")
    if not independent_valid: blockers.append("NO_INDEPENDENT_BULK_OPTICS_VALIDATION")
    row = {
        "step3c_version": STEP3C_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "step3c_mode": STEP3C_MODE,
        "GFSV16_REIFLAG2_SOURCE_FORMULA_PINNED": source_formula,
        "REIFLAG2_DOCUMENTATION_LABEL_CONSISTENT": doc_consistent,
        "GFDL_REI_IS_BULK_EFFECTIVE_RADIUS": bulk_rei,
        "YANG_BI_SIZE_AXIS_IS_MAXIMUM_DIMENSION": yang_dmax,
        "DIRECT_REI_TO_DMAX_ONE_TO_ONE_ELIGIBLE": direct_ok,
        "BULK_PSD_INTEGRATION_PATH_IDENTIFIED": bulk_path,
        "WYSER_PSD_RECONSTRUCTION_PINNED": psd_pinned,
        "YANG_BI_HABIT_BRIDGE_VALIDATED": habit_valid,
        "YANG_BI_ROUGHNESS_BRIDGE_VALIDATED": rough_valid,
        "NCEP_PRODUCTION_BINARY_EXACT_COMMIT_PINNED": prod_commit,
        "BULK_OPTICS_UNCERTAINTY_DOMAIN_VALIDATED": uncertainty_valid,
        "INDEPENDENT_BULK_OPTICS_VALIDATION_PASS": independent_valid,
        "BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE": bulk_eligible,
        "GFSV16_DMAX_MAPPING_ELIGIBLE": False,
        "PRODUCTION_ICE_OPTICS_READY": False,
        "physics_promotion_allowed": False,
        "evidence_row_count": int(len(df)),
        "qualification_state": "DIRECT_DMAX_BRIDGE_REJECTED_BULK_PSD_PATH_IDENTIFIED_NOT_QUALIFIED",
        "qualification_blockers": "|".join(blockers),
        "detail": "Direct bulk-rei→single-particle-Dmax mapping is rejected. A same-population PSD integration over Yang/Bi Dmax is identified as the candidate path but remains unqualified.",
    }
    return pd.DataFrame([row])


def gfsv16_rei_dmax_bridge_contract_payload(*, physicscore_version: str | None = None) -> dict[str, Any]:
    return {
        "contract_version": "FIRECLOUD_ICE_GFSV16_REI_DMAX_BRIDGE_FEASIBILITY_V1",
        "physicscore_version": physicscore_version or "",
        "step3c_version": STEP3C_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "mode": STEP3C_MODE,
        "source_model": "NOAA/NCEP GFS v16 / GFDL Cloud Microphysics v1-compatible public reproduction path",
        "source_size_semantic": "bulk_cloud_ice_effective_radius_rei",
        "authoritative_optical_size_axis": "maximum_dimension_um",
        "effective_radius_is_dmax": False,
        "direct_rei_to_dmax_one_to_one_eligible": False,
        "bulk_psd_integration_path_identified": True,
        "bulk_yang_bi_psd_integration_eligible": False,
        "gfsv16_dmax_mapping_eligible": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "source_documentation_label_consistent": False,
        "candidate_bridge": "reconstruct_exact_Wyser_population_then_integrate_Yang_Bi_single_particle_optics_over_Dmax",
        "forbidden_shortcuts": [
            "GFDL_rei_treated_as_Yang_Bi_Dmax",
            "Dmax_equal_2_times_rei",
            "generalized_effective_diameter_treated_as_Dmax",
            "GFDL_MPv3_PSD_substituted_for_GFSv16_v1",
            "Yang_Bi_solid_column_habit_silently_selected",
            "Yang_Bi_surface_roughness_silently_selected",
            "reimin_reimax_used_as_Dmax_bounds",
            "production_promotion_before_independent_bulk_optics_validation",
        ],
        "qualification_requirements": [
            "resolve_reiflag2_documentation_source_mismatch_or_pin_exact_production_semantics",
            "pin_exact_Wyser_PSD_coefficients_integration_limits_and_size_dependent_aspect_ratio",
            "validate_Wyser_geometry_to_Yang_Bi_habit_mapping",
            "qualify_surface_roughness_as_state_or_uncertainty_ensemble",
            "define_bulk_integration_normalization_and_six_band_outputs",
            "quantify_validity_domain_uncertainty_and_fail_close_boundaries",
            "independent_bulk_optics_validation",
            "separate_production_promotion_gate",
        ],
        "frozen_science_unchanged": True,
    }
