"""Diagnostic RRTMG Band-25 forward-reproduction harness (Step 3Q.20).

This module is provenance/diagnostic tooling only.  It regenerates the recovered
Fu96 first-primary-band broadband control at the 46 Dge nodes used by the pinned
archived RRTMG Band-25 table and quantifies the residual topology.

It deliberately does *not* invent the unrecovered historical fine spectral grid,
interpolation realization, source-wavelength optical samples, or discrete solar
weights.  Therefore it cannot promote exact RRTMG Band-25 reproduction and cannot
unlock production ice optics.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .fu96_primary_band_forward_model import evaluate_fu96_primary_solar_band

BAND25_WAVENUMBER_MIN_CM1 = 16000.0
BAND25_WAVENUMBER_MAX_CM1 = 22650.0
# Wavelength interval is reciprocal of wavenumber and therefore reverses order.
BAND25_WAVELENGTH_MIN_UM = 1.0e4 / BAND25_WAVENUMBER_MAX_CM1
BAND25_WAVELENGTH_MAX_UM = 1.0e4 / BAND25_WAVENUMBER_MIN_CM1
BAND25_FU96_PRIMARY_BAND_INDEX = 1
EXPECTED_REFERENCE_NODE_COUNT = 46
EXPECTED_DGE_MIN_UM = 5.0
EXPECTED_DGE_MAX_UM = 140.0
EXPECTED_DGE_STEP_UM = 3.0
PRODUCTION_PROMOTION_ALLOWED = False
EXACT_REPRODUCTION_ALLOWED = False

REFERENCE_CSV = Path(__file__).resolve().parent / "data" / "ice_optics" / "fu96_rrtmg_visible_band24_25_reference_v1.csv"
REFERENCE_SOURCE_SHA = "0ccf597d6aa3d6ed40ec592560e3ed94b653ef32"


@dataclass(frozen=True)
class Band25ResidualSummary:
    reference_node_count: int
    dge_min_um: float
    dge_max_um: float
    dge_step_um: float
    band_wavenumber_min_cm1: float
    band_wavenumber_max_cm1: float
    band_wavelength_min_um: float
    band_wavelength_max_um: float
    fu96_primary_band_index: int
    extinction_rmse: float
    extinction_relative_rmse_over_mean: float
    ssa_rmse: float
    ssa_relative_rmse_over_mean: float
    asymmetry_rmse: float
    asymmetry_relative_rmse_over_mean: float
    extinction_residual_monotonic_nonincreasing: bool
    extinction_residual_zero_crossing_count: int
    extinction_first_zero_crossing_bracket_um: tuple[float, float] | None
    ssa_residual_all_negative: bool
    asymmetry_residual_all_negative: bool
    fine_spectral_grid_realization_recovered: bool
    exact_historical_solar_weights_recovered: bool
    preaveraging_spectral_samples_recovered: bool
    exact_band25_reproduction_pass: bool
    production_promotion_allowed: bool


def _load_reference_band25() -> pd.DataFrame:
    frame = pd.read_csv(REFERENCE_CSV)
    required = {
        "rrtmg_band",
        "dge_um",
        "single_scattering_albedo",
        "asymmetry_parameter",
        "extinction_coefficient_per_iwc",
        "source_sha",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Band25 reference CSV missing columns: {missing}")
    out = frame.loc[frame["rrtmg_band"].eq(25)].copy().sort_values("dge_um").reset_index(drop=True)
    if len(out) != EXPECTED_REFERENCE_NODE_COUNT:
        raise ValueError(f"Expected {EXPECTED_REFERENCE_NODE_COUNT} Band25 nodes, found {len(out)}")
    dge = out["dge_um"].to_numpy(dtype=float)
    expected = np.arange(EXPECTED_DGE_MIN_UM, EXPECTED_DGE_MAX_UM + 0.5 * EXPECTED_DGE_STEP_UM, EXPECTED_DGE_STEP_UM)
    if len(expected) != EXPECTED_REFERENCE_NODE_COUNT or not np.array_equal(dge, expected):
        raise ValueError("Band25 Dge grid is not the pinned 5..140 um / 3 um / 46-node grid")
    shas = set(out["source_sha"].astype(str))
    if shas != {REFERENCE_SOURCE_SHA}:
        raise ValueError(f"Band25 reference source SHA mismatch: {sorted(shas)}")
    return out


def build_band25_direct_primary_control_residuals() -> pd.DataFrame:
    """Build 46-node residuals for the recovered Fu primary-band direct-copy control.

    This is a *negative control*: exact agreement is not expected and must not be
    interpreted as a historical generator.  The purpose is to provide a stable,
    executable baseline for future forward-reconstruction candidates.
    """
    ref = _load_reference_band25()
    rows: list[dict[str, Any]] = []
    for r in ref.itertuples(index=False):
        v = evaluate_fu96_primary_solar_band(BAND25_FU96_PRIMARY_BAND_INDEX, float(r.dge_um))
        row = {
            "rrtmg_band": 25,
            "dge_um": float(r.dge_um),
            "reference_extinction_per_iwc": float(r.extinction_coefficient_per_iwc),
            "control_extinction_per_iwc": float(v.mass_extinction_m2_g),
            "extinction_residual": float(v.mass_extinction_m2_g - r.extinction_coefficient_per_iwc),
            "reference_ssa": float(r.single_scattering_albedo),
            "control_ssa": float(v.single_scattering_albedo),
            "ssa_residual": float(v.single_scattering_albedo - r.single_scattering_albedo),
            "reference_asymmetry": float(r.asymmetry_parameter),
            "control_asymmetry": float(v.asymmetry_factor),
            "asymmetry_residual": float(v.asymmetry_factor - r.asymmetry_parameter),
            "reference_source_sha": str(r.source_sha),
            "control_source": "FU96_PRIMARY_BAND_1_EQ3P9_RECOVERED_BROADBAND_CONTROL",
            "exact_reproduction_claim_allowed": False,
            "physics_promotion_allowed": False,
        }
        rows.append(row)
    return pd.DataFrame(rows)


def _rmse(a: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(a))))


def summarize_band25_direct_primary_control() -> Band25ResidualSummary:
    residuals = build_band25_direct_primary_control_residuals()
    ext_r = residuals["extinction_residual"].to_numpy(dtype=float)
    ssa_r = residuals["ssa_residual"].to_numpy(dtype=float)
    asy_r = residuals["asymmetry_residual"].to_numpy(dtype=float)
    ext_ref = residuals["reference_extinction_per_iwc"].to_numpy(dtype=float)
    ssa_ref = residuals["reference_ssa"].to_numpy(dtype=float)
    asy_ref = residuals["reference_asymmetry"].to_numpy(dtype=float)
    dge = residuals["dge_um"].to_numpy(dtype=float)

    crossings: list[tuple[float, float]] = []
    for i in range(len(ext_r) - 1):
        if ext_r[i] == 0.0:
            crossings.append((float(dge[i]), float(dge[i])))
        elif ext_r[i] * ext_r[i + 1] < 0.0:
            crossings.append((float(dge[i]), float(dge[i + 1])))

    return Band25ResidualSummary(
        reference_node_count=len(residuals),
        dge_min_um=float(dge.min()),
        dge_max_um=float(dge.max()),
        dge_step_um=float(np.diff(dge)[0]),
        band_wavenumber_min_cm1=BAND25_WAVENUMBER_MIN_CM1,
        band_wavenumber_max_cm1=BAND25_WAVENUMBER_MAX_CM1,
        band_wavelength_min_um=BAND25_WAVELENGTH_MIN_UM,
        band_wavelength_max_um=BAND25_WAVELENGTH_MAX_UM,
        fu96_primary_band_index=BAND25_FU96_PRIMARY_BAND_INDEX,
        extinction_rmse=_rmse(ext_r),
        extinction_relative_rmse_over_mean=float(_rmse(ext_r) / np.mean(ext_ref)),
        ssa_rmse=_rmse(ssa_r),
        ssa_relative_rmse_over_mean=float(_rmse(ssa_r) / np.mean(ssa_ref)),
        asymmetry_rmse=_rmse(asy_r),
        asymmetry_relative_rmse_over_mean=float(_rmse(asy_r) / np.mean(asy_ref)),
        extinction_residual_monotonic_nonincreasing=bool(np.all(np.diff(ext_r) <= 0.0)),
        extinction_residual_zero_crossing_count=len(crossings),
        extinction_first_zero_crossing_bracket_um=crossings[0] if crossings else None,
        ssa_residual_all_negative=bool(np.all(ssa_r < 0.0)),
        asymmetry_residual_all_negative=bool(np.all(asy_r < 0.0)),
        fine_spectral_grid_realization_recovered=False,
        exact_historical_solar_weights_recovered=False,
        preaveraging_spectral_samples_recovered=False,
        exact_band25_reproduction_pass=False,
        production_promotion_allowed=False,
    )


def band25_reproduction_prerequisite_matrix() -> dict[str, bool]:
    """Return the exact-reproduction prerequisites with strict fail-close semantics."""
    summary = summarize_band25_direct_primary_control()
    return {
        "RRTMG_BAND25_PINNED_REFERENCE_GRID_46_NODES": summary.reference_node_count == EXPECTED_REFERENCE_NODE_COUNT,
        "RRTMG_BAND25_FORWARD_REPRODUCTION_HARNESS_READY": True,
        "RRTMG_BAND25_DIRECT_PRIMARY_CONTROL_RESIDUAL_TOPOLOGY_QUALIFIED": (
            summary.extinction_residual_monotonic_nonincreasing
            and summary.extinction_residual_zero_crossing_count == 1
            and summary.ssa_residual_all_negative
            and summary.asymmetry_residual_all_negative
        ),
        "RRTMG_BAND25_FINE_SPECTRAL_GRID_REALIZATION_RECOVERED": False,
        "RRTMG_BAND25_PREAVERAGING_SPECTRAL_SAMPLES_RECOVERED": False,
        "RRTMG_BAND25_EXACT_HISTORICAL_SOLAR_WEIGHTS_RECOVERED": False,
        "RRTMG_BAND25_EXACT_REPRODUCTION_PASS": False,
        "TAU_ICE_PRODUCTION_ALLOWED": False,
        "PRODUCTION_ICE_OPTICS_READY": False,
        "physics_promotion_allowed": False,
    }


def band25_reproduction_diagnostic_payload() -> dict[str, Any]:
    summary = summarize_band25_direct_primary_control()
    return {
        "schema": "twfc.fu96-rrtmg-band25-reproduction-diagnostic.v1",
        "mode": "DIAGNOSTIC_ONLY_FAIL_CLOSED",
        "reference_csv": str(REFERENCE_CSV.relative_to(Path(__file__).resolve().parents[1])),
        "reference_source_sha": REFERENCE_SOURCE_SHA,
        "summary": asdict(summary),
        "prerequisites": band25_reproduction_prerequisite_matrix(),
        "missing_exact_historical_inputs": [
            "fine_spectral_grid_nodes",
            "fine_grid_interpolation_realization",
            "preaveraging_source_wavelength_optical_samples",
            "exact_historical_solar_spectrum_identity",
            "exact_discrete_solar_weight_vector",
        ],
        "forbidden_substitutes": [
            "direct_fu_primary_broadband_copy_as_exact_rrtmg_band25",
            "runtime_rrtmg_gpoint_solar_weights_as_unproven_cloud_table_generator_weights",
            "inverse_fit_archived_final_band25_table_to_claim_historical_generator",
            "synthetic_or_assumed_fine_grid",
        ],
        "production_promotion_allowed": False,
    }
