"""Ice Optics Phase 2 Step 3Q.1 — Fu96/RRTMG band-weighting semantic narrowing.

This step refines Step 3Q without promoting exact historical weighting.  Peer-reviewed
Fu-lineage and RRTMG-band integrations establish the physically appropriate semantic
class for shortwave band averaging: solar-spectrum weighting, with SSA derived from
band-integrated scattering/extinction and asymmetry factor scattering-weighted.

The historical Fu96 -> RRTM/RRTMG default-table transformation still remains fail-closed
unless its version-pinned pre-averaging samples, exact solar spectrum / discrete weights,
and reproduction of the archived band-24/25 tables are recovered.
"""
from __future__ import annotations
from typing import Any
import json
import pandas as pd
from . import __version__ as PHYSICSCORE_VERSION

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
STEP3Q_VERSION = "R5.7.41.3.4.10.30.1"
STEP3Q_MODE = "FU96_RRTMG_BAND_WEIGHTING_SEMANTIC_NARROWING_FAIL_CLOSED"
EVIDENCE_AS_OF = "2026-09-18"

FU96_DOI = "https://doi.org/10.1175/1520-0442(1996)009<2058:AAPOTS>2.0.CO;2"
FU2007_DOI = "https://doi.org/10.1175/2007JAS2289.1"
YI2013_DOI = "https://doi.org/10.1175/JAS-D-13-020.1"
BAEK2018_DOI = "https://doi.org/10.1029/2018MS001398"
AER_RRTMG_SW_REPOSITORY = "https://github.com/AER-RC/RRTMG_SW"
AER_RRTM_SW_INSTRUCTIONS = "https://github.com/AER-RC/RRTM_SW/blob/master/rrtm_sw_instructions"
GEOSCHEM_RRTMG_PINNED_SOURCE = (
    "https://github.com/geoschem/geos-chem/blob/"
    "a4551f9442183bb572b23e9c2d362e2d34420d3a/GeosRad/rrtmg_sw_init.F90"
)
GEOSCHEM_RRTMG_SOURCE_SHA = "0ccf597d6aa3d6ed40ec592560e3ed94b653ef32"
RRTMG_BANDS = (24, 25)


def _row(check_id: str, category: str, status: str, observed: str, required: str, notes: str = "") -> dict[str, Any]:
    return {
        "check_id": check_id,
        "category": category,
        "status": status,
        "observed": observed,
        "required": required,
        "physics_promotion_allowed": False,
        "notes": notes,
    }


def build_fu96_rrtmg_band_weighting_provenance_evidence() -> pd.DataFrame:
    rows = [
        _row(
            "FU96_PRIMARY_SOLAR_ICE_PARAMETERIZATION_PINNED", "PRIMARY_SCIENCE_SOURCE", "PASS_PINNED",
            "Fu 1996 solar cirrus parameterization; Dge-based extinction/SSA framework; spectral averaging is scientifically material",
            "PRIMARY_FU96_SOURCE_PINNED", FU96_DOI,
        ),
        _row(
            "FU96_SSA_SPECTRAL_AVERAGING_SIGNIFICANCE", "PRIMARY_SCIENCE_SOURCE", "PASS_CONFIRMED",
            "Fu 1996 identifies SSA averaging technique in absorption-band spectral intervals as important",
            "AVERAGING_SEMANTICS_MUST_NOT_BE_REPLACED_BY_ARBITRARY_MEAN",
            "Primary source establishes materiality but not the later historical RRTM_SW discrete weight vector.",
        ),
        _row(
            "FU96_LINEAGE_SOLAR_IRRADIANCE_WEIGHTING_SEMANTIC", "WEIGHTING_SEMANTICS", "PASS_CONFIRMED",
            "Fu 2007 states that calculations following Fu 1996 divide the solar spectrum into Fu96 bands and weight data with solar irradiance to obtain band averages",
            "SOLAR_IRRADIANCE_WEIGHTING_SEMANTIC_CLASS_SUPPORTED", FU2007_DOI,
        ),
        _row(
            "RRTMG_SW_BAND_INTEGRATION_FORMULA_SEMANTIC", "WEIGHTING_SEMANTICS", "PASS_QUALIFIED",
            "Yi 2013 RRTMG-band ice optics integrates SW properties over wavelength with solar spectrum S(lambda); SSA is derived from integrated scattering/extinction and g is scattering-weighted",
            "RRTMG_COMPATIBLE_SW_BAND_INTEGRATION_SEMANTIC_CLASS_QUALIFIED", YI2013_DOI,
        ),
        _row(
            "RRTMG_SW_BAND_LIMITS_24_25_PINNED", "SPECTRAL_DOMAIN", "PASS_PINNED",
            "RRTMG band 24 = 0.63-0.78 um; band 25 = 0.44-0.63 um in Yi 2013; Baek 2018 independently documents RRTMG spectral-band averaging and band 25 near 0.44-0.63 um",
            "BAND_24_25_LIMITS_PINNED", f"{YI2013_DOI}; {BAEK2018_DOI}",
        ),
        _row(
            "RRTMG_ICEFLAG3_FU96_DGE_LINEAGE", "MODEL_LINEAGE", "PASS_PINNED",
            "RRTM/RRTMG SW ICEFLAG=3 uses Fu (1996) generalized effective size Dge; valid 5-140 um",
            "FU96_DGE_LINEAGE_PINNED", AER_RRTM_SW_INSTRUCTIONS,
        ),
        _row(
            "RRTMG_FU96_FINAL_BAND_TABLES_PINNED", "MODEL_REFERENCE_TABLE", "PASS_PINNED",
            "Final band-24/band-25 Fu96 extice3/ssaice3/asyice3 reference tables are available in pinned RRTMG implementation source",
            "FINAL_REFERENCE_TABLES_PINNED", f"{GEOSCHEM_RRTMG_PINNED_SOURCE}; source_sha={GEOSCHEM_RRTMG_SOURCE_SHA}",
        ),
        _row(
            "RRTMG_HIGH_RES_TO_BAND_LINEAGE_STATEMENT", "MODEL_LINEAGE", "PASS_LINEAGE_ONLY",
            "RRTMG lineage documents that Fu high-resolution ice optical tables were averaged for RRTM_SW",
            "LINEAGE_STATEMENT_IS_NOT_EQUIVALENT_TO_REPRODUCIBLE_WEIGHT_VECTOR",
            "The final tables and semantic class are known; the exact historical transformation remains unrecovered.",
        ),
        _row(
            "FU96_RRTMG_PREAVERAGING_SPECTRAL_SAMPLE_SET", "EXACT_WEIGHTING_PREREQUISITE", "BLOCKED_NOT_RECOVERED",
            "No version-pinned authoritative pre-averaging spectral sample set tied to the archived default RRTMG band-24/25 Fu96 tables has been recovered",
            "EXACT_PREAVERAGING_SPECTRAL_SAMPLES_REQUIRED",
        ),
        _row(
            "FU96_RRTMG_EXACT_SOLAR_SPECTRUM_AND_DISCRETE_WEIGHTS", "EXACT_WEIGHTING_PREREQUISITE", "BLOCKED_NOT_RECOVERED",
            "Solar-irradiance weighting is supported as the semantic class, but the exact historical solar spectrum version, sampling grid, and discrete weights used to generate the archived default Fu96 RRTMG tables are not recovered",
            "VERSION_PINNED_SOLAR_SPECTRUM_PLUS_DISCRETE_WEIGHT_VECTOR_OR_EXACTLY_EQUIVALENT_ALGORITHM_REQUIRED",
        ),
        _row(
            "FU96_RRTMG_WEIGHTING_SEMANTICS_CLASS", "EXACT_WEIGHTING_PREREQUISITE", "PASS_NARROWED_NOT_EXACT",
            "Qualified class: SW solar-spectrum weighting; SSA from integrated scattering/extinction; g scattering-weighted. Historical exact spectrum/sample realization remains unresolved",
            "SEMANTIC_CLASS_QUALIFIED_BUT_HISTORICAL_EXACT_REALIZATION_STILL_REQUIRED",
        ),
        _row(
            "FU96_RRTMG_BAND24_EXACT_REPRODUCTION", "NUMERIC_REPRODUCTION", "BLOCKED_NO_EXACT_WEIGHT_VECTOR",
            "not executed", "REPRODUCE_PINNED_RRTMG_BAND24_REFERENCE_FROM_AUTHORITATIVE_HISTORICAL_INPUTS",
        ),
        _row(
            "FU96_RRTMG_BAND25_EXACT_REPRODUCTION", "NUMERIC_REPRODUCTION", "BLOCKED_NO_EXACT_WEIGHT_VECTOR",
            "not executed", "REPRODUCE_PINNED_RRTMG_BAND25_REFERENCE_FROM_AUTHORITATIVE_HISTORICAL_INPUTS",
        ),
        _row("ARBITRARY_EQUAL_WEIGHT_SUBSTITUTE", "SCOPE_GUARD", "PASS_FORBIDDEN", "false", "MUST_NOT_SUBSTITUTE_FOR_EXACT_FU96_RRTMG_WEIGHTING"),
        _row("UNVERSIONED_OR_ASSUMED_SOLAR_SPECTRUM_WEIGHTS", "SCOPE_GUARD", "PASS_FORBIDDEN", "false", "SOLAR_WEIGHTING_CLASS_IS_SUPPORTED_BUT_EXACT_HISTORICAL_SPECTRUM_AND_WEIGHTS_MUST_BE_PINNED"),
        _row("GPOINT_WEIGHT_SUBSTITUTE", "SCOPE_GUARD", "PASS_FORBIDDEN", "false", "MUST_NOT_BE_ASSUMED_AS_THE_CLOUD_OPTICS_BAND_AVERAGING_RULE"),
        _row("AD_HOC_EXTINCTION_OR_SCATTERING_WEIGHT_SUBSTITUTE", "SCOPE_GUARD", "PASS_FORBIDDEN", "false", "ONLY_THE_QUALIFIED_SSA_AND_G_FORMULAS_MAY_BE_USED; NO_AD_HOC_REWEIGHTING"),
        _row(
            "EXACT_FU96_RRTMG_BAND_WEIGHTING", "QUALIFICATION_RESULT", "BLOCKED_NOT_PROVEN", "false",
            "PREAVERAGING_SAMPLES_PLUS_VERSION_PINNED_SOLAR_SPECTRUM_AND_DISCRETE_WEIGHTS_PLUS_NUMERIC_REPRODUCTION_REQUIRED",
        ),
        _row(
            "YANG_FULL_SPECTRAL_BAND_INTEGRATION_VALIDATION", "DOWNSTREAM_BLOCKER", "BLOCKED", "false",
            "EXACT_FU96_RRTMG_BAND_WEIGHTING_REQUIRED_BEFORE_LIKE_FOR_LIKE_YANG_INTEGRATION",
        ),
        _row(
            "PRODUCTION_PROMOTION_GUARD", "PRODUCTION_GUARD", "PASS_FAIL_CLOSED",
            "independent_ssa=false; independent_g=false; tau_ice=false; production_ice_optics=false; physics_promotion=false",
            "NO_STEP3Q1_PRODUCTION_PROMOTION",
        ),
    ]
    return pd.DataFrame(rows)


def build_fu96_rrtmg_band_weighting_provenance_gate(evidence: pd.DataFrame | None = None) -> pd.DataFrame:
    evidence = evidence if evidence is not None else build_fu96_rrtmg_band_weighting_provenance_evidence()
    status = {str(r.check_id): str(r.status) for r in evidence.itertuples(index=False)}
    primary = status.get("FU96_PRIMARY_SOLAR_ICE_PARAMETERIZATION_PINNED") == "PASS_PINNED"
    lineage = status.get("RRTMG_ICEFLAG3_FU96_DGE_LINEAGE") == "PASS_PINNED"
    tables = status.get("RRTMG_FU96_FINAL_BAND_TABLES_PINNED") == "PASS_PINNED"
    semantic = status.get("FU96_RRTMG_WEIGHTING_SEMANTICS_CLASS") == "PASS_NARROWED_NOT_EXACT"
    band_limits = status.get("RRTMG_SW_BAND_LIMITS_24_25_PINNED") == "PASS_PINNED"
    exact = status.get("EXACT_FU96_RRTMG_BAND_WEIGHTING") == "PASS"
    state = (
        "PASS_EXACT_WEIGHTING_PROVENANCE_QUALIFIED" if primary and lineage and tables and semantic and exact
        else "PASS_FAIL_CLOSED_WEIGHTING_SEMANTIC_CLASS_QUALIFIED_EXACT_HISTORY_UNRESOLVED"
    )
    return pd.DataFrame([{
        "qualification_state": state,
        "FU96_PRIMARY_SOURCE_PINNED": bool(primary),
        "RRTMG_FU96_DGE_LINEAGE_PINNED": bool(lineage),
        "RRTMG_FINAL_FU96_BAND_TABLES_PINNED": bool(tables),
        "RRTMG_BAND24_25_LIMITS_PINNED": bool(band_limits),
        "SOLAR_IRRADIANCE_WEIGHTING_SEMANTIC_SUPPORTED": True,
        "RRTMG_BAND_INTEGRATION_SEMANTIC_CLASS_QUALIFIED": bool(semantic),
        "PREAVERAGING_SPECTRAL_SAMPLES_RECOVERED": False,
        "EXACT_HISTORICAL_SOLAR_SPECTRUM_AND_WEIGHTS_RECOVERED": False,
        "HISTORICAL_EXACT_WEIGHTING_REALIZATION_UNAMBIGUOUS": False,
        "RRTMG_BAND24_EXACT_REPRODUCTION_PASS": False,
        "RRTMG_BAND25_EXACT_REPRODUCTION_PASS": False,
        "EXACT_FU96_BAND_WEIGHTING_AVAILABLE": False,
        "BAND_INTEGRATED_OPTICAL_VALIDATION_READY": False,
        "INDEPENDENT_SSA_VALIDATION_PASS": False,
        "INDEPENDENT_ASYMMETRY_VALIDATION_PASS": False,
        "FULL_SIX_BAND_LIKE_FOR_LIKE_OPTICAL_VALIDATION_PASS": False,
        "TAU_ICE_PRODUCTION_ALLOWED": False,
        "PRODUCTION_ICE_OPTICS_READY": False,
        "physics_promotion_allowed": False,
    }])


def fu96_rrtmg_band_weighting_provenance_contract_payload(*, evidence: pd.DataFrame | None = None, gate: pd.DataFrame | None = None, physicscore_version: str = PHYSICSCORE_VERSION) -> dict[str, Any]:
    evidence = evidence if evidence is not None else build_fu96_rrtmg_band_weighting_provenance_evidence()
    gate = gate if gate is not None else build_fu96_rrtmg_band_weighting_provenance_gate(evidence)
    g = gate.iloc[0].to_dict()
    return {
        "contract_version": "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_1",
        "physicscore_version": str(physicscore_version),
        "step_version": STEP3Q_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "mode": STEP3Q_MODE,
        "evidence_as_of": EVIDENCE_AS_OF,
        "sources": {
            "fu96_doi": FU96_DOI,
            "fu2007_doi": FU2007_DOI,
            "yi2013_doi": YI2013_DOI,
            "baek2018_doi": BAEK2018_DOI,
            "aer_rrtmg_sw_repository": AER_RRTMG_SW_REPOSITORY,
            "aer_rrtm_sw_instructions": AER_RRTM_SW_INSTRUCTIONS,
            "pinned_rrtmg_reference_source": GEOSCHEM_RRTMG_PINNED_SOURCE,
            "pinned_rrtmg_reference_source_sha": GEOSCHEM_RRTMG_SOURCE_SHA,
        },
        "bands": list(RRTMG_BANDS),
        "qualified_weighting_semantic_class": {
            "shortwave_spectral_weighting": "solar_spectrum_S_lambda",
            "single_scattering_albedo": "band_integrated_scattering_divided_by_band_integrated_extinction",
            "asymmetry_factor": "scattering_cross_section_weighted_with_solar_spectrum",
            "historical_exact_solar_spectrum_and_discrete_weights_recovered": False,
        },
        "qualification_state": str(g["qualification_state"]),
        "capabilities": {k: bool(v) for k, v in g.items() if k != "qualification_state"},
        "forbidden_substitutes": [
            "equal_weighting",
            "unversioned_or_assumed_solar_spectrum_weights",
            "assumed_gpoint_weighting_for_cloud_optics_band_average",
            "ad_hoc_extinction_or_scattering_reweighting_outside_qualified_formulas",
        ],
        "production_guards": {"tau_ice_production_allowed": False, "production_ice_optics_ready": False, "physics_promotion_allowed": False},
        "scope_note": (
            "Step 3Q.1 narrows the physically supported RRTMG-compatible shortwave band-integration semantic class. "
            "It does not claim recovery of the exact historical Fu96-to-default-RRTMG discrete weighting realization. "
            "Exact weighting and production gates remain fail-closed."
        ),
    }


def serialize_fu96_rrtmg_band_weighting_provenance_contract_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
