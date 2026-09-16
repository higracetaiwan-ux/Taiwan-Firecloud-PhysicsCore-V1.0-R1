"""Ice Optics Phase 2 Step 3G — primary Wyser Eq.(5)/(6) numeric recovery.

This module pins diagnostic numeric forms for Wyser (1998) Eq.(5) and Eq.(6)
from primary indexed text plus an independent Eq.(5) transcription, verifies
unit-equivalent reproductions, and reproduces the pinned mixed-PSD IWC
normalization numerically with the recovered primary Eq.(6).  That reproduction
is a diagnostic numerical preflight only.  Eq.(6) still lacks an independent
external numeric transcription, so scientific PSD mass-closure, L->Yang/Bi
Dmax, bulk ice optics and production promotion remain disabled.
"""
from __future__ import annotations

from typing import Any, Iterable
import math
import numpy as np
import pandas as pd

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
STEP3G_VERSION = "R5.7.41.3.4.10.20.1"
STEP3G_MODE = "WYSER_PRIMARY_EQ5_EQ6_NUMERIC_RECOVERY_DIAGNOSTIC_MASS_CLOSURE_EXTERNAL_EQ6_CORROBORATION_PENDING"
PHYSICS_PROMOTION_ALLOWED = False
EVIDENCE_AS_OF = "2026-09-17"
WAVELENGTHS_NM = [550, 575, 600, 650, 700, 750]

_WYSER_PRIMARY = "https://doi.org/10.1175/1520-0442(1998)011%3C1793:TERIIC%3E2.0.CO;2"
_CHEN_2006 = "https://www.ess.uci.edu/~ychen17/publications/Chen-2006-Dissertation.pdf"
_WYSER_YANG_1998 = "https://doi.org/10.1016/S0169-8095(98)00083-0"
_ACP_LINEAGE = "https://acp.copernicus.org/preprints/9/24361/2009/acpd-9-24361-2009-print.pdf"
_YANG_REF = "https://www.giss.nasa.gov/pubs/abs/ya07100h.html"

WYSER_EQ5_TRANSITION_LENGTH_UM = 30.0
WYSER_EQ5_ASPECT_SLOPE_PER_UM = 0.003
WYSER_EQ6_COEFFICIENT_G = 2.311e-2
WYSER_EQ6_REFERENCE_LENGTH_UM = 1.0e4
WYSER_EQ6_EXPONENT = 2.7625
WYSER_PSD_SWITCH_LENGTH_UM = 20.0
WYSER_PSD_NU = 3.0
WYSER_PSD_LAMBDA_PER_UM = 0.3
WYSER_PSD_IWC_REFERENCE_G_M3 = 50.0
WYSER_PSD_TICE_K = 273.16
WYSER_PSD_LMIN_UM = 10.0
WYSER_PSD_LMAX_UM = 1000.0


def _positive_finite(value: float, *, name: str) -> float:
    out = float(value)
    if not math.isfinite(out) or out <= 0:
        raise ValueError(f"{name} must be positive and finite")
    return out


def wyser_eq5_aspect_ratio(length_um: float) -> float:
    """Return Wyser (1998) Eq.(5) L/D for a crystal length L in microns."""
    length = _positive_finite(length_um, name="length_um")
    if length < WYSER_EQ5_TRANSITION_LENGTH_UM:
        return 1.0
    return 1.0 + WYSER_EQ5_ASPECT_SLOPE_PER_UM * (length - WYSER_EQ5_TRANSITION_LENGTH_UM)


def wyser_eq5_width_um(length_um: float) -> float:
    """Return the Eq.(5) hexagonal-column width D in microns."""
    length = _positive_finite(length_um, name="length_um")
    return length / wyser_eq5_aspect_ratio(length)


def wyser_eq6_mass_g(length_um: float) -> float:
    """Return Wyser (1998) Eq.(6) particle mass in grams for L in microns."""
    length = _positive_finite(length_um, name="length_um")
    return WYSER_EQ6_COEFFICIENT_G * (length / WYSER_EQ6_REFERENCE_LENGTH_UM) ** WYSER_EQ6_EXPONENT


def wyser_eq6_mass_g_expanded_um(length_um: float) -> float:
    """Independent algebraic reproduction of Eq.(6) as C_um * L_um**p."""
    length = _positive_finite(length_um, name="length_um")
    coefficient = WYSER_EQ6_COEFFICIENT_G / (WYSER_EQ6_REFERENCE_LENGTH_UM ** WYSER_EQ6_EXPONENT)
    return coefficient * length ** WYSER_EQ6_EXPONENT


def wyser_eq6_mass_kg_si(length_m: float) -> float:
    """Independent SI-unit reproduction of Eq.(6), returning kg for L in metres."""
    length = _positive_finite(length_m, name="length_m")
    coefficient_g_per_um_p = WYSER_EQ6_COEFFICIENT_G / (WYSER_EQ6_REFERENCE_LENGTH_UM ** WYSER_EQ6_EXPONENT)
    coefficient_kg_per_m_p = coefficient_g_per_um_p * 1e-3 * (1e6 ** WYSER_EQ6_EXPONENT)
    return coefficient_kg_per_m_p * length ** WYSER_EQ6_EXPONENT


def verify_wyser_eq5_eq6_unit_consistency() -> dict[str, Any]:
    """Numerically reproduce Eq.(5)/(6) across unit forms without promoting physics."""
    benchmark_um = (10.0, 30.0, 100.0, 1000.0)
    eq5_continuity_error_um = abs(wyser_eq5_width_um(30.0 - 1e-9) - wyser_eq5_width_um(30.0 + 1e-9))
    eq6_relative_errors: list[float] = []
    for length_um in benchmark_um:
        primary_g = wyser_eq6_mass_g(length_um)
        expanded_g = wyser_eq6_mass_g_expanded_um(length_um)
        si_g = wyser_eq6_mass_kg_si(length_um * 1e-6) * 1e3
        eq6_relative_errors.extend([
            abs(expanded_g - primary_g) / primary_g,
            abs(si_g - primary_g) / primary_g,
        ])
    max_eq6_relative_error = max(eq6_relative_errors)
    passed = eq5_continuity_error_um <= 2e-9 and max_eq6_relative_error <= 1e-12
    return {
        "diagnostic_only": True,
        "eq5_continuity_error_um": float(eq5_continuity_error_um),
        "eq6_max_relative_error": float(max_eq6_relative_error),
        "benchmark_lengths_um": list(benchmark_um),
        "unit_consistency_pass": bool(passed),
    }


def wyser_powerlaw_exponent(*, temperature_k: float, iwc_g_m3: float) -> float:
    """Return the pinned GFS-v16/Wyser mixed-PSD power-law exponent B.

    This is a diagnostic reconstruction of the already pinned Step-3D/3E
    expression.  It does not establish an operational validity domain.
    """
    temperature = _positive_finite(temperature_k, name="temperature_k")
    iwc = _positive_finite(iwc_g_m3, name="iwc_g_m3")
    cold_delta = max(0.0, WYSER_PSD_TICE_K - temperature)
    return -2.0 + 1.0e-3 * math.log10(iwc / WYSER_PSD_IWC_REFERENCE_G_M3) * cold_delta ** 1.5


def wyser_mixed_psd_shape(
    length_um: float,
    *,
    temperature_k: float,
    iwc_g_m3: float,
) -> float:
    """Return the unnormalised pinned mixed Wyser PSD shape ``phi(L)``.

    The small-particle branch is Gamma-like through 20 um.  The large branch
    uses the pinned B(T,IWC) exponent with its analytic continuity factor.
    """
    length = _positive_finite(length_um, name="length_um")
    b = wyser_powerlaw_exponent(temperature_k=temperature_k, iwc_g_m3=iwc_g_m3)
    if length <= WYSER_PSD_SWITCH_LENGTH_UM:
        return length ** WYSER_PSD_NU * math.exp(-WYSER_PSD_LAMBDA_PER_UM * length)
    alpha = (
        WYSER_PSD_SWITCH_LENGTH_UM ** (WYSER_PSD_NU - b)
        * math.exp(-WYSER_PSD_LAMBDA_PER_UM * WYSER_PSD_SWITCH_LENGTH_UM)
    )
    return alpha * length ** b


def _wyser_length_grid(grid_points: int) -> np.ndarray:
    points = int(grid_points)
    if points < 65:
        raise ValueError("grid_points must be >= 65")
    grid = np.geomspace(WYSER_PSD_LMIN_UM, WYSER_PSD_LMAX_UM, points)
    # Force the piecewise switch onto every grid so branch treatment is
    # resolution-independent rather than relying on accidental sampling.
    return np.unique(np.concatenate([grid, np.array([WYSER_PSD_SWITCH_LENGTH_UM], dtype=float)]))


def _wyser_shape_array(length_um: np.ndarray, *, temperature_k: float, iwc_g_m3: float) -> np.ndarray:
    b = wyser_powerlaw_exponent(temperature_k=temperature_k, iwc_g_m3=iwc_g_m3)
    length = np.asarray(length_um, dtype=float)
    small = length ** WYSER_PSD_NU * np.exp(-WYSER_PSD_LAMBDA_PER_UM * length)
    alpha = (
        WYSER_PSD_SWITCH_LENGTH_UM ** (WYSER_PSD_NU - b)
        * math.exp(-WYSER_PSD_LAMBDA_PER_UM * WYSER_PSD_SWITCH_LENGTH_UM)
    )
    large = alpha * length ** b
    return np.where(length <= WYSER_PSD_SWITCH_LENGTH_UM, small, large)


def _wyser_mass_array_g(length_um: np.ndarray) -> np.ndarray:
    length = np.asarray(length_um, dtype=float)
    return WYSER_EQ6_COEFFICIENT_G * (length / WYSER_EQ6_REFERENCE_LENGTH_UM) ** WYSER_EQ6_EXPONENT


def diagnostic_wyser_primary_mass_closure_reproduction(
    *,
    temperature_k: float,
    iwc_g_m3: float,
    grid_points: int = 4097,
    reference_grid_points: int = 32769,
) -> dict[str, Any]:
    """Reproduce IWC closure using the recovered primary Eq.(6) diagnostically.

    The normalization denominator is also recomputed on a denser independent
    numerical grid.  This checks integration convergence in addition to the
    algebraic closure identity.  It is intentionally *not* a scientific
    promotion gate while external Eq.(6) corroboration remains open.
    """
    temperature = _positive_finite(temperature_k, name="temperature_k")
    iwc = _positive_finite(iwc_g_m3, name="iwc_g_m3")
    if int(reference_grid_points) <= int(grid_points):
        raise ValueError("reference_grid_points must exceed grid_points")

    length = _wyser_length_grid(grid_points)
    phi = _wyser_shape_array(length, temperature_k=temperature, iwc_g_m3=iwc)
    mass = _wyser_mass_array_g(length)
    denominator = float(np.trapezoid(mass * phi, length))
    if not math.isfinite(denominator) or denominator <= 0.0:
        raise ValueError("primary Eq.(6) normalization denominator must be positive and finite")
    amplitude = iwc / denominator
    reconstructed = float(np.trapezoid(mass * amplitude * phi, length))
    closure_error = abs(reconstructed - iwc) / iwc

    ref_length = _wyser_length_grid(reference_grid_points)
    ref_phi = _wyser_shape_array(ref_length, temperature_k=temperature, iwc_g_m3=iwc)
    ref_mass = _wyser_mass_array_g(ref_length)
    reference_denominator = float(np.trapezoid(ref_mass * ref_phi, ref_length))
    convergence_error = abs(denominator - reference_denominator) / reference_denominator

    switch = WYSER_PSD_SWITCH_LENGTH_UM
    b = wyser_powerlaw_exponent(temperature_k=temperature, iwc_g_m3=iwc)
    small_at_switch = switch ** WYSER_PSD_NU * math.exp(-WYSER_PSD_LAMBDA_PER_UM * switch)
    alpha = switch ** (WYSER_PSD_NU - b) * math.exp(-WYSER_PSD_LAMBDA_PER_UM * switch)
    large_at_switch = alpha * switch ** b
    continuity_error = abs(large_at_switch - small_at_switch) / small_at_switch

    numeric_pass = bool(
        closure_error <= 1e-12
        and continuity_error <= 1e-9
        and convergence_error <= 5e-5
    )
    return {
        "diagnostic_only": True,
        "input_contract": "WYSER_PRIMARY_EQ6_WITH_PINNED_MIXED_PSD_DIAGNOSTIC_ONLY",
        "temperature_k": float(temperature),
        "iwc_g_m3": float(iwc),
        "powerlaw_B": float(b),
        "domain_um": [WYSER_PSD_LMIN_UM, WYSER_PSD_LMAX_UM],
        "branch_switch_um": WYSER_PSD_SWITCH_LENGTH_UM,
        "grid_points_requested": int(grid_points),
        "grid_points_actual": int(length.size),
        "reference_grid_points_requested": int(reference_grid_points),
        "reference_grid_points_actual": int(ref_length.size),
        "normalization_denominator": float(denominator),
        "reference_normalization_denominator": float(reference_denominator),
        "normalization_amplitude": float(amplitude),
        "target_iwc_g_m3": float(iwc),
        "reconstructed_iwc_g_m3": float(reconstructed),
        "mass_closure_relative_error": float(closure_error),
        "branch_continuity_relative_error": float(continuity_error),
        "normalization_convergence_relative_error": float(convergence_error),
        "numeric_mass_closure_pass": numeric_pass,
        "scientific_mass_closure_pass": False,
    }


def run_diagnostic_wyser_primary_mass_closure_grid(
    *,
    temperatures_k: Iterable[float] = (233.16, 253.16, 273.16),
    iwc_values_g_m3: Iterable[float] = (0.001, 0.1, 10.0),
    grid_points: Iterable[int] = (1025, 4097),
    reference_grid_points: int = 32769,
) -> dict[str, Any]:
    """Run a numerical-preflight matrix without defining an operational domain."""
    temperatures = tuple(float(v) for v in temperatures_k)
    iwcs = tuple(float(v) for v in iwc_values_g_m3)
    grids = tuple(int(v) for v in grid_points)
    if not temperatures or not iwcs or not grids:
        raise ValueError("temperatures_k, iwc_values_g_m3 and grid_points must be non-empty")

    cases: list[dict[str, Any]] = []
    for temperature in temperatures:
        for iwc in iwcs:
            for points in grids:
                cases.append(diagnostic_wyser_primary_mass_closure_reproduction(
                    temperature_k=temperature,
                    iwc_g_m3=iwc,
                    grid_points=points,
                    reference_grid_points=reference_grid_points,
                ))
    all_pass = all(bool(case["numeric_mass_closure_pass"]) for case in cases)
    return {
        "diagnostic_only": True,
        "grid_scope": "NUMERICAL_PREFLIGHT_NOT_OPERATIONAL_VALIDITY_DOMAIN",
        "temperatures_k": list(temperatures),
        "iwc_values_g_m3": list(iwcs),
        "grid_points": list(grids),
        "reference_grid_points": int(reference_grid_points),
        "case_count": int(len(cases)),
        "all_numeric_mass_closure_pass": bool(all_pass),
        "max_mass_closure_relative_error": float(max(case["mass_closure_relative_error"] for case in cases)),
        "max_branch_continuity_relative_error": float(max(case["branch_continuity_relative_error"] for case in cases)),
        "max_normalization_convergence_relative_error": float(max(case["normalization_convergence_relative_error"] for case in cases)),
        "scientific_mass_closure_pass": False,
        "absolute_psd_reconstruction_executable": False,
        "production_ice_optics_ready": False,
        "cases": cases,
    }


EVIDENCE_COLUMNS = [
    "step3g_version", "science_baseline", "step3g_mode", "evidence_id",
    "evidence_type", "pin_status", "value", "semantic_role",
    "authoritative_for_runtime_mapping", "source_reference", "source_path",
    "source_sha", "notes",
]

_EVIDENCE: tuple[dict[str, Any], ...] = (
    {
        "evidence_id": "WYSER_PRIMARY_EQ5_ROLE",
        "evidence_type": "PRIMARY_GEOMETRY_SEMANTIC",
        "pin_status": "PINNED_PRIMARY_SEMANTIC",
        "value": "Eq.(5) defines L/D for solid hexagonal columns; L is length/maximum dimension and D is width/minimum dimension",
        "semantic_role": "PRIMARY_EQ5_ROLE",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Wyser (1998), Eq.(5) surrounding primary text",
        "source_sha": "",
        "notes": "Primary article semantics distinguish axial length L from width D.",
    },
    {
        "evidence_id": "WYSER_YANG_1998_GEOMETRY_LINEAGE",
        "evidence_type": "SEPARATE_GEOMETRY_LINEAGE",
        "pin_status": "SEPARATE_REFERENCE_NOT_WYSER_1998_EQ5",
        "value": "D=2.5*L^0.6",
        "semantic_role": "WYSER_YANG_1998_GEOMETRY_LINEAGE_NOT_SINGLE_AUTHOR_WYSER_EQ5",
        "authoritative_for_runtime_mapping": False,
        "source_reference": f"{_WYSER_YANG_1998}|{_ACP_LINEAGE}",
        "source_path": "Later literature attributes D=2.5 L^0.6 to Wyser and Yang (1998), not to single-author Wyser (1998) Eq.(5)",
        "source_sha": "",
        "notes": "This relation is retained only as a separate lineage reference and is forbidden as a substitute for Eq.(5).",
    },
    {
        "evidence_id": "WYSER_EQ5_PRIMARY_MACHINE_NUMERIC_RECOVERY",
        "evidence_type": "PRIMARY_NUMERIC_RECOVERY_GATE",
        "pin_status": "PINNED_PRIMARY_NUMERIC_WITH_INDEPENDENT_TRANSCRIPTION",
        "value": "L/D=1 for L<30 um; L/D=1+0.003*(L-30 um) for L>=30 um",
        "semantic_role": "PRIMARY_EQ5_NUMERIC_RECOVERED_DIAGNOSTIC_ONLY",
        "authoritative_for_runtime_mapping": False,
        "source_reference": f"{_WYSER_PRIMARY}|{_CHEN_2006}",
        "source_path": "Wyser (1998) indexed Eq.(5) text + Chen (2006) independent transcription Eq.(5.1)",
        "source_sha": "",
        "notes": "Primary indexed text exposes the 0.003 and 30-um piecewise relation; Chen independently transcribes the complete equation.",
    },
    {
        "evidence_id": "WYSER_PRIMARY_EQ6_ROLE_UNITS",
        "evidence_type": "PRIMARY_MASS_SIZE_SEMANTIC",
        "pin_status": "PINNED_PRIMARY_SEMANTIC_AND_UNITS",
        "value": "m(L)=rho(L)*V(L); m in grams; L in microns; parameters chosen for cold solid columns with L/D>2",
        "semantic_role": "PRIMARY_EQ6_ROLE_AND_UNITS",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Wyser (1998), Eq.(6) and surrounding primary text",
        "source_sha": "",
        "notes": "The particle-regime statement is preserved as provenance and is not silently broadened into a production validity claim.",
    },
    {
        "evidence_id": "WYSER_EQ6_INDEXED_TEXT_RECOVERY",
        "evidence_type": "PRIMARY_INDEXED_NUMERIC_RECOVERY",
        "pin_status": "RECOVERED_WITH_EXPLICIT_OLD_TYPESETTING_PARSE",
        "value": "indexed form: 2.311 3 10^-2 (L/10^4)^2.7625",
        "semantic_role": "PRIMARY_EQ6_MACHINE_INDEX_RECOVERY",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "AMS indexed/searchable rendering of Wyser (1998) Eq.(6)",
        "source_sha": "",
        "notes": "Old typography is parsed explicitly as multiplication and powers; this row supersedes the earlier blanket corrupt-extraction rejection for diagnostic numeric recovery only.",
    },
    {
        "evidence_id": "WYSER_EQ6_PRIMARY_MACHINE_NUMERIC_RECOVERY",
        "evidence_type": "PRIMARY_NUMERIC_RECOVERY_GATE",
        "pin_status": "PINNED_PRIMARY_NUMERIC_INDEX_RECOVERY",
        "value": "m_g(L_um)=2.311e-2*(L_um/1e4)^2.7625",
        "semantic_role": "PRIMARY_EQ6_NUMERIC_RECOVERED_DIAGNOSTIC_ONLY",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Wyser (1998), Eq.(6) indexed primary text",
        "source_sha": "",
        "notes": "Primary numeric form and units are now reproducible; independent external Eq.(6) numeric corroboration remains open, so promotion stays blocked.",
    },
    {
        "evidence_id": "DUAL_SOURCE_NUMERIC_PROMOTION_POLICY",
        "evidence_type": "PROMOTION_POLICY",
        "pin_status": "PINNED_FAIL_CLOSED_POLICY",
        "value": "primary numeric Eq.(5)+Eq.(6) AND independent external transcription/reproduction AND unit-consistency must pass before scientific closure promotion",
        "semantic_role": "NUMERIC_RECOVERY_PROMOTION_GATE",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "",
        "source_path": "PhysicsCore Step 3G qualification policy",
        "source_sha": "",
        "notes": "Eq.(5) has independent transcription. Eq.(6) has primary indexed recovery plus internal unit reproduction but still lacks independent external numeric corroboration.",
    },
    {
        "evidence_id": "DIAGNOSTIC_MASS_CLOSURE_HARNESS",
        "evidence_type": "SOFTWARE_READINESS",
        "pin_status": "READY_SYNTHETIC_ONLY",
        "value": "A=IWC/integral[m(L)*phi(L)dL]; reconstruct integral[m*A*phi dL]",
        "semantic_role": "GENERIC_SYNTHETIC_CLOSURE_HARNESS",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Wyser Eq.(7)/(8) algebra + PhysicsCore diagnostic utility",
        "source_sha": "",
        "notes": "Harness readiness validates code algebra only; it is not scientific validation.",
    },
    {
        "evidence_id": "SCIENTIFIC_MASS_CLOSURE_EXECUTED",
        "evidence_type": "SCIENTIFIC_VALIDATION_GATE",
        "pin_status": "BLOCKED_EXTERNAL_EQ6_CORROBORATION_PENDING",
        "value": "false",
        "semantic_role": "NO_PROMOTABLE_WYSER_SCIENTIFIC_CLOSURE_YET",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Step 3G dual-source promotion policy",
        "source_sha": "",
        "notes": "Exact primary numeric Eq.(5)/(6) and unit consistency are recovered, but external Eq.(6) numeric corroboration is still required before promotable scientific closure.",
    },
    {
        "evidence_id": "ABSOLUTE_PSD_RECONSTRUCTION_EXECUTABLE",
        "evidence_type": "EXECUTION_GATE",
        "pin_status": "BLOCKED_EXTERNAL_EQ6_CORROBORATION_PENDING",
        "value": "false",
        "semantic_role": "NO_ABSOLUTE_WYSER_PSD_EXECUTION",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Step 3G promotion gate",
        "source_sha": "",
        "notes": "Numeric mass law is diagnostic-only until the independent Eq.(6) corroboration gate is satisfied.",
    },
    {
        "evidence_id": "WYSER_L_TO_YANG_DMAX_COORDINATE",
        "evidence_type": "COORDINATE_BRIDGE_GATE",
        "pin_status": "UNRESOLVED",
        "value": "false",
        "semantic_role": "NO_L_TO_DMAX_RUNTIME_COORDINATE",
        "authoritative_for_runtime_mapping": False,
        "source_reference": f"{_WYSER_PRIMARY}|{_YANG_REF}",
        "source_path": "Wyser primary geometry versus Yang/Bi maximum-dimension convention",
        "source_sha": "",
        "notes": "Recovering Wyser Eq.(5) does not prove coordinate identity with the Yang/Bi maximum_dimension_um axis.",
    },
    {
        "evidence_id": "STEP3G_PRODUCTION_PROMOTION",
        "evidence_type": "PROMOTION_GATE",
        "pin_status": "BLOCKED",
        "value": "false",
        "semantic_role": "NUMERIC_RECOVERY_ONLY_NO_OPTICAL_PROMOTION",
        "authoritative_for_runtime_mapping": False,
        "source_reference": "",
        "source_path": "PhysicsCore frozen promotion policy",
        "source_sha": "",
        "notes": "No PSD runtime reconstruction, Dmax synthesis, habit/roughness selection, bulk tau synthesis or Formation promotion in this increment.",
    },
)


def build_wyser_primary_numeric_recovery_evidence() -> pd.DataFrame:
    rows = [
        {
            "step3g_version": STEP3G_VERSION,
            "science_baseline": SCIENCE_BASELINE,
            "step3g_mode": STEP3G_MODE,
            **item,
        }
        for item in _EVIDENCE
    ]
    preflight = run_diagnostic_wyser_primary_mass_closure_grid()
    rows.append({
        "step3g_version": STEP3G_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "step3g_mode": STEP3G_MODE,
        "evidence_id": "DIAGNOSTIC_PRIMARY_EQ6_PSD_MASS_CLOSURE_PREFLIGHT",
        "evidence_type": "NUMERICAL_PREFLIGHT",
        "pin_status": "PASS_DIAGNOSTIC_ONLY" if preflight["all_numeric_mass_closure_pass"] else "FAIL_DIAGNOSTIC_ONLY",
        "value": (
            f"cases={preflight['case_count']};"
            f"max_mass_closure_relative_error={preflight['max_mass_closure_relative_error']:.17g};"
            f"max_branch_continuity_relative_error={preflight['max_branch_continuity_relative_error']:.17g};"
            f"max_normalization_convergence_relative_error={preflight['max_normalization_convergence_relative_error']:.17g}"
        ),
        "semantic_role": "PRIMARY_EQ6_MIXED_PSD_NUMERICAL_PREFLIGHT_NOT_SCIENTIFIC_PROMOTION",
        "authoritative_for_runtime_mapping": False,
        "source_reference": _WYSER_PRIMARY,
        "source_path": "Recovered primary Eq.(6) + pinned Wyser mixed PSD + Eq.(7)/(8) normalization",
        "source_sha": "",
        "notes": "Numerical preflight spans explicit T/IWC/resolution test points only; it does not define or validate an operational physical domain and cannot satisfy the external Eq.(6) corroboration gate.",
    })
    return pd.DataFrame(rows, columns=EVIDENCE_COLUMNS)


def build_wyser_primary_numeric_recovery_gate(evidence: pd.DataFrame | None = None) -> pd.DataFrame:
    df = evidence.copy() if isinstance(evidence, pd.DataFrame) else build_wyser_primary_numeric_recovery_evidence()
    status = dict(zip(df["evidence_id"].astype(str), df["pin_status"].astype(str)))
    eq5 = status.get("WYSER_EQ5_PRIMARY_MACHINE_NUMERIC_RECOVERY") == "PINNED_PRIMARY_NUMERIC_WITH_INDEPENDENT_TRANSCRIPTION"
    eq6 = status.get("WYSER_EQ6_PRIMARY_MACHINE_NUMERIC_RECOVERY") == "PINNED_PRIMARY_NUMERIC_INDEX_RECOVERY"
    eq5_independent = bool(eq5)
    eq6_external = False
    independent_combined = bool(eq5_independent and eq6_external)
    unit_check = verify_wyser_eq5_eq6_unit_consistency()
    unit_consistency = bool(eq5 and eq6 and unit_check["unit_consistency_pass"])
    harness = status.get("DIAGNOSTIC_MASS_CLOSURE_HARNESS") == "READY_SYNTHETIC_ONLY"
    preflight = run_diagnostic_wyser_primary_mass_closure_grid()
    diagnostic_primary_closure_executed = True
    diagnostic_primary_closure_pass = bool(preflight["all_numeric_mass_closure_pass"])
    diagnostic_primary_convergence_pass = bool(preflight["max_normalization_convergence_relative_error"] <= 5e-5)
    scientific = False
    blockers = [
        "INDEPENDENT_EQ6_EXTERNAL_NUMERIC_CORROBORATION_NOT_PASSED",
        "INDEPENDENT_TRANSCRIPTION_REPRODUCTION_NOT_PASSED",
        "SCIENTIFIC_MASS_CLOSURE_NOT_EXECUTED",
        "ABSOLUTE_PSD_RECONSTRUCTION_BLOCKED",
        "WYSER_L_TO_YANG_DMAX_COORDINATE_UNRESOLVED",
        "YANG_BI_HABIT_BRIDGE_NOT_VALIDATED",
        "YANG_BI_ROUGHNESS_POLICY_NOT_VALIDATED",
        "NO_INDEPENDENT_BULK_OPTICS_VALIDATION",
    ]
    return pd.DataFrame([{
        "step3g_version": STEP3G_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "step3g_mode": STEP3G_MODE,
        "WYSER_EQ5_PRIMARY_MACHINE_NUMERIC_RECOVERED": bool(eq5),
        "WYSER_EQ6_PRIMARY_MACHINE_NUMERIC_RECOVERED": bool(eq6),
        "INDEPENDENT_EQ5_TRANSCRIPTION_PASS": bool(eq5_independent),
        "INDEPENDENT_EQ6_EXTERNAL_NUMERIC_CORROBORATION_PASS": bool(eq6_external),
        "INDEPENDENT_TRANSCRIPTION_REPRODUCTION_PASS": bool(independent_combined),
        "EQ5_EQ6_UNIT_CONSISTENCY_PASS": bool(unit_consistency),
        "DIAGNOSTIC_MASS_CLOSURE_HARNESS_READY": bool(harness),
        "DIAGNOSTIC_PRIMARY_EQ6_PSD_MASS_CLOSURE_EXECUTED": bool(diagnostic_primary_closure_executed),
        "DIAGNOSTIC_PRIMARY_EQ6_PSD_MASS_CLOSURE_NUMERIC_PASS": bool(diagnostic_primary_closure_pass),
        "DIAGNOSTIC_PRIMARY_EQ6_PSD_CONVERGENCE_PASS": bool(diagnostic_primary_convergence_pass),
        "SCIENTIFIC_MASS_CLOSURE_EXECUTED": bool(scientific),
        "ABSOLUTE_PSD_RECONSTRUCTION_EXECUTABLE": False,
        "PSD_MASS_CLOSURE_VALIDATION_PASS": False,
        "WYSER_L_TO_YANG_DMAX_COORDINATE_VALIDATED": False,
        "BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE": False,
        "GFSV16_DMAX_MAPPING_ELIGIBLE": False,
        "PRODUCTION_ICE_OPTICS_READY": False,
        "physics_promotion_allowed": False,
        "evidence_row_count": int(len(df)),
        "qualification_state": "WYSER_PRIMARY_EQ5_EQ6_NUMERIC_RECOVERED_DIAGNOSTIC_MASS_CLOSURE_PASS_EXTERNAL_EQ6_CORROBORATION_BLOCKED",
        "qualification_blockers": "|".join(blockers),
        "detail": "Primary Eq.5 and Eq.6 numeric forms are recovered, unit-equivalent reproductions pass, and the recovered Eq.6 closes the pinned mixed-PSD IWC normalization numerically on the diagnostic preflight grid. Eq.6 still lacks independent external numeric corroboration, so scientific mass closure, absolute PSD, L->Dmax and production promotion remain fail-closed.",
    }])


def diagnostic_mass_closure(
    *,
    length_um: Iterable[float],
    shape_weights: Iterable[float],
    mass_g: Iterable[float],
    iwc_g_m3: float,
) -> dict[str, Any]:
    """Generic synthetic normalization closure harness.

    The input arrays are caller supplied and are deliberately *not* interpreted
    as Wyser Eq.(5)/(6).  Passing this calculation cannot satisfy a scientific
    Wyser mass-closure gate.
    """
    L = np.asarray(list(length_um), dtype=float)
    phi = np.asarray(list(shape_weights), dtype=float)
    mass = np.asarray(list(mass_g), dtype=float)
    iwc = float(iwc_g_m3)
    if L.ndim != 1 or phi.ndim != 1 or mass.ndim != 1 or not (len(L) == len(phi) == len(mass)):
        raise ValueError("length_um, shape_weights and mass_g must be equal-length 1-D arrays")
    if len(L) < 2:
        raise ValueError("at least two size points are required")
    if not np.all(np.isfinite(L)) or not np.all(np.isfinite(phi)) or not np.all(np.isfinite(mass)) or not math.isfinite(iwc):
        raise ValueError("all inputs must be finite")
    if np.any(L <= 0) or np.any(np.diff(L) <= 0):
        raise ValueError("length_um must be strictly increasing and positive")
    if np.any(phi < 0) or np.any(mass <= 0) or iwc <= 0:
        raise ValueError("shape_weights must be nonnegative; mass_g and iwc_g_m3 must be positive")
    denom = float(np.trapezoid(mass * phi, L))
    if not math.isfinite(denom) or denom <= 0:
        raise ValueError("normalization denominator must be positive and finite")
    amplitude = iwc / denom
    reconstructed = float(np.trapezoid(mass * amplitude * phi, L))
    relative_error = abs(reconstructed - iwc) / iwc
    return {
        "diagnostic_only": True,
        "input_contract": "SYNTHETIC_GENERIC_NOT_WYSER_SCIENTIFIC_VALIDATION",
        "integration_coordinate": "caller_supplied_length_um",
        "amplitude": float(amplitude),
        "normalization_denominator": denom,
        "target_iwc_g_m3": iwc,
        "reconstructed_iwc_g_m3": reconstructed,
        "relative_error": float(relative_error),
        "numeric_closure_pass": bool(relative_error <= 1e-12),
        "scientific_mass_closure_pass": False,
    }


def wyser_primary_numeric_recovery_contract_payload(*, physicscore_version: str | None = None) -> dict[str, Any]:
    unit_check = verify_wyser_eq5_eq6_unit_consistency()
    preflight = run_diagnostic_wyser_primary_mass_closure_grid()
    preflight_summary = {key: value for key, value in preflight.items() if key != "cases"}
    return {
        "contract_version": "FIRECLOUD_ICE_WYSER_PRIMARY_NUMERIC_RECOVERY_V3",
        "physicscore_version": physicscore_version or "",
        "step3g_version": STEP3G_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "mode": STEP3G_MODE,
        "wavelengths_nm": list(WAVELENGTHS_NM),
        "wyser_eq5_primary_machine_numeric_recovered": True,
        "wyser_eq5_primary_numeric": {
            "coordinate": "L_um_to_width_D_um",
            "definition": "L is length/maximum dimension; D is width/minimum dimension",
            "transition_length_um": WYSER_EQ5_TRANSITION_LENGTH_UM,
            "small_branch": "L/D=1 for L<30 um",
            "large_branch": "L/D=1+0.003*(L-30 um) for L>=30 um",
            "aspect_slope_per_um": WYSER_EQ5_ASPECT_SLOPE_PER_UM,
        },
        "wyser_eq6_primary_machine_numeric_recovered": True,
        "wyser_eq6_primary_numeric": {
            "formula": "m_g=2.311e-2*(L_um/1e4)^2.7625",
            "coefficient_g": WYSER_EQ6_COEFFICIENT_G,
            "reference_length_um": WYSER_EQ6_REFERENCE_LENGTH_UM,
            "exponent": WYSER_EQ6_EXPONENT,
            "mass_unit": "g",
            "length_unit": "um",
            "primary_regime_note": "parameters chosen for cold solid columns with L/D>2",
        },
        "separate_wyser_yang_1998_geometry_lineage": "D=2.5*L^0.6",
        "separate_wyser_yang_lineage_is_wyser_1998_eq5": False,
        "independent_eq5_transcription_pass": True,
        "independent_eq6_external_numeric_corroboration_pass": False,
        "independent_transcription_reproduction_pass": False,
        "eq5_eq6_unit_consistency_pass": bool(unit_check["unit_consistency_pass"]),
        "unit_consistency_diagnostic": unit_check,
        "diagnostic_mass_closure_harness_ready": True,
        "diagnostic_harness_scope": "SYNTHETIC_GENERIC_ONLY_NOT_WYSER_SCIENTIFIC_VALIDATION",
        "diagnostic_primary_eq6_psd_mass_closure_executed": True,
        "diagnostic_primary_eq6_psd_mass_closure_numeric_pass": bool(preflight["all_numeric_mass_closure_pass"]),
        "diagnostic_primary_eq6_psd_convergence_pass": bool(preflight["max_normalization_convergence_relative_error"] <= 5e-5),
        "diagnostic_primary_eq6_psd_mass_closure": preflight_summary,
        "scientific_mass_closure_executed": False,
        "absolute_psd_reconstruction_executable": False,
        "psd_mass_closure_validation_pass": False,
        "wyser_L_to_yang_dmax_coordinate_validated": False,
        "yang_bi_habit_bridge_validated": False,
        "yang_bi_roughness_bridge_validated": False,
        "bulk_yang_bi_psd_integration_eligible": False,
        "gfsv16_dmax_mapping_eligible": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "numeric_promotion_policy": {
            "requires_primary_eq5_machine_numeric": True,
            "requires_primary_eq6_machine_numeric": True,
            "requires_independent_external_numeric_corroboration": True,
            "requires_unit_consistency": True,
            "internal_unit_reproduction_does_not_replace_external_corroboration": True,
            "synthetic_harness_cannot_satisfy_scientific_gate": True,
            "diagnostic_primary_eq6_mass_closure_cannot_replace_external_corroboration": True,
        },
        "forbidden_shortcuts": [
            "Wyser_Yang_1998_D_2p5_L_0p6_substituted_for_single_author_Wyser_1998_equation_5",
            "indexed_equation_6_parse_treated_as_independent_external_corroboration",
            "unrelated_mass_size_law_substituted_for_Wyser_equation_6",
            "synthetic_harness_pass_treated_as_scientific_Wyser_mass_closure",
            "scientific_mass_closure_claimed_before_independent_eq6_numeric_corroboration",
            "diagnostic_primary_eq6_mass_closure_pass_promoted_as_scientific_validation",
            "absolute_PSD_reconstruction_before_dual_source_numeric_promotion",
            "Wyser_L_silently_equal_to_Yang_Bi_Dmax",
            "Yang_Bi_habit_selected_before_geometry_coordinate_validation",
            "single_roughness_state_silently_selected",
            "bulk_tau_synthesized_before_independent_validation",
            "production_promotion_before_step3g_and_later_gates_pass",
        ],
        "qualification_requirements": [
            "obtain_independent_external_numeric_corroboration_for_Wyser_equation_6",
            "execute_scientific_IWC_mass_closure_grid_over_supported_domain_after_dual_source_gate",
            "validate_Wyser_L_to_Yang_Bi_maximum_dimension_coordinate",
            "validate_Yang_Bi_habit_geometry_bridge",
            "validate_roughness_uncertainty_policy",
            "independent_bulk_shortwave_optics_validation",
            "separate_production_promotion_gate",
        ],
        "frozen_science_unchanged": True,
    }
