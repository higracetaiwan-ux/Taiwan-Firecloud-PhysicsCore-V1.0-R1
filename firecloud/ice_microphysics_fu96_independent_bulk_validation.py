"""Ice Optics Phase 2 Step 3K — Fu (1996) independent bulk-extinction cross-check.

This module deliberately does *not* reuse the Yang/Bi C_ext kernel in its
reference chain.  It keeps the already-qualified Wyser number population,
reconstructs the randomly oriented hexagonal-column projected area from
Wyser Eq.(5), and applies the Fu (1996) geometric-optics relation

    beta_ext ~= 2 * A_c

where A_c is total particle projected area per unit volume.

The resulting mass-extinction coefficient is compared against Step 3J's
Yang/Bi-C_ext weighted diagnostic k_ext.  The comparison is a scientific
cross-check, not a production promotion.  In particular, the Wyser Eq.(6)
population mass semantic is kept distinct from the solid-ice volume semantic
used in the classical Fu D_ge definition.
"""
from __future__ import annotations

from typing import Any, Iterable
import math

import numpy as np
import pandas as pd

from .ice_microphysics_wyser_primary_numeric_recovery import (
    _wyser_length_grid,
    _wyser_shape_array,
    _wyser_mass_array_g,
    wyser_eq5_width_um,
)
from .ice_microphysics_wyser_yang_diagnostic_bulk_integration import (
    diagnostic_bulk_extinction,
)

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
STEP3K_VERSION = "R5.7.41.3.4.10.24"
STEP3K_MODE = "FU96_PROJECTED_AREA_INDEPENDENT_BULK_EXTINCTION_CROSSCHECK_FAIL_CLOSED"
PHYSICS_PROMOTION_ALLOWED = False
EVIDENCE_AS_OF = "2026-09-17"

FU96_PRIMARY_DOI = "https://doi.org/10.1175/1520-0442(1996)009%3C2058:AAPOTS%3E2.0.CO;2"
FU96_NCEP_TECHNICAL_NOTE = "https://www.emc.ncep.noaa.gov/mmb/ea/bf/tmp/Ice_Effective_Radius_Papers/Effective%20Radius%20of%20Ice.pdf"
FU96_PROJECTED_AREA_SECONDARY = "https://atmos.washington.edu/academic/grad/html/theses/MStheses/RobinsonS_MS2007.pdf"
FU96_ICE_DENSITY_KG_M3 = 917.0
FU96_EXTINCTION_COEFFICIENT = 2.5184
FU96_UNIT_CHAIN_TOLERANCE = 2.0e-5

# Step 3K uses integrations whose last few floating-point digits can vary
# across BLAS/libm/platform combinations.  Canonicalize *evidence output only*
# to 11 significant digits; all scientific calculations above remain full
# double precision.  This precision is far tighter than the Step 3K diagnostic
# tolerances while collapsing the platform variants observed in FIELD CASEs.
STABLE_STEP3K_EVIDENCE_SIGNIFICANT_DIGITS = 11


def stable_step3k_evidence_float(value: float) -> str:
    return format(float(value), f".{STABLE_STEP3K_EVIDENCE_SIGNIFICANT_DIGITS}g")


def stable_step3k_evidence_number(value: float) -> float:
    return float(stable_step3k_evidence_float(value))

INDEPENDENT_OPTICAL_KERNEL = "FU96_GEOMETRIC_OPTICS_BETA_APPROX_2AC"
PROJECTED_AREA_DEFINITION = "Pbar=(3/4)*(D*L+(sqrt(3)/4)*D^2)"
MASS_AREA_DGE_DEFINITION = "Dge=(2*sqrt(3)/(3*rho_ice))*IWC/Ac"
SOLID_HEX_DGE_DEFINITION = "Dge=integral[D^2*L*n dL]/integral[(D*L+(sqrt(3)/4)*D^2)*n dL]"


def _positive_finite(value: float, *, name: str) -> float:
    out = float(value)
    if not math.isfinite(out) or out <= 0.0:
        raise ValueError(f"{name} must be positive and finite")
    return out


def _wyser_population_projected_area_solution(
    *,
    temperature_k: float,
    iwc_g_m3: float,
    grid_points: int,
) -> dict[str, float]:
    temperature = _positive_finite(temperature_k, name="temperature_k")
    iwc = _positive_finite(iwc_g_m3, name="iwc_g_m3")
    length_um = _wyser_length_grid(int(grid_points))
    phi = _wyser_shape_array(length_um, temperature_k=temperature, iwc_g_m3=iwc)
    mass_g = _wyser_mass_array_g(length_um)
    denominator_g = float(np.trapezoid(mass_g * phi, length_um))
    if not math.isfinite(denominator_g) or denominator_g <= 0.0:
        raise ValueError("Wyser Eq.(6) PSD normalization denominator must be positive and finite")

    amplitude = iwc / denominator_g
    number_density_per_um = amplitude * phi
    reconstructed_iwc_g_m3 = float(np.trapezoid(mass_g * number_density_per_um, length_um))
    mass_closure_error = abs(reconstructed_iwc_g_m3 - iwc) / iwc

    width_um = np.asarray([wyser_eq5_width_um(float(v)) for v in length_um], dtype=float)
    projected_area_um2 = 0.75 * (
        width_um * length_um + (math.sqrt(3.0) / 4.0) * width_um * width_um
    )
    projected_area_total_m_inv = float(
        np.trapezoid(projected_area_um2 * 1.0e-12 * number_density_per_um, length_um)
    )
    if not math.isfinite(projected_area_total_m_inv) or projected_area_total_m_inv <= 0.0:
        raise ValueError("total projected area per volume must be positive and finite")

    iwc_kg_m3 = iwc * 1.0e-3
    beta_ext_m_inv = 2.0 * projected_area_total_m_inv
    k_ext_m2_kg = beta_ext_m_inv / iwc_kg_m3

    mass_area_dge_m = (
        2.0 * math.sqrt(3.0) / (3.0 * FU96_ICE_DENSITY_KG_M3)
    ) * (iwc_kg_m3 / projected_area_total_m_inv)
    mass_area_dge_um = mass_area_dge_m * 1.0e6
    k_ext_via_dge_m2_kg = FU96_EXTINCTION_COEFFICIENT * 1.0e3 / mass_area_dge_um
    unit_chain_error = abs(k_ext_m2_kg - k_ext_via_dge_m2_kg) / k_ext_m2_kg

    solid_num = float(np.trapezoid(width_um * width_um * length_um * number_density_per_um, length_um))
    solid_den = float(np.trapezoid(
        (width_um * length_um + (math.sqrt(3.0) / 4.0) * width_um * width_um)
        * number_density_per_um,
        length_um,
    ))
    solid_hex_dge_um = solid_num / solid_den

    return {
        "grid_points_actual": int(length_um.size),
        "normalization_amplitude": float(amplitude),
        "reconstructed_iwc_g_m3": float(reconstructed_iwc_g_m3),
        "mass_closure_relative_error": float(mass_closure_error),
        "projected_area_total_m_inv": float(projected_area_total_m_inv),
        "beta_ext_m_inv": float(beta_ext_m_inv),
        "k_ext_m2_kg": float(k_ext_m2_kg),
        "mass_area_equivalent_dge_um": float(mass_area_dge_um),
        "solid_hex_geometry_dge_um": float(solid_hex_dge_um),
        "k_ext_via_dge_m2_kg": float(k_ext_via_dge_m2_kg),
        "fu96_unit_chain_relative_error": float(unit_chain_error),
    }


def diagnostic_fu96_independent_bulk_validation(
    *,
    temperature_k: float,
    iwc_g_m3: float,
    grid_points: int = 4097,
    reference_grid_points: int = 16385,
) -> dict[str, Any]:
    temperature = _positive_finite(temperature_k, name="temperature_k")
    iwc = _positive_finite(iwc_g_m3, name="iwc_g_m3")
    if int(reference_grid_points) <= int(grid_points):
        raise ValueError("reference_grid_points must exceed grid_points")

    solution = _wyser_population_projected_area_solution(
        temperature_k=temperature,
        iwc_g_m3=iwc,
        grid_points=int(grid_points),
    )
    reference = _wyser_population_projected_area_solution(
        temperature_k=temperature,
        iwc_g_m3=iwc,
        grid_points=int(reference_grid_points),
    )
    projected_area_convergence_error = abs(
        solution["k_ext_m2_kg"] - reference["k_ext_m2_kg"]
    ) / reference["k_ext_m2_kg"]

    step3j = diagnostic_bulk_extinction(
        temperature_k=temperature,
        iwc_g_m3=iwc,
        grid_points=int(grid_points),
        reference_grid_points=int(reference_grid_points),
    )
    fu_kext = float(solution["k_ext_m2_kg"])
    bands: list[dict[str, float]] = []
    for row in step3j.get("bands", []):
        step3j_kext = float(row["k_ext_m2_kg"])
        bands.append({
            "wavelength_nm": int(row["wavelength_nm"]),
            "step3j_k_ext_m2_kg": step3j_kext,
            "fu96_k_ext_m2_kg": fu_kext,
            "relative_difference_vs_fu96": abs(step3j_kext - fu_kext) / fu_kext,
        })

    projected_area_numeric_pass = bool(
        solution["projected_area_total_m_inv"] > 0.0
        and solution["mass_closure_relative_error"] <= 1.0e-12
        and projected_area_convergence_error <= 5.0e-4
    )
    unit_chain_pass = bool(solution["fu96_unit_chain_relative_error"] <= FU96_UNIT_CHAIN_TOLERANCE)
    extinction_chain_pass = bool(projected_area_numeric_pass and unit_chain_pass and len(bands) == 6)

    return {
        "diagnostic_only": True,
        "temperature_k": temperature,
        "iwc_g_m3": iwc,
        "independent_optical_kernel": INDEPENDENT_OPTICAL_KERNEL,
        "uses_yang_bi_cext_in_reference_chain": False,
        "projected_area_definition": PROJECTED_AREA_DEFINITION,
        "mass_area_dge_definition": MASS_AREA_DGE_DEFINITION,
        "solid_hex_dge_definition": SOLID_HEX_DGE_DEFINITION,
        "projected_area_total_m_inv": solution["projected_area_total_m_inv"],
        "projected_area_convergence_relative_error": float(projected_area_convergence_error),
        "projected_area_numeric_pass": projected_area_numeric_pass,
        "fu96_beta_ext_m_inv": solution["beta_ext_m_inv"],
        "fu96_k_ext_m2_kg": solution["k_ext_m2_kg"],
        "mass_area_equivalent_dge_um": solution["mass_area_equivalent_dge_um"],
        "solid_hex_geometry_dge_um": solution["solid_hex_geometry_dge_um"],
        "dge_semantics_interchangeable": False,
        "fu96_k_ext_via_dge_m2_kg": solution["k_ext_via_dge_m2_kg"],
        "fu96_unit_chain_relative_error": solution["fu96_unit_chain_relative_error"],
        "fu96_unit_chain_pass": unit_chain_pass,
        "fu96_extinction_chain_numeric_pass": extinction_chain_pass,
        "step3j_bands": bands,
        "min_relative_difference_vs_fu96": float(min(r["relative_difference_vs_fu96"] for r in bands)),
        "max_relative_difference_vs_fu96": float(max(r["relative_difference_vs_fu96"] for r in bands)),
        "scientific_bulk_validation_pass": False,
        "bulk_yang_bi_psd_integration_eligible": False,
        "tau_ice_production_allowed": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "missing_reason": "",
    }


def run_fu96_independent_bulk_validation_grid(
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
                cases.append(diagnostic_fu96_independent_bulk_validation(
                    temperature_k=temperature,
                    iwc_g_m3=iwc,
                    grid_points=points,
                    reference_grid_points=int(reference_grid_points),
                ))

    all_diffs = [
        float(row["relative_difference_vs_fu96"])
        for case in cases for row in case["step3j_bands"]
    ]
    return {
        "diagnostic_only": True,
        "case_count": len(cases),
        "temperatures_k": list(temperatures),
        "iwc_values_g_m3": list(iwcs),
        "grid_points": list(grids),
        "reference_grid_points": int(reference_grid_points),
        "all_fu96_extinction_chain_numeric_pass": bool(all(c["fu96_extinction_chain_numeric_pass"] for c in cases)),
        "all_projected_area_numeric_pass": bool(all(c["projected_area_numeric_pass"] for c in cases)),
        "max_fu96_unit_chain_relative_error": float(max(c["fu96_unit_chain_relative_error"] for c in cases)),
        "min_relative_difference_vs_fu96": float(min(all_diffs)),
        "max_relative_difference_vs_fu96": float(max(all_diffs)),
        "scientific_bulk_validation_pass": False,
        "bulk_yang_bi_psd_integration_eligible": False,
        "tau_ice_production_allowed": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "cases": cases,
    }


EVIDENCE_COLUMNS = [
    "step3k_version", "science_baseline", "step3k_mode", "evidence_id",
    "evidence_type", "pin_status", "value", "semantic_role",
    "authoritative_for_runtime_mapping", "source_reference", "source_path",
    "source_sha", "notes",
]


def build_fu96_independent_bulk_validation_evidence() -> pd.DataFrame:
    grid = run_fu96_independent_bulk_validation_grid()
    sample = diagnostic_fu96_independent_bulk_validation(
        temperature_k=253.16,
        iwc_g_m3=0.1,
        grid_points=4097,
        reference_grid_points=16385,
    )
    rows = [
        {
            "evidence_id": "FU96_PRIMARY_PARAMETERIZATION_PROVENANCE",
            "evidence_type": "PRIMARY_LITERATURE_PROVENANCE",
            "pin_status": "PINNED_PRIMARY_FU96_SOLAR_CIRRUS_PARAMETERIZATION",
            "value": "Fu (1996): cirrus solar radiative properties parameterized by IWC and generalized effective size Dge",
            "semantic_role": "INDEPENDENT_OPTICAL_FRAMEWORK_PROVENANCE",
            "authoritative_for_runtime_mapping": False,
            "source_reference": FU96_PRIMARY_DOI,
            "source_path": "Fu (1996), J. Climate 9, 2058-2082",
            "source_sha": "",
            "notes": "Used only as an independent diagnostic optical framework; not a replacement production scheme.",
        },
        {
            "evidence_id": "FU96_PROJECTED_AREA_EXTINCTION_CHAIN",
            "evidence_type": "INDEPENDENT_OPTICAL_CROSSCHECK",
            "pin_status": "PASS_INDEPENDENT_OPTICAL_CROSSCHECK_EXECUTED" if grid["all_fu96_extinction_chain_numeric_pass"] else "BLOCKED_NUMERIC_CHAIN_FAILED",
            "value": f"beta_ext≈2Ac;all_18_cases_pass={grid['all_fu96_extinction_chain_numeric_pass']};max_unit_chain_relerr={stable_step3k_evidence_float(grid['max_fu96_unit_chain_relative_error'])}",
            "semantic_role": "REFERENCE_CHAIN_DOES_NOT_USE_YANG_BI_CEXT",
            "authoritative_for_runtime_mapping": False,
            "source_reference": f"{FU96_PRIMARY_DOI}|{FU96_NCEP_TECHNICAL_NOTE}|{FU96_PROJECTED_AREA_SECONDARY}",
            "source_path": "Fu geometric-optics projected-area extinction relation",
            "source_sha": "",
            "notes": "The population remains Wyser-normalized so only the optical-kernel path is changed for the cross-check.",
        },
        {
            "evidence_id": "FU96_PROJECTED_AREA_GEOMETRY",
            "evidence_type": "HEX_COLUMN_PROJECTED_AREA_CONTRACT",
            "pin_status": "PINNED_RANDOM_ORIENTATION_PROJECTED_AREA_FORM",
            "value": PROJECTED_AREA_DEFINITION,
            "semantic_role": "WYSER_EQ5_GEOMETRY_TO_FU_PROJECTED_AREA",
            "authoritative_for_runtime_mapping": False,
            "source_reference": FU96_PROJECTED_AREA_SECONDARY,
            "source_path": "Robinson (2007) Fu-Liou cirrus parameterization thesis, projected-area/volume definitions",
            "source_sha": "",
            "notes": "Applied to Wyser Eq.(5) width D(L); no Yang/Bi geometry is used in the reference chain.",
        },
        {
            "evidence_id": "FU96_DGE_DUAL_SEMANTICS",
            "evidence_type": "MASS_SEMANTICS_GUARD",
            "pin_status": "PASS_DGE_SEMANTICS_SEPARATED",
            "value": f"sample_mass_area_Dge_um={stable_step3k_evidence_float(sample['mass_area_equivalent_dge_um'])};sample_solid_hex_Dge_um={stable_step3k_evidence_float(sample['solid_hex_geometry_dge_um'])}",
            "semantic_role": "WYser_EQ6_MASS_AREA_EQUIVALENT_DGE_NOT_SOLID_HEX_DGE",
            "authoritative_for_runtime_mapping": False,
            "source_reference": f"{FU96_PRIMARY_DOI}|R5.7.41.3.4.10.20.1 Wyser Eq.(6)",
            "source_path": "Step 3K dual-semantics audit",
            "source_sha": "",
            "notes": "The two Dge values are intentionally not interchangeable because Wyser Eq.(6) mass is not assumed equal to solid-ice rho*V geometry.",
        },
        {
            "evidence_id": "FU96_STEP3J_BULK_DIFFERENCE_CHARACTERIZATION",
            "evidence_type": "INDEPENDENT_BULK_DIFFERENCE_CHARACTERIZATION",
            "pin_status": "PASS_DIFFERENCE_CHARACTERIZED_NO_PROMOTION",
            "value": f"relative_difference_range={stable_step3k_evidence_float(grid['min_relative_difference_vs_fu96'])}..{stable_step3k_evidence_float(grid['max_relative_difference_vs_fu96'])}",
            "semantic_role": "QUANTIFIED_CROSSCHECK_NOT_EQUIVALENCE_CLAIM",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Step 3J Yang/Bi Cext diagnostic vs Step 3K Fu projected-area chain",
            "source_path": "18-case x six-band comparison",
            "source_sha": "",
            "notes": "Difference is material and consistent with unresolved geometry/projected-area/habit semantics; no promotion threshold is asserted.",
        },
        {
            "evidence_id": "SCIENTIFIC_BULK_VALIDATION",
            "evidence_type": "SCIENTIFIC_PROMOTION_GATE",
            "pin_status": "BLOCKED_REFERENCE_NOT_LIKE_FOR_LIKE_PRODUCTION_VALIDATION",
            "value": "false",
            "semantic_role": "INDEPENDENT_CROSSCHECK_EXECUTED_BUT_PRODUCTION_VALIDATION_NOT_MET",
            "authoritative_for_runtime_mapping": False,
            "source_reference": FU96_PRIMARY_DOI,
            "source_path": "Step 3K qualification policy",
            "source_sha": "",
            "notes": "Fu geometric-optics reference is an independent kernel sanity check, not a like-for-like Yang/Bi habit/roughness production validation.",
        },
        {
            "evidence_id": "YANG_BI_HABIT_BRIDGE",
            "evidence_type": "MICROPHYSICS_TO_OPTICS_GATE",
            "pin_status": "BLOCKED",
            "value": "false",
            "semantic_role": "NO_RUNTIME_HABIT_DEFAULT",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Step 3I/3J carry-forward",
            "source_path": "Step 3K promotion policy",
            "source_sha": "",
            "notes": "Independent cross-check does not choose a runtime Yang/Bi habit.",
        },
        {
            "evidence_id": "YANG_BI_ROUGHNESS_BRIDGE",
            "evidence_type": "MICROPHYSICS_TO_OPTICS_GATE",
            "pin_status": "BLOCKED",
            "value": "false",
            "semantic_role": "NO_RUNTIME_ROUGHNESS_DEFAULT",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Step 3I/3J carry-forward",
            "source_path": "Step 3K promotion policy",
            "source_sha": "",
            "notes": "Independent cross-check does not choose a runtime roughness state.",
        },
        {
            "evidence_id": "BULK_YANG_BI_PSD_INTEGRATION_ELIGIBILITY",
            "evidence_type": "PROMOTION_GATE",
            "pin_status": "BLOCKED",
            "value": "false",
            "semantic_role": "DIAGNOSTIC_ONLY",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Step 3K fail-close",
            "source_path": "Step 3K promotion policy",
            "source_sha": "",
            "notes": "Cross-check execution does not make the hybrid bulk path production eligible.",
        },
        {
            "evidence_id": "TAU_ICE_PRODUCTION_PROMOTION",
            "evidence_type": "PROMOTION_GATE",
            "pin_status": "BLOCKED_NOT_COMPUTED_IN_STEP3K",
            "value": "false",
            "semantic_role": "NO_TAU_ICE_PRODUCTION",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Frozen PhysicsCore promotion policy",
            "source_path": "Step 3K fail-close",
            "source_sha": "",
            "notes": "No diagnostic k_ext is written into runtime tau synthesis.",
        },
        {
            "evidence_id": "STEP3K_PRODUCTION_PROMOTION",
            "evidence_type": "PROMOTION_GATE",
            "pin_status": "BLOCKED",
            "value": "false",
            "semantic_role": "NO_PRODUCTION_ICE_OPTICS_PROMOTION",
            "authoritative_for_runtime_mapping": False,
            "source_reference": "Frozen PhysicsCore promotion policy",
            "source_path": "Step 3K fail-close",
            "source_sha": "",
            "notes": "Formation/Viewing/Twilight Glow and runtime ice optics remain unchanged.",
        },
    ]
    return pd.DataFrame([
        {
            "step3k_version": STEP3K_VERSION,
            "science_baseline": SCIENCE_BASELINE,
            "step3k_mode": STEP3K_MODE,
            **row,
        }
        for row in rows
    ], columns=EVIDENCE_COLUMNS)


def build_fu96_independent_bulk_validation_gate(evidence: pd.DataFrame | None = None) -> pd.DataFrame:
    df = evidence.copy() if isinstance(evidence, pd.DataFrame) else build_fu96_independent_bulk_validation_evidence()
    if "evidence_id" not in df.columns and df.index.name == "evidence_id":
        df = df.reset_index()
    status = dict(zip(df["evidence_id"].astype(str), df["pin_status"].astype(str))) if not df.empty else {}
    executed = status.get("FU96_PROJECTED_AREA_EXTINCTION_CHAIN") == "PASS_INDEPENDENT_OPTICAL_CROSSCHECK_EXECUTED"
    geometry = status.get("FU96_PROJECTED_AREA_GEOMETRY") == "PINNED_RANDOM_ORIENTATION_PROJECTED_AREA_FORM"
    dge_sep = status.get("FU96_DGE_DUAL_SEMANTICS") == "PASS_DGE_SEMANTICS_SEPARATED"
    characterized = status.get("FU96_STEP3J_BULK_DIFFERENCE_CHARACTERIZATION") == "PASS_DIFFERENCE_CHARACTERIZED_NO_PROMOTION"
    scientific = False
    return pd.DataFrame([{
        "step3k_version": STEP3K_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "step3k_mode": STEP3K_MODE,
        "FU96_INDEPENDENT_OPTICAL_CROSSCHECK_EXECUTED": bool(executed),
        "FU96_PROJECTED_AREA_CHAIN_NUMERIC_PASS": bool(executed and geometry),
        "FU96_DGE_DUAL_SEMANTICS_SEPARATED_PASS": bool(dge_sep),
        "FU96_BULK_DIFFERENCE_CHARACTERIZED": bool(characterized),
        "SCIENTIFIC_BULK_VALIDATION_PASS": scientific,
        "BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE": False,
        "TAU_ICE_PRODUCTION_ALLOWED": False,
        "PRODUCTION_ICE_OPTICS_READY": False,
        "physics_promotion_allowed": False,
        "evidence_row_count": int(len(df)),
        "qualification_state": "FU96_INDEPENDENT_CROSSCHECK_EXECUTED_SCIENTIFIC_PROMOTION_BLOCKED",
        "qualification_blockers": "FU96_REFERENCE_NOT_LIKE_FOR_LIKE_YANG_BI_PRODUCTION_VALIDATION|YANG_BI_HABIT_BRIDGE_NOT_VALIDATED|YANG_BI_ROUGHNESS_BRIDGE_NOT_VALIDATED|WYSER_YANG_PROJECTED_AREA_EQUIVALENCE_NOT_VALIDATED|EQ6_EXTERNAL_NUMERIC_CORROBORATION_PENDING",
        "detail": "Fu projected-area geometric-optics cross-check is executable and quantified, but material differences and unresolved shape/habit/roughness semantics prevent scientific/production promotion.",
    }])


def fu96_independent_bulk_validation_contract_payload(*, physicscore_version: str | None = None) -> dict[str, Any]:
    grid = run_fu96_independent_bulk_validation_grid()
    return {
        "contract_version": "FIRECLOUD_ICE_FU96_INDEPENDENT_BULK_VALIDATION_V1",
        "physicscore_version": physicscore_version or "",
        "step3k_version": STEP3K_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "mode": STEP3K_MODE,
        "primary_reference": FU96_PRIMARY_DOI,
        "reference_chain": INDEPENDENT_OPTICAL_KERNEL,
        "uses_yang_bi_cext_in_reference_chain": False,
        "projected_area_definition": PROJECTED_AREA_DEFINITION,
        "mass_area_dge_definition": MASS_AREA_DGE_DEFINITION,
        "solid_hex_dge_definition": SOLID_HEX_DGE_DEFINITION,
        "dge_semantics_interchangeable": False,
        "fu96_ice_density_kg_m3": FU96_ICE_DENSITY_KG_M3,
        "fu96_extinction_coefficient": FU96_EXTINCTION_COEFFICIENT,
        "diagnostic_matrix": {
            "case_count": grid["case_count"],
            "all_fu96_extinction_chain_numeric_pass": grid["all_fu96_extinction_chain_numeric_pass"],
            "all_projected_area_numeric_pass": grid["all_projected_area_numeric_pass"],
            "max_fu96_unit_chain_relative_error": stable_step3k_evidence_number(grid["max_fu96_unit_chain_relative_error"]),
            "min_relative_difference_vs_fu96": stable_step3k_evidence_number(grid["min_relative_difference_vs_fu96"]),
            "max_relative_difference_vs_fu96": stable_step3k_evidence_number(grid["max_relative_difference_vs_fu96"]),
        },
        "scientific_bulk_validation_pass": False,
        "bulk_yang_bi_psd_integration_eligible": False,
        "tau_ice_production_allowed": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "forbidden_shortcuts": [
            "Fu_mass_area_equivalent_Dge_treated_as_solid_hex_geometry_Dge",
            "Fu_crosscheck_difference_treated_as_Yang_Bi_shape_equivalence",
            "Fu_geometric_optics_crosscheck_treated_as_like_for_like_production_validation",
            "diagnostic_k_ext_written_into_runtime_ice_optics",
            "tau_ice_synthesized_from_step3k_reference_chain",
            "runtime_habit_or_roughness_selected_by_step3k",
        ],
        "frozen_science_unchanged": True,
    }
