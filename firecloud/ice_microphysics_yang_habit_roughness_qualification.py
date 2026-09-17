"""Ice Optics Phase 2 Step 3L — Yang/Bi habit + roughness qualification.

This step separates three questions that must not be collapsed:
1) model-family semantics: Wyser's solid-column lineage can be paired with the
   Yang/Bi ``single_column`` habit family on the already-qualified Dmax axis;
2) exact geometry: the Wyser and Yang/Bi column shape laws are not equivalent;
3) runtime inference: GFS does not provide native particle habit or Yang/Bi
   surface-roughness state, so neither habit nor roughness may be silently
   defaulted in production.

Rough000/Rough003/Rough050 are therefore treated as a diagnostic uncertainty
ensemble for the model-family single-column bridge.  No tau_ice is produced.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import math

import numpy as np
import pandas as pd

from . import __version__ as PHYSICSCORE_VERSION
from .ice_cloud_spectral_optics import BUNDLED_CALIBRATED_LUT_PATH, ICE_OPTICS_WAVELENGTHS_NM
from .ice_microphysics_wyser_primary_numeric_recovery import (
    WYSER_PSD_LMIN_UM, WYSER_PSD_LMAX_UM, _wyser_mass_array_g, _wyser_shape_array,
)
from .ice_microphysics_wyser_yang_coordinate_qualification import yang_single_column_semiwidth_um
from .ice_microphysics_wyser_yang_population_bridge import _regular_hexagonal_column_geometry
from .ice_microphysics_wyser_yang_diagnostic_bulk_integration import _integration_grid, _loglog_interp_positive

SCIENCE_BASELINE = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
STEP3L_VERSION = "R5.7.41.3.4.10.25"
STEP3L_MODE = "YANG_HABIT_ROUGHNESS_MODEL_FAMILY_QUALIFICATION_ENSEMBLE_FAIL_CLOSED"
PHYSICS_PROMOTION_ALLOWED = False
EVIDENCE_AS_OF = "2026-09-18"

SOURCE_DATASET = "TAMU_ICE_SINGLE_SCATTERING_V2"
SOURCE_VERSION = "Yang2013_Bi2017_V2"
SOURCE_ZENODO = "https://zenodo.org/records/5348402"
YANG2013_DOI = "https://doi.org/10.1175/JAS-D-12-039.1"
BI2017_DOI = "https://doi.org/10.1016/j.jqsrt.2016.12.007"
SOURCE_RELATIVE_PATH = "firecloud/data/ice_optics/portable_ice_optics_lut_v1.csv"
SOURCE_MANIFEST_RELATIVE_PATH = "firecloud/data/ice_optics/authoritative_source_manifest_v1.json"
EXPECTED_HABITS = ["10_plates", "5_plates", "8_columns", "HBR", "HC", "SBR", "droxtal", "plate", "single_column"]
EXPECTED_ROUGHNESS = ["Rough000", "Rough003", "Rough050"]
MODEL_FAMILY_HABIT = "single_column"
STABLE_EVIDENCE_SIGNIFICANT_DIGITS = 11


def _stable(value: float) -> str:
    return format(float(value), f".{STABLE_EVIDENCE_SIGNIFICANT_DIGITS}g")


def _lut() -> pd.DataFrame:
    df = pd.read_csv(BUNDLED_CALIBRATED_LUT_PATH)
    return df


def authoritative_habit_roughness_inventory() -> dict[str, Any]:
    df = _lut()
    habits = sorted(df["ice_habit"].astype(str).unique().tolist())
    roughness = sorted(df["surface_roughness"].astype(str).unique().tolist())
    waves = sorted(pd.to_numeric(df["wavelength_nm"], errors="coerce").dropna().astype(int).unique().tolist())
    sizes = sorted(pd.to_numeric(df["maximum_dimension_um"], errors="coerce").dropna().unique().tolist())
    expected_rows = len(EXPECTED_HABITS) * len(EXPECTED_ROUGHNESS) * len(ICE_OPTICS_WAVELENGTHS_NM) * 189
    coverage = bool(
        habits == sorted(EXPECTED_HABITS)
        and roughness == EXPECTED_ROUGHNESS
        and waves == [int(v) for v in ICE_OPTICS_WAVELENGTHS_NM]
        and len(sizes) == 189
        and float(min(sizes)) == 2.0
        and float(max(sizes)) == 10000.0
        and len(df) == expected_rows
    )
    return {
        "source_dataset": SOURCE_DATASET,
        "source_version": SOURCE_VERSION,
        "habit_count": len(habits),
        "habits": habits,
        "roughness_count": len(roughness),
        "roughness_states": roughness,
        "wavelength_count": len(waves),
        "wavelengths_nm": waves,
        "particle_size_count": len(sizes),
        "particle_size_range_um": [float(min(sizes)), float(max(sizes))],
        "row_count": int(len(df)),
        "coverage_complete": coverage,
    }


def _relative_spread(frame: pd.DataFrame, *, index: list[str], columns: str, value: str) -> tuple[float, float]:
    piv = frame.pivot_table(index=index, columns=columns, values=value)
    spread = piv.max(axis=1) - piv.min(axis=1)
    denom = piv.mean(axis=1).replace(0.0, np.nan).abs()
    rel = (spread / denom).replace([np.inf, -np.inf], np.nan).dropna()
    return float(rel.max()), float(spread.max())


def source_row_habit_roughness_uncertainty() -> dict[str, Any]:
    df = _lut().copy()
    df = df.loc[pd.to_numeric(df["maximum_dimension_um"], errors="coerce").between(10.0, 1000.0)].copy()
    for col in ("mass_extinction_coefficient_m2_kg", "single_scattering_albedo", "asymmetry_parameter"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    habit_k_rel, habit_k_abs = _relative_spread(
        df, index=["surface_roughness", "maximum_dimension_um", "wavelength_nm"],
        columns="ice_habit", value="mass_extinction_coefficient_m2_kg")
    habit_g_rel, habit_g_abs = _relative_spread(
        df, index=["surface_roughness", "maximum_dimension_um", "wavelength_nm"],
        columns="ice_habit", value="asymmetry_parameter")

    sc = df.loc[df["ice_habit"].astype(str) == MODEL_FAMILY_HABIT].copy()
    rough_k_rel, rough_k_abs = _relative_spread(
        sc, index=["maximum_dimension_um", "wavelength_nm"],
        columns="surface_roughness", value="mass_extinction_coefficient_m2_kg")
    rough_g_rel, rough_g_abs = _relative_spread(
        sc, index=["maximum_dimension_um", "wavelength_nm"],
        columns="surface_roughness", value="asymmetry_parameter")
    rough_w_rel, rough_w_abs = _relative_spread(
        sc, index=["maximum_dimension_um", "wavelength_nm"],
        columns="surface_roughness", value="single_scattering_albedo")

    return {
        "domain_um": [10.0, 1000.0],
        "habit_mass_extinction_max_relative_spread": habit_k_rel,
        "habit_mass_extinction_max_absolute_spread": habit_k_abs,
        "habit_asymmetry_max_relative_spread": habit_g_rel,
        "habit_asymmetry_max_absolute_spread": habit_g_abs,
        "single_column_roughness_mass_extinction_max_relative_spread": rough_k_rel,
        "single_column_roughness_mass_extinction_max_absolute_spread": rough_k_abs,
        "single_column_roughness_asymmetry_max_relative_spread": rough_g_rel,
        "single_column_roughness_asymmetry_max_absolute_spread": rough_g_abs,
        "single_column_roughness_ssa_max_relative_spread": rough_w_rel,
        "single_column_roughness_ssa_max_absolute_spread": rough_w_abs,
    }


def _single_column_source(roughness: str) -> dict[int, tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]:
    df = _lut()
    sub = df.loc[
        (df["ice_habit"].astype(str) == MODEL_FAMILY_HABIT)
        & (df["surface_roughness"].astype(str) == str(roughness))
        & pd.to_numeric(df["maximum_dimension_um"], errors="coerce").between(WYSER_PSD_LMIN_UM, WYSER_PSD_LMAX_UM)
    ].copy()
    result = {}
    for wave in ICE_OPTICS_WAVELENGTHS_NM:
        b = sub.loc[pd.to_numeric(sub["wavelength_nm"], errors="coerce") == float(wave)].sort_values("maximum_dimension_um")
        d = b["maximum_dimension_um"].to_numpy(dtype=float)
        k = b["mass_extinction_coefficient_m2_kg"].to_numpy(dtype=float)
        w0 = b["single_scattering_albedo"].to_numpy(dtype=float)
        g = b["asymmetry_parameter"].to_numpy(dtype=float)
        cext = []
        for dv, kv in zip(d, k):
            geom = _regular_hexagonal_column_geometry(
                length_um=float(dv), semiwidth_um=float(yang_single_column_semiwidth_um(float(dv))))
            cext.append(float(kv) * float(geom["solid_ice_mass_kg"]))
        result[int(wave)] = (d, np.asarray(cext), w0, g)
    return result


def _bulk_state(*, roughness: str, temperature_k: float, iwc_g_m3: float, grid_points: int) -> dict[str, Any]:
    source = _single_column_source(roughness)
    first_d = source[int(ICE_OPTICS_WAVELENGTHS_NM[0])][0]
    d = _integration_grid(grid_points, first_d)
    phi = _wyser_shape_array(d, temperature_k=float(temperature_k), iwc_g_m3=float(iwc_g_m3))
    mass_g = _wyser_mass_array_g(d)
    den = float(np.trapezoid(mass_g * phi, d))
    amp = float(iwc_g_m3) / den
    n = amp * phi
    iwc_kg_m3 = float(iwc_g_m3) * 1.0e-3
    bands = []
    for wave in ICE_OPTICS_WAVELENGTHS_NM:
        sx, scext, sw0, sg = source[int(wave)]
        cext = _loglog_interp_positive(d, sx, scext)
        w0 = np.interp(np.log(d), np.log(sx), sw0)
        g = np.interp(np.log(d), np.log(sx), sg)
        beta_ext = float(np.trapezoid(n * cext, d))
        beta_sca = float(np.trapezoid(n * cext * w0, d))
        bulk_g = float(np.trapezoid(n * cext * w0 * g, d) / beta_sca)
        bands.append({
            "wavelength_nm": int(wave),
            "k_ext_m2_kg": beta_ext / iwc_kg_m3,
            "single_scattering_albedo_bulk": beta_sca / beta_ext,
            "asymmetry_parameter_bulk": bulk_g,
        })
    return {"roughness": roughness, "bands": bands}


def single_column_roughness_bulk_ensemble(
    *, temperature_k: float, iwc_g_m3: float, grid_points: int = 4097, reference_grid_points: int = 16385,
) -> dict[str, Any]:
    states = [_bulk_state(roughness=r, temperature_k=temperature_k, iwc_g_m3=iwc_g_m3, grid_points=grid_points) for r in EXPECTED_ROUGHNESS]
    refs = {r: _bulk_state(roughness=r, temperature_k=temperature_k, iwc_g_m3=iwc_g_m3, grid_points=reference_grid_points) for r in EXPECTED_ROUGHNESS}
    max_conv = 0.0
    for state in states:
        ref = refs[state["roughness"]]
        rb = {x["wavelength_nm"]: x for x in ref["bands"]}
        for b in state["bands"]:
            q = rb[b["wavelength_nm"]]
            conv = abs(b["k_ext_m2_kg"] - q["k_ext_m2_kg"]) / q["k_ext_m2_kg"]
            max_conv = max(max_conv, conv)
    # cross-roughness bulk spread by band
    k_spreads=[]; w_spreads=[]; g_spreads=[]
    for wave in ICE_OPTICS_WAVELENGTHS_NM:
        rows=[next(b for b in s["bands"] if b["wavelength_nm"]==int(wave)) for s in states]
        k_spreads.append(max(r["k_ext_m2_kg"] for r in rows)-min(r["k_ext_m2_kg"] for r in rows))
        w_spreads.append(max(r["single_scattering_albedo_bulk"] for r in rows)-min(r["single_scattering_albedo_bulk"] for r in rows))
        g_spreads.append(max(r["asymmetry_parameter_bulk"] for r in rows)-min(r["asymmetry_parameter_bulk"] for r in rows))
    numeric = bool(max_conv <= 5e-4 and all(len(s["bands"]) == 6 for s in states))
    return {
        "diagnostic_only": True,
        "temperature_k": float(temperature_k), "iwc_g_m3": float(iwc_g_m3),
        "roughness_states": list(EXPECTED_ROUGHNESS), "states": states,
        "numeric_pass": numeric, "max_grid_convergence_relative_error": float(max_conv),
        "max_bulk_k_ext_spread_m2_kg": float(max(k_spreads)),
        "max_bulk_ssa_spread": float(max(w_spreads)),
        "max_bulk_g_spread": float(max(g_spreads)),
        "runtime_roughness_selected": False,
        "roughness_production_default_allowed": False,
        "tau_ice_production_allowed": False,
        "physics_promotion_allowed": False,
    }


EVIDENCE_COLUMNS = [
    "step3l_version", "science_baseline", "step3l_mode", "evidence_id", "evidence_type", "pin_status",
    "value", "semantic_role", "authoritative_for_runtime_mapping", "source_reference", "source_path", "source_sha", "notes",
]


def build_yang_habit_roughness_qualification_evidence() -> pd.DataFrame:
    inv = authoritative_habit_roughness_inventory()
    unc = source_row_habit_roughness_uncertainty()
    ens = single_column_roughness_bulk_ensemble(temperature_k=253.16, iwc_g_m3=0.1, grid_points=2049, reference_grid_points=8193)
    rows = [
        ("YANG_V2_HABIT_ROUGHNESS_INVENTORY", "SOURCE_INVENTORY", "PASS_SOURCE_INVENTORY_COMPLETE", f"habits={inv['habit_count']};roughness={inv['roughness_count']};rows={inv['row_count']}", "AUTHORITATIVE_SOURCE_COVERAGE", False, f"{SOURCE_ZENODO}|{YANG2013_DOI}|{BI2017_DOI}", SOURCE_RELATIVE_PATH, "", "Nine bundled nonspherical habits and three source roughness states are preserved."),
        ("WYSER_YANG_SOLID_COLUMN_HABIT_FAMILY_BRIDGE", "MODEL_FAMILY_SEMANTIC_BRIDGE", "PASS_SOLID_COLUMN_FAMILY_SEMANTICS", "true", "WYSER_SOLID_COLUMN_LINEAGE_TO_YANG_SINGLE_COLUMN_FAMILY", False, f"R5.7.41.3.4.10.20.1 Wyser lineage|{YANG2013_DOI}", "Step 3L qualification", "", "Model-family bridge only; it is not a claim of exact geometry or observed cloud habit."),
        ("EXACT_GEOMETRY_EQUIVALENCE", "GEOMETRY_GATE", "BLOCKED_STEP3I_GEOMETRY_DIFFERENCE", "false", "HABIT_FAMILY_DOES_NOT_IMPLY_SHAPE_EQUIVALENCE", False, "R5.7.41.3.4.10.22 Step 3I", "Step 3L carry-forward", "", "Wyser Eq.(5) and Yang V2 column geometry remain distinct."),
        ("GFS_NATIVE_HABIT_INFERENCE", "RUNTIME_INPUT_GATE", "BLOCKED_NO_NATIVE_HABIT_FIELD", "false", "NO_OBSERVED_OR_FORECAST_HABIT_SELECTION", False, "GFSv16 native capability audit", "Step 3L qualification", "", "GFS condensate fields do not encode Yang/Bi particle habit."),
        ("ROUGHNESS_SOURCE_STATES", "SOURCE_SEMANTICS", "PASS_THREE_SOURCE_STATES_PINNED", "Rough000|Rough003|Rough050", "YANG_BI_ROUGHNESS_SOURCE_COORDINATE", False, f"{YANG2013_DOI}|{SOURCE_ZENODO}", SOURCE_RELATIVE_PATH, "", "Smooth/moderately/severely roughened source states; no interpolation or guessed state."),
        ("ROUGHNESS_ENSEMBLE_DIAGNOSTIC", "UNCERTAINTY_ENSEMBLE", "PASS_DIAGNOSTIC_ENSEMBLE_EXECUTABLE" if ens["numeric_pass"] else "BLOCKED_NUMERIC", "true" if ens["numeric_pass"] else "false", "SINGLE_COLUMN_THREE_STATE_ROUGHNESS_UNCERTAINTY", False, SOURCE_RELATIVE_PATH, SOURCE_RELATIVE_PATH, "", f"max_bulk_kext_spread={_stable(ens['max_bulk_k_ext_spread_m2_kg'])};max_bulk_g_spread={_stable(ens['max_bulk_g_spread'])}"),
        ("HABIT_OPTICAL_SENSITIVITY", "SOURCE_ROW_UNCERTAINTY", "PASS_MATERIAL_HABIT_SPREAD_CHARACTERIZED", _stable(unc["habit_mass_extinction_max_relative_spread"]), "HABIT_CANNOT_BE_SILENTLY_IGNORED", False, SOURCE_RELATIVE_PATH, SOURCE_RELATIVE_PATH, "", f"max_g_abs_spread={_stable(unc['habit_asymmetry_max_absolute_spread'])}"),
        ("ROUGHNESS_OPTICAL_SENSITIVITY", "SOURCE_ROW_UNCERTAINTY", "PASS_MATERIAL_ROUGHNESS_SPREAD_CHARACTERIZED", _stable(unc["single_column_roughness_mass_extinction_max_relative_spread"]), "ROUGHNESS_CANNOT_BE_SILENTLY_IGNORED", False, SOURCE_RELATIVE_PATH, SOURCE_RELATIVE_PATH, "", f"max_g_abs_spread={_stable(unc['single_column_roughness_asymmetry_max_absolute_spread'])}"),
        ("RUNTIME_HABIT_DEFAULT", "PROMOTION_GATE", "BLOCKED_NO_NATIVE_HABIT_INFERENCE", "false", "NO_HIDDEN_HABIT_DEFAULT", False, "Step 3L policy", "Step 3L fail-close", "", "single_column is a diagnostic/model-family bridge, not a runtime truth label."),
        ("RUNTIME_ROUGHNESS_DEFAULT", "PROMOTION_GATE", "BLOCKED_NO_NATIVE_ROUGHNESS_INFERENCE", "false", "NO_HIDDEN_ROUGHNESS_DEFAULT", False, "Step 3L policy", "Step 3L fail-close", "", "Rough000/Rough003/Rough050 must remain an uncertainty ensemble unless separately constrained."),
        ("TAU_ICE_PRODUCTION_PROMOTION", "PROMOTION_GATE", "BLOCKED", "false", "NO_TAU_ICE_PRODUCTION", False, "Frozen PhysicsCore policy", "Step 3L fail-close", "", "Habit/roughness qualification does not write diagnostic optics into production tau."),
        ("STEP3L_PRODUCTION_PROMOTION", "PROMOTION_GATE", "BLOCKED", "false", "NO_PRODUCTION_ICE_OPTICS_PROMOTION", False, "Frozen PhysicsCore policy", "Step 3L fail-close", "", "Formation/Viewing/Twilight Glow remain unchanged."),
    ]
    return pd.DataFrame([{
        "step3l_version": STEP3L_VERSION, "science_baseline": SCIENCE_BASELINE, "step3l_mode": STEP3L_MODE,
        "evidence_id": r[0], "evidence_type": r[1], "pin_status": r[2], "value": r[3], "semantic_role": r[4],
        "authoritative_for_runtime_mapping": r[5], "source_reference": r[6], "source_path": r[7], "source_sha": r[8], "notes": r[9],
    } for r in rows], columns=EVIDENCE_COLUMNS)


def build_yang_habit_roughness_qualification_gate(evidence: pd.DataFrame | None = None) -> pd.DataFrame:
    df = evidence.copy() if isinstance(evidence, pd.DataFrame) else build_yang_habit_roughness_qualification_evidence()
    if "evidence_id" not in df.columns and df.index.name == "evidence_id":
        df = df.reset_index()
    vals = dict(zip(df["evidence_id"].astype(str), df["value"].astype(str)))
    inventory = vals.get("YANG_V2_HABIT_ROUGHNESS_INVENTORY", "").startswith("habits=9;roughness=3")
    family = vals.get("WYSER_YANG_SOLID_COLUMN_HABIT_FAMILY_BRIDGE") == "true"
    exact_geometry = vals.get("EXACT_GEOMETRY_EQUIVALENCE") == "true"
    native_habit = vals.get("GFS_NATIVE_HABIT_INFERENCE") == "true"
    ensemble = vals.get("ROUGHNESS_ENSEMBLE_DIAGNOSTIC") == "true"
    habit_default = vals.get("RUNTIME_HABIT_DEFAULT") == "true"
    rough_default = vals.get("RUNTIME_ROUGHNESS_DEFAULT") == "true"
    tau = vals.get("TAU_ICE_PRODUCTION_PROMOTION") == "true"
    return pd.DataFrame([{
        "step3l_version": STEP3L_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "step3l_mode": STEP3L_MODE,
        "source_inventory_complete": inventory,
        "wyser_yang_solid_column_habit_family_bridge_pass": family,
        "exact_geometry_equivalence_pass": exact_geometry,
        "gfs_native_habit_inference_pass": native_habit,
        "roughness_ensemble_diagnostic_ready": ensemble,
        "runtime_habit_default_allowed": habit_default,
        "runtime_roughness_default_allowed": rough_default,
        "tau_ice_production_allowed": tau,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "YANG_V2_SOURCE_INVENTORY_PASS": inventory,
        "WYSER_YANG_SOLID_COLUMN_HABIT_FAMILY_BRIDGE_PASS": family,
        "EXACT_GEOMETRY_EQUIVALENCE_PASS": exact_geometry,
        "GFS_NATIVE_HABIT_INFERENCE_PASS": native_habit,
        "ROUGHNESS_ENSEMBLE_DIAGNOSTIC_READY": ensemble,
        "RUNTIME_HABIT_DEFAULT_ALLOWED": habit_default,
        "RUNTIME_ROUGHNESS_DEFAULT_ALLOWED": rough_default,
        "TAU_ICE_PRODUCTION_ALLOWED": tau,
        "PRODUCTION_ICE_OPTICS_READY": False,
        "qualification_state": "HABIT_FAMILY_BRIDGE_AND_ROUGHNESS_ENSEMBLE_READY_RUNTIME_DEFAULTS_BLOCKED",
        "qualification_blockers": "EXACT_GEOMETRY_EQUIVALENCE_NOT_VALIDATED|GFS_NATIVE_HABIT_INFERENCE_UNAVAILABLE|RUNTIME_ROUGHNESS_SELECTION_UNAVAILABLE|LIKE_FOR_LIKE_OPTICAL_VALIDATION_PENDING",
        "evidence_row_count": int(len(df)),
        "detail": "Solid-column model-family bridge is qualified and three-state roughness uncertainty is executable, but no runtime habit/roughness truth is inferred and tau/production remain blocked.",
    }])


def yang_habit_roughness_qualification_contract_payload(*, physicscore_version: str | None = None) -> dict[str, Any]:
    inv = authoritative_habit_roughness_inventory()
    unc = source_row_habit_roughness_uncertainty()
    ens = single_column_roughness_bulk_ensemble(temperature_k=253.16, iwc_g_m3=0.1, grid_points=2049, reference_grid_points=8193)
    return {
        "contract_version": "FIRECLOUD_ICE_YANG_HABIT_ROUGHNESS_QUALIFICATION_V1",
        "physicscore_version": physicscore_version or PHYSICSCORE_VERSION,
        "step3l_version": STEP3L_VERSION,
        "science_baseline": SCIENCE_BASELINE,
        "mode": STEP3L_MODE,
        "source_dataset": SOURCE_DATASET,
        "source_version": SOURCE_VERSION,
        "source_inventory": inv,
        "model_family_habit": MODEL_FAMILY_HABIT,
        "wyser_yang_solid_column_habit_family_bridge_pass": True,
        "exact_geometry_equivalence_pass": False,
        "gfs_native_habit_inference_pass": False,
        "roughness_states": list(EXPECTED_ROUGHNESS),
        "roughness_ensemble_diagnostic_ready": bool(ens["numeric_pass"]),
        "runtime_habit_default_allowed": False,
        "runtime_roughness_default_allowed": False,
        "source_row_uncertainty": {k: ([_stable(x) for x in v] if isinstance(v, list) else _stable(v) if isinstance(v, float) else v) for k, v in unc.items()},
        "sample_roughness_bulk_ensemble": {
            "temperature_k": ens["temperature_k"], "iwc_g_m3": ens["iwc_g_m3"],
            "max_bulk_k_ext_spread_m2_kg": _stable(ens["max_bulk_k_ext_spread_m2_kg"]),
            "max_bulk_ssa_spread": _stable(ens["max_bulk_ssa_spread"]),
            "max_bulk_g_spread": _stable(ens["max_bulk_g_spread"]),
            "max_grid_convergence_relative_error": _stable(ens["max_grid_convergence_relative_error"]),
        },
        "bulk_yang_bi_psd_integration_eligible": False,
        "tau_ice_production_allowed": False,
        "production_ice_optics_ready": False,
        "physics_promotion_allowed": False,
        "forbidden_shortcuts": [
            "Do not infer habit from IWP/IWC/T/RH/cloud fraction.",
            "Do not silently default to single_column in production runtime.",
            "Do not silently default to Rough000, Rough003 or Rough050.",
            "Do not interpolate across habit or roughness states.",
            "Do not promote diagnostic k_ext to tau_ice production in Step 3L.",
        ],
    }
