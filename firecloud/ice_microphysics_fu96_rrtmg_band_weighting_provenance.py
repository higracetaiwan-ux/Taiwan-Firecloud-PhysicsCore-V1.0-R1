"""Ice Optics Phase 2 Step 3Q.4 — Fu96/RRTMG historical h-domain constraint qualification.

This step refines Step 3Q.1 without promoting exact historical weighting.  It separates
(a) historical Fu96 broadband co-albedo semantics from (b) later RRTMG-band integration
semantics.  Fu-lineage literature states that Fu (1996) used solar-weighted broadband
averaging with a mix of linear and logarithmic co-albedo averages depending on absorption
strength.  Later RRTMG-band ice-optics work provides a solar-spectrum integration formula,
but that later formula is not treated as proof of how the archived default Fu96 tables were
historically generated.

The historical Fu96 -> RRTM/RRTMG default-table transformation remains fail-closed unless
its version-pinned pre-averaging samples, band-specific Fu96 averaging realization, exact
solar spectrum / discrete weights, and reproduction of the archived band-24/25 tables are
recovered.
"""
from __future__ import annotations
from typing import Any
import json
import pandas as pd
from . import __version__ as PHYSICSCORE_VERSION

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
STEP3Q_VERSION = "R5.7.41.3.4.10.30.4"
STEP3Q_MODE = "FU96_RRTMG_HISTORICAL_H_DOMAIN_CONSTRAINT_QUALIFICATION_FAIL_CLOSED"
EVIDENCE_AS_OF = "2026-09-18"

FU96_DOI = "https://doi.org/10.1175/1520-0442(1996)009<2058:AAPOTS>2.0.CO;2"
FU2007_DOI = "https://doi.org/10.1175/2007JAS2289.1"
YI2013_DOI = "https://doi.org/10.1175/JAS-D-13-020.1"
CHOU1998_DOI = "https://doi.org/10.1175/1520-0442(1998)011<0202:PFCOAS>2.0.CO;2"
CHOU2002_DOI = "https://doi.org/10.1029/2002JD002061"
AER_RRTMG_SW_DESCRIPTION = "https://rtweb.aer.com/rrtmg_sw_description.html"
CAM5_DESCRIPTION = "https://www.cesm.ucar.edu/models/cesm1.0/cam/docs/description/cam5_desc.pdf"
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
            "FU96_HISTORICAL_COALBEDO_MIXED_LINEAR_LOG_SEMANTIC", "WEIGHTING_SEMANTICS", "PASS_CONFIRMED",
            "Fu-lineage documentation states Fu (1996) used a mix of solar-weighted linear and logarithmic averaging for single-scattering coalbedo depending on absorption strength",
            "HISTORICAL_FU96_SSA_COALBEDO_MUST_NOT_BE_REPLACED_BY_SIMPLE_LINEAR_OR_MODERN_RATIO_FORMULA", CHOU1998_DOI,
        ),

        _row(
            "FU96_LINEAGE_LINEAR_COALBEDO_EQUATION", "HISTORICAL_EQUATION_FAMILY", "PASS_QUALIFIED",
            "alpha_linear = sum(alpha_lambda * S_lambda * dLambda) / sum(S_lambda * dLambda), where alpha=1-SSA",
            "SOLAR_WEIGHTED_LINEAR_COALBEDO_EQUATION_PINNED", CHOU1998_DOI,
        ),
        _row(
            "FU96_LINEAGE_LOG_COALBEDO_EQUATION", "HISTORICAL_EQUATION_FAMILY", "PASS_QUALIFIED",
            "ln(alpha_log) = sum(ln(alpha_lambda) * S_lambda * dLambda) / sum(S_lambda * dLambda)",
            "SOLAR_WEIGHTED_LOG_COALBEDO_EQUATION_PINNED", CHOU1998_DOI,
        ),
        _row(
            "FU96_LINEAGE_MIXED_COALBEDO_EQUATION", "HISTORICAL_EQUATION_FAMILY", "PASS_QUALIFIED",
            "alpha_eff = h*alpha_linear + (1-h)*alpha_log; h in [0,1]; h near 1 for weak absorption and decreases as absorption strengthens",
            "LINEAR_LOG_MIXING_EQUATION_FAMILY_PINNED", CHOU1998_DOI,
        ),
        _row(
            "FU96_LINEAGE_H_EMPIRICAL_SELECTION", "HISTORICAL_EQUATION_FAMILY", "PASS_QUALIFIED",
            "Chou et al. 1998 determines optimal h empirically by trial and error to minimize TOA/surface flux differences against high-resolution calculations",
            "H_IS_EMPIRICAL_FLUX_CALIBRATION_PARAMETER_NOT_DERIVABLE_FROM_ABSORPTION_STRENGTH_ALONE", CHOU1998_DOI,
        ),
        _row(
            "FU96_LINEAGE_H_DOMAIN_VALUES_CHOU1998", "H_DOMAIN_CONSTRAINT", "PASS_QUALIFIED",
            "For ice clouds Chou et al. 1998 Table 1 gives h=1 for 0.18-0.70 um and h=2/3 for 0.70-1.22 um",
            "FU_LINEAGE_H_DOMAIN_VALUES_PINNED_AS_CONSTRAINT_NOT_RRTM_GENERATOR", CHOU1998_DOI,
        ),
        _row(
            "FU96_LINEAGE_H_DOMAIN_VALUES_CHOU2002", "H_DOMAIN_CONSTRAINT", "PASS_QUALIFIED",
            "Chou et al. 2002 explicitly gives h=1 for bands 1-8 (0.175-0.700 um) and h=2/3 for band 9 (0.700-1.220 um)",
            "FU_LINEAGE_H_DOMAIN_VALUES_INDEPENDENTLY_RESTATED", CHOU2002_DOI,
        ),
        _row(
            "RRTMG_BAND25_H_DOMAIN_CONSTRAINT", "H_DOMAIN_CONSTRAINT", "PASS_QUALIFIED",
            "RRTMG band 25 is 16000-22650 cm-1 = 0.441501-0.625000 um, entirely inside the Fu-lineage weak-absorption h=1 domain below 0.700 um",
            "BAND25_H1_DOMAIN_CONSTRAINT_QUALIFIED_BUT_ARCHIVED_RRTMG_GENERATOR_IDENTITY_NOT_PROVEN",
            f"{AER_RRTMG_SW_REPOSITORY}; {CHOU1998_DOI}; {CHOU2002_DOI}",
        ),
        _row(
            "RRTMG_BAND24_H_DOMAIN_BOUNDARY_CROSSING", "H_DOMAIN_CONSTRAINT", "PASS_QUALIFIED",
            "RRTMG band 24 is 12850-16000 cm-1 = 0.625000-0.778210 um and crosses the 0.700 um Fu-lineage h-domain boundary: 0.625-0.700 lies in h=1 domain while 0.700-0.778210 lies in h=2/3 domain",
            "BAND24_CANNOT_BE_ASSIGNED_ONE_H_FROM_CHOU_DOMAIN_VALUES_WITHOUT_HISTORICAL_RRTM_GENERATOR_RULE",
            f"{AER_RRTMG_SW_REPOSITORY}; {CHOU1998_DOI}; {CHOU2002_DOI}",
        ),
        _row(
            "RRTMG_BAND25_EXACT_H_FOR_ARCHIVED_TABLE", "EXACT_WEIGHTING_PREREQUISITE", "BLOCKED_NOT_PROVEN",
            "Fu-lineage domain evidence constrains all band-25 wavelengths to h=1, but no source ties that Chou/Fu-lineage h realization byte-for-byte to the archived RRTM/RRTMG Fu96 band-25 table generator",
            "ARCHIVED_RRTM_GENERATOR_IDENTITY_OR_NUMERIC_REPRODUCTION_REQUIRED_BEFORE_EXACT_H_CLAIM",
        ),
        _row(
            "FU96_RRTMG_BAND24_25_H_VALUES", "EXACT_WEIGHTING_PREREQUISITE", "BLOCKED_NOT_RECOVERED",
            "Fu-lineage h domains are now constrained; however no authoritative RRTM/RRTMG-specific band-24 historical mixing realization, nor a fully provenance-linked band-25 generator, has been recovered",
            "BAND24_HISTORICAL_MIXING_OR_EQUIVALENT_GENERATOR_AND_BAND25_GENERATOR_IDENTITY_REQUIRED",
        ),
        _row(
            "FU96_HISTORICAL_BAND_SPECIFIC_MIXING_REALIZATION", "EXACT_WEIGHTING_PREREQUISITE", "BLOCKED_NOT_RECOVERED",
            "The exact band-specific linear/log mixing realization used for the archived RRTM/RRTMG Fu96 tables has not been recovered",
            "BAND_SPECIFIC_FU96_LINEAR_LOG_MIXING_RULE_OR_EQUIVALENT_GENERATOR_REQUIRED",
        ),
        _row(
            "FU96_LINEAGE_SOLAR_IRRADIANCE_WEIGHTING_SEMANTIC", "WEIGHTING_SEMANTICS", "PASS_CONFIRMED",
            "Fu 2007 states that calculations following Fu 1996 divide the solar spectrum into Fu96 bands and weight data with solar irradiance to obtain band averages",
            "SOLAR_IRRADIANCE_WEIGHTING_SEMANTIC_CLASS_SUPPORTED", FU2007_DOI,
        ),
        _row(
            "RRTMG_SW_BAND_INTEGRATION_FORMULA_SEMANTIC", "WEIGHTING_SEMANTICS", "PASS_QUALIFIED",
            "Yi 2013 later RRTMG-band ice optics integrates SW properties over wavelength with solar spectrum S(lambda); SSA is derived from integrated scattering/extinction and g is scattering-weighted",
            "LATER_RRTMG_BAND_INTEGRATION_SEMANTIC_QUALIFIED_BUT_NOT_HISTORICAL_FU96_DEFAULT_TABLE_PROVENANCE", YI2013_DOI,
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
            "RRTMG_PRE_V4_RUNTIME_SOLAR_SOURCE_KURUCZ", "HISTORICAL_SOLAR_SOURCE_CONTEXT", "PASS_PINNED_RUNTIME_CONTEXT",
            "RRTMG_SW documentation states versions prior to v4.0 used the Kurucz solar source with total solar irradiance 1368.22 W m-2",
            "RUNTIME_SOLAR_SOURCE_CONTEXT_PINNED_BUT_NOT_EQUATED_TO_CLOUD_TABLE_GENERATOR", AER_RRTMG_SW_DESCRIPTION,
        ),
        _row(
            "RRTMG_PRE_V4_BAND24_25_SOLAR_IRRADIANCE_TOTALS", "HISTORICAL_SOLAR_SOURCE_CONTEXT", "PASS_PINNED_BAND_TOTALS",
            "Documented RRTMG_SW band-integrated solar irradiance: band 24 (0.625-0.778 um) about 218.19 W m-2; band 25 (0.442-0.625 um) about 347.20 W m-2",
            "BAND_TOTALS_ARE_CONTEXT_ONLY_AND_DO_NOT_DEFINE_WITHIN_BAND_DISCRETE_WEIGHTS", CAM5_DESCRIPTION,
        ),
        _row(
            "RRTMG_RUNTIME_SOLAR_SOURCE_EQUALS_FU96_TABLE_GENERATION_SOURCE", "EXACT_WEIGHTING_PREREQUISITE", "BLOCKED_NOT_PROVEN",
            "No authoritative source recovered that proves the runtime Kurucz solar spectrum realization is exactly the spectrum/grid/weights used when Q. Fu high-resolution tables were averaged into the archived default RRTM_SW cloud tables",
            "EXACT_GENERATOR_SOLAR_SOURCE_IDENTITY_MUST_BE_PROVEN_BEFORE_REUSE",
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
            "Qualified constraints: solar irradiance is a weighting basis; historical Fu96 coalbedo used absorption-dependent linear/log averaging; later RRTMG-band schemes may use integrated scattering/extinction SSA and scattering-weighted g. These are not interchangeable provenance claims",
            "HISTORICAL_FU96_AND_LATER_RRTMG_SEMANTICS_SEPARATED; EXACT_HISTORICAL_REALIZATION_STILL_REQUIRED",
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
        _row("AD_HOC_EXTINCTION_OR_SCATTERING_WEIGHT_SUBSTITUTE", "SCOPE_GUARD", "PASS_FORBIDDEN", "false", "NO_AD_HOC_REWEIGHTING"),
        _row("YI2013_FORMULA_AS_HISTORICAL_FU96_DEFAULT_TABLE_GENERATOR", "SCOPE_GUARD", "PASS_FORBIDDEN", "false", "LATER_RRTMG_BAND_FORMULA_MUST_NOT_BE_SUBSTITUTED_FOR_UNRECOVERED_HISTORICAL_FU96_AVERAGING"),
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
            "NO_STEP3Q2_PRODUCTION_PROMOTION",
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
    equation_family = all(status.get(k) == "PASS_QUALIFIED" for k in ["FU96_LINEAGE_LINEAR_COALBEDO_EQUATION","FU96_LINEAGE_LOG_COALBEDO_EQUATION","FU96_LINEAGE_MIXED_COALBEDO_EQUATION","FU96_LINEAGE_H_EMPIRICAL_SELECTION"])
    h_domain_constraints = all(status.get(k) == "PASS_QUALIFIED" for k in [
        "FU96_LINEAGE_H_DOMAIN_VALUES_CHOU1998",
        "FU96_LINEAGE_H_DOMAIN_VALUES_CHOU2002",
        "RRTMG_BAND25_H_DOMAIN_CONSTRAINT",
        "RRTMG_BAND24_H_DOMAIN_BOUNDARY_CROSSING",
    ])
    exact = status.get("EXACT_FU96_RRTMG_BAND_WEIGHTING") == "PASS"
    state = (
        "PASS_EXACT_WEIGHTING_PROVENANCE_QUALIFIED" if primary and lineage and tables and semantic and exact
        else "PASS_FAIL_CLOSED_H_DOMAIN_CONSTRAINTS_QUALIFIED_RRTMG_EXACT_H_UNRESOLVED"
    )
    return pd.DataFrame([{
        "qualification_state": state,
        "FU96_PRIMARY_SOURCE_PINNED": bool(primary),
        "RRTMG_FU96_DGE_LINEAGE_PINNED": bool(lineage),
        "RRTMG_FINAL_FU96_BAND_TABLES_PINNED": bool(tables),
        "RRTMG_BAND24_25_LIMITS_PINNED": bool(band_limits),
        "SOLAR_IRRADIANCE_WEIGHTING_SEMANTIC_SUPPORTED": True,
        "FU96_HISTORICAL_MIXED_LINEAR_LOG_COALBEDO_SEMANTIC_PINNED": True,
        "FU96_HISTORICAL_COALBEDO_EQUATION_FAMILY_QUALIFIED": bool(equation_family),
        "FU96_HISTORICAL_H_DOMAIN_CONSTRAINTS_QUALIFIED": bool(h_domain_constraints),
        "RRTMG_BAND25_FULLY_WITHIN_FU_LINEAGE_H1_DOMAIN": bool(status.get("RRTMG_BAND25_H_DOMAIN_CONSTRAINT") == "PASS_QUALIFIED"),
        "RRTMG_BAND24_CROSSES_FU_LINEAGE_H_DOMAIN_BOUNDARY": bool(status.get("RRTMG_BAND24_H_DOMAIN_BOUNDARY_CROSSING") == "PASS_QUALIFIED"),
        "RRTMG_BAND24_SINGLE_H_ASSIGNMENT_JUSTIFIED": False,
        "RRTMG_BAND25_EXACT_ARCHIVED_GENERATOR_H_PROVEN": False,
        "FU96_HISTORICAL_BAND24_25_H_VALUES_RECOVERED": False,
        "LATER_RRTMG_BAND_INTEGRATION_SEMANTIC_CLASS_QUALIFIED": bool(semantic),
        "YI2013_FORMULA_PROVEN_AS_HISTORICAL_FU96_TABLE_GENERATOR": False,
        "RRTMG_PRE_V4_KURUCZ_RUNTIME_SOLAR_SOURCE_PINNED": True,
        "RRTMG_BAND24_25_SOLAR_IRRADIANCE_TOTALS_PINNED": True,
        "RUNTIME_SOLAR_SOURCE_IDENTITY_WITH_FU96_TABLE_GENERATOR_PROVEN": False,
        "FU96_HISTORICAL_BAND_SPECIFIC_LINEAR_LOG_MIXING_RECOVERED": False,
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
        "contract_version": "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_4",
        "physicscore_version": str(physicscore_version),
        "step_version": STEP3Q_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "mode": STEP3Q_MODE,
        "evidence_as_of": EVIDENCE_AS_OF,
        "sources": {
            "fu96_doi": FU96_DOI,
            "fu2007_doi": FU2007_DOI,
            "yi2013_doi": YI2013_DOI,
            "chou1998_doi": CHOU1998_DOI,
            "chou2002_doi": CHOU2002_DOI,
            "baek2018_doi": BAEK2018_DOI,
            "aer_rrtmg_sw_description": AER_RRTMG_SW_DESCRIPTION,
            "cam5_description": CAM5_DESCRIPTION,
            "aer_rrtmg_sw_repository": AER_RRTMG_SW_REPOSITORY,
            "aer_rrtm_sw_instructions": AER_RRTM_SW_INSTRUCTIONS,
            "pinned_rrtmg_reference_source": GEOSCHEM_RRTMG_PINNED_SOURCE,
            "pinned_rrtmg_reference_source_sha": GEOSCHEM_RRTMG_SOURCE_SHA,
        },
        "bands": list(RRTMG_BANDS),
        "qualified_weighting_semantic_class": {
            "shortwave_weighting_basis": "solar_irradiance",
            "historical_fu96_coalbedo": "absorption_dependent_mix_of_solar_weighted_linear_and_logarithmic_averages",
            "historical_fu96_alpha_linear": "sum(alpha_lambda*S_lambda*dLambda)/sum(S_lambda*dLambda)",
            "historical_fu96_alpha_log": "exp(sum(ln(alpha_lambda)*S_lambda*dLambda)/sum(S_lambda*dLambda))",
            "historical_fu96_h_semantic": "empirical flux-calibration parameter; h near 1 for weak absorption and decreases with stronger absorption",
            "historical_fu96_band24_25_h_values_recovered": False,
            "fu_lineage_h_domains": {
                "0.175_to_0.700_um": 1.0,
                "0.700_to_1.220_um": "2/3",
            },
            "rrtmg_band25_domain_constraint": "0.441501-0.625000 um lies entirely inside Fu-lineage h=1 domain; exact archived-generator identity still unproven",
            "rrtmg_band24_domain_constraint": "0.625000-0.778210 um crosses 0.700 um h-domain boundary; no single h may be assigned without historical generator proof",
            "rrtmg_band24_single_h_assignment_allowed": False,
            "rrtmg_band25_exact_archived_generator_h_proven": False,
            "later_rrtmg_band_ssa_example": "band_integrated_scattering_divided_by_band_integrated_extinction",
            "later_rrtmg_band_g_example": "scattering_cross_section_weighted_with_solar_spectrum",
            "later_formula_is_historical_fu96_generator": False,
            "historical_exact_solar_spectrum_and_discrete_weights_recovered": False,
            "historical_band_specific_linear_log_mixing_recovered": False,
        },
        "qualification_state": str(g["qualification_state"]),
        "capabilities": {k: bool(v) for k, v in g.items() if k != "qualification_state"},
        "forbidden_substitutes": [
            "equal_weighting",
            "unversioned_or_assumed_solar_spectrum_weights",
            "assumed_gpoint_weighting_for_cloud_optics_band_average",
            "ad_hoc_extinction_or_scattering_reweighting",
            "yi2013_formula_substituted_as_historical_fu96_generator",
        ],
        "production_guards": {"tau_ice_production_allowed": False, "production_ice_optics_ready": False, "physics_promotion_allowed": False},
        "scope_note": (
            "Step 3Q.4 pins Fu-lineage h-domain constraints onto the RRTMG band-24/25 wavelength domains while preserving the distinction between lineage constraints and the unrecovered archived RRTM/RRTMG generator. "
            "It does not claim recovery of the exact historical Fu96-to-default-RRTMG discrete weighting realization, "
            "nor does it equate the later Yi2013 integration formula or runtime Kurucz spectrum with the historical table generator. "
            "Exact weighting and production gates remain fail-closed."
        ),
    }


def serialize_fu96_rrtmg_band_weighting_provenance_contract_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
