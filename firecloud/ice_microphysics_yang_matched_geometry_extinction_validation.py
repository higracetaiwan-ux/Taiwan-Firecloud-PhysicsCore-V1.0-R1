"""Ice Optics Phase 2 Step 3M — Yang/Bi matched-geometry extinction validation.

This step removes the deliberate geometry mismatch that remained in Step 3K.
The reference chain uses the *same* Yang/Bi V2 ``single_column`` geometry
(maximum dimension and random-orientation mean projected area), but it does not
use Yang/Bi C_ext/Q_ext in the reference optical law.  Instead, the independent
solar geometric-optics relation ``C_ext ≈ 2 A`` (Fu 1996 / extinction paradox)
is applied to that matched geometry.

The scope is intentionally narrow:
* extinction only;
* diagnostic / qualification only;
* no independent SSA or asymmetry-factor validation;
* no runtime habit or roughness truth inference;
* no tau_ice production;
* no Formation/Viewing/Twilight-Glow promotion.
"""
from __future__ import annotations

from typing import Any, Iterable
import math

import numpy as np
import pandas as pd

from . import __version__ as PHYSICSCORE_VERSION
from .ice_cloud_spectral_optics import (
    BUNDLED_CALIBRATED_LUT_PATH,
    ICE_OPTICS_WAVELENGTHS_NM,
)
from .ice_microphysics_wyser_primary_numeric_recovery import (
    WYSER_PSD_LMAX_UM,
    WYSER_PSD_LMIN_UM,
)
from .ice_microphysics_wyser_yang_coordinate_qualification import (
    yang_single_column_semiwidth_um,
)
from .ice_microphysics_wyser_yang_population_bridge import (
    _regular_hexagonal_column_geometry,
)
from .ice_microphysics_wyser_yang_diagnostic_bulk_integration import (
    BULK_CONVERGENCE_TOLERANCE,
    MASS_CLOSURE_TOLERANCE,
    _bulk_solution_on_grid,
)

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
STEP3M_VERSION = "R5.7.41.3.4.10.26"
STEP3M_MODE = "YANG_MATCHED_GEOMETRY_FU96_EXTINCTION_VALIDATION_DIAGNOSTIC_FAIL_CLOSED"
PHYSICS_PROMOTION_ALLOWED = False
EVIDENCE_AS_OF = "2026-09-18"

REFERENCE_HABIT = "single_column"
ROUGHNESS_STATES = ("Rough000", "Rough003", "Rough050")
FU96_PRIMARY_DOI = "https://doi.org/10.1175/1520-0442(1996)009<2058:AAPOTS>2.0.CO;2"
YANG_LIOU_1997_DOI = "https://doi.org/10.1364/JOSAA.14.002278"
BARAN_2001_DOI = "https://doi.org/10.1364/AO.40.004376"
FU96_REFERENCE_LAW = "Cext_reference_m2=2*Yang_single_column_mean_projected_area_m2"
GEOMETRIC_OPTICS_MIN_SIZE_PARAMETER = 15.0
EVIDENCE_SIGNIFICANT_DIGITS = 11
CONTRACT_SAMPLE_SIGNIFICANT_DIGITS = 8


def _stable(value: float) -> str:
    return format(float(value), f".{EVIDENCE_SIGNIFICANT_DIGITS}g")


def _stable_contract(value: float) -> str:
    return format(float(value), f".{CONTRACT_SAMPLE_SIGNIFICANT_DIGITS}g")


def _source_frame() -> pd.DataFrame:
    frame = pd.read_csv(BUNDLED_CALIBRATED_LUT_PATH)
    required = {
        "wavelength_nm",
        "maximum_dimension_um",
        "ice_habit",
        "surface_roughness",
        "mass_extinction_coefficient_m2_kg",
    }
    if not required.issubset(frame.columns):
        return pd.DataFrame()
    out = frame.loc[
        (frame["ice_habit"].astype(str) == REFERENCE_HABIT)
        & frame["surface_roughness"].astype(str).isin(ROUGHNESS_STATES)
        & pd.to_numeric(frame["maximum_dimension_um"], errors="coerce").between(
            WYSER_PSD_LMIN_UM, WYSER_PSD_LMAX_UM, inclusive="both"
        )
        & pd.to_numeric(frame["wavelength_nm"], errors="coerce").isin(ICE_OPTICS_WAVELENGTHS_NM),
        [
            "wavelength_nm",
            "maximum_dimension_um",
            "ice_habit",
            "surface_roughness",
            "mass_extinction_coefficient_m2_kg",
        ],
    ].copy()
    for col in ("wavelength_nm", "maximum_dimension_um", "mass_extinction_coefficient_m2_kg"):
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna().sort_values(
        ["surface_roughness", "maximum_dimension_um", "wavelength_nm"]
    ).reset_index(drop=True)
    return out


def _geometry_metrics(dmax_um: float, wavelength_nm: float) -> dict[str, float]:
    dmax = float(dmax_um)
    wavelength_um = float(wavelength_nm) / 1000.0
    semiwidth = float(yang_single_column_semiwidth_um(dmax))
    geom = _regular_hexagonal_column_geometry(length_um=dmax, semiwidth_um=semiwidth)
    full_width_um = 2.0 * semiwidth
    minimum_dimension_um = min(dmax, full_width_um)
    minimum_dimension_size_parameter = 2.0 * math.pi * minimum_dimension_um / wavelength_um
    return {
        **geom,
        "full_width_um": float(full_width_um),
        "minimum_dimension_um": float(minimum_dimension_um),
        "minimum_dimension_size_parameter": float(minimum_dimension_size_parameter),
    }


def _single_particle_rows() -> pd.DataFrame:
    frame = _source_frame()
    rows: list[dict[str, Any]] = []
    for source in frame.itertuples(index=False):
        wave = int(source.wavelength_nm)
        dmax = float(source.maximum_dimension_um)
        roughness = str(source.surface_roughness)
        geometry = _geometry_metrics(dmax, wave)
        area_m2 = float(geometry["mean_projected_area_um2"]) * 1.0e-12
        mass_kg = float(geometry["solid_ice_mass_kg"])
        yang_cext_m2 = float(source.mass_extinction_coefficient_m2_kg) * mass_kg
        fu96_cext_m2 = 2.0 * area_m2
        qext_yang = yang_cext_m2 / area_m2
        relative_difference = abs(yang_cext_m2 - fu96_cext_m2) / fu96_cext_m2
        rows.append({
            "ice_habit": REFERENCE_HABIT,
            "surface_roughness": roughness,
            "wavelength_nm": wave,
            "maximum_dimension_um": dmax,
            "minimum_dimension_um": float(geometry["minimum_dimension_um"]),
            "minimum_dimension_size_parameter": float(geometry["minimum_dimension_size_parameter"]),
            "mean_projected_area_m2": area_m2,
            "solid_ice_mass_kg": mass_kg,
            "yang_cext_m2": yang_cext_m2,
            "fu96_matched_geometry_cext_m2": fu96_cext_m2,
            "yang_qext": qext_yang,
            "relative_difference_vs_2A": relative_difference,
        })
    return pd.DataFrame(rows)


def matched_geometry_single_particle_extinction_reference() -> dict[str, Any]:
    rows = _single_particle_rows()
    expected_rows = 109 * len(ICE_OPTICS_WAVELENGTHS_NM) * len(ROUGHNESS_STATES)
    if rows.empty:
        return {
            "diagnostic_only": True,
            "ice_habit": REFERENCE_HABIT,
            "roughness_states": list(ROUGHNESS_STATES),
            "dmax_count": 0,
            "wavelength_count": len(ICE_OPTICS_WAVELENGTHS_NM),
            "row_count": 0,
            "coverage_complete": False,
            "uses_yang_bi_cext_in_reference_chain": False,
            "same_yang_geometry_as_test_kernel": True,
            "geometric_optics_domain_pass": False,
            "missing_reason": "YANG_SINGLE_COLUMN_LUT_ROWS_UNAVAILABLE",
        }
    by_roughness: dict[str, dict[str, float]] = {}
    for roughness in ROUGHNESS_STATES:
        sub = rows.loc[rows["surface_roughness"] == roughness]
        by_roughness[roughness] = {
            "row_count": int(len(sub)),
            "min_yang_qext": float(sub["yang_qext"].min()),
            "max_yang_qext": float(sub["yang_qext"].max()),
            "max_relative_difference_vs_2A": float(sub["relative_difference_vs_2A"].max()),
            "mean_relative_difference_vs_2A": float(sub["relative_difference_vs_2A"].mean()),
        }
    min_size_parameter = float(rows["minimum_dimension_size_parameter"].min())
    return {
        "diagnostic_only": True,
        "reference_law": FU96_REFERENCE_LAW,
        "reference_source": FU96_PRIMARY_DOI,
        "geometric_optics_domain_support": [FU96_PRIMARY_DOI, YANG_LIOU_1997_DOI],
        "ice_habit": REFERENCE_HABIT,
        "roughness_states": list(ROUGHNESS_STATES),
        "dmax_domain_um": [float(WYSER_PSD_LMIN_UM), float(WYSER_PSD_LMAX_UM)],
        "dmax_count": int(rows["maximum_dimension_um"].nunique()),
        "wavelength_count": int(rows["wavelength_nm"].nunique()),
        "row_count": int(len(rows)),
        "expected_row_count": int(expected_rows),
        "coverage_complete": bool(len(rows) == expected_rows),
        "uses_yang_bi_cext_in_reference_chain": False,
        "uses_yang_bi_projected_area_geometry": True,
        "same_yang_geometry_as_test_kernel": True,
        "minimum_size_parameter": min_size_parameter,
        "geometric_optics_minimum_size_parameter_required": GEOMETRIC_OPTICS_MIN_SIZE_PARAMETER,
        "geometric_optics_domain_pass": bool(min_size_parameter > GEOMETRIC_OPTICS_MIN_SIZE_PARAMETER),
        "min_yang_qext": float(rows["yang_qext"].min()),
        "max_yang_qext": float(rows["yang_qext"].max()),
        "max_single_particle_relative_difference_vs_2A": float(rows["relative_difference_vs_2A"].max()),
        "mean_single_particle_relative_difference_vs_2A": float(rows["relative_difference_vs_2A"].mean()),
        "roughness_summary": by_roughness,
        "independent_ssa_validation_pass": False,
        "independent_asymmetry_validation_pass": False,
        "full_like_for_like_optical_validation_pass": False,
        "tau_ice_production_allowed": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "missing_reason": "",
    }


def _kernel_sets() -> tuple[
    dict[int, tuple[np.ndarray, np.ndarray]],
    dict[str, dict[int, tuple[np.ndarray, np.ndarray]]],
]:
    frame = _source_frame()
    fu_kernel: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    yang_kernels: dict[str, dict[int, tuple[np.ndarray, np.ndarray]]] = {
        roughness: {} for roughness in ROUGHNESS_STATES
    }
    for wave in ICE_OPTICS_WAVELENGTHS_NM:
        base = frame.loc[
            (frame["surface_roughness"] == ROUGHNESS_STATES[0])
            & (frame["wavelength_nm"].astype(int) == int(wave))
        ].sort_values("maximum_dimension_um")
        dmax = base["maximum_dimension_um"].to_numpy(dtype=float)
        fu_cext: list[float] = []
        for d in dmax:
            geometry = _geometry_metrics(float(d), float(wave))
            fu_cext.append(2.0 * float(geometry["mean_projected_area_um2"]) * 1.0e-12)
        fu_kernel[int(wave)] = (dmax, np.asarray(fu_cext, dtype=float))

        for roughness in ROUGHNESS_STATES:
            band = frame.loc[
                (frame["surface_roughness"] == roughness)
                & (frame["wavelength_nm"].astype(int) == int(wave))
            ].sort_values("maximum_dimension_um")
            d = band["maximum_dimension_um"].to_numpy(dtype=float)
            k = band["mass_extinction_coefficient_m2_kg"].to_numpy(dtype=float)
            cext: list[float] = []
            for d_um, kext in zip(d, k):
                geometry = _geometry_metrics(float(d_um), float(wave))
                cext.append(float(kext) * float(geometry["solid_ice_mass_kg"]))
            yang_kernels[roughness][int(wave)] = (d, np.asarray(cext, dtype=float))
    return fu_kernel, yang_kernels


def run_matched_geometry_bulk_extinction_validation_grid(
    *,
    temperatures_k: Iterable[float] = (233.16, 253.16, 273.16),
    iwc_values_g_m3: Iterable[float] = (0.001, 0.1, 10.0),
    grid_points: Iterable[int] = (1025, 4097),
    reference_grid_points: int = 16385,
) -> dict[str, Any]:
    single_particle = matched_geometry_single_particle_extinction_reference()
    fu_kernel, yang_kernels = _kernel_sets()
    temperatures = tuple(float(v) for v in temperatures_k)
    iwcs = tuple(float(v) for v in iwc_values_g_m3)
    grids = tuple(int(v) for v in grid_points)
    if not temperatures or not iwcs or not grids:
        raise ValueError("temperatures_k, iwc_values_g_m3 and grid_points must be non-empty")
    if int(reference_grid_points) <= max(grids):
        raise ValueError("reference_grid_points must exceed all grid_points")

    comparisons: list[dict[str, Any]] = []
    numeric_passes: list[bool] = []
    convergence_errors: list[float] = []
    case_count = 0
    for temperature in temperatures:
        for iwc in iwcs:
            for points in grids:
                case_count += 1
                fu = _bulk_solution_on_grid(
                    temperature_k=temperature,
                    iwc_g_m3=iwc,
                    grid_points=points,
                    kernel_by_band=fu_kernel,
                )
                fu_ref = _bulk_solution_on_grid(
                    temperature_k=temperature,
                    iwc_g_m3=iwc,
                    grid_points=int(reference_grid_points),
                    kernel_by_band=fu_kernel,
                )
                fu_by_wave = {int(r["wavelength_nm"]): r for r in fu["bands"]}
                fu_ref_by_wave = {int(r["wavelength_nm"]): r for r in fu_ref["bands"]}
                fu_conv = max(
                    abs(float(fu_by_wave[w]["k_ext_m2_kg"]) - float(fu_ref_by_wave[w]["k_ext_m2_kg"]))
                    / float(fu_ref_by_wave[w]["k_ext_m2_kg"])
                    for w in fu_by_wave
                )
                convergence_errors.append(float(fu_conv))
                fu_numeric = bool(
                    fu["mass_closure_relative_error"] <= MASS_CLOSURE_TOLERANCE
                    and fu_conv <= BULK_CONVERGENCE_TOLERANCE
                )
                numeric_passes.append(fu_numeric)

                for roughness in ROUGHNESS_STATES:
                    yang = _bulk_solution_on_grid(
                        temperature_k=temperature,
                        iwc_g_m3=iwc,
                        grid_points=points,
                        kernel_by_band=yang_kernels[roughness],
                    )
                    yang_ref = _bulk_solution_on_grid(
                        temperature_k=temperature,
                        iwc_g_m3=iwc,
                        grid_points=int(reference_grid_points),
                        kernel_by_band=yang_kernels[roughness],
                    )
                    yang_by_wave = {int(r["wavelength_nm"]): r for r in yang["bands"]}
                    yang_ref_by_wave = {int(r["wavelength_nm"]): r for r in yang_ref["bands"]}
                    yang_conv = max(
                        abs(float(yang_by_wave[w]["k_ext_m2_kg"]) - float(yang_ref_by_wave[w]["k_ext_m2_kg"]))
                        / float(yang_ref_by_wave[w]["k_ext_m2_kg"])
                        for w in yang_by_wave
                    )
                    convergence_errors.append(float(yang_conv))
                    yang_numeric = bool(
                        yang["mass_closure_relative_error"] <= MASS_CLOSURE_TOLERANCE
                        and yang_conv <= BULK_CONVERGENCE_TOLERANCE
                    )
                    numeric_passes.append(yang_numeric)
                    for wave in ICE_OPTICS_WAVELENGTHS_NM:
                        fu_k = float(fu_by_wave[int(wave)]["k_ext_m2_kg"])
                        yang_k = float(yang_by_wave[int(wave)]["k_ext_m2_kg"])
                        comparisons.append({
                            "temperature_k": temperature,
                            "iwc_g_m3": iwc,
                            "grid_points": points,
                            "surface_roughness": roughness,
                            "wavelength_nm": int(wave),
                            "yang_k_ext_m2_kg": yang_k,
                            "fu96_matched_geometry_k_ext_m2_kg": fu_k,
                            "relative_difference_vs_matched_fu96": abs(yang_k - fu_k) / fu_k,
                        })

    differences = [float(r["relative_difference_vs_matched_fu96"]) for r in comparisons]
    return {
        "diagnostic_only": True,
        "reference_law": FU96_REFERENCE_LAW,
        "reference_source": FU96_PRIMARY_DOI,
        "same_yang_geometry_as_test_kernel": True,
        "uses_yang_bi_cext_in_reference_chain": False,
        "temperatures_k": list(temperatures),
        "iwc_values_g_m3": list(iwcs),
        "grid_points": list(grids),
        "reference_grid_points": int(reference_grid_points),
        "case_count": int(case_count),
        "comparison_row_count": int(len(comparisons)),
        "roughness_states": list(ROUGHNESS_STATES),
        "all_geometric_optics_domain_pass": bool(single_particle.get("geometric_optics_domain_pass", False)),
        "all_reference_chains_numeric_pass": bool(numeric_passes and all(numeric_passes)),
        "max_grid_convergence_relative_error": float(max(convergence_errors)) if convergence_errors else float("nan"),
        "min_bulk_relative_difference_vs_matched_fu96": float(min(differences)) if differences else float("nan"),
        "max_bulk_relative_difference_vs_matched_fu96": float(max(differences)) if differences else float("nan"),
        "mean_bulk_relative_difference_vs_matched_fu96": float(np.mean(differences)) if differences else float("nan"),
        "matched_geometry_extinction_reference_ready": bool(
            single_particle.get("coverage_complete", False)
            and single_particle.get("geometric_optics_domain_pass", False)
            and numeric_passes
            and all(numeric_passes)
        ),
        "matched_geometry_bulk_difference_characterized": bool(differences),
        "independent_ssa_validation_pass": False,
        "independent_asymmetry_validation_pass": False,
        "full_like_for_like_optical_validation_pass": False,
        "scientific_bulk_validation_pass": False,
        "bulk_yang_bi_psd_integration_eligible": False,
        "tau_ice_production_allowed": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "comparisons": comparisons,
    }


EVIDENCE_COLUMNS = [
    "step3m_version", "science_baseline", "step3m_mode", "evidence_id",
    "evidence_type", "pin_status", "value", "semantic_role",
    "authoritative_for_runtime_mapping", "source_reference", "source_path",
    "source_sha", "notes",
]


def build_yang_matched_geometry_extinction_validation_evidence() -> pd.DataFrame:
    particle = matched_geometry_single_particle_extinction_reference()
    bulk = run_matched_geometry_bulk_extinction_validation_grid()
    rows = [
        ("FU96_GEOMETRIC_OPTICS_PROVENANCE", "PRIMARY_LITERATURE_PROVENANCE", "PINNED", FU96_REFERENCE_LAW, "INDEPENDENT_EXTINCTION_REFERENCE_LAW", False, FU96_PRIMARY_DOI, "Fu (1996) solar cirrus geometric-optics framework", "", "Reference law only; not a production scheme replacement."),
        ("GEOMETRIC_OPTICS_SIZE_DOMAIN", "DOMAIN_QUALIFICATION", "PASS" if particle["geometric_optics_domain_pass"] else "BLOCKED", f"min_size_parameter={_stable(particle['minimum_size_parameter'])};required>{GEOMETRIC_OPTICS_MIN_SIZE_PARAMETER:g}", "MATCHED_SINGLE_COLUMN_DOMAIN", False, f"{FU96_PRIMARY_DOI}|{YANG_LIOU_1997_DOI}", "Yang single-column minimum-dimension size parameter", "", "All 10-1000 µm / six-band source rows are tested against the geometric-optics applicability floor."),
        ("MATCHED_YANG_GEOMETRY_REFERENCE", "LIKE_FOR_LIKE_GEOMETRY_GUARD", "PASS", "true", "SAME_DMAX_AND_PROJECTED_AREA_GEOMETRY", False, "R5.7.41.3.4.10.21 Step 3H", "Yang single-column source geometry", "", "Unlike Step 3K, the Fu reference now uses the same Yang/Bi single-column geometry as the tested optical kernel."),
        ("REFERENCE_CHAIN_CEXT_INDEPENDENCE", "INDEPENDENT_OPTICAL_CHAIN_GUARD", "PASS", "false", "USES_YANG_BI_CEXT_IN_REFERENCE_CHAIN", False, FU96_PRIMARY_DOI, "Cext_reference=2A_yang", "", "The geometry is matched deliberately; Yang/Bi Cext/Qext is not used to construct the reference optical law."),
        ("SINGLE_PARTICLE_EXTINCTION_DIFFERENCE", "NUMERIC_CHARACTERIZATION", "PASS_CHARACTERIZED", f"rows={particle['row_count']};max_rel={_stable(particle['max_single_particle_relative_difference_vs_2A'])};mean_rel={_stable(particle['mean_single_particle_relative_difference_vs_2A'])}", "QEXT_VS_EXTINCTION_PARADOX", False, f"{FU96_PRIMARY_DOI}|{YANG_LIOU_1997_DOI}", "Step 3M source-row comparison", "", "Characterization only; no arbitrary single-particle production tolerance is introduced."),
        ("MATCHED_GEOMETRY_BULK_DIFFERENCE", "BULK_NUMERIC_CHARACTERIZATION", "PASS_CHARACTERIZED", f"cases={bulk['case_count']};rows={bulk['comparison_row_count']};min_rel={_stable(bulk['min_bulk_relative_difference_vs_matched_fu96'])};max_rel={_stable(bulk['max_bulk_relative_difference_vs_matched_fu96'])}", "WYser_POPULATION_SAME_GEOMETRY_EXTINCTION_CROSSCHECK", False, f"{FU96_PRIMARY_DOI}|R5.7.41.3.4.10.23 Step 3J", "Step 3M matched-geometry bulk matrix", "", "The cross-geometry 26-31% Step 3K difference is not reused as a like-for-like validation metric."),
        ("MATCHED_GEOMETRY_EXTINCTION_REFERENCE_READY", "EXTINCTION_REFERENCE_GATE", "PASS" if bulk["matched_geometry_extinction_reference_ready"] else "BLOCKED", str(bool(bulk["matched_geometry_extinction_reference_ready"])).lower(), "EXTINCTION_ONLY_REFERENCE_READY", False, f"{FU96_PRIMARY_DOI}|{YANG_LIOU_1997_DOI}", "Step 3M qualification", "", "This advances the extinction reference only; it does not certify full optical properties."),
        ("INDEPENDENT_SSA_VALIDATION", "FULL_OPTICS_BLOCKER", "BLOCKED_NOT_EXECUTED", "false", "SSA_VALIDATION_PENDING", False, BARAN_2001_DOI, "Step 3M scope guard", "", "Step 3M does not claim an independent single-scattering-albedo validation chain."),
        ("INDEPENDENT_ASYMMETRY_VALIDATION", "FULL_OPTICS_BLOCKER", "BLOCKED_NOT_EXECUTED", "false", "ASYMMETRY_VALIDATION_PENDING", False, BARAN_2001_DOI, "Step 3M scope guard", "", "Visible-wavelength asymmetry is habit/shape sensitive and remains independently unvalidated."),
        ("FULL_LIKE_FOR_LIKE_OPTICAL_VALIDATION", "FULL_OPTICS_GATE", "BLOCKED", "false", "EXTINCTION_ONLY_NOT_FULL_OPTICS", False, "Step 3M policy", "Step 3M fail-close", "", "SSA/g are still blocked, so full like-for-like optical validation is not passed."),
        ("TAU_ICE_PRODUCTION_PROMOTION", "PROMOTION_GATE", "BLOCKED", "false", "NO_TAU_ICE_PRODUCTION", False, "Frozen PhysicsCore policy", "Step 3M fail-close", "", "Matched-geometry extinction validation does not write diagnostic optics into production tau."),
        ("STEP3M_PRODUCTION_PROMOTION", "PROMOTION_GATE", "BLOCKED", "false", "NO_PRODUCTION_ICE_OPTICS_PROMOTION", False, "Frozen PhysicsCore policy", "Step 3M fail-close", "", "Formation/Viewing/Twilight Glow and production ice optics remain unchanged."),
    ]
    return pd.DataFrame([
        dict(zip(EVIDENCE_COLUMNS, (STEP3M_VERSION, SCIENCE_BASELINE, STEP3M_MODE, *row)))
        for row in rows
    ], columns=EVIDENCE_COLUMNS)


def build_yang_matched_geometry_extinction_validation_gate(evidence: pd.DataFrame | None = None) -> pd.DataFrame:
    ev = evidence if evidence is not None else build_yang_matched_geometry_extinction_validation_evidence()
    particle = matched_geometry_single_particle_extinction_reference()
    bulk = run_matched_geometry_bulk_extinction_validation_grid()
    ready = bool(bulk["matched_geometry_extinction_reference_ready"])
    blockers = [
        "INDEPENDENT_SSA_VALIDATION_PENDING",
        "INDEPENDENT_ASYMMETRY_VALIDATION_PENDING",
        "FULL_LIKE_FOR_LIKE_OPTICAL_VALIDATION_PENDING",
        "SCIENTIFIC_BULK_VALIDATION_PENDING",
        "GFS_RUNTIME_HABIT_ROUGHNESS_TRUTH_UNAVAILABLE",
    ]
    row = {
        "step3m_version": STEP3M_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "step3m_mode": STEP3M_MODE,
        "matched_geometry_extinction_reference_ready": ready,
        "geometric_optics_domain_pass": bool(particle["geometric_optics_domain_pass"]),
        "matched_geometry_bulk_difference_characterized": bool(bulk["matched_geometry_bulk_difference_characterized"]),
        "independent_ssa_validation_pass": False,
        "independent_asymmetry_validation_pass": False,
        "full_like_for_like_optical_validation_pass": False,
        "scientific_bulk_validation_pass": False,
        "bulk_yang_bi_psd_integration_eligible": False,
        "tau_ice_production_allowed": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "MATCHED_GEOMETRY_EXTINCTION_REFERENCE_READY": ready,
        "GEOMETRIC_OPTICS_DOMAIN_PASS": bool(particle["geometric_optics_domain_pass"]),
        "MATCHED_GEOMETRY_BULK_DIFFERENCE_CHARACTERIZED": bool(bulk["matched_geometry_bulk_difference_characterized"]),
        "INDEPENDENT_SSA_VALIDATION_PASS": False,
        "INDEPENDENT_ASYMMETRY_VALIDATION_PASS": False,
        "FULL_LIKE_FOR_LIKE_OPTICAL_VALIDATION_PASS": False,
        "SCIENTIFIC_BULK_VALIDATION_PASS": False,
        "TAU_ICE_PRODUCTION_ALLOWED": False,
        "PRODUCTION_ICE_OPTICS_READY": False,
        "qualification_state": "MATCHED_GEOMETRY_EXTINCTION_REFERENCE_READY_FULL_OPTICS_AND_PRODUCTION_BLOCKED" if ready else "MATCHED_GEOMETRY_EXTINCTION_REFERENCE_BLOCKED",
        "qualification_blockers": "|".join(blockers),
        "evidence_row_count": int(len(ev)),
        "max_single_particle_relative_difference_vs_2A": _stable(particle["max_single_particle_relative_difference_vs_2A"]),
        "max_bulk_relative_difference_vs_matched_fu96": _stable(bulk["max_bulk_relative_difference_vs_matched_fu96"]),
        "detail": "Same-geometry Fu96 extinction reference is executable and characterized, but SSA/g/full-optics validation, runtime microphysics truth, tau and production promotion remain blocked.",
    }
    return pd.DataFrame([row])


def yang_matched_geometry_extinction_validation_contract_payload(*, physicscore_version: str | None = None) -> dict[str, Any]:
    particle = matched_geometry_single_particle_extinction_reference()
    bulk = run_matched_geometry_bulk_extinction_validation_grid()
    return {
        "contract_version": "FIRECLOUD_ICE_YANG_MATCHED_GEOMETRY_EXTINCTION_VALIDATION_V1",
        "physicscore_version": physicscore_version or PHYSICSCORE_VERSION,
        "step3m_version": STEP3M_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "mode": STEP3M_MODE,
        "reference_law": FU96_REFERENCE_LAW,
        "reference_source": FU96_PRIMARY_DOI,
        "geometric_optics_domain_support": [FU96_PRIMARY_DOI, YANG_LIOU_1997_DOI],
        "reference_habit_family": REFERENCE_HABIT,
        "roughness_states": list(ROUGHNESS_STATES),
        "dmax_domain_um": [float(WYSER_PSD_LMIN_UM), float(WYSER_PSD_LMAX_UM)],
        "wavelengths_nm": [int(v) for v in ICE_OPTICS_WAVELENGTHS_NM],
        "same_yang_geometry_as_test_kernel": True,
        "uses_yang_bi_cext_in_reference_chain": False,
        "minimum_size_parameter": _stable_contract(particle["minimum_size_parameter"]),
        "geometric_optics_domain_pass": bool(particle["geometric_optics_domain_pass"]),
        "single_particle_row_count": int(particle["row_count"]),
        "matched_geometry_extinction_reference_ready": bool(bulk["matched_geometry_extinction_reference_ready"]),
        "matched_geometry_bulk_difference_characterized": bool(bulk["matched_geometry_bulk_difference_characterized"]),
        "sample_numeric_characterization": {
            "max_single_particle_relative_difference_vs_2A": _stable_contract(particle["max_single_particle_relative_difference_vs_2A"]),
            "mean_single_particle_relative_difference_vs_2A": _stable_contract(particle["mean_single_particle_relative_difference_vs_2A"]),
            "max_bulk_relative_difference_vs_matched_fu96": _stable_contract(bulk["max_bulk_relative_difference_vs_matched_fu96"]),
            "mean_bulk_relative_difference_vs_matched_fu96": _stable_contract(bulk["mean_bulk_relative_difference_vs_matched_fu96"]),
            "max_grid_convergence_relative_error": _stable_contract(bulk["max_grid_convergence_relative_error"]),
        },
        "independent_ssa_validation_pass": False,
        "independent_asymmetry_validation_pass": False,
        "full_like_for_like_optical_validation_pass": False,
        "scientific_bulk_validation_pass": False,
        "bulk_yang_bi_psd_integration_eligible": False,
        "tau_ice_production_allowed": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "forbidden_shortcuts": [
            "Do not treat an extinction-only matched-geometry cross-check as SSA/g validation.",
            "Do not infer runtime habit from the single_column model-family reference.",
            "Do not select a hidden production roughness state from the diagnostic ensemble.",
            "Do not treat the Step 3M regression characterization as a universal production tolerance.",
            "Do not promote diagnostic k_ext to tau_ice production in Step 3M.",
            "Do not alter Formation/Viewing/Twilight Glow from Step 3M evidence.",
        ],
    }
