"""Ice Optics Phase 2 Step 3J — diagnostic Wyser PSD × Yang/Bi Cext bulk integration.

This module performs the first *diagnostic-only* six-band bulk extinction
integration on the already-qualified shared maximum-dimension coordinate.

Population semantics remain Wyser:
    n(D) = A * phi(D)
    A = IWC / integral[m_wyser(D) * phi(D) dD]

Optical-kernel semantics remain Yang/Bi V2:
    C_ext(D, lambda) = k_ext_yang(D, lambda) * m_yang_geometric(D)

The two particle-mass semantics are intentionally distinct.  Step 3J combines
Wyser number weighting with the Yang/Bi single-particle C_ext kernel only after
Step 3I established that this hybrid numerical bridge is executable.  It does
not select a runtime habit/roughness policy, does not compute tau_ice, and does
not permit production promotion.
"""
from __future__ import annotations

from typing import Any, Iterable
import math

import numpy as np
import pandas as pd

from .ice_cloud_spectral_optics import ICE_OPTICS_WAVELENGTHS_NM
from .ice_microphysics_wyser_primary_numeric_recovery import (
    WYSER_PSD_LMAX_UM,
    WYSER_PSD_LMIN_UM,
    WYSER_PSD_SWITCH_LENGTH_UM,
    _wyser_mass_array_g,
    _wyser_shape_array,
)
from .ice_microphysics_wyser_yang_population_bridge import (
    DIAGNOSTIC_REFERENCE_HABIT,
    DIAGNOSTIC_REFERENCE_ROUGHNESS,
    OPTICAL_KERNEL_MASS_SEMANTIC,
    POPULATION_MASS_SEMANTIC,
    _kernel_source_frame,
    _regular_hexagonal_column_geometry,
)
from .ice_microphysics_wyser_yang_coordinate_qualification import (
    yang_single_column_semiwidth_um,
)

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
STEP3J_VERSION = "R5.7.41.3.4.10.23"
STEP3J_MODE = "WYSER_PSD_YANG_CEXT_DIAGNOSTIC_BULK_INTEGRATION_FAIL_CLOSED"
PHYSICS_PROMOTION_ALLOWED = False
EVIDENCE_AS_OF = "2026-09-17"

BETA_EXT_DEFINITION = "integral[n_wyser(D)*Cext_yang(D,lambda)dD]"
K_EXT_DEFINITION = "beta_ext/IWC_kg_m3"
INTERPOLATION_CONTRACT = "LOG_D_LOG_CEXT_PIECEWISE_LINEAR_WITH_SOURCE_KNOTS_NO_EXTRAPOLATION"
BULK_CONVERGENCE_TOLERANCE = 5.0e-4
MASS_CLOSURE_TOLERANCE = 1.0e-12


def _positive_finite(value: float, *, name: str) -> float:
    out = float(value)
    if not math.isfinite(out) or out <= 0.0:
        raise ValueError(f"{name} must be positive and finite")
    return out


def _integration_grid(grid_points: int, source_dmax_um: np.ndarray) -> np.ndarray:
    points = int(grid_points)
    if points < 65:
        raise ValueError("grid_points must be >= 65")
    base = np.geomspace(WYSER_PSD_LMIN_UM, WYSER_PSD_LMAX_UM, points)
    knots = np.asarray(source_dmax_um, dtype=float)
    return np.unique(np.concatenate([
        base,
        knots,
        np.asarray([WYSER_PSD_SWITCH_LENGTH_UM], dtype=float),
    ]))


def _diagnostic_cext_source_by_band() -> tuple[dict[int, tuple[np.ndarray, np.ndarray]], str]:
    """Return Yang/Bi single-column Rough000 C_ext source knots by wavelength."""
    frame, source_path = _kernel_source_frame()
    if frame.empty:
        return {}, source_path

    result: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for wavelength in ICE_OPTICS_WAVELENGTHS_NM:
        band = frame.loc[frame["wavelength_nm"].astype(float) == float(wavelength)].copy()
        band = band.sort_values("maximum_dimension_um")
        dmax = band["maximum_dimension_um"].to_numpy(dtype=float)
        kext = band["mass_extinction_coefficient_m2_kg"].to_numpy(dtype=float)
        cext: list[float] = []
        for d_um, k_m2_kg in zip(dmax, kext):
            a_um = float(yang_single_column_semiwidth_um(float(d_um)))
            geometry = _regular_hexagonal_column_geometry(length_um=float(d_um), semiwidth_um=a_um)
            cext.append(float(k_m2_kg) * float(geometry["solid_ice_mass_kg"]))
        cext_arr = np.asarray(cext, dtype=float)
        if (
            dmax.size == 0
            or np.any(~np.isfinite(dmax))
            or np.any(~np.isfinite(cext_arr))
            or np.any(dmax <= 0.0)
            or np.any(cext_arr <= 0.0)
        ):
            return {}, source_path
        result[int(wavelength)] = (dmax, cext_arr)
    return result, source_path


def _loglog_interp_positive(x: np.ndarray, source_x: np.ndarray, source_y: np.ndarray) -> np.ndarray:
    x_arr = np.asarray(x, dtype=float)
    sx = np.asarray(source_x, dtype=float)
    sy = np.asarray(source_y, dtype=float)
    if (
        x_arr.size == 0
        or sx.size < 2
        or sx.size != sy.size
        or np.any(x_arr < sx[0])
        or np.any(x_arr > sx[-1])
        or np.any(x_arr <= 0.0)
        or np.any(sx <= 0.0)
        or np.any(sy <= 0.0)
    ):
        raise ValueError("log-log interpolation requires positive in-domain coordinates")
    return np.exp(np.interp(np.log(x_arr), np.log(sx), np.log(sy)))


def _bulk_solution_on_grid(
    *,
    temperature_k: float,
    iwc_g_m3: float,
    grid_points: int,
    kernel_by_band: dict[int, tuple[np.ndarray, np.ndarray]],
) -> dict[str, Any]:
    first = kernel_by_band[int(ICE_OPTICS_WAVELENGTHS_NM[0])][0]
    length_um = _integration_grid(grid_points, first)
    phi = _wyser_shape_array(length_um, temperature_k=temperature_k, iwc_g_m3=iwc_g_m3)
    mass_g = _wyser_mass_array_g(length_um)
    denominator_g = float(np.trapezoid(mass_g * phi, length_um))
    if not math.isfinite(denominator_g) or denominator_g <= 0.0:
        raise ValueError("Wyser PSD normalization denominator must be positive and finite")

    amplitude = float(iwc_g_m3) / denominator_g
    number_density_per_um = amplitude * phi
    reconstructed_iwc_g_m3 = float(np.trapezoid(mass_g * number_density_per_um, length_um))
    mass_closure_error = abs(reconstructed_iwc_g_m3 - float(iwc_g_m3)) / float(iwc_g_m3)
    iwc_kg_m3 = float(iwc_g_m3) * 1.0e-3

    bands: list[dict[str, float]] = []
    for wavelength in ICE_OPTICS_WAVELENGTHS_NM:
        source_x, source_cext = kernel_by_band[int(wavelength)]
        cext_m2 = _loglog_interp_positive(length_um, source_x, source_cext)
        beta_ext_m_inv = float(np.trapezoid(number_density_per_um * cext_m2, length_um))
        k_ext_m2_kg = beta_ext_m_inv / iwc_kg_m3
        bands.append({
            "wavelength_nm": int(wavelength),
            "beta_ext_m_inv": float(beta_ext_m_inv),
            "k_ext_m2_kg": float(k_ext_m2_kg),
        })

    return {
        "grid_points_requested": int(grid_points),
        "grid_points_actual": int(length_um.size),
        "normalization_denominator_g_shape": float(denominator_g),
        "normalization_amplitude": float(amplitude),
        "reconstructed_iwc_g_m3": float(reconstructed_iwc_g_m3),
        "mass_closure_relative_error": float(mass_closure_error),
        "bands": bands,
    }


def diagnostic_bulk_extinction(
    *,
    temperature_k: float,
    iwc_g_m3: float,
    grid_points: int = 4097,
    reference_grid_points: int = 16385,
) -> dict[str, Any]:
    """Compute diagnostic six-band beta_ext and k_ext, without tau promotion."""
    temperature = _positive_finite(temperature_k, name="temperature_k")
    iwc = _positive_finite(iwc_g_m3, name="iwc_g_m3")
    if int(reference_grid_points) <= int(grid_points):
        raise ValueError("reference_grid_points must exceed grid_points")

    kernel_by_band, source_path = _diagnostic_cext_source_by_band()
    expected = [int(v) for v in ICE_OPTICS_WAVELENGTHS_NM]
    if sorted(kernel_by_band) != expected:
        return {
            "diagnostic_only": True,
            "temperature_k": temperature,
            "iwc_g_m3": iwc,
            "wavelengths_nm": expected,
            "kernel_source_path": source_path,
            "bulk_extinction_numeric_pass": False,
            "grid_convergence_pass": False,
            "mass_closure_numeric_pass": False,
            "scientific_bulk_validation_pass": False,
            "bulk_yang_bi_psd_integration_eligible": False,
            "tau_ice_computed": False,
            "runtime_habit_roughness_selected": False,
            "production_ice_optics_ready": False,
            "physics_promotion_allowed": False,
            "missing_reason": "DIAGNOSTIC_CEXT_KERNEL_UNAVAILABLE",
            "bands": [],
        }

    solution = _bulk_solution_on_grid(
        temperature_k=temperature,
        iwc_g_m3=iwc,
        grid_points=int(grid_points),
        kernel_by_band=kernel_by_band,
    )
    reference = _bulk_solution_on_grid(
        temperature_k=temperature,
        iwc_g_m3=iwc,
        grid_points=int(reference_grid_points),
        kernel_by_band=kernel_by_band,
    )
    ref_by_wave = {int(r["wavelength_nm"]): r for r in reference["bands"]}

    bands: list[dict[str, float]] = []
    for row in solution["bands"]:
        wave = int(row["wavelength_nm"])
        ref = ref_by_wave[wave]
        convergence = abs(float(row["k_ext_m2_kg"]) - float(ref["k_ext_m2_kg"])) / float(ref["k_ext_m2_kg"])
        bands.append({
            **row,
            "reference_beta_ext_m_inv": float(ref["beta_ext_m_inv"]),
            "reference_k_ext_m2_kg": float(ref["k_ext_m2_kg"]),
            "convergence_relative_error": float(convergence),
        })

    mass_pass = bool(solution["mass_closure_relative_error"] <= MASS_CLOSURE_TOLERANCE)
    convergence_pass = bool(
        bands
        and max(r["convergence_relative_error"] for r in bands) <= BULK_CONVERGENCE_TOLERANCE
    )
    finite_positive = bool(
        bands
        and all(
            math.isfinite(float(r["beta_ext_m_inv"]))
            and math.isfinite(float(r["k_ext_m2_kg"]))
            and float(r["beta_ext_m_inv"]) > 0.0
            and float(r["k_ext_m2_kg"]) > 0.0
            for r in bands
        )
    )
    numeric_pass = bool(mass_pass and convergence_pass and finite_positive)

    return {
        "diagnostic_only": True,
        "input_contract": "WYSER_EQ6_NORMALIZED_PSD_X_YANG_V2_SINGLE_COLUMN_ROUGH000_CEXT_REFERENCE_KERNEL",
        "population_mass_semantic": POPULATION_MASS_SEMANTIC,
        "optical_kernel_mass_semantic": OPTICAL_KERNEL_MASS_SEMANTIC,
        "mass_semantics_interchangeable": False,
        "diagnostic_reference_habit": DIAGNOSTIC_REFERENCE_HABIT,
        "diagnostic_reference_roughness": DIAGNOSTIC_REFERENCE_ROUGHNESS,
        "runtime_habit_roughness_selected": False,
        "interpolation_contract": INTERPOLATION_CONTRACT,
        "kernel_source_path": source_path,
        "temperature_k": float(temperature),
        "iwc_g_m3": float(iwc),
        "iwc_kg_m3": float(iwc * 1.0e-3),
        "domain_um": [float(WYSER_PSD_LMIN_UM), float(WYSER_PSD_LMAX_UM)],
        "wavelengths_nm": expected,
        "grid_points_requested": int(grid_points),
        "grid_points_actual": int(solution["grid_points_actual"]),
        "reference_grid_points_requested": int(reference_grid_points),
        "reference_grid_points_actual": int(reference["grid_points_actual"]),
        "normalization_amplitude": float(solution["normalization_amplitude"]),
        "reconstructed_iwc_g_m3": float(solution["reconstructed_iwc_g_m3"]),
        "mass_closure_relative_error": float(solution["mass_closure_relative_error"]),
        "mass_closure_numeric_pass": mass_pass,
        "max_bulk_convergence_relative_error": float(max(r["convergence_relative_error"] for r in bands)),
        "grid_convergence_pass": convergence_pass,
        "bulk_extinction_numeric_pass": numeric_pass,
        "scientific_bulk_validation_pass": False,
        "bulk_yang_bi_psd_integration_eligible": False,
        "tau_ice_computed": False,
        "tau_ice_production_allowed": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "bands": bands,
        "missing_reason": "" if numeric_pass else "DIAGNOSTIC_BULK_NUMERIC_PREFLIGHT_FAILED",
    }


def run_diagnostic_bulk_extinction_grid(
    *,
    temperatures_k: Iterable[float] = (233.16, 253.16, 273.16),
    iwc_values_g_m3: Iterable[float] = (0.001, 0.1, 10.0),
    grid_points: Iterable[int] = (1025, 4097),
    reference_grid_points: int = 16385,
) -> dict[str, Any]:
    temperatures = tuple(float(v) for v in temperatures_k)
    iwcs = tuple(float(v) for v in iwc_values_g_m3)
    grids = tuple(int(v) for v in grid_points)
    if not temperatures or not iwcs or not grids:
        raise ValueError("temperatures_k, iwc_values_g_m3 and grid_points must be non-empty")

    cases: list[dict[str, Any]] = []
    for temperature in temperatures:
        for iwc in iwcs:
            for points in grids:
                cases.append(diagnostic_bulk_extinction(
                    temperature_k=temperature,
                    iwc_g_m3=iwc,
                    grid_points=points,
                    reference_grid_points=int(reference_grid_points),
                ))

    return {
        "diagnostic_only": True,
        "grid_scope": "NUMERICAL_PREFLIGHT_NOT_OPERATIONAL_VALIDITY_DOMAIN",
        "temperatures_k": list(temperatures),
        "iwc_values_g_m3": list(iwcs),
        "grid_points": list(grids),
        "reference_grid_points": int(reference_grid_points),
        "case_count": int(len(cases)),
        "all_numeric_bulk_extinction_pass": bool(all(c["bulk_extinction_numeric_pass"] for c in cases)),
        "all_grid_convergence_pass": bool(all(c["grid_convergence_pass"] for c in cases)),
        "max_mass_closure_relative_error": float(max(c["mass_closure_relative_error"] for c in cases)),
        "max_bulk_convergence_relative_error": float(max(c["max_bulk_convergence_relative_error"] for c in cases)),
        "scientific_bulk_validation_pass": False,
        "bulk_yang_bi_psd_integration_eligible": False,
        "tau_ice_computed": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "cases": cases,
    }


STABLE_EVIDENCE_SIGNIFICANT_DIGITS = 16


def stable_evidence_float(value: float) -> str:
    """Serialize diagnostic evidence floats without platform-specific 1-ULP noise."""
    return format(float(value), f".{STABLE_EVIDENCE_SIGNIFICANT_DIGITS}g")


EVIDENCE_COLUMNS = [
    "step3j_version",
    "science_baseline",
    "step3j_mode",
    "evidence_id",
    "evidence_type",
    "pin_status",
    "value",
    "semantic_role",
    "authoritative_for_runtime_mapping",
    "source_reference",
    "source_path",
    "source_sha",
    "notes",
]


def build_wyser_yang_diagnostic_bulk_evidence() -> pd.DataFrame:
    grid = run_diagnostic_bulk_extinction_grid()
    sample = diagnostic_bulk_extinction(
        temperature_k=253.16,
        iwc_g_m3=0.1,
        grid_points=4097,
        reference_grid_points=16385,
    )
    kext_summary = "|".join(
        f"{r['wavelength_nm']}:{stable_evidence_float(r['k_ext_m2_kg'])}" for r in sample["bands"]
    )
    rows = [
        {
            "evidence_id": "STEP3I_HYBRID_POPULATION_BRIDGE_INHERITANCE",
            "evidence_type": "PRIOR_QUALIFICATION_INHERITANCE",
            "pin_status": "PASS_INHERITED_STEP3I_NUMERIC_BRIDGE",
            "value": "Wyser number population + Yang/Bi single-particle Cext reference kernel",
            "semantic_role": "DIAGNOSTIC_BULK_INPUTS_ONLY",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "R5.7.41.3.4.10.22 Step 3I",
            "source_path": "ice_microphysics_wyser_yang_population_bridge",
            "source_sha": "",
            "notes": "Step 3J inherits numeric executability without inheriting production eligibility.",
        },
        {
            "evidence_id": "DIAGNOSTIC_BULK_INTEGRATION_DEFINITION",
            "evidence_type": "MATHEMATICAL_NUMERIC_CONTRACT",
            "pin_status": "PINNED_DIAGNOSTIC_BETA_KEXT_DEFINITION",
            "value": f"beta_ext={BETA_EXT_DEFINITION};k_ext={K_EXT_DEFINITION}",
            "semantic_role": "DIAGNOSTIC_BULK_EXTINCTION_ONLY",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Step 3D mathematical contract + Step 3I hybrid bridge",
            "source_path": "ice_microphysics_wyser_yang_diagnostic_bulk_integration",
            "source_sha": "",
            "notes": "IWC is converted from g/m3 to kg/m3 only when forming k_ext in m2/kg.",
        },
        {
            "evidence_id": "DIAGNOSTIC_CEXT_INTERPOLATION",
            "evidence_type": "NUMERICAL_METHOD_CONTRACT",
            "pin_status": "PINNED_LOGLOG_WITH_SOURCE_KNOTS_NO_EXTRAPOLATION",
            "value": INTERPOLATION_CONTRACT,
            "semantic_role": "NUMERICAL_INTERPOLATION_NOT_MICROPHYSICAL_MAPPING",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Yang/Bi V2 compact source knots",
            "source_path": sample["kernel_source_path"],
            "source_sha": "",
            "notes": "Every source Dmax knot is forced onto each integration grid; interpolation never extrapolates beyond 10-1000 um.",
        },
        {
            "evidence_id": "DIAGNOSTIC_SIX_BAND_BULK_EXTINCTION",
            "evidence_type": "DIAGNOSTIC_NUMERIC_BULK_RESULT",
            "pin_status": "PASS_DIAGNOSTIC_BETA_KEXT_NUMERIC" if grid["all_numeric_bulk_extinction_pass"] else "BLOCKED_DIAGNOSTIC_BULK_FAILED",
            "value": f"sample_T=253.16K;IWC=0.1g/m3;kext_m2kg={kext_summary}",
            "semantic_role": "SIX_BAND_BETA_EXT_AND_K_EXT_DIAGNOSTIC_ONLY",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Wyser Eq.(6) PSD normalization + Yang/Bi V2 Cext kernel",
            "source_path": "Step 3J 18-case diagnostic matrix",
            "source_sha": "",
            "notes": "These are diagnostic bulk coefficients and are not written to runtime ice optics.",
        },
        {
            "evidence_id": "DIAGNOSTIC_BULK_GRID_CONVERGENCE",
            "evidence_type": "NUMERICAL_CONVERGENCE_GATE",
            "pin_status": "PASS_DIAGNOSTIC_GRID_CONVERGENCE" if grid["all_grid_convergence_pass"] else "BLOCKED_GRID_CONVERGENCE_FAILED",
            "value": f"max_relative_error={stable_evidence_float(grid['max_bulk_convergence_relative_error'])};tolerance={stable_evidence_float(BULK_CONVERGENCE_TOLERANCE)}",
            "semantic_role": "NUMERICAL_STABILITY_NOT_SCIENTIFIC_VALIDATION",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "1025/4097 point grids vs 16385 point reference",
            "source_path": "Step 3J diagnostic matrix",
            "source_sha": "",
            "notes": "Convergence only qualifies the numerical integrator; it does not validate habit/roughness or physical representativeness.",
        },
        {
            "evidence_id": "DIAGNOSTIC_PSD_MASS_CLOSURE",
            "evidence_type": "NUMERICAL_MASS_CLOSURE_GATE",
            "pin_status": "PASS_DIAGNOSTIC_MASS_CLOSURE" if grid["max_mass_closure_relative_error"] <= MASS_CLOSURE_TOLERANCE else "BLOCKED_MASS_CLOSURE_FAILED",
            "value": f"max_relative_error={stable_evidence_float(grid['max_mass_closure_relative_error'])}",
            "semantic_role": "WYSER_EQ6_POPULATION_NORMALIZATION_DIAGNOSTIC_ONLY",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "R5.7.41.3.4.10.20.1 Step 3G",
            "source_path": "Step 3J integration grids",
            "source_sha": "",
            "notes": "Scientific mass closure remains blocked by independent Eq.(6) corroboration policy.",
        },
        {
            "evidence_id": "SCIENTIFIC_BULK_INDEPENDENT_VALIDATION",
            "evidence_type": "SCIENTIFIC_PROMOTION_GATE",
            "pin_status": "BLOCKED_NOT_PERFORMED",
            "value": "false",
            "semantic_role": "INDEPENDENT_REFERENCE_REQUIRED",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "future independent bulk optics comparison",
            "source_path": "Step 3J promotion policy",
            "source_sha": "",
            "notes": "Diagnostic numeric convergence is not independent scientific validation.",
        },
        {
            "evidence_id": "YANG_BI_HABIT_BRIDGE",
            "evidence_type": "MICROPHYSICS_TO_OPTICS_GATE",
            "pin_status": "BLOCKED",
            "value": "false",
            "semantic_role": "NO_RUNTIME_HABIT_DEFAULT",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Step 3I",
            "source_path": "single_column is diagnostic reference only",
            "source_sha": "",
            "notes": "No GFS/Wyser runtime habit variable has been validated to select single_column.",
        },
        {
            "evidence_id": "YANG_BI_ROUGHNESS_BRIDGE",
            "evidence_type": "MICROPHYSICS_TO_OPTICS_GATE",
            "pin_status": "BLOCKED",
            "value": "false",
            "semantic_role": "NO_RUNTIME_ROUGHNESS_DEFAULT",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Step 3I",
            "source_path": "Rough000 is diagnostic reference only",
            "source_sha": "",
            "notes": "Rough000 is not a production default.",
        },
        {
            "evidence_id": "BULK_YANG_BI_PSD_PRODUCTION_ELIGIBILITY",
            "evidence_type": "PRODUCTION_PROMOTION_GATE",
            "pin_status": "BLOCKED_DIAGNOSTIC_ONLY",
            "value": "false",
            "semantic_role": "NO_BULK_RUNTIME_PROMOTION",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Step 3J",
            "source_path": "diagnostic-only bulk integration",
            "source_sha": "",
            "notes": "Numeric beta/k_ext availability does not make the hybrid PSD×kernel scientifically eligible for runtime use.",
        },
        {
            "evidence_id": "TAU_ICE_PRODUCTION_PROMOTION",
            "evidence_type": "PRODUCTION_PROMOTION_GATE",
            "pin_status": "BLOCKED_NOT_COMPUTED_IN_STEP3J",
            "value": "false",
            "semantic_role": "NO_TAU_SYNTHESIS",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Step 3J scope boundary",
            "source_path": "tau_ice intentionally omitted",
            "source_sha": "",
            "notes": "Step 3J stops at beta_ext and k_ext. tau_ice=IWP*k_ext remains disabled.",
        },
        {
            "evidence_id": "STEP3J_PRODUCTION_PROMOTION",
            "evidence_type": "MASTER_PROMOTION_GATE",
            "pin_status": "BLOCKED",
            "value": "false",
            "semantic_role": "PHYSICS_PROMOTION_FAIL_CLOSED",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Frozen science baseline",
            "source_path": "Step 3J master gate",
            "source_sha": "",
            "notes": "Frozen Formation/Viewing/Twilight Glow and current ice runtime remain unchanged.",
        },
    ]
    return pd.DataFrame([
        {
            "step3j_version": STEP3J_VERSION,
            "science_baseline": SCIENCE_BASELINE,
            "step3j_mode": STEP3J_MODE,
            **row,
        }
        for row in rows
    ], columns=EVIDENCE_COLUMNS)


def build_wyser_yang_diagnostic_bulk_gate(evidence: pd.DataFrame | None = None) -> pd.DataFrame:
    df = evidence.copy() if isinstance(evidence, pd.DataFrame) else build_wyser_yang_diagnostic_bulk_evidence()
    if not df.empty and "evidence_id" not in df.columns and df.index.name == "evidence_id":
        df = df.reset_index()
    status = {str(r["evidence_id"]): str(r["pin_status"]) for _, r in df.iterrows()} if not df.empty else {}
    numeric = status.get("DIAGNOSTIC_SIX_BAND_BULK_EXTINCTION") == "PASS_DIAGNOSTIC_BETA_KEXT_NUMERIC"
    convergence = status.get("DIAGNOSTIC_BULK_GRID_CONVERGENCE") == "PASS_DIAGNOSTIC_GRID_CONVERGENCE"
    mass_closure = status.get("DIAGNOSTIC_PSD_MASS_CLOSURE") == "PASS_DIAGNOSTIC_MASS_CLOSURE"

    scientific = False
    habit = False
    roughness = False
    eligible = False
    tau_allowed = False
    production = False
    blockers = [
        "INDEPENDENT_EQ6_EXTERNAL_NUMERIC_CORROBORATION_PENDING",
        "SCIENTIFIC_BULK_INDEPENDENT_VALIDATION_NOT_PERFORMED",
        "YANG_BI_HABIT_BRIDGE_NOT_VALIDATED",
        "YANG_BI_ROUGHNESS_BRIDGE_NOT_VALIDATED",
        "BULK_RUNTIME_PROMOTION_NOT_ALLOWED",
        "TAU_ICE_NOT_COMPUTED_IN_STEP3J",
    ]
    qualification = (
        "DIAGNOSTIC_BETA_KEXT_NUMERIC_READY_SCIENTIFIC_AND_TAU_PROMOTION_BLOCKED"
        if numeric and convergence and mass_closure else
        "DIAGNOSTIC_BULK_NUMERIC_PREFLIGHT_INCOMPLETE"
    )
    return pd.DataFrame([{
        "step3j_version": STEP3J_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "step3j_mode": STEP3J_MODE,
        "DIAGNOSTIC_SIX_BAND_BULK_EXTINCTION_PASS": bool(numeric),
        "DIAGNOSTIC_BULK_GRID_CONVERGENCE_PASS": bool(convergence),
        "DIAGNOSTIC_PSD_MASS_CLOSURE_PASS": bool(mass_closure),
        "SCIENTIFIC_BULK_VALIDATION_PASS": bool(scientific),
        "YANG_BI_HABIT_BRIDGE_VALIDATED": bool(habit),
        "YANG_BI_ROUGHNESS_BRIDGE_VALIDATED": bool(roughness),
        "BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE": bool(eligible),
        "TAU_ICE_PRODUCTION_ALLOWED": bool(tau_allowed),
        "PRODUCTION_ICE_OPTICS_READY": bool(production),
        "physics_promotion_allowed": False,
        "qualification_state": qualification,
        "blocking_reasons": "|".join(blockers),
    }])


def wyser_yang_diagnostic_bulk_contract_payload(*, physicscore_version: str | None = None) -> dict[str, Any]:
    grid = run_diagnostic_bulk_extinction_grid()
    return {
        "contract_version": "FIRECLOUD_ICE_WYSER_YANG_DIAGNOSTIC_BULK_V1",
        "physicscore_version": physicscore_version or "",
        "step3j_version": STEP3J_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "mode": STEP3J_MODE,
        "diagnostic_only": True,
        "population_mass_semantic": POPULATION_MASS_SEMANTIC,
        "optical_kernel_mass_semantic": OPTICAL_KERNEL_MASS_SEMANTIC,
        "mass_semantics_interchangeable": False,
        "beta_ext_definition": BETA_EXT_DEFINITION,
        "k_ext_definition": K_EXT_DEFINITION,
        "diagnostic_reference_habit": DIAGNOSTIC_REFERENCE_HABIT,
        "diagnostic_reference_roughness": DIAGNOSTIC_REFERENCE_ROUGHNESS,
        "runtime_habit_roughness_selected": False,
        "interpolation_contract": INTERPOLATION_CONTRACT,
        "wavelengths_nm": [int(v) for v in ICE_OPTICS_WAVELENGTHS_NM],
        "dmax_domain_um": [float(WYSER_PSD_LMIN_UM), float(WYSER_PSD_LMAX_UM)],
        "diagnostic_matrix": {
            "temperatures_k": grid["temperatures_k"],
            "iwc_values_g_m3": grid["iwc_values_g_m3"],
            "grid_points": grid["grid_points"],
            "reference_grid_points": grid["reference_grid_points"],
            "case_count": grid["case_count"],
            "all_numeric_bulk_extinction_pass": grid["all_numeric_bulk_extinction_pass"],
            "all_grid_convergence_pass": grid["all_grid_convergence_pass"],
            "max_mass_closure_relative_error": grid["max_mass_closure_relative_error"],
            "max_bulk_convergence_relative_error": grid["max_bulk_convergence_relative_error"],
        },
        "scientific_bulk_validation_pass": False,
        "bulk_yang_bi_psd_integration_eligible": False,
        "tau_ice_computed": False,
        "tau_ice_production_allowed": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "forbidden_shortcuts": [
            "diagnostic_single_column_rough000_treated_as_runtime_habit_roughness_default",
            "diagnostic_k_ext_written_into_runtime_ice_optics",
            "tau_ice_synthesized_from_step3j_k_ext",
            "numerical_grid_convergence_treated_as_independent_scientific_validation",
            "yang_geometric_mass_used_to_normalize_wyser_psd",
        ],
    }
