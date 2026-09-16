"""Ice Optics Phase 2 Step 3 global mapping-candidate intake.

R5.7.41.3.4.10.14 is a qualification/evidence layer only.  It identifies
scheme-level candidates that *might* support a future Dmax/PSD mapping, with
GLOBAL forecast coverage as the preferred operational criterion.  No mapping
formula is executed here and no candidate is authorized to promote Ice Optics.

Frozen science remains R5.7.41.2_SHADOW_COT_AB_FROZEN.
"""
from __future__ import annotations

from typing import Any
import pandas as pd

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
STEP3_VERSION = "R5.7.41.3.4.10.14"
STEP3_MODE = "GLOBAL_MAPPING_CANDIDATE_QUALIFICATION_ONLY"
EVIDENCE_AS_OF = "2026-09-16"
PHYSICS_PROMOTION_ALLOWED = False
GLOBAL_COVERAGE_PREFERRED = True

CANDIDATE_COLUMNS = [
    "step3_version", "science_baseline", "step3_mode", "candidate_id",
    "organization", "model_product", "temporal_status", "source_scope",
    "global_coverage", "taiwan_coverage", "current_operational",
    "public_forecast_data", "runtime_ingested", "microphysics_scheme",
    "scheme_identity_status", "ice_mass_state", "ice_number_state",
    "psd_scheme_state", "size_semantic_state", "direct_dmax_state",
    "reconstruction_path", "investigation_priority", "qualification_state",
    "mapping_candidate_eligible", "production_eligible", "qualification_blockers",
    "evidence_as_of", "source_reference", "scheme_reference", "notes",
]

GATE_COLUMNS = [
    "step3_version", "science_baseline", "step3_mode", "global_coverage_preferred",
    "GLOBAL_CURRENT_OPERATIONAL_CANDIDATE_IDENTIFIED",
    "GLOBAL_FUTURE_MOMENT_CANDIDATE_IDENTIFIED",
    "GLOBAL_EXPLICIT_PSD_REFERENCE_IDENTIFIED",
    "CURRENT_GLOBAL_DIRECT_DMAX_ELIGIBLE",
    "CURRENT_GLOBAL_SCHEME_PSD_RECONSTRUCTION_ELIGIBLE",
    "MAPPING_CANDIDATE_ELIGIBLE", "PRODUCTION_ICE_OPTICS_READY",
    "physics_promotion_allowed", "primary_investigation_target",
    "eligible_candidate_count", "qualification_state", "qualification_blockers", "detail",
]

_CANDIDATES: tuple[dict[str, Any], ...] = (
    {
        "candidate_id": "NOAA_GFS_V16_GFDL_MP_CURRENT",
        "organization": "NOAA/NCEP",
        "model_product": "Operational GFS v16 global forecast",
        "temporal_status": "CURRENT_OPERATIONAL_2026_09_16",
        "source_scope": "GLOBAL_OPERATIONAL",
        "global_coverage": True,
        "taiwan_coverage": True,
        "current_operational": True,
        "public_forecast_data": True,
        "runtime_ingested": True,
        "microphysics_scheme": "GFDL Cloud Microphysics",
        "scheme_identity_status": "FAMILY_CONFIRMED_EXACT_RUNTIME_REVISION_NOT_PINNED",
        "ice_mass_state": "NATIVE_GFS_ICMR_AVAILABLE",
        "ice_number_state": "NOT_EXPOSED_BY_CURRENT_PHYSICSCORE_GFS_CONTRACT",
        "psd_scheme_state": "SCHEME_LEVEL_PSD_RECONSTRUCTION_POTENTIALLY_AVAILABLE_AFTER_EXACT_REVISION_PIN",
        "size_semantic_state": "SCHEME_PARTICLE_DIAMETER_NOT_YET_PROVEN_YANG_BI_DMAX_COMPATIBLE",
        "direct_dmax_state": "NO_DIRECT_PROVIDER_DMAX_FIELD",
        "reconstruction_path": "SCHEME_SPECIFIC_SINGLE_MOMENT_PSD_RECONSTRUCTION_CANDIDATE",
        "investigation_priority": 1,
        "qualification_state": "BLOCKED_EXACT_RUNTIME_SCHEME_CONTRACT_NOT_PINNED",
        "mapping_candidate_eligible": False,
        "production_eligible": False,
        "qualification_blockers": "EXACT_GFSV16_MICROPHYSICS_REVISION_UNPINNED|OPERATIONAL_NAMELIST_PROVENANCE_REQUIRED|PSD_PARAMETER_SET_NOT_RUNTIME_PINNED|DIAMETER_TO_YANG_BI_DMAX_SEMANTICS_UNPROVEN|HABIT_UNRESOLVED|ROUGHNESS_UNRESOLVED",
        "source_reference": "https://www.emc.ncep.noaa.gov/emc/pages/numerical_forecast_systems/gfs/documentation.php",
        "scheme_reference": "https://dtcenter.ucar.edu/GMTB/v7.0.0/sci_doc/_g_f_s_v16_page.html",
        "notes": "Highest-priority current global candidate because PhysicsCore already ingests GFS mass fields. GFS v16 is confirmed to use GFDL Cloud Microphysics, but CCPP documentation emulates the operational implementation; exact runtime source revision and scheme parameters must be pinned before reconstructing PSD/size.",
    },
    {
        "candidate_id": "NOAA_GFS_V17_THOMPSON_FUTURE",
        "organization": "NOAA/NCEP",
        "model_product": "Proposed GFS v17 global forecast",
        "temporal_status": "PROPOSED_FOR_2026_10_OPERATIONAL_UPGRADE",
        "source_scope": "GLOBAL_FUTURE_OPERATIONAL_CANDIDATE",
        "global_coverage": True,
        "taiwan_coverage": True,
        "current_operational": False,
        "public_forecast_data": False,
        "runtime_ingested": False,
        "microphysics_scheme": "Thompson Cloud Microphysics (GFS v17 prototype/non-aerosol configuration)",
        "scheme_identity_status": "PROTOTYPE_SCHEME_CONFIRMED_OPERATIONAL_RELEASE_NOT_YET_ACTIVE",
        "ice_mass_state": "SCHEME_PROGNOSTIC_QI",
        "ice_number_state": "SCHEME_PROGNOSTIC_ICE_NUMBER_CONCENTRATION",
        "psd_scheme_state": "MASS_PLUS_NUMBER_AND_INTERNAL_ICE_DISTRIBUTION_LOGIC_DOCUMENTED",
        "size_semantic_state": "SCHEME_SIZE_DISTRIBUTION_PRESENT_BUT_PROVIDER_OUTPUT_CONTRACT_UNPROVEN",
        "direct_dmax_state": "NO_CONFIRMED_GLOBAL_PROVIDER_DMAX_OUTPUT",
        "reconstruction_path": "FUTURE_GLOBAL_MASS_PLUS_NUMBER_SCHEME_CANDIDATE",
        "investigation_priority": 2,
        "qualification_state": "BLOCKED_NOT_CURRENT_OPERATIONAL_AND_OUTPUT_CONTRACT_UNPROVEN",
        "mapping_candidate_eligible": False,
        "production_eligible": False,
        "qualification_blockers": "GFSV17_NOT_OPERATIONAL_AS_OF_2026_09_16|FINAL_OPERATIONAL_SCHEME_REVISION_UNPINNED|PUBLIC_ICE_NUMBER_OUTPUT_UNPROVEN|DIAMETER_TO_YANG_BI_DMAX_SEMANTICS_UNPROVEN|HABIT_UNRESOLVED|ROUGHNESS_UNRESOLVED",
        "source_reference": "https://www.weather.gov/media/notification/pdf_2026/pns26-29_Science_for_GFSv17.pdf",
        "scheme_reference": "https://dtcenter.ucar.edu/GMTB/v7.0.0/sci_doc/_g_f_s_v17_p8_ugwpv1_page.html",
        "notes": "Strong future global candidate because Thompson predicts cloud-ice number concentration in addition to ice mass and contains explicit ice-distribution logic. It cannot drive current PhysicsCore until the operational v17 release, exact scheme revision, and public output fields are verified.",
    },
    {
        "candidate_id": "DWD_ICON_GLOBAL_SINGLE_MOMENT_CURRENT",
        "organization": "DWD",
        "model_product": "ICON global operational forecast",
        "temporal_status": "CURRENT_OPERATIONAL",
        "source_scope": "GLOBAL_OPERATIONAL",
        "global_coverage": True,
        "taiwan_coverage": True,
        "current_operational": True,
        "public_forecast_data": True,
        "runtime_ingested": False,
        "microphysics_scheme": "ICON single-moment cloud microphysics (global/coarse-grid operational family)",
        "scheme_identity_status": "GLOBAL_FAMILY_DOCUMENTED_EXACT_RUNTIME_CONFIGURATION_REQUIRES_PIN",
        "ice_mass_state": "QI_AVAILABLE_IN_GLOBAL_OPEN_DATA",
        "ice_number_state": "QNI_NOT_EXPOSED_IN_SURVEYED_GLOBAL_OPEN_DATA",
        "psd_scheme_state": "SINGLE_MOMENT_SCHEME_RECONSTRUCTION_REQUIRES_EXACT_OPERATIONAL_PARAMETERS",
        "size_semantic_state": "SCHEME_SIZE_RELATIONS_NOT_AUTHORIZED_AS_YANG_BI_DMAX",
        "direct_dmax_state": "NO_DIRECT_PROVIDER_DMAX_FIELD",
        "reconstruction_path": "SCHEME_SPECIFIC_SINGLE_MOMENT_PSD_RECONSTRUCTION_CANDIDATE",
        "investigation_priority": 3,
        "qualification_state": "BLOCKED_EXACT_OPERATIONAL_CONFIGURATION_AND_SIZE_SEMANTICS_UNPROVEN",
        "mapping_candidate_eligible": False,
        "production_eligible": False,
        "qualification_blockers": "SOURCE_NOT_INGESTED|ICON_GLOBAL_OPERATIONAL_SCHEME_CONFIG_UNPINNED|QNI_NOT_PUBLIC_GLOBAL_OUTPUT|DIAMETER_TO_YANG_BI_DMAX_SEMANTICS_UNPROVEN|HABIT_UNRESOLVED|ROUGHNESS_UNRESOLVED",
        "source_reference": "https://opendata.dwd.de/weather/nwp/icon/grib/",
        "scheme_reference": "https://dwd.de/EN/ourservices/nwp_icon_tutorial/pdf_volume/icon_tutorial2025_en.pdf?__blob=publicationFile&v=3",
        "notes": "Global and operational. DWD documents both single- and double-moment ICON schemes; the double-moment option is targeted at ~3 km convection-permitting scales, so it must not be assumed for global operational ICON. Global open data surveyed so far exposes qi but not qni.",
    },
    {
        "candidate_id": "GFDL_SHIELD_MPV3_GLOBAL_REFERENCE",
        "organization": "NOAA/GFDL",
        "model_product": "SHiELD global forecast with GFDL MP v3",
        "temporal_status": "GLOBAL_RESEARCH_REALTIME_REFERENCE",
        "source_scope": "GLOBAL_RESEARCH_FORECAST_REFERENCE",
        "global_coverage": True,
        "taiwan_coverage": True,
        "current_operational": False,
        "public_forecast_data": False,
        "runtime_ingested": False,
        "microphysics_scheme": "GFDL MP v3",
        "scheme_identity_status": "EXPLICIT_SCHEME_VERSION_DOCUMENTED",
        "ice_mass_state": "SCHEME_PROGNOSTIC_MASS",
        "ice_number_state": "SINGLE_MOMENT_DERIVED_FROM_SCHEME_PSD",
        "psd_scheme_state": "EXPLICIT_GAMMA_PSD_WITH_N0_MU_AND_LAMBDA_DERIVABLE_FROM_Q",
        "size_semantic_state": "SCHEME_DIAMETER_DEFINED_BUT_NONSHPHERICAL_YANG_BI_HABIT_MAPPING_UNRESOLVED",
        "direct_dmax_state": "NO_PROVIDER_DIRECT_DMAX_FIELD",
        "reconstruction_path": "EXPLICIT_PSD_MATHEMATICS_REFERENCE",
        "investigation_priority": 4,
        "qualification_state": "REFERENCE_ONLY_NOT_CURRENT_OPERATIONAL_SOURCE",
        "mapping_candidate_eligible": False,
        "production_eligible": False,
        "qualification_blockers": "NOT_CURRENT_OPERATIONAL_SOURCE|NOT_PHYSICSCORE_RUNTIME_PROVIDER|GFDL_MPV3_NOT_PROVEN_IDENTICAL_TO_GFSV16_RUNTIME|HABIT_UNRESOLVED|ROUGHNESS_UNRESOLVED",
        "source_reference": "https://www.gfdl.noaa.gov/shield/",
        "scheme_reference": "https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2021MS002971",
        "notes": "Best global mathematical reference for a scheme-native PSD reconstruction: GFDL MP v3 defines a gamma PSD and derives slope from prognostic mass in the single-moment formulation. It is deliberately isolated from GFS v16 because version identity is not established.",
    },
    {
        "candidate_id": "ECMWF_IFS_EFFECTIVE_DIMENSION_CURRENT",
        "organization": "ECMWF",
        "model_product": "IFS global operational radiation effective-size diagnostic",
        "temporal_status": "CURRENT_OPERATIONAL_REFERENCE_SEMANTIC",
        "source_scope": "GLOBAL_OPERATIONAL_REFERENCE",
        "global_coverage": True,
        "taiwan_coverage": True,
        "current_operational": True,
        "public_forecast_data": True,
        "runtime_ingested": False,
        "microphysics_scheme": "IFS stratiform cloud + radiation effective-size diagnostic",
        "scheme_identity_status": "DOCUMENTED_EFFECTIVE_SIZE_SEMANTIC",
        "ice_mass_state": "IFS_MODEL_HAS_PROGNOSTIC_CLOUD_ICE_AND_SNOW",
        "ice_number_state": "NO_PUBLIC_OPERATIONAL_ICE_NUMBER_CONTRACT",
        "psd_scheme_state": "NO_EXPLICIT_PROVIDER_PSD_OUTPUT_FOR_PHYSICSCORE",
        "size_semantic_state": "EFFECTIVE_DIAMETER_FROM_T_AND_IWC_NOT_MAXIMUM_DIMENSION",
        "direct_dmax_state": "NO_DIRECT_DMAX",
        "reconstruction_path": "EFFECTIVE_SIZE_REFERENCE_ONLY",
        "investigation_priority": 5,
        "qualification_state": "BLOCKED_SIZE_SEMANTIC_MISMATCH",
        "mapping_candidate_eligible": False,
        "production_eligible": False,
        "qualification_blockers": "EFFECTIVE_DIAMETER_NOT_DMAX|SOURCE_NOT_INGESTED|NO_VALIDATED_EFFECTIVE_SIZE_TO_DMAX_CONTRACT|HABIT_UNRESOLVED|ROUGHNESS_UNRESOLVED",
        "source_reference": "https://www.ecmwf.int/en/forecasts/datasets/open-data",
        "scheme_reference": "https://www.ecmwf.int/en/publications/ifs-documentation",
        "notes": "IFS provides a physically documented ice effective dimension/radius diagnostic for radiation. It remains useful for validation/context, but effective diameter is not authorized as Yang/Bi maximum dimension.",
    },
    {
        "candidate_id": "NASA_GEOS_FP_CURRENT",
        "organization": "NASA/GMAO",
        "model_product": "GEOS-FP 5.43 global forecast",
        "temporal_status": "CURRENT_OPERATIONAL",
        "source_scope": "GLOBAL_OPERATIONAL",
        "global_coverage": True,
        "taiwan_coverage": True,
        "current_operational": True,
        "public_forecast_data": True,
        "runtime_ingested": False,
        "microphysics_scheme": "GEOS cloud microphysics/radiation",
        "scheme_identity_status": "FORECAST_PRODUCT_FIELDS_DOCUMENTED",
        "ice_mass_state": "QI_QS_AVAILABLE",
        "ice_number_state": "NOT_IN_STANDARD_FORECAST_STATE",
        "psd_scheme_state": "NO_PUBLIC_FORECAST_PSD_CONTRACT",
        "size_semantic_state": "NO_STANDARD_FORECAST_SIZE_FIELD",
        "direct_dmax_state": "NO_DIRECT_DMAX",
        "reconstruction_path": "MASS_ONLY_NO_MAPPING_CANDIDATE_YET",
        "investigation_priority": 6,
        "qualification_state": "BLOCKED_INSUFFICIENT_PARTICLE_SIZE_STATE",
        "mapping_candidate_eligible": False,
        "production_eligible": False,
        "qualification_blockers": "SOURCE_NOT_INGESTED|ICE_NUMBER_UNAVAILABLE|PSD_CONTRACT_UNAVAILABLE|DIRECT_SIZE_UNAVAILABLE|HABIT_UNRESOLVED|ROUGHNESS_UNRESOLVED",
        "source_reference": "https://gmao.gsfc.nasa.gov/geos-system-news/geos-fp-upgrade-to-system-version-5430-on-feb-26-2026/",
        "scheme_reference": "https://gmao.gsfc.nasa.gov/publications/office_notes/",
        "notes": "Global operational forecast source with cloud-ice mass, but current public forecast collections do not expose sufficient particle-size/number/PSD state for a mapping candidate.",
    },
)


def build_global_mapping_candidate_registry() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for spec in _CANDIDATES:
        row = {c: None for c in CANDIDATE_COLUMNS}
        row.update({
            "step3_version": STEP3_VERSION,
            "science_baseline": SCIENCE_BASELINE,
            "step3_mode": STEP3_MODE,
            "evidence_as_of": EVIDENCE_AS_OF,
        })
        row.update(spec)
        rows.append(row)
    return pd.DataFrame(rows, columns=CANDIDATE_COLUMNS).sort_values(
        ["investigation_priority", "candidate_id"], kind="stable"
    ).reset_index(drop=True)


def build_global_mapping_qualification_gate(registry: pd.DataFrame | None = None) -> pd.DataFrame:
    r = build_global_mapping_candidate_registry() if registry is None else registry.copy()
    current_global = r[
        r.get("global_coverage", pd.Series(dtype=bool)).fillna(False).astype(bool)
        & r.get("current_operational", pd.Series(dtype=bool)).fillna(False).astype(bool)
    ] if not r.empty else pd.DataFrame()
    future_moment = False
    explicit_psd_ref = False
    if not r.empty:
        future_moment = bool(
            r["reconstruction_path"].astype(str).str.contains("MASS_PLUS_NUMBER", regex=False).any()
        )
        explicit_psd_ref = bool(
            r["psd_scheme_state"].astype(str).str.contains("EXPLICIT_GAMMA_PSD", regex=False).any()
        )
    eligible_count = int(r.get("mapping_candidate_eligible", pd.Series(dtype=bool)).fillna(False).astype(bool).sum()) if not r.empty else 0
    primary = "NOAA_GFS_V16_GFDL_MP_CURRENT" if "candidate_id" in r.columns and (r["candidate_id"] == "NOAA_GFS_V16_GFDL_MP_CURRENT").any() else "NONE"
    blockers = [
        "NO_EXACT_RUNTIME_SCHEME_CONTRACT_PINNED",
        "NO_YANG_BI_DMAX_SEMANTIC_BRIDGE_VALIDATED",
        "ICE_HABIT_UNRESOLVED",
        "ICE_ROUGHNESS_UNRESOLVED",
        "NO_INDEPENDENT_MAPPING_VALIDATION",
    ]
    rec = {
        "step3_version": STEP3_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "step3_mode": STEP3_MODE,
        "global_coverage_preferred": True,
        "GLOBAL_CURRENT_OPERATIONAL_CANDIDATE_IDENTIFIED": bool(not current_global.empty),
        "GLOBAL_FUTURE_MOMENT_CANDIDATE_IDENTIFIED": future_moment,
        "GLOBAL_EXPLICIT_PSD_REFERENCE_IDENTIFIED": explicit_psd_ref,
        "CURRENT_GLOBAL_DIRECT_DMAX_ELIGIBLE": False,
        "CURRENT_GLOBAL_SCHEME_PSD_RECONSTRUCTION_ELIGIBLE": False,
        "MAPPING_CANDIDATE_ELIGIBLE": False,
        "PRODUCTION_ICE_OPTICS_READY": False,
        "physics_promotion_allowed": False,
        "primary_investigation_target": primary,
        "eligible_candidate_count": eligible_count,
        "qualification_state": "GLOBAL_CANDIDATES_IDENTIFIED_QUALIFICATION_NOT_COMPLETE",
        "qualification_blockers": "|".join(blockers),
        "detail": "Global-first candidate intake is complete. Current GFS v16 is the primary investigation target because it is global, operational, and already ingested, but no PSD/Dmax reconstruction is authorized until the exact operational microphysics revision/configuration and size semantics are pinned and independently validated.",
    }
    return pd.DataFrame([rec], columns=GATE_COLUMNS)


def global_mapping_candidate_contract_payload(*, physicscore_version: str) -> dict[str, Any]:
    return {
        "contract_version": "FIRECLOUD_ICE_GLOBAL_MAPPING_CANDIDATE_V1",
        "step3_version": STEP3_VERSION,
        "physicscore_version": str(physicscore_version),
        "science_baseline": SCIENCE_BASELINE,
        "mode": STEP3_MODE,
        "evidence_as_of": EVIDENCE_AS_OF,
        "global_coverage_preferred": True,
        "physics_promotion_allowed": False,
        "authoritative_runtime_size_axis": "maximum_dimension_um",
        "primary_investigation_target": "NOAA_GFS_V16_GFDL_MP_CURRENT",
        "global_candidate_requires": [
            "global forecast coverage including Taiwan",
            "current operational status for production selection; future systems remain candidates only",
            "exact model and microphysics scheme identity including source revision/tag/commit where available",
            "exact operational namelist/configuration affecting ice PSD/effective size",
            "traceable provider run/cycle/valid-time/vertical-level provenance",
            "hydrometeor population identity: cloud ice must be distinguished from snow/graupel/hail",
            "scheme-native PSD equation and every required parameter from the same compatible scheme",
            "scheme-native mass-size/density relation and units",
            "proof that the scheme size variable is geometrically/semantically compatible with Yang/Bi maximum_dimension_um or a separately validated bridge",
            "authorized input domain, uncertainty, fail-close behavior, QA and independent validation",
            "habit and surface roughness mapping resolved by evidence rather than defaults before production promotion",
        ],
        "forbidden_shortcuts": [
            "GFDL_MPv3_parameters_assumed_identical_to_GFSv16_without_version_proof",
            "GFSv17_Thompson_assumed_operational_before_implementation",
            "ICON_double_moment_assumed_for_global_operational_grid",
            "effective_radius_or_effective_diameter_treated_as_Dmax",
            "mass_only_treated_as_PSD_without_exact_scheme_contract",
            "mass_plus_number_treated_as_Dmax_without_distribution_and_mass_size_contract",
            "scheme_particle_diameter_treated_as_Yang_Bi_Dmax_without_semantic_validation",
            "fixed_habit_default",
            "fixed_surface_roughness_default",
            "research_reference_promoted_as_operational_provider",
        ],
        "current_state": "GLOBAL_CANDIDATES_IDENTIFIED_QUALIFICATION_NOT_COMPLETE",
        "frozen_science_unchanged": True,
    }
