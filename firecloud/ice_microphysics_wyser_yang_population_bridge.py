"""Ice Optics Phase 2 Step 3I — Wyser↔Yang/Bi population bridge.

Step 3I qualifies a narrow *diagnostic* hybrid bridge on the already-qualified
maximum-dimension coordinate:

* Wyser Eq.(6) particle mass is the population-mass semantic used for PSD/IWC
  normalization.
* Yang/Bi V2 geometric mass (rho_ice * V) is the optical-kernel mass semantic
  used only to invert the portable LUT mass-extinction coefficient back to a
  single-particle extinction cross section, C_ext = k_ext * m_yang.

Those masses are intentionally not interchangeable.  Likewise, a shared Dmax
coordinate is not shape, projected-area, volume, habit, roughness, or optical
equivalence.  This module therefore permits diagnostic numerical execution of
the bridge while keeping all scientific/production promotion gates closed.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
import math

import pandas as pd

from .ice_cloud_spectral_optics import (
    BUNDLED_CALIBRATED_LUT_PATH,
    ICE_DENSITY_KG_M3,
    ICE_OPTICS_WAVELENGTHS_NM,
)
from .ice_microphysics_wyser_primary_numeric_recovery import (
    WYSER_PSD_LMAX_UM,
    WYSER_PSD_LMIN_UM,
    wyser_eq5_width_um,
    wyser_eq6_mass_g,
)
from .ice_microphysics_wyser_yang_coordinate_qualification import (
    coordinate_qualification_diagnostic,
    yang_single_column_semiwidth_um,
)

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
STEP3I_VERSION = "R5.7.41.3.4.10.22"
STEP3I_MODE = "WYSER_POPULATION_YANG_OPTICAL_KERNEL_BRIDGE_DIAGNOSTIC_ONLY_FAIL_CLOSED"
PHYSICS_PROMOTION_ALLOWED = False
EVIDENCE_AS_OF = "2026-09-17"

POPULATION_MASS_SEMANTIC = "WYSER_EQ6_EMPIRICAL_PARTICLE_MASS"
OPTICAL_KERNEL_MASS_SEMANTIC = "YANG_GEOMETRIC_RHO_ICE_TIMES_VOLUME"
DIAGNOSTIC_REFERENCE_HABIT = "single_column"
DIAGNOSTIC_REFERENCE_ROUGHNESS = "Rough000"
_BUNDLED_LUT_RELATIVE_PATH = "firecloud/data/ice_optics/portable_ice_optics_lut_v1.csv"


def _positive_finite(value: float, *, name: str) -> float:
    out = float(value)
    if not math.isfinite(out) or out <= 0.0:
        raise ValueError(f"{name} must be positive and finite")
    return out


def _regular_hexagonal_column_geometry(*, length_um: float, semiwidth_um: float) -> dict[str, float]:
    """Return volume, random-orientation mean projected area and solid-ice mass.

    The hexagonal semiwidth is the regular-hexagon side-length coordinate used
    by the pinned Yang single-column geometry.  The random-orientation mean
    projected area follows Cauchy's convex-body result, Abar = surface_area/4.
    """
    length = _positive_finite(length_um, name="length_um")
    a = _positive_finite(semiwidth_um, name="semiwidth_um")
    volume_um3 = (3.0 * math.sqrt(3.0) / 2.0) * a * a * length
    projected_area_um2 = (3.0 * math.sqrt(3.0) * a * a + 6.0 * a * length) / 4.0
    mass_kg = ICE_DENSITY_KG_M3 * volume_um3 * 1.0e-18
    effective_diameter_um = 1.5 * volume_um3 / projected_area_um2
    return {
        "volume_um3": float(volume_um3),
        "mean_projected_area_um2": float(projected_area_um2),
        "solid_ice_mass_kg": float(mass_kg),
        "effective_diameter_um": float(effective_diameter_um),
    }


def wyser_yang_geometry_mass_comparison(
    *,
    lengths_um: Iterable[float] = (10.0, 30.0, 100.0, 1000.0),
) -> dict[str, Any]:
    """Quantify geometry/mass differences at the shared maximum-dimension axis.

    This function does not create a correction factor.  Ratios are evidence
    that the two source lineages must keep distinct geometry/mass semantics.
    """
    lengths = [float(v) for v in lengths_um]
    if not lengths:
        raise ValueError("lengths_um must be non-empty")
    if any((not math.isfinite(v) or v <= 0.0) for v in lengths):
        raise ValueError("lengths_um values must be positive and finite")

    rows: list[dict[str, float]] = []
    for length in lengths:
        wyser_width = float(wyser_eq5_width_um(length))
        yang_a = float(yang_single_column_semiwidth_um(length))
        yang_width = 2.0 * yang_a

        # Step 3H already interprets Wyser D as the full basal width for the
        # geometry comparison only; this does not turn Eq.(5) into Eq.(6).
        wyser_geom = _regular_hexagonal_column_geometry(
            length_um=length,
            semiwidth_um=wyser_width / 2.0,
        )
        yang_geom = _regular_hexagonal_column_geometry(
            length_um=length,
            semiwidth_um=yang_a,
        )
        wyser_eq6_mass_kg = float(wyser_eq6_mass_g(length) * 1.0e-3)

        area_rel = abs(
            yang_geom["mean_projected_area_um2"] - wyser_geom["mean_projected_area_um2"]
        ) / max(yang_geom["mean_projected_area_um2"], wyser_geom["mean_projected_area_um2"])
        volume_rel = abs(yang_geom["volume_um3"] - wyser_geom["volume_um3"]) / max(
            yang_geom["volume_um3"], wyser_geom["volume_um3"]
        )
        yang_vs_eq6 = abs(yang_geom["solid_ice_mass_kg"] - wyser_eq6_mass_kg) / wyser_eq6_mass_kg
        wyser_geom_vs_eq6 = abs(wyser_geom["solid_ice_mass_kg"] - wyser_eq6_mass_kg) / wyser_eq6_mass_kg

        rows.append({
            "maximum_dimension_um": float(length),
            "wyser_eq5_full_width_um": wyser_width,
            "yang_v2_full_width_um": yang_width,
            "wyser_mean_projected_area_um2": wyser_geom["mean_projected_area_um2"],
            "yang_mean_projected_area_um2": yang_geom["mean_projected_area_um2"],
            "wyser_geometric_volume_um3": wyser_geom["volume_um3"],
            "yang_geometric_volume_um3": yang_geom["volume_um3"],
            "wyser_eq6_population_mass_kg": wyser_eq6_mass_kg,
            "wyser_geometric_solid_mass_kg": wyser_geom["solid_ice_mass_kg"],
            "yang_geometric_solid_mass_kg": yang_geom["solid_ice_mass_kg"],
            "relative_projected_area_difference": float(area_rel),
            "relative_volume_difference": float(volume_rel),
            "relative_yang_mass_vs_wyser_eq6_difference": float(yang_vs_eq6),
            "relative_wyser_geometric_mass_vs_eq6_difference": float(wyser_geom_vs_eq6),
        })

    # Source laws are distinct.  Numerical closeness at an isolated size is
    # never promoted to equivalence; all samples would have to reproduce the
    # same quantity within the tight source-reproduction tolerance.
    shape_equal = all(
        math.isclose(r["wyser_eq5_full_width_um"], r["yang_v2_full_width_um"], rel_tol=1e-6, abs_tol=1e-12)
        for r in rows
    )
    area_equal = all(r["relative_projected_area_difference"] <= 1e-6 for r in rows)
    volume_equal = all(r["relative_volume_difference"] <= 1e-6 for r in rows)
    mass_equal = all(r["relative_yang_mass_vs_wyser_eq6_difference"] <= 1e-6 for r in rows)

    return {
        "diagnostic_only": True,
        "shared_coordinate": "maximum_dimension_um",
        "tested_lengths_um": lengths,
        "wyser_population_mass_semantic": POPULATION_MASS_SEMANTIC,
        "yang_optical_kernel_mass_semantic": OPTICAL_KERNEL_MASS_SEMANTIC,
        "mass_semantics_interchangeable": False,
        "shape_equivalence_pass": bool(shape_equal),
        "projected_area_equivalence_pass": bool(area_equal),
        "volume_mass_equivalence_pass": bool(volume_equal and mass_equal),
        "max_relative_projected_area_difference": float(max(r["relative_projected_area_difference"] for r in rows)),
        "max_relative_volume_difference": float(max(r["relative_volume_difference"] for r in rows)),
        "max_relative_yang_mass_vs_wyser_eq6_difference": float(max(r["relative_yang_mass_vs_wyser_eq6_difference"] for r in rows)),
        "max_relative_wyser_geometric_mass_vs_eq6_difference": float(max(r["relative_wyser_geometric_mass_vs_eq6_difference"] for r in rows)),
        "rows": rows,
    }


def _kernel_source_frame(lut_path: str | Path | None = None) -> tuple[pd.DataFrame, str]:
    path = Path(lut_path) if lut_path is not None else BUNDLED_CALIBRATED_LUT_PATH
    source_path = str(path) if lut_path is not None else _BUNDLED_LUT_RELATIVE_PATH
    if not path.exists():
        return pd.DataFrame(), source_path
    frame = pd.read_csv(path)
    required = {
        "wavelength_nm",
        "maximum_dimension_um",
        "effective_diameter_um",
        "ice_habit",
        "surface_roughness",
        "mass_extinction_coefficient_m2_kg",
    }
    if not required.issubset(frame.columns):
        return pd.DataFrame(), source_path
    subset = frame.loc[
        (frame["ice_habit"].astype(str) == DIAGNOSTIC_REFERENCE_HABIT)
        & (frame["surface_roughness"].astype(str) == DIAGNOSTIC_REFERENCE_ROUGHNESS),
        list(required),
    ].copy()
    for col in ("wavelength_nm", "maximum_dimension_um", "effective_diameter_um", "mass_extinction_coefficient_m2_kg"):
        subset[col] = pd.to_numeric(subset[col], errors="coerce")
    subset = subset.dropna()
    subset = subset.loc[
        subset["maximum_dimension_um"].between(WYSER_PSD_LMIN_UM, WYSER_PSD_LMAX_UM, inclusive="both")
        & subset["wavelength_nm"].isin(ICE_OPTICS_WAVELENGTHS_NM)
    ].copy()
    subset = subset.sort_values(["maximum_dimension_um", "wavelength_nm"]).reset_index(drop=True)
    return subset, source_path


def reconstruct_yang_single_column_optical_kernel(
    lut_path: str | Path | None = None,
) -> dict[str, Any]:
    """Reconstruct single-particle Yang C_ext from the compact mass-extinction LUT.

    `Rough000` is a diagnostic reference kernel only.  It is not promoted as a
    runtime roughness default, and the function does not alter the ice runtime.
    """
    frame, source_path = _kernel_source_frame(lut_path)
    if frame.empty:
        return {
            "diagnostic_only": True,
            "ice_habit": DIAGNOSTIC_REFERENCE_HABIT,
            "surface_roughness": DIAGNOSTIC_REFERENCE_ROUGHNESS,
            "runtime_default_selected": False,
            "source_path": source_path,
            "dmax_domain_um": [WYSER_PSD_LMIN_UM, WYSER_PSD_LMAX_UM],
            "dmax_count": 0,
            "row_count": 0,
            "wavelengths_nm": [],
            "six_band_coverage_pass": False,
            "cext_reconstruction_pass": False,
            "effective_diameter_reproduction_pass": False,
            "min_reconstructed_qext": None,
            "max_reconstructed_qext": None,
            "max_effective_diameter_relative_error": None,
            "missing_reason": "BUNDLED_DIAGNOSTIC_KERNEL_UNAVAILABLE",
        }

    qext_values: list[float] = []
    cext_values: list[float] = []
    de_errors: list[float] = []
    reconstructed_rows = 0
    for row in frame.itertuples(index=False):
        length = float(row.maximum_dimension_um)
        a = float(yang_single_column_semiwidth_um(length))
        geometry = _regular_hexagonal_column_geometry(length_um=length, semiwidth_um=a)
        mass_kg = geometry["solid_ice_mass_kg"]
        area_m2 = geometry["mean_projected_area_um2"] * 1.0e-12
        kext = float(row.mass_extinction_coefficient_m2_kg)
        cext = kext * mass_kg
        qext = cext / area_m2
        observed_de = float(row.effective_diameter_um)
        de_rel = abs(geometry["effective_diameter_um"] - observed_de) / observed_de
        if all(math.isfinite(v) and v > 0.0 for v in (mass_kg, area_m2, kext, cext, qext, observed_de)):
            reconstructed_rows += 1
            qext_values.append(float(qext))
            cext_values.append(float(cext))
            de_errors.append(float(de_rel))

    expected_wavelengths = list(ICE_OPTICS_WAVELENGTHS_NM)
    wavelengths = sorted(int(round(v)) for v in frame["wavelength_nm"].unique())
    per_size_counts = frame.groupby("maximum_dimension_um")["wavelength_nm"].nunique()
    six_band = bool(
        wavelengths == expected_wavelengths
        and len(per_size_counts) > 0
        and int(per_size_counts.min()) == len(expected_wavelengths)
        and int(per_size_counts.max()) == len(expected_wavelengths)
    )
    max_de_error = max(de_errors) if de_errors else None
    de_pass = bool(max_de_error is not None and max_de_error <= 1.0e-6)
    cext_pass = bool(
        reconstructed_rows == len(frame)
        and reconstructed_rows > 0
        and six_band
        and de_pass
        and all(math.isfinite(v) and v > 0.0 for v in cext_values)
        and all(math.isfinite(v) and v > 0.0 for v in qext_values)
    )

    return {
        "diagnostic_only": True,
        "ice_habit": DIAGNOSTIC_REFERENCE_HABIT,
        "surface_roughness": DIAGNOSTIC_REFERENCE_ROUGHNESS,
        "runtime_default_selected": False,
        "source_path": source_path,
        "dmax_domain_um": [float(WYSER_PSD_LMIN_UM), float(WYSER_PSD_LMAX_UM)],
        "dmax_count": int(frame["maximum_dimension_um"].nunique()),
        "row_count": int(len(frame)),
        "wavelengths_nm": wavelengths,
        "six_band_coverage_pass": six_band,
        "cext_reconstruction_pass": cext_pass,
        "effective_diameter_reproduction_pass": de_pass,
        "min_reconstructed_qext": float(min(qext_values)) if qext_values else None,
        "max_reconstructed_qext": float(max(qext_values)) if qext_values else None,
        "min_reconstructed_cext_m2": float(min(cext_values)) if cext_values else None,
        "max_reconstructed_cext_m2": float(max(cext_values)) if cext_values else None,
        "max_effective_diameter_relative_error": float(max_de_error) if max_de_error is not None else None,
        "missing_reason": "" if cext_pass else "DIAGNOSTIC_KERNEL_RECONSTRUCTION_NOT_QUALIFIED",
    }


def population_bridge_diagnostic() -> dict[str, Any]:
    """Return Step 3I numeric readiness without scientific/production promotion."""
    coordinate = coordinate_qualification_diagnostic()
    kernel = reconstruct_yang_single_column_optical_kernel()

    # Compare every Dmax actually present in the diagnostic reference kernel,
    # not only four display points.
    source_frame, _ = _kernel_source_frame()
    lengths = sorted(float(v) for v in source_frame["maximum_dimension_um"].unique()) if not source_frame.empty else []
    geometry = wyser_yang_geometry_mass_comparison(lengths_um=lengths) if lengths else None

    coordinate_pass = bool(coordinate.get("wyser_L_to_yang_dmax_coordinate_validated"))
    cext_pass = bool(kernel.get("cext_reconstruction_pass"))
    dual_mass_separated = True
    numeric_executable = bool(
        coordinate_pass
        and cext_pass
        and dual_mass_separated
        and geometry is not None
        and len(lengths) > 0
    )

    return {
        "diagnostic_only": True,
        "bridge_scope": "WYSER_PSD_NUMBER_POPULATION_PLUS_YANG_SINGLE_COLUMN_ROUGH000_REFERENCE_OPTICAL_KERNEL",
        "runtime_habit_roughness_selected": False,
        "population_mass_semantic": POPULATION_MASS_SEMANTIC,
        "optical_kernel_mass_semantic": OPTICAL_KERNEL_MASS_SEMANTIC,
        "mass_semantics_interchangeable": False,
        "wyser_L_to_yang_dmax_coordinate_validated": coordinate_pass,
        "yang_bi_single_column_kernel_cext_reconstruction_pass": cext_pass,
        "wyser_yang_dual_mass_semantics_separated_pass": dual_mass_separated,
        "wyser_yang_hybrid_population_bridge_numeric_executable": numeric_executable,
        "direct_shape_compatibility_pass": False,
        "direct_projected_area_equivalence_pass": False,
        "direct_volume_mass_equivalence_pass": False,
        "independent_eq6_external_numeric_corroboration_pass": False,
        "scientific_mass_closure_executed": False,
        "yang_bi_habit_bridge_validated": False,
        "yang_bi_roughness_bridge_validated": False,
        "bulk_yang_bi_psd_integration_eligible": False,
        "gfsv16_dmax_mapping_eligible": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "kernel_reconstruction": kernel,
        "geometry_mass_comparison": geometry,
    }


EVIDENCE_COLUMNS = [
    "step3i_version",
    "science_baseline",
    "step3i_mode",
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


def build_wyser_yang_population_bridge_evidence() -> pd.DataFrame:
    diagnostic = population_bridge_diagnostic()
    kernel = diagnostic["kernel_reconstruction"]
    geom = diagnostic["geometry_mass_comparison"]
    rows = [
        {
            "evidence_id": "STEP3H_DMAX_COORDINATE_INHERITANCE",
            "evidence_type": "PRIOR_QUALIFICATION_INHERITANCE",
            "pin_status": "PASS_INHERITED_STEP3H_COORDINATE",
            "value": "Wyser L_um == Yang/Bi maximum_dimension_um",
            "semantic_role": "SHARED_SIZE_COORDINATE_ONLY",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "R5.7.41.3.4.10.21 Step 3H",
            "source_path": "ice_microphysics_wyser_yang_coordinate_qualification",
            "source_sha": "",
            "notes": "Coordinate identity is inherited without promoting shape or runtime mapping.",
        },
        {
            "evidence_id": "YANG_SINGLE_COLUMN_CEXT_KERNEL_RECONSTRUCTION",
            "evidence_type": "DIAGNOSTIC_OPTICAL_KERNEL_RECONSTRUCTION",
            "pin_status": "PASS_DIAGNOSTIC_KERNEL_RECONSTRUCTION" if kernel["cext_reconstruction_pass"] else "BLOCKED_KERNEL_RECONSTRUCTION_FAILED",
            "value": (
                f"rows={kernel['row_count']};dmax_count={kernel['dmax_count']};"
                f"qext_range={kernel['min_reconstructed_qext']:.17g}-{kernel['max_reconstructed_qext']:.17g};"
                f"max_De_relerr={kernel['max_effective_diameter_relative_error']:.17g}"
                if kernel["cext_reconstruction_pass"] else "false"
            ),
            "semantic_role": "YANG_SINGLE_PARTICLE_CEXT_REFERENCE_KERNEL_ONLY",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Yang2013_Bi2017_V2 portable LUT",
            "source_path": kernel["source_path"],
            "source_sha": "",
            "notes": "Rough000 is a diagnostic reference kernel only; it is not a runtime roughness default.",
        },
        {
            "evidence_id": "WYSER_YANG_DUAL_MASS_SEMANTICS",
            "evidence_type": "SEMANTIC_SEPARATION_GATE",
            "pin_status": "PASS_SEMANTIC_SEPARATION",
            "value": f"population={POPULATION_MASS_SEMANTIC};optical_kernel={OPTICAL_KERNEL_MASS_SEMANTIC}",
            "semantic_role": "NO_MASS_SEMANTIC_SUBSTITUTION",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Wyser (1998) Eq.(6)|Yang/Bi V2 geometry",
            "source_path": "Step 3I explicit dual-mass contract",
            "source_sha": "",
            "notes": "Wyser Eq.(6) normalizes PSD/IWC; Yang rho*V only inverts k_ext to C_ext.",
        },
        {
            "evidence_id": "WYSER_YANG_HYBRID_POPULATION_BRIDGE_NUMERIC",
            "evidence_type": "DIAGNOSTIC_NUMERIC_BRIDGE_GATE",
            "pin_status": "PASS_DIAGNOSTIC_NUMERIC_EXECUTABLE" if diagnostic["wyser_yang_hybrid_population_bridge_numeric_executable"] else "BLOCKED_NUMERIC_INGREDIENTS_INCOMPLETE",
            "value": "true" if diagnostic["wyser_yang_hybrid_population_bridge_numeric_executable"] else "false",
            "semantic_role": "NUMERIC_EXECUTABILITY_NOT_SCIENTIFIC_PROMOTION",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Step 3G Eq.(6)|Step 3H coordinate|Yang/Bi V2 kernel",
            "source_path": "Step 3I diagnostic bridge",
            "source_sha": "",
            "notes": "All numeric ingredients exist for a later diagnostic PSD×Cext integration, but Step 3I does not run/promote bulk optics.",
        },
        {
            "evidence_id": "WYSER_TO_YANG_SHAPE_EQUIVALENCE",
            "evidence_type": "SHAPE_EQUIVALENCE_GATE",
            "pin_status": "BLOCKED_NON_EQUIVALENT_GEOMETRY",
            "value": "false",
            "semantic_role": "NO_DIRECT_SHAPE_EQUIVALENCE",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Wyser Eq.(5)|Yang/Bi V2 single_column",
            "source_path": "Step 3I geometry comparison",
            "source_sha": "",
            "notes": "Distinct source-pinned width laws remain non-equivalent.",
        },
        {
            "evidence_id": "WYSER_TO_YANG_PROJECTED_AREA_EQUIVALENCE",
            "evidence_type": "PROJECTED_AREA_EQUIVALENCE_GATE",
            "pin_status": "BLOCKED_NON_EQUIVALENT_GEOMETRY",
            "value": f"false;max_relative_difference={geom['max_relative_projected_area_difference']:.17g}",
            "semantic_role": "NO_HIDDEN_AREA_CORRECTION",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Wyser Eq.(5)|Yang/Bi V2 single_column",
            "source_path": "Step 3I full-domain geometry comparison",
            "source_sha": "",
            "notes": "Area ratios are diagnostics only and are not used as an optical correction factor.",
        },
        {
            "evidence_id": "WYSER_TO_YANG_VOLUME_MASS_EQUIVALENCE",
            "evidence_type": "VOLUME_MASS_EQUIVALENCE_GATE",
            "pin_status": "BLOCKED_NON_EQUIVALENT_MASS_SEMANTICS",
            "value": f"false;max_yang_mass_vs_eq6_relative_difference={geom['max_relative_yang_mass_vs_wyser_eq6_difference']:.17g}",
            "semantic_role": "NO_HIDDEN_MASS_RENORMALIZATION",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Wyser Eq.(6)|Yang/Bi V2 geometric mass",
            "source_path": "Step 3I full-domain mass comparison",
            "source_sha": "",
            "notes": "Yang geometric mass and Wyser Eq.(6) population mass remain distinct by contract.",
        },
        {
            "evidence_id": "INDEPENDENT_EQ6_EXTERNAL_NUMERIC_CORROBORATION",
            "evidence_type": "SCIENTIFIC_PROMOTION_GATE",
            "pin_status": "BLOCKED_NO_INDEPENDENT_EXACT_NUMERIC_SOURCE",
            "value": "false",
            "semantic_role": "SCIENTIFIC_MASS_CLOSURE_STILL_BLOCKED",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Wyser (1998) primary only",
            "source_path": "Step 3G/3I dual-source promotion policy",
            "source_sha": "",
            "notes": "Numeric bridge execution does not relax the independent Eq.(6) corroboration requirement.",
        },
        {
            "evidence_id": "YANG_BI_HABIT_BRIDGE",
            "evidence_type": "MICROPHYSICS_TO_OPTICS_GATE",
            "pin_status": "BLOCKED",
            "value": "false",
            "semantic_role": "NO_RUNTIME_HABIT_DEFAULT",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Yang/Bi V2 habit dimension",
            "source_path": "Step 3I diagnostic single_column reference only",
            "source_sha": "",
            "notes": "Using single_column diagnostically does not validate a GFS/Wyser-to-habit production bridge.",
        },
        {
            "evidence_id": "YANG_BI_ROUGHNESS_BRIDGE",
            "evidence_type": "MICROPHYSICS_TO_OPTICS_GATE",
            "pin_status": "BLOCKED",
            "value": "false",
            "semantic_role": "NO_RUNTIME_ROUGHNESS_DEFAULT",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Yang/Bi V2 roughness dimension",
            "source_path": "Step 3I diagnostic Rough000 reference only",
            "source_sha": "",
            "notes": "Rough000 is not silently promoted to runtime.",
        },
        {
            "evidence_id": "BULK_YANG_BI_PSD_INTEGRATION",
            "evidence_type": "BULK_OPTICS_GATE",
            "pin_status": "BLOCKED_SCIENTIFIC_INPUTS_PENDING",
            "value": "false",
            "semantic_role": "NO_BULK_KEXT_OR_TAU_PROMOTION",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Step 3I bridge policy",
            "source_path": "Downstream Step 3J candidate",
            "source_sha": "",
            "notes": "Step 3I stops at numeric bridge qualification and does not emit production bulk optics.",
        },
        {
            "evidence_id": "STEP3I_PRODUCTION_PROMOTION",
            "evidence_type": "PROMOTION_GATE",
            "pin_status": "BLOCKED",
            "value": "false",
            "semantic_role": "DIAGNOSTIC_ONLY_NO_PRODUCTION_PROMOTION",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "PhysicsCore frozen promotion policy",
            "source_path": "Step 3I contract",
            "source_sha": "",
            "notes": "No Dmax runtime synthesis, habit/roughness default, bulk tau, or Formation promotion is enabled.",
        },
    ]
    return pd.DataFrame([
        {
            "step3i_version": STEP3I_VERSION,
            "science_baseline": SCIENCE_BASELINE,
            "step3i_mode": STEP3I_MODE,
            **row,
        }
        for row in rows
    ], columns=EVIDENCE_COLUMNS)


def build_wyser_yang_population_bridge_gate(evidence: pd.DataFrame | None = None) -> pd.DataFrame:
    df = evidence.copy() if isinstance(evidence, pd.DataFrame) else build_wyser_yang_population_bridge_evidence()
    diagnostic = population_bridge_diagnostic()
    blockers = [
        "DIRECT_SHAPE_EQUIVALENCE_NOT_PASSED",
        "PROJECTED_AREA_EQUIVALENCE_NOT_PASSED",
        "VOLUME_MASS_EQUIVALENCE_NOT_PASSED",
        "INDEPENDENT_EQ6_EXTERNAL_NUMERIC_CORROBORATION_NOT_PASSED",
        "SCIENTIFIC_MASS_CLOSURE_NOT_EXECUTED",
        "YANG_BI_HABIT_BRIDGE_NOT_VALIDATED",
        "YANG_BI_ROUGHNESS_BRIDGE_NOT_VALIDATED",
        "NO_INDEPENDENT_BULK_OPTICS_VALIDATION",
    ]
    return pd.DataFrame([{
        "step3i_version": STEP3I_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "step3i_mode": STEP3I_MODE,
        "WYSER_L_TO_YANG_DMAX_COORDINATE_VALIDATED": bool(diagnostic["wyser_L_to_yang_dmax_coordinate_validated"]),
        "YANG_BI_SINGLE_COLUMN_KERNEL_CEXT_RECONSTRUCTION_PASS": bool(diagnostic["yang_bi_single_column_kernel_cext_reconstruction_pass"]),
        "WYSER_YANG_DUAL_MASS_SEMANTICS_SEPARATED_PASS": bool(diagnostic["wyser_yang_dual_mass_semantics_separated_pass"]),
        "WYSER_YANG_HYBRID_POPULATION_BRIDGE_NUMERIC_EXECUTABLE": bool(diagnostic["wyser_yang_hybrid_population_bridge_numeric_executable"]),
        "WYSER_TO_YANG_SOLID_COLUMN_SHAPE_COMPATIBILITY_PASS": False,
        "WYSER_TO_YANG_PROJECTED_AREA_EQUIVALENCE_PASS": False,
        "WYSER_TO_YANG_VOLUME_MASS_EQUIVALENCE_PASS": False,
        "INDEPENDENT_EQ6_EXTERNAL_NUMERIC_CORROBORATION_PASS": False,
        "SCIENTIFIC_MASS_CLOSURE_EXECUTED": False,
        "YANG_BI_HABIT_BRIDGE_VALIDATED": False,
        "YANG_BI_ROUGHNESS_BRIDGE_VALIDATED": False,
        "BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE": False,
        "GFSV16_DMAX_MAPPING_ELIGIBLE": False,
        "PRODUCTION_ICE_OPTICS_READY": False,
        "physics_promotion_allowed": False,
        "evidence_row_count": int(len(df)),
        "qualification_state": "WYSER_YANG_HYBRID_POPULATION_BRIDGE_NUMERIC_READY_SCIENTIFIC_PROMOTION_BLOCKED",
        "qualification_blockers": "|".join(blockers),
        "detail": "The shared Dmax axis plus Yang Cext kernel are numerically usable with explicitly separated Wyser population mass and Yang optical-kernel mass. Direct geometry/mass equivalence, Eq.6 independent corroboration, habit/roughness, bulk validation and production remain blocked.",
    }])


def wyser_yang_population_bridge_contract_payload(*, physicscore_version: str | None = None) -> dict[str, Any]:
    diagnostic = population_bridge_diagnostic()
    kernel = diagnostic["kernel_reconstruction"]
    geom = diagnostic["geometry_mass_comparison"]
    return {
        "contract_version": "FIRECLOUD_ICE_WYSER_YANG_POPULATION_BRIDGE_V1",
        "physicscore_version": physicscore_version or "",
        "step3i_version": STEP3I_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "mode": STEP3I_MODE,
        "bridge_scope": diagnostic["bridge_scope"],
        "population_mass_semantic": POPULATION_MASS_SEMANTIC,
        "optical_kernel_mass_semantic": OPTICAL_KERNEL_MASS_SEMANTIC,
        "mass_semantics_interchangeable": False,
        "diagnostic_reference_habit": DIAGNOSTIC_REFERENCE_HABIT,
        "diagnostic_reference_roughness": DIAGNOSTIC_REFERENCE_ROUGHNESS,
        "runtime_habit_roughness_selected": False,
        "wyser_L_to_yang_dmax_coordinate_validated": bool(diagnostic["wyser_L_to_yang_dmax_coordinate_validated"]),
        "yang_bi_single_column_kernel_cext_reconstruction_pass": bool(diagnostic["yang_bi_single_column_kernel_cext_reconstruction_pass"]),
        "wyser_yang_dual_mass_semantics_separated_pass": bool(diagnostic["wyser_yang_dual_mass_semantics_separated_pass"]),
        "wyser_yang_hybrid_population_bridge_numeric_executable": bool(diagnostic["wyser_yang_hybrid_population_bridge_numeric_executable"]),
        "direct_shape_compatibility_pass": False,
        "direct_projected_area_equivalence_pass": False,
        "direct_volume_mass_equivalence_pass": False,
        "independent_eq6_external_numeric_corroboration_pass": False,
        "scientific_mass_closure_executed": False,
        "yang_bi_habit_bridge_validated": False,
        "yang_bi_roughness_bridge_validated": False,
        "bulk_yang_bi_psd_integration_eligible": False,
        "gfsv16_dmax_mapping_eligible": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "frozen_science_unchanged": True,
        "kernel_reconstruction": kernel,
        "geometry_mass_summary": {
            "tested_lengths_count": len(geom["tested_lengths_um"]),
            "tested_domain_um": [min(geom["tested_lengths_um"]), max(geom["tested_lengths_um"])],
            "max_relative_projected_area_difference": geom["max_relative_projected_area_difference"],
            "max_relative_volume_difference": geom["max_relative_volume_difference"],
            "max_relative_yang_mass_vs_wyser_eq6_difference": geom["max_relative_yang_mass_vs_wyser_eq6_difference"],
            "max_relative_wyser_geometric_mass_vs_eq6_difference": geom["max_relative_wyser_geometric_mass_vs_eq6_difference"],
        },
        "forbidden_shortcuts": [
            "yang_geometric_mass_used_to_normalize_wyser_psd",
            "wyser_eq6_mass_used_to_invert_yang_mass_extinction_coefficient",
            "diagnostic_single_column_rough000_kernel_treated_as_runtime_habit_roughness_default",
            "shared_dmax_coordinate_treated_as_shape_equivalence",
            "projected_area_ratio_used_as_hidden_optical_correction",
            "volume_mass_ratio_used_as_hidden_psd_correction",
            "diagnostic_numeric_bridge_treated_as_scientific_bulk_optics_validation",
            "diagnostic_numeric_bridge_used_to_enable_tau_or_formation_promotion",
        ],
        "evidence_as_of": EVIDENCE_AS_OF,
    }
