"""Ice Optics Phase 2 Step 3O — Fu96/RRTMG SSA/g numeric cross-check.

This step executes a reproducible *broad-band diagnostic cross-check* between:

- RRTMG SW Fu(1996) ice-cloud band-24/band-25 ``ssaice3`` / ``asyice3``
  tables indexed by generalized effective size ``Dge``; and
- the existing six monochromatic Yang/Bi V2 samples integrated over the
  qualified Wyser population for ``single_column`` and the three diagnostic
  roughness states.

The comparison is intentionally not promoted to a scientific validation pass:
RRTMG values are band averages, while the Yang/Bi portable LUT contains only
three monochromatic samples within each corresponding broad band.  No spectral
weights are invented, and no production ice optics are enabled.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable
import json
import math

import numpy as np
import pandas as pd

from . import __version__ as PHYSICSCORE_VERSION
from .ice_cloud_spectral_optics import BUNDLED_CALIBRATED_LUT_PATH
from .ice_microphysics_wyser_primary_numeric_recovery import (
    WYSER_PSD_LMAX_UM,
    WYSER_PSD_LMIN_UM,
    _wyser_mass_array_g,
    _wyser_shape_array,
)
from .ice_microphysics_wyser_yang_coordinate_qualification import (
    yang_single_column_semiwidth_um,
)
from .ice_microphysics_wyser_yang_diagnostic_bulk_integration import (
    _integration_grid,
    _loglog_interp_positive,
)
from .ice_microphysics_wyser_yang_population_bridge import (
    _regular_hexagonal_column_geometry,
)

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
STEP3O_VERSION = "R5.7.41.3.4.10.28.1"
STEP3O_MODE = "FU96_RRTMG_SSA_ASYMMETRY_NUMERIC_CROSSCHECK_DIAGNOSTIC_FAIL_CLOSED"
EVIDENCE_AS_OF = "2026-09-18"

FU96_PRIMARY_DOI = "https://doi.org/10.1175/1520-0442(1996)009<2058:AAPOTS>2.0.CO;2"
RRTMG_SOURCE = (
    "https://github.com/geoschem/geos-chem/blob/"
    "a4551f9442183bb572b23e9c2d362e2d34420d3a/GeosRad/rrtmg_sw_init.F90"
)
RRTMG_SOURCE_SHA = "0ccf597d6aa3d6ed40ec592560e3ed94b653ef32"
REFERENCE_TABLE_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "ice_optics"
    / "fu96_rrtmg_visible_band24_25_reference_v1.csv"
)
REFERENCE_HABIT = "single_column"
ROUGHNESS_STATES = ("Rough000", "Rough003", "Rough050")
BAND_WAVELENGTHS: dict[int, tuple[int, int, int]] = {
    25: (550, 575, 600),
    24: (650, 700, 750),
}
TEMPERATURES_K = (233.16, 253.16, 273.16)
IWC_VALUES_G_M3 = (0.001, 0.1, 10.0)
DEFAULT_GRID_POINTS = 4097

# Yang-style effective diameter: De = 3/2 * V/A.
# Fu generalized effective size: Dge = 2/sqrt(3) * V/A.
# Therefore Dge = 4/(3*sqrt(3)) * De.
DGE_FROM_EFFECTIVE_DIAMETER_FACTOR = 4.0 / (3.0 * math.sqrt(3.0))
DGE_MIN_UM = 5.0
DGE_MAX_UM = 140.0
EVIDENCE_SIGNIFICANT_DIGITS = 11
CONTRACT_SIGNIFICANT_DIGITS = 8


def _stable(value: float) -> str:
    return format(float(value), f".{EVIDENCE_SIGNIFICANT_DIGITS}g")


def _stable_contract(value: float) -> str:
    return format(float(value), f".{CONTRACT_SIGNIFICANT_DIGITS}g")


def _reference_table() -> pd.DataFrame:
    if not REFERENCE_TABLE_PATH.exists():
        return pd.DataFrame()
    frame = pd.read_csv(REFERENCE_TABLE_PATH)
    required = {
        "rrtmg_band",
        "dge_um",
        "single_scattering_albedo",
        "asymmetry_parameter",
        "extinction_coefficient_per_iwc",
        "source_sha",
    }
    if not required.issubset(frame.columns):
        return pd.DataFrame()
    for col in (
        "rrtmg_band",
        "dge_um",
        "single_scattering_albedo",
        "asymmetry_parameter",
        "extinction_coefficient_per_iwc",
    ):
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame.dropna().sort_values(["rrtmg_band", "dge_um"]).reset_index(drop=True)
    return frame


def _reference_table_valid(frame: pd.DataFrame) -> bool:
    if len(frame) != 92:
        return False
    if set(frame["source_sha"].astype(str)) != {RRTMG_SOURCE_SHA}:
        return False
    for band in (24, 25):
        sub = frame.loc[frame["rrtmg_band"].astype(int) == band].sort_values("dge_um")
        if len(sub) != 46:
            return False
        expected = np.arange(5.0, 141.0, 3.0)
        if not np.allclose(sub["dge_um"].to_numpy(float), expected, rtol=0.0, atol=0.0):
            return False
        if not sub["single_scattering_albedo"].between(0.0, 1.0).all():
            return False
        if not sub["asymmetry_parameter"].between(0.0, 1.0).all():
            return False
        if not (sub["extinction_coefficient_per_iwc"] > 0.0).all():
            return False
    return True


def _yang_source_frame(roughness: str) -> pd.DataFrame:
    frame = pd.read_csv(BUNDLED_CALIBRATED_LUT_PATH)
    required = {
        "wavelength_nm",
        "maximum_dimension_um",
        "ice_habit",
        "surface_roughness",
        "mass_extinction_coefficient_m2_kg",
        "single_scattering_albedo",
        "asymmetry_parameter",
    }
    if not required.issubset(frame.columns):
        return pd.DataFrame()
    out = frame.loc[
        (frame["ice_habit"].astype(str) == REFERENCE_HABIT)
        & (frame["surface_roughness"].astype(str) == str(roughness))
        & pd.to_numeric(frame["maximum_dimension_um"], errors="coerce").between(
            WYSER_PSD_LMIN_UM, WYSER_PSD_LMAX_UM, inclusive="both"
        ),
        list(required),
    ].copy()
    for col in (
        "wavelength_nm",
        "maximum_dimension_um",
        "mass_extinction_coefficient_m2_kg",
        "single_scattering_albedo",
        "asymmetry_parameter",
    ):
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out.dropna().sort_values(["wavelength_nm", "maximum_dimension_um"]).reset_index(drop=True)


def _population_state(temperature_k: float, iwc_g_m3: float, source_knots: np.ndarray) -> dict[str, Any]:
    dmax_um = _integration_grid(DEFAULT_GRID_POINTS, source_knots)
    phi = _wyser_shape_array(dmax_um, temperature_k=float(temperature_k), iwc_g_m3=float(iwc_g_m3))
    wyser_mass_g = _wyser_mass_array_g(dmax_um)
    denominator = float(np.trapezoid(wyser_mass_g * phi, dmax_um))
    if not math.isfinite(denominator) or denominator <= 0.0:
        raise ValueError("Wyser population normalization denominator must be positive")
    amplitude = float(iwc_g_m3) / denominator
    number_density = amplitude * phi

    volume_um3 = np.empty_like(dmax_um, dtype=float)
    projected_area_um2 = np.empty_like(dmax_um, dtype=float)
    for i, d in enumerate(dmax_um):
        geom = _regular_hexagonal_column_geometry(
            length_um=float(d),
            semiwidth_um=float(yang_single_column_semiwidth_um(float(d))),
        )
        volume_um3[i] = float(geom["volume_um3"])
        projected_area_um2[i] = float(geom["mean_projected_area_um2"])

    volume_integral = float(np.trapezoid(number_density * volume_um3, dmax_um))
    area_integral = float(np.trapezoid(number_density * projected_area_um2, dmax_um))
    effective_diameter_um = 1.5 * volume_integral / area_integral
    dge_um = DGE_FROM_EFFECTIVE_DIAMETER_FACTOR * effective_diameter_um
    return {
        "dmax_um": dmax_um,
        "number_density_per_um": number_density,
        "effective_diameter_um": float(effective_diameter_um),
        "dge_um": float(dge_um),
    }


def _yang_bulk_optics(
    source: pd.DataFrame,
    *,
    wavelength_nm: int,
    dmax_um: np.ndarray,
    number_density_per_um: np.ndarray,
) -> tuple[float, float]:
    band = source.loc[source["wavelength_nm"].astype(int) == int(wavelength_nm)].sort_values("maximum_dimension_um")
    source_d = band["maximum_dimension_um"].to_numpy(float)
    source_kext = band["mass_extinction_coefficient_m2_kg"].to_numpy(float)
    source_ssa = band["single_scattering_albedo"].to_numpy(float)
    source_g = band["asymmetry_parameter"].to_numpy(float)
    if len(source_d) < 2:
        raise ValueError(f"Yang/Bi source rows unavailable for {wavelength_nm} nm")

    cext_source = np.empty_like(source_d, dtype=float)
    for i, (d, kext) in enumerate(zip(source_d, source_kext)):
        geom = _regular_hexagonal_column_geometry(
            length_um=float(d),
            semiwidth_um=float(yang_single_column_semiwidth_um(float(d))),
        )
        cext_source[i] = float(kext) * float(geom["solid_ice_mass_kg"])

    cext = _loglog_interp_positive(dmax_um, source_d, cext_source)
    ssa = np.interp(dmax_um, source_d, source_ssa)
    asymmetry = np.interp(dmax_um, source_d, source_g)
    csca = cext * ssa
    beta_ext = float(np.trapezoid(number_density_per_um * cext, dmax_um))
    beta_sca = float(np.trapezoid(number_density_per_um * csca, dmax_um))
    if beta_ext <= 0.0 or beta_sca <= 0.0:
        raise ValueError("bulk optical coefficients must be positive")
    bulk_ssa = beta_sca / beta_ext
    bulk_g = float(np.trapezoid(number_density_per_um * csca * asymmetry, dmax_um)) / beta_sca
    return float(bulk_ssa), float(bulk_g)


def _rrtmg_reference_at_dge(frame: pd.DataFrame, band: int, dge_um: float) -> tuple[float, float]:
    sub = frame.loc[frame["rrtmg_band"].astype(int) == int(band)].sort_values("dge_um")
    x = sub["dge_um"].to_numpy(float)
    if float(dge_um) < x[0] or float(dge_um) > x[-1]:
        raise ValueError("Dge outside pinned RRTMG reference domain; extrapolation forbidden")
    ssa = float(np.interp(float(dge_um), x, sub["single_scattering_albedo"].to_numpy(float)))
    g = float(np.interp(float(dge_um), x, sub["asymmetry_parameter"].to_numpy(float)))
    return ssa, g


def _run_crosscheck(
    temperatures_k: Iterable[float],
    iwc_values_g_m3: Iterable[float],
    roughness_states: Iterable[str],
) -> dict[str, Any]:
    reference = _reference_table()
    reference_valid = _reference_table_valid(reference)
    rows: list[dict[str, Any]] = []
    if not reference_valid:
        return {
            "diagnostic_only": True,
            "reference_table_pinned_pass": False,
            "comparison_rows": [],
            "comparison_row_count": 0,
            "population_state_count": 0,
            "dge_domain_pass": False,
            "numeric_crosscheck_executed_pass": False,
            "independent_ssa_validation_pass": False,
            "independent_asymmetry_validation_pass": False,
            "full_six_band_like_for_like_optical_validation_pass": False,
            "tau_ice_production_allowed": False,
            "production_ice_optics_ready": False,
            "physics_promotion_allowed": False,
            "missing_reason": "RRTMG_REFERENCE_TABLE_INVALID_OR_MISSING",
        }

    sources = {rough: _yang_source_frame(str(rough)) for rough in roughness_states}
    if any(frame.empty for frame in sources.values()):
        raise ValueError("Yang/Bi source frame unavailable for requested roughness states")
    source_knots = sources[str(tuple(roughness_states)[0])]
    source_knots = source_knots.loc[source_knots["wavelength_nm"].astype(int) == 550, "maximum_dimension_um"].to_numpy(float)

    population_count = 0
    for temperature in temperatures_k:
        for iwc in iwc_values_g_m3:
            pop = _population_state(float(temperature), float(iwc), source_knots)
            for roughness in roughness_states:
                population_count += 1
                source = sources[str(roughness)]
                mono: dict[int, tuple[float, float]] = {}
                for wave in (550, 575, 600, 650, 700, 750):
                    mono[wave] = _yang_bulk_optics(
                        source,
                        wavelength_nm=wave,
                        dmax_um=pop["dmax_um"],
                        number_density_per_um=pop["number_density_per_um"],
                    )
                for rrtmg_band, waves in BAND_WAVELENGTHS.items():
                    fu_ssa, fu_g = _rrtmg_reference_at_dge(reference, rrtmg_band, pop["dge_um"])
                    yang_ssa = np.asarray([mono[w][0] for w in waves], dtype=float)
                    yang_g = np.asarray([mono[w][1] for w in waves], dtype=float)
                    rows.append({
                        "temperature_k": float(temperature),
                        "iwc_g_m3": float(iwc),
                        "surface_roughness": str(roughness),
                        "rrtmg_band": int(rrtmg_band),
                        "yang_sample_wavelengths_nm": "/".join(str(w) for w in waves),
                        "yang_population_effective_diameter_um": float(pop["effective_diameter_um"]),
                        "fu_generalized_effective_size_dge_um": float(pop["dge_um"]),
                        "rrtmg_ssa": float(fu_ssa),
                        "yang_ssa_sample_mean": float(yang_ssa.mean()),
                        "yang_ssa_sample_min": float(yang_ssa.min()),
                        "yang_ssa_sample_max": float(yang_ssa.max()),
                        "ssa_sample_mean_absolute_difference": abs(float(yang_ssa.mean()) - float(fu_ssa)),
                        "rrtmg_asymmetry": float(fu_g),
                        "yang_asymmetry_sample_mean": float(yang_g.mean()),
                        "yang_asymmetry_sample_min": float(yang_g.min()),
                        "yang_asymmetry_sample_max": float(yang_g.max()),
                        "asymmetry_sample_mean_absolute_difference": abs(float(yang_g.mean()) - float(fu_g)),
                    })

    compare = pd.DataFrame(rows)
    finite_columns = [
        "yang_population_effective_diameter_um",
        "fu_generalized_effective_size_dge_um",
        "rrtmg_ssa",
        "yang_ssa_sample_mean",
        "rrtmg_asymmetry",
        "yang_asymmetry_sample_mean",
    ]
    finite_pass = bool(
        len(compare) == 54
        and np.isfinite(compare[finite_columns].to_numpy(float)).all()
        and compare["rrtmg_ssa"].between(0.0, 1.0).all()
        and compare["yang_ssa_sample_mean"].between(0.0, 1.0).all()
        and compare["rrtmg_asymmetry"].between(0.0, 1.0).all()
        and compare["yang_asymmetry_sample_mean"].between(0.0, 1.0).all()
    )
    dge_domain = bool(
        len(compare) == 54
        and compare["fu_generalized_effective_size_dge_um"].between(DGE_MIN_UM, DGE_MAX_UM).all()
    )
    executed = bool(reference_valid and finite_pass and dge_domain and len(compare) == 54 and population_count == 27)

    return {
        "diagnostic_only": True,
        "reference_table_pinned_pass": bool(reference_valid),
        "rrtmg_reference_is_broad_band": True,
        "yang_reference_is_six_monochromatic_samples_only": True,
        "full_band_spectral_weighting_available": False,
        "dge_bridge_formula": "Dge=(4/(3*sqrt(3)))*De_bulk",
        "dge_bridge_executed_pass": bool(dge_domain),
        "dge_domain_pass": bool(dge_domain),
        "population_state_count": int(population_count),
        "comparison_row_count": int(len(compare)),
        "minimum_dge_um": float(compare["fu_generalized_effective_size_dge_um"].min()) if not compare.empty else None,
        "maximum_dge_um": float(compare["fu_generalized_effective_size_dge_um"].max()) if not compare.empty else None,
        "max_ssa_sample_mean_absolute_difference": float(compare["ssa_sample_mean_absolute_difference"].max()) if not compare.empty else None,
        "mean_ssa_sample_mean_absolute_difference": float(compare["ssa_sample_mean_absolute_difference"].mean()) if not compare.empty else None,
        "max_asymmetry_sample_mean_absolute_difference": float(compare["asymmetry_sample_mean_absolute_difference"].max()) if not compare.empty else None,
        "mean_asymmetry_sample_mean_absolute_difference": float(compare["asymmetry_sample_mean_absolute_difference"].mean()) if not compare.empty else None,
        "numeric_crosscheck_executed_pass": bool(executed),
        "independent_ssa_validation_pass": False,
        "independent_asymmetry_validation_pass": False,
        "full_six_band_like_for_like_optical_validation_pass": False,
        "tau_ice_production_allowed": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "comparison_rows": rows,
        "missing_reason": "" if executed else "NUMERIC_CROSSCHECK_INCOMPLETE",
    }


@lru_cache(maxsize=1)
def _default_result_cached() -> dict[str, Any]:
    return _run_crosscheck(TEMPERATURES_K, IWC_VALUES_G_M3, ROUGHNESS_STATES)


def run_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_grid() -> dict[str, Any]:
    return _default_result_cached()


EVIDENCE_COLUMNS = [
    "step3o_version",
    "science_baseline",
    "step3o_mode",
    "evidence_id",
    "evidence_type",
    "pin_status",
    "value",
    "semantic_role",
    "authoritative_for_runtime_mapping",
    "source_reference",
    "notes",
]


def _evidence_row(
    evidence_id: str,
    evidence_type: str,
    pin_status: str,
    value: str,
    semantic_role: str,
    source_reference: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "step3o_version": STEP3O_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "step3o_mode": STEP3O_MODE,
        "evidence_id": evidence_id,
        "evidence_type": evidence_type,
        "pin_status": pin_status,
        "value": value,
        "semantic_role": semantic_role,
        "authoritative_for_runtime_mapping": False,
        "source_reference": source_reference,
        "notes": notes,
    }


def build_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_evidence() -> pd.DataFrame:
    result = run_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_grid()
    rows = [
        _evidence_row(
            "RRTMG_FU96_VISIBLE_REFERENCE_TABLE",
            "PINNED_NUMERIC_REFERENCE",
            "PASS_PINNED_REFERENCE_TABLE" if result["reference_table_pinned_pass"] else "BLOCKED_REFERENCE_TABLE_INVALID",
            "bands=24/25;dge_nodes=46_each;records=92",
            "INDEPENDENT_BROAD_BAND_NUMERIC_REFERENCE",
            f"{FU96_PRIMARY_DOI}|{RRTMG_SOURCE}",
            "Exact source values are vendored from the pinned RRTMG implementation; no runtime network dependency.",
        ),
        _evidence_row(
            "YANG_TO_FU_DGE_BRIDGE",
            "POPULATION_SIZE_BRIDGE",
            "PASS_DIAGNOSTIC_BRIDGE_EXECUTED" if result["dge_bridge_executed_pass"] else "BLOCKED_DGE_BRIDGE",
            f"Dge=4/(3sqrt3)*De;range={_stable(result['minimum_dge_um'])}-{_stable(result['maximum_dge_um'])}um",
            "DIAGNOSTIC_POPULATION_DGE_BRIDGE",
            FU96_PRIMARY_DOI,
            "Bridge uses volume/projected-area definitions; it is diagnostic and is not runtime habit/size truth.",
        ),
        _evidence_row(
            "NUMERIC_CROSSCHECK_MATRIX",
            "NUMERIC_EXECUTION_GATE",
            "PASS_NUMERIC_CROSSCHECK_EXECUTED" if result["numeric_crosscheck_executed_pass"] else "BLOCKED_NUMERIC_CROSSCHECK",
            f"population_states={result['population_state_count']};comparison_rows={result['comparison_row_count']}",
            "BROAD_BAND_NUMERIC_CROSSCHECK_EXECUTED",
            f"{RRTMG_SOURCE}|Yang2013_Bi2017_V2",
            "Execution pass means complete finite in-domain comparison only; it is not a scientific agreement threshold.",
        ),
        _evidence_row(
            "SSA_DIFFERENCE_CHARACTERIZATION",
            "REGRESSION_CHARACTERIZATION",
            "CHARACTERIZED_NO_SCIENCE_THRESHOLD",
            f"max_abs={_stable(result['max_ssa_sample_mean_absolute_difference'])};mean_abs={_stable(result['mean_ssa_sample_mean_absolute_difference'])}",
            "SSA_BROAD_BAND_VS_MONOCHROMATIC_SAMPLE_CHARACTERIZATION",
            f"{RRTMG_SOURCE}|Yang2013_Bi2017_V2",
            "No new SSA tolerance is introduced by Step 3O.",
        ),
        _evidence_row(
            "ASYMMETRY_DIFFERENCE_CHARACTERIZATION",
            "REGRESSION_CHARACTERIZATION",
            "CHARACTERIZED_NO_SCIENCE_THRESHOLD",
            f"max_abs={_stable(result['max_asymmetry_sample_mean_absolute_difference'])};mean_abs={_stable(result['mean_asymmetry_sample_mean_absolute_difference'])}",
            "ASYMMETRY_BROAD_BAND_VS_MONOCHROMATIC_SAMPLE_CHARACTERIZATION",
            f"{RRTMG_SOURCE}|Yang2013_Bi2017_V2",
            "No new asymmetry tolerance is introduced by Step 3O.",
        ),
        _evidence_row(
            "FULL_BAND_SPECTRAL_WEIGHTING",
            "SPECTRAL_EQUIVALENCE_BLOCKER",
            "BLOCKED_YANG_FULL_BAND_SPECTRAL_WEIGHTING_UNAVAILABLE",
            "false",
            "EXACT_BROAD_BAND_LIKE_FOR_LIKE_VALIDATION_PENDING",
            "Yang2013_Bi2017_V2 portable six-band LUT",
            "Six monochromatic samples cannot reconstruct RRTMG band-average weighting without the full source spectrum and weighting contract.",
        ),
        _evidence_row(
            "INDEPENDENT_SSA_NUMERIC_VALIDATION",
            "FULL_OPTICS_BLOCKER",
            "BLOCKED_SPECTRAL_NON_EQUIVALENCE",
            "false",
            "INDEPENDENT_SSA_VALIDATION_PENDING",
            f"{FU96_PRIMARY_DOI}|{RRTMG_SOURCE}",
            "Numeric cross-check is executed, but broad-band vs sparse monochromatic sampling is not like-for-like validation.",
        ),
        _evidence_row(
            "INDEPENDENT_ASYMMETRY_NUMERIC_VALIDATION",
            "FULL_OPTICS_BLOCKER",
            "BLOCKED_SPECTRAL_NON_EQUIVALENCE",
            "false",
            "INDEPENDENT_ASYMMETRY_VALIDATION_PENDING",
            f"{FU96_PRIMARY_DOI}|{RRTMG_SOURCE}",
            "Numeric cross-check is executed, but broad-band vs sparse monochromatic sampling is not like-for-like validation.",
        ),
        _evidence_row(
            "PRODUCTION_PROMOTION_GUARD",
            "PRODUCTION_GUARD",
            "PASS_FAIL_CLOSED",
            "tau_ice=false;production_ice_optics=false;physics_promotion=false",
            "NO_PRODUCTION_PROMOTION",
            STEP3O_VERSION,
            "Frozen Formation/Viewing/Twilight Glow and production science remain unchanged.",
        ),
    ]
    return pd.DataFrame(rows, columns=EVIDENCE_COLUMNS)


GATE_COLUMNS = [
    "step3o_version",
    "science_baseline",
    "step3o_mode",
    "RRTMG_REFERENCE_TABLE_PINNED_PASS",
    "DGE_BRIDGE_EXECUTED_PASS",
    "NUMERIC_CROSSCHECK_EXECUTED_PASS",
    "FULL_BAND_SPECTRAL_WEIGHTING_AVAILABLE",
    "INDEPENDENT_SSA_VALIDATION_PASS",
    "INDEPENDENT_ASYMMETRY_VALIDATION_PASS",
    "FULL_SIX_BAND_LIKE_FOR_LIKE_OPTICAL_VALIDATION_PASS",
    "TAU_ICE_PRODUCTION_ALLOWED",
    "PRODUCTION_ICE_OPTICS_READY",
    "physics_promotion_allowed",
    "qualification_state",
    "qualification_blockers",
]


def build_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_gate(evidence: pd.DataFrame | None = None) -> pd.DataFrame:
    result = run_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_grid()
    return pd.DataFrame([{
        "step3o_version": STEP3O_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "step3o_mode": STEP3O_MODE,
        "RRTMG_REFERENCE_TABLE_PINNED_PASS": bool(result["reference_table_pinned_pass"]),
        "DGE_BRIDGE_EXECUTED_PASS": bool(result["dge_bridge_executed_pass"]),
        "NUMERIC_CROSSCHECK_EXECUTED_PASS": bool(result["numeric_crosscheck_executed_pass"]),
        "FULL_BAND_SPECTRAL_WEIGHTING_AVAILABLE": False,
        "INDEPENDENT_SSA_VALIDATION_PASS": False,
        "INDEPENDENT_ASYMMETRY_VALIDATION_PASS": False,
        "FULL_SIX_BAND_LIKE_FOR_LIKE_OPTICAL_VALIDATION_PASS": False,
        "TAU_ICE_PRODUCTION_ALLOWED": False,
        "PRODUCTION_ICE_OPTICS_READY": False,
        "physics_promotion_allowed": False,
        "qualification_state": "BROAD_BAND_NUMERIC_CROSSCHECK_EXECUTED_EXACT_SPECTRAL_VALIDATION_BLOCKED",
        "qualification_blockers": "YANG_FULL_BAND_SPECTRAL_WEIGHTING_UNAVAILABLE|RRTMG_BROAD_BAND_NOT_MONOCHROMATIC|INDEPENDENT_SSA_VALIDATION_PENDING|INDEPENDENT_ASYMMETRY_VALIDATION_PENDING|EXACT_SIX_BAND_LIKE_FOR_LIKE_REFERENCE_PENDING",
    }], columns=GATE_COLUMNS)



def serialize_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_contract_json_bytes(
    payload: dict[str, Any],
) -> bytes:
    """Canonical Step 3O contract serialization shared by release and CASE export."""
    return json.dumps(
        payload, ensure_ascii=False, indent=2, sort_keys=True, default=str
    ).encode("utf-8")

def fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_contract_payload(
    *, physicscore_version: str = PHYSICSCORE_VERSION,
) -> dict[str, Any]:
    result = run_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_grid()
    gate = build_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_gate().iloc[0].to_dict()
    return {
        "contract_version": "FIRECLOUD_ICE_FU96_RRTMG_SSA_ASYMMETRY_NUMERIC_CROSSCHECK_V1",
        "physicscore_version": str(physicscore_version),
        "step3o_version": STEP3O_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "mode": STEP3O_MODE,
        "evidence_as_of": EVIDENCE_AS_OF,
        "rrtmg_reference_source": RRTMG_SOURCE,
        "rrtmg_reference_source_sha": RRTMG_SOURCE_SHA,
        "rrtmg_reference_table": str(REFERENCE_TABLE_PATH.name),
        "rrtmg_reference_is_broad_band": True,
        "yang_reference_is_six_monochromatic_samples_only": True,
        "full_band_spectral_weighting_available": False,
        "dge_bridge_formula": result["dge_bridge_formula"],
        "dge_bridge_executed_pass": bool(result["dge_bridge_executed_pass"]),
        "population_state_count": int(result["population_state_count"]),
        "comparison_row_count": int(result["comparison_row_count"]),
        "minimum_dge_um": _stable_contract(result["minimum_dge_um"]),
        "maximum_dge_um": _stable_contract(result["maximum_dge_um"]),
        "max_ssa_sample_mean_absolute_difference": _stable_contract(result["max_ssa_sample_mean_absolute_difference"]),
        "mean_ssa_sample_mean_absolute_difference": _stable_contract(result["mean_ssa_sample_mean_absolute_difference"]),
        "max_asymmetry_sample_mean_absolute_difference": _stable_contract(result["max_asymmetry_sample_mean_absolute_difference"]),
        "mean_asymmetry_sample_mean_absolute_difference": _stable_contract(result["mean_asymmetry_sample_mean_absolute_difference"]),
        "numeric_crosscheck_executed_pass": bool(result["numeric_crosscheck_executed_pass"]),
        "science_tolerance_introduced": False,
        "independent_ssa_validation_pass": False,
        "independent_asymmetry_validation_pass": False,
        "full_six_band_like_for_like_optical_validation_pass": False,
        "tau_ice_production_allowed": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "formation_viewing_twilight_glow_frozen": True,
        "runtime_habit_inference_allowed": False,
        "runtime_roughness_inference_allowed": False,
        "qualification_state": gate["qualification_state"],
        "qualification_blockers": gate["qualification_blockers"],
    }
