"""Ice Optics Phase 2 Step 2 source-capability registry.

R5.7.41.3.4.10.13 records what authoritative external forecast/model sources
actually expose for cloud-ice particle-size / PSD work.  This module is an
evidence and eligibility gate only.  It does not download a new source, infer
Dmax, create a PSD, choose habit/roughness, or promote production Ice Optics.

Frozen science remains R5.7.41.2_SHADOW_COT_AB_FROZEN.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
STEP2_VERSION = "R5.7.41.3.4.10.13"
STEP2_MODE = "SOURCE_CAPABILITY_SURVEY_ONLY"
EVIDENCE_AS_OF = "2026-09-16"
PHYSICS_PROMOTION_ALLOWED = False

SOURCE_REGISTRY_COLUMNS = [
    "step2_version", "science_baseline", "step2_mode", "source_id",
    "organization", "model_product", "source_scope", "forecast_capable",
    "taiwan_operational_coverage", "public_access_class", "runtime_ingested",
    "ice_mass_fields", "ice_number_concentration_fields", "effective_size_fields",
    "direct_dmax_fields", "psd_fields", "capability_class",
    "dmax_semantic_status", "psd_semantic_status", "mapping_eligible",
    "production_eligible", "eligibility_blockers", "evidence_as_of",
    "source_reference", "notes",
]

SOURCE_GATE_COLUMNS = [
    "step2_version", "science_baseline", "step2_mode",
    "TAIWAN_MASS_SOURCE_AVAILABLE", "TAIWAN_EFFECTIVE_SIZE_SOURCE_AVAILABLE",
    "TAIWAN_MOMENT_SOURCE_AVAILABLE", "TAIWAN_DIRECT_DMAX_SOURCE_AVAILABLE",
    "TAIWAN_PSD_SOURCE_AVAILABLE", "DMAX_SOURCE_SELECTION_ELIGIBLE",
    "PSD_SOURCE_SELECTION_ELIGIBLE", "PRODUCTION_ICE_OPTICS_READY",
    "physics_promotion_allowed", "eligible_source_count", "reference_only_source_count",
    "eligibility_state", "eligibility_blockers", "detail",
]

# The registry intentionally stores official-source URLs as provenance metadata.
# It is static in this release so a CASE can show exactly which survey contract
# was used without making a network request during a field run.
_SOURCE_ROWS: tuple[dict[str, Any], ...] = (
    {
        "source_id": "NOAA_GFS_0P25",
        "organization": "NOAA/NCEP",
        "model_product": "GFS 0.25-degree operational forecast",
        "source_scope": "GLOBAL_OPERATIONAL",
        "forecast_capable": True,
        "taiwan_operational_coverage": True,
        "public_access_class": "PUBLIC_OPERATIONAL",
        "runtime_ingested": True,
        "ice_mass_fields": "ICMR;SNMR;GRLE",
        "ice_number_concentration_fields": "",
        "effective_size_fields": "",
        "direct_dmax_fields": "",
        "psd_fields": "",
        "capability_class": "MASS_ONLY",
        "dmax_semantic_status": "NO_DIRECT_DMAX_SEMANTIC",
        "psd_semantic_status": "NO_PARTICLE_NUMBER_OR_PSD_SEMANTIC",
        "mapping_eligible": False,
        "production_eligible": False,
        "eligibility_blockers": "ICE_DMAX_NATIVE_FIELD_UNAVAILABLE|ICE_PSD_INPUT_INCOMPLETE",
        "source_reference": "https://www.nco.ncep.noaa.gov/pmb/products/gfs/",
        "notes": "Current PhysicsCore native provider. ICMR supplies cloud-ice mass only; no Dmax, ice effective radius, number concentration, PSD bins, habit, or roughness field is exposed by the current GFS ingest contract.",
    },
    {
        "source_id": "DWD_ICON_GLOBAL_OPEN",
        "organization": "DWD",
        "model_product": "ICON global open data",
        "source_scope": "GLOBAL_OPERATIONAL",
        "forecast_capable": True,
        "taiwan_operational_coverage": True,
        "public_access_class": "PUBLIC_OPERATIONAL",
        "runtime_ingested": False,
        "ice_mass_fields": "qi;tqi;tqi_dia",
        "ice_number_concentration_fields": "",
        "effective_size_fields": "",
        "direct_dmax_fields": "",
        "psd_fields": "",
        "capability_class": "MASS_ONLY",
        "dmax_semantic_status": "NO_DIRECT_DMAX_SEMANTIC",
        "psd_semantic_status": "NO_QNI_OR_PSD_FIELD_IN_SURVEYED_GLOBAL_OPEN_DIRECTORY",
        "mapping_eligible": False,
        "production_eligible": False,
        "eligibility_blockers": "ICE_DMAX_NATIVE_FIELD_UNAVAILABLE|ICE_PSD_INPUT_INCOMPLETE|SOURCE_NOT_INGESTED",
        "source_reference": "https://opendata.dwd.de/weather/nwp/icon/grib/00/",
        "notes": "Global open directory exposes qi and total-column ice products but the surveyed directory does not expose qni. Mass evidence cannot be promoted to particle size.",
    },
    {
        "source_id": "ECMWF_IFS_OPEN_DATA",
        "organization": "ECMWF",
        "model_product": "IFS Open Data public subset (Cycle 50r1)",
        "source_scope": "GLOBAL_OPERATIONAL_PUBLIC_SUBSET",
        "forecast_capable": True,
        "taiwan_operational_coverage": True,
        "public_access_class": "PUBLIC_OPERATIONAL_SUBSET",
        "runtime_ingested": False,
        "ice_mass_fields": "",
        "ice_number_concentration_fields": "",
        "effective_size_fields": "",
        "direct_dmax_fields": "",
        "psd_fields": "",
        "capability_class": "CONTEXT_ONLY",
        "dmax_semantic_status": "NO_DIRECT_DMAX_IN_PUBLIC_OPEN_PARAMETER_TABLE",
        "psd_semantic_status": "NO_PSD_OR_ICE_NUMBER_IN_PUBLIC_OPEN_PARAMETER_TABLE",
        "mapping_eligible": False,
        "production_eligible": False,
        "eligibility_blockers": "ICE_MASS_FIELD_NOT_IN_PUBLIC_OPEN_SUBSET|ICE_DMAX_NATIVE_FIELD_UNAVAILABLE|ICE_PSD_INPUT_INCOMPLETE|SOURCE_NOT_INGESTED",
        "source_reference": "https://www.ecmwf.int/en/forecasts/datasets/open-data",
        "notes": "The current public Open Data parameter table does not expose ciwc, direct ice size, ice number concentration, or PSD fields. Full IFS has additional model variables but that is a different access contract.",
    },
    {
        "source_id": "ECMWF_IFS_RADIATION_EFFECTIVE_SIZE_REFERENCE",
        "organization": "ECMWF",
        "model_product": "IFS radiation cloud-ice effective-size diagnostic",
        "source_scope": "REFERENCE_SCHEMA_ONLY",
        "forecast_capable": False,
        "taiwan_operational_coverage": False,
        "public_access_class": "DOCUMENTATION_REFERENCE",
        "runtime_ingested": False,
        "ice_mass_fields": "IWC_context",
        "ice_number_concentration_fields": "",
        "effective_size_fields": "De_ice;effective_radius",
        "direct_dmax_fields": "",
        "psd_fields": "",
        "capability_class": "EFFECTIVE_RADIUS_ONLY|REFERENCE_ONLY",
        "dmax_semantic_status": "EFFECTIVE_DIAMETER_IS_NOT_YANG_BI_DMAX",
        "psd_semantic_status": "NO_EXPLICIT_PSD_OUTPUT_CONTRACT",
        "mapping_eligible": False,
        "production_eligible": False,
        "eligibility_blockers": "EFFECTIVE_SIZE_NOT_DMAX|REFERENCE_ONLY|SOURCE_NOT_INGESTED",
        "source_reference": "https://www.ecmwf.int/en/publications/ifs-documentation",
        "notes": "IFS radiation documentation derives an ice effective diameter/radius from temperature and in-cloud ice water content. This is a radiation effective-size diagnostic, not a Yang/Bi maximum-dimension field and is not authorized as an r_eff/De-to-Dmax conversion.",
    },
    {
        "source_id": "NASA_GEOS_FP_5_43",
        "organization": "NASA GMAO",
        "model_product": "GEOS-FP 5.43.0",
        "source_scope": "GLOBAL_OPERATIONAL",
        "forecast_capable": True,
        "taiwan_operational_coverage": True,
        "public_access_class": "PUBLIC_PRODUCT_SPECIFICATION",
        "runtime_ingested": False,
        "ice_mass_fields": "QI;QS",
        "ice_number_concentration_fields": "",
        "effective_size_fields": "",
        "direct_dmax_fields": "",
        "psd_fields": "",
        "capability_class": "MASS_ONLY",
        "dmax_semantic_status": "NO_DIRECT_DMAX_IN_2026_FILE_SPEC",
        "psd_semantic_status": "NO_ICE_NUMBER_OR_PSD_IN_FORECAST_STATE_COLLECTIONS",
        "mapping_eligible": False,
        "production_eligible": False,
        "eligibility_blockers": "ICE_DMAX_NATIVE_FIELD_UNAVAILABLE|ICE_PSD_INPUT_INCOMPLETE|SOURCE_NOT_INGESTED",
        "source_reference": "https://gmao.gsfc.nasa.gov/publications/office_notes/",
        "notes": "GEOS-FP forecast-capable assimilated-state collections expose QI/QL/QR/QS mass fractions. The 2026 file specification does not expose RICE/direct ice effective radius/Dmax in the standard forecast state, so this remains mass-only for PhysicsCore Phase 2.",
    },
    {
        "source_id": "NOAA_RAP_NATIVE_REFERENCE",
        "organization": "NOAA/NCEP",
        "model_product": "Rapid Refresh (RAP) native/hybrid forecast",
        "source_scope": "NORTH_AMERICA_REFERENCE_ONLY",
        "forecast_capable": True,
        "taiwan_operational_coverage": False,
        "public_access_class": "PUBLIC_REGIONAL_OPERATIONAL",
        "runtime_ingested": False,
        "ice_mass_fields": "CIMIXR;SNMR;GRLE",
        "ice_number_concentration_fields": "NCCICE",
        "effective_size_fields": "",
        "direct_dmax_fields": "",
        "psd_fields": "",
        "capability_class": "MASS_PLUS_NUMBER_MOMENT|REFERENCE_ONLY",
        "dmax_semantic_status": "NO_DIRECT_DMAX_FIELD",
        "psd_semantic_status": "MASS_PLUS_NUMBER_IS_NOT_A_FULL_PSD_WITHOUT_SCHEME_CONTRACT",
        "mapping_eligible": False,
        "production_eligible": False,
        "eligibility_blockers": "NO_TAIWAN_COVERAGE|ICE_DMAX_NATIVE_FIELD_UNAVAILABLE|PSD_MAPPING_REQUIRES_SCHEME_CONTRACT|SOURCE_NOT_INGESTED",
        "source_reference": "https://www.nco.ncep.noaa.gov/pmb/products/rap/",
        "notes": "Useful reference proving an operational model can expose cloud-ice mass plus ice number concentration. RAP covers North America, not Taiwan; NCCICE+CIMIXR still require an explicit scheme-specific distribution/mass-size contract before any Dmax/PSD derivation.",
    },
)


def build_source_capability_registry() -> pd.DataFrame:
    """Return the frozen Step-2 external-source capability survey."""
    rows: list[dict[str, Any]] = []
    for spec in _SOURCE_ROWS:
        row = {c: None for c in SOURCE_REGISTRY_COLUMNS}
        row.update({
            "step2_version": STEP2_VERSION,
            "science_baseline": SCIENCE_BASELINE,
            "step2_mode": STEP2_MODE,
            "evidence_as_of": EVIDENCE_AS_OF,
        })
        row.update(spec)
        rows.append(row)
    return pd.DataFrame(rows, columns=SOURCE_REGISTRY_COLUMNS)


def build_source_eligibility_gate(registry: pd.DataFrame | None = None) -> pd.DataFrame:
    """Fail closed unless a Taiwan-capable source proves Dmax/PSD semantics."""
    r = build_source_capability_registry() if registry is None else registry.copy()
    taiwan = r[r.get("taiwan_operational_coverage", pd.Series(dtype=bool)).fillna(False).astype(bool)] if not r.empty else pd.DataFrame()

    def has_class(token: str) -> bool:
        if taiwan.empty or "capability_class" not in taiwan.columns:
            return False
        return taiwan["capability_class"].astype(str).str.contains(token, regex=False).any()

    mapping_eligible_count = int(r.get("mapping_eligible", pd.Series(dtype=bool)).fillna(False).astype(bool).sum()) if not r.empty else 0
    reference_only_count = int(r.get("capability_class", pd.Series(dtype=str)).astype(str).str.contains("REFERENCE_ONLY", regex=False).sum()) if not r.empty else 0
    blockers = [
        "NO_TAIWAN_DIRECT_DMAX_SOURCE",
        "NO_TAIWAN_PSD_SOURCE",
        "EFFECTIVE_RADIUS_OR_DIAMETER_IS_NOT_DMAX",
        "MASS_PLUS_NUMBER_REQUIRES_SCHEME_SPECIFIC_PSD_CONTRACT",
        "ICE_HABIT_UNRESOLVED",
        "ICE_ROUGHNESS_UNRESOLVED",
    ]
    rec = {
        "step2_version": STEP2_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "step2_mode": STEP2_MODE,
        "TAIWAN_MASS_SOURCE_AVAILABLE": bool(has_class("MASS_ONLY") or has_class("MASS_PLUS_NUMBER_MOMENT")),
        "TAIWAN_EFFECTIVE_SIZE_SOURCE_AVAILABLE": bool(has_class("EFFECTIVE_RADIUS_ONLY")),
        "TAIWAN_MOMENT_SOURCE_AVAILABLE": bool(has_class("MASS_PLUS_NUMBER_MOMENT")),
        "TAIWAN_DIRECT_DMAX_SOURCE_AVAILABLE": bool(has_class("DMAX_CAPABLE")),
        "TAIWAN_PSD_SOURCE_AVAILABLE": bool(has_class("PSD_CAPABLE")),
        "DMAX_SOURCE_SELECTION_ELIGIBLE": False,
        "PSD_SOURCE_SELECTION_ELIGIBLE": False,
        "PRODUCTION_ICE_OPTICS_READY": False,
        "physics_promotion_allowed": False,
        "eligible_source_count": mapping_eligible_count,
        "reference_only_source_count": reference_only_count,
        "eligibility_state": "NO_AUTHORITATIVE_TAIWAN_SIZE_OR_PSD_SOURCE",
        "eligibility_blockers": "|".join(blockers),
        "detail": "Global Taiwan-capable candidates remain mass/context-only; no surveyed source directly supplies Yang/Bi-compatible Dmax or a production-eligible PSD. RAP mass+NCCICE is reference-only and outside Taiwan.",
    }
    return pd.DataFrame([rec], columns=SOURCE_GATE_COLUMNS)


def source_registry_contract_payload(*, physicscore_version: str) -> dict[str, Any]:
    """Machine-readable Step-2 source-selection contract for every CASE."""
    return {
        "contract_version": "FIRECLOUD_ICE_MICROPHYSICS_SOURCE_REGISTRY_V1",
        "step2_version": STEP2_VERSION,
        "physicscore_version": str(physicscore_version),
        "science_baseline": SCIENCE_BASELINE,
        "mode": STEP2_MODE,
        "evidence_as_of": EVIDENCE_AS_OF,
        "physics_promotion_allowed": False,
        "authoritative_runtime_size_axis": "maximum_dimension_um",
        "capability_classes": {
            "MASS_ONLY": "cloud-ice mass is available but no particle-size/number/PSD semantic is proven",
            "EFFECTIVE_RADIUS_ONLY": "effective radius/diameter may exist but is not maximum dimension",
            "MASS_PLUS_NUMBER_MOMENT": "bulk ice mass plus ice number concentration; still requires an explicit microphysics scheme/PSD contract",
            "DMAX_CAPABLE": "direct provider field proven semantically compatible with maximum particle dimension",
            "PSD_CAPABLE": "provider exposes a documented PSD or sufficient scheme parameters under an explicit source contract",
            "REFERENCE_ONLY": "may inform model design/validation but cannot drive Taiwan operational runtime",
            "CONTEXT_ONLY": "thermodynamic/cloud context only; no ice-size mapping authorization",
        },
        "dmax_source_requires": [
            "Taiwan operational coverage for the requested forecast valid time",
            "raw provider field with direct maximum-dimension semantics",
            "units directly convertible to micrometres without a physical-shape assumption",
            "run/cycle/valid-time/vertical-level/provider provenance",
            "cloud-ice population compatibility with the Yang/Bi LUT contract",
            "finite positive values inside the authorized LUT domain",
        ],
        "psd_source_requires": [
            "Taiwan operational coverage for the requested forecast valid time",
            "native PSD bins or a documented microphysics distribution/moment contract",
            "mass-size/density/habit assumptions sourced from the same compatible scheme or a separately validated mapping contract",
            "explicit units, vertical semantics, validity domain, uncertainty and fail-close behavior",
            "independent validation before any production promotion",
        ],
        "forbidden_shortcuts": [
            "effective_radius_to_Dmax_without_validated_contract",
            "effective_diameter_to_Dmax_without_validated_contract",
            "IWC_or_IWP_to_Dmax",
            "temperature_to_Dmax",
            "cloud_fraction_or_RH_to_Dmax",
            "mass_plus_number_to_Dmax_without_scheme_specific_distribution_contract",
            "assumed_PSD",
            "fixed_habit_default",
            "fixed_surface_roughness_default",
            "reference_only_source_used_as_Taiwan_operational_source",
        ],
        "current_state": "NO_AUTHORITATIVE_TAIWAN_SIZE_OR_PSD_SOURCE",
        "frozen_science_unchanged": True,
    }
