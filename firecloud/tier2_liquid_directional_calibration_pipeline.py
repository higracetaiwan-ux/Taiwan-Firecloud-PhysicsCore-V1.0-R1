from __future__ import annotations
"""R5.7.23 genuine liquid-cloud full-directional calibration pipeline.

This module does *not* synthesize or approximate production radiative-transfer
responses.  It prepares a reproducible external-calibration job bundle from
Tier-2-ready PhysicsCore targets, validates externally computed Monte-Carlo RT
results, and only then delegates to the existing R5.7.22 calibrated-LUT package
builder.

Frozen production response axes remain:
    R_lambda = f(COT, r_eff, theta0, thetav, Delta-phi, wavelength)

Cloud geometric thickness is retained as evidence but is not silently promoted
into a LUT interpolation axis.  Any future promotion requires a separate
sensitivity contract.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from .contracts import SIX_BAND_WAVELENGTHS_NM
from .tier2_libradtran_mystic_adapter import (
    MYSTIC_ADAPTER_CONTRACT,
    INCIDENT_IRRADIANCE_REFERENCE,
    ATMOSPHERIC_COUPLING,
    SURFACE_BOUNDARY,
    CALIBRATION_SCOPE,
    geometry_to_uvspec,
    unit_solar_spectrum_text,
    liquid_cloud_profile_text,
    render_uvspec_input,
    parse_mc_rad_spc,
    parse_mc_rad_std_spc,
    external_result_row,
)
from .tier2_directional_scattering_calibration import (
    DIRECTIONAL_CALIBRATION_CONTRACT,
    DIRECTIONAL_GEOMETRY_CONVENTION,
    DIRECTIONAL_INTERPOLATION_AXES,
    DIRECTIONAL_RESPONSE_DEFINITION,
    DIRECTIONAL_RESPONSE_UNITS,
    DIRECTIONAL_SUPPORTED_SOLVER_FAMILIES,
    build_directional_calibration_jobs,
    build_directional_calibration_package,
)

PIPELINE_CONTRACT = "R5.7.23_LIQUID_FULL_DIRECTIONAL_CALIBRATION_PIPELINE_V1"
SOLVER_RECIPE_CONTRACT = "R5.7.23_LIBRADTRAN_MYSTIC_SPHERICAL_RECIPE_V1"
RESULT_CONTRACT = "R5.7.23_EXTERNAL_DIRECTIONAL_RT_RESULT_V1"
DOMAIN_CONTRACT = "R5.7.23_LIQUID_DIRECTIONAL_CALIBRATION_DOMAIN_V1"

# Deliberately broad, physics-motivated candidate axes.  The planner only keeps
# the subset needed to bracket the supplied real Tier-2-ready targets, plus one
# guard knot where possible.  These are calibration design knots, not empirical
# firecloud-scoring thresholds.
DEFAULT_COT_KNOTS = (
    0.03, 0.05, 0.10, 0.20, 0.30, 0.50, 0.75, 1.0, 1.5, 2.0,
    3.0, 5.0, 7.5, 10.0, 15.0, 20.0, 30.0, 50.0,
)
DEFAULT_REFF_KNOTS_UM = (4.0, 6.0, 8.0, 10.0, 12.0, 15.0, 20.0, 25.0, 30.0)

CALIBRATION_TARGET_COLUMNS = [
    "time", "solar_altitude_deg", "canvas_id", "cloud_layer_id",
    "operational_domain", "distance_km", "target_optical_truth_state",
    "target_cot_semantics", "cot_lower_bound", "cot_upper_bound", "phase",
    "effective_radius_um", "cloud_thickness_km", "solar_zenith_deg",
    "view_zenith_deg", "relative_azimuth_deg", "scattering_angle_deg",
    "tier2_input_contract_state", "directional_geometry_state",
    "calibration_target_state", "calibration_pipeline_contract",
]

EXTERNAL_RESULT_REQUIRED_COLUMNS = [
    "job_id", "response_factor", "response_factor_std", "mc_absolute_sigma",
    "mc_relative_sigma", "photon_count", "sample_qc_state", "solver_run_id",
    "solver_exit_code", "solver_family", "solver_version", "result_contract",
    "adapter_contract",
]


def canonical_domain_spec_sha256(domain_spec: dict[str, Any]) -> str:
    payload = json.dumps(domain_spec, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class CalibrationResultAudit:
    ok: bool
    state: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    expected_job_count: int
    result_row_count: int
    passed_row_count: int
    max_mc_relative_sigma: float | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "state": self.state,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "expected_job_count": self.expected_job_count,
            "result_row_count": self.result_row_count,
            "passed_row_count": self.passed_row_count,
            "max_mc_relative_sigma": self.max_mc_relative_sigma,
            "result_contract": RESULT_CONTRACT,
            "pipeline_contract": PIPELINE_CONTRACT,
        }


def _finite(v: Any) -> bool:
    try:
        return bool(math.isfinite(float(v)))
    except Exception:
        return False


def _phase(v: Any) -> str:
    p = str(v or "").strip().upper()
    return "LIQUID" if p == "WATER" else p


def _key_frame(df: pd.DataFrame) -> pd.DataFrame:
    q = df.copy()
    if "canvas_id" not in q.columns:
        q["canvas_id"] = ""
    if "solar_altitude_deg" not in q.columns:
        q["solar_altitude_deg"] = np.nan
    q["_canvas_key"] = q["canvas_id"].astype(str)
    q["_angle_key"] = pd.to_numeric(q["solar_altitude_deg"], errors="coerce").round(6)
    return q


def select_liquid_calibration_targets(
    *, foundation: pd.DataFrame, readiness: pd.DataFrame,
) -> pd.DataFrame:
    """Return only physically eligible liquid-cloud calibration targets.

    This function never infers COT, phase, r_eff or geometry.  It only joins
    evidence that is already present in the Tier-2 readiness/foundation tables.
    """
    if foundation is None or foundation.empty or readiness is None or readiness.empty:
        return pd.DataFrame(columns=CALIBRATION_TARGET_COLUMNS)

    f = _key_frame(foundation)
    r = _key_frame(readiness)
    r_keep = [
        "_canvas_key", "_angle_key", "target_optical_truth_state",
        "target_cot_semantics", "cot_lower_bound", "cot_upper_bound", "phase",
        "effective_radius_um", "cloud_thickness_km", "tier2_input_contract_state",
    ]
    r_keep = [c for c in r_keep if c in r.columns]
    q = f.merge(r[r_keep], on=["_canvas_key", "_angle_key"], how="left", suffixes=("", "_r"))

    if "tier2_input_contract_state_r" in q.columns:
        q["tier2_input_contract_state"] = q["tier2_input_contract_state_r"].fillna(q.get("tier2_input_contract_state", ""))
    if "phase" not in q.columns:
        q["phase"] = ""
    q["phase"] = q["phase"].map(_phase)

    input_state = q.get("tier2_input_contract_state", pd.Series("", index=q.index)).astype(str)
    geom_state = q.get("directional_geometry_state", pd.Series("", index=q.index)).astype(str)
    truth = q.get("target_optical_truth_state", pd.Series("", index=q.index)).astype(str)
    semantics = q.get("target_cot_semantics", pd.Series("", index=q.index)).astype(str)

    cot_eligible = (
        (truth.str.startswith("EXACT_") & semantics.eq("EXACT_VALUE"))
        | (truth.eq("BOUNDED_NATIVE_BRACKET") & semantics.eq("BOUNDED_INTERVAL"))
    )
    mask = (
        input_state.eq("INPUTS_READY_AWAITING_LUT_SOLVER")
        & geom_state.eq("FULL_DIRECTIONAL_GEOMETRY_READY")
        & q["phase"].eq("LIQUID")
        & cot_eligible
    )
    q = q.loc[mask].copy()
    if q.empty:
        return pd.DataFrame(columns=CALIBRATION_TARGET_COLUMNS)

    for c in (
        "cot_lower_bound", "cot_upper_bound", "effective_radius_um",
        "cloud_thickness_km", "solar_zenith_deg", "view_zenith_deg",
        "relative_azimuth_deg", "scattering_angle_deg",
    ):
        q[c] = pd.to_numeric(q.get(c), errors="coerce")

    finite_required = q[[
        "cot_lower_bound", "cot_upper_bound", "effective_radius_um",
        "solar_zenith_deg", "view_zenith_deg", "relative_azimuth_deg",
    ]].notna().all(axis=1)
    q = q.loc[finite_required].copy()
    q["calibration_target_state"] = "REAL_TIER2_READY_LIQUID_TARGET"
    q["calibration_pipeline_contract"] = PIPELINE_CONTRACT

    out = pd.DataFrame()
    for c in CALIBRATION_TARGET_COLUMNS:
        if c == "solar_altitude_deg" and "solar_altitude_deg" not in q.columns:
            out[c] = q["_angle_key"]
        else:
            out[c] = q[c] if c in q.columns else None
    return out.reset_index(drop=True)


def _range_from_series(values: Iterable[Any]) -> tuple[float, float]:
    vals = [float(v) for v in values if _finite(v)]
    if not vals:
        raise ValueError("CALIBRATION_DOMAIN_AXIS_HAS_NO_FINITE_VALUES")
    return min(vals), max(vals)


def _subset_bracketing_knots(
    base_knots: Iterable[float], lo: float, hi: float, *, guard_knots: int = 1,
) -> list[float]:
    vals = sorted({float(x) for x in base_knots})
    if not vals:
        raise ValueError("CALIBRATION_BASE_KNOTS_EMPTY")
    if lo > hi:
        lo, hi = hi, lo
    if lo < vals[0]:
        vals = [float(lo)] + vals
    if hi > vals[-1]:
        vals = vals + [float(hi)]
    left = max(i for i, x in enumerate(vals) if x <= lo)
    right = min(i for i, x in enumerate(vals) if x >= hi)
    left = max(0, left - int(guard_knots))
    right = min(len(vals) - 1, right + int(guard_knots))
    return vals[left:right + 1]


def _adaptive_angle_knots(
    values: Iterable[Any], *, margin_deg: float, step_deg: float, lower: float = 0.0, upper: float = 180.0,
) -> list[float]:
    vals = sorted(float(v) for v in values if _finite(v))
    if not vals:
        raise ValueError("CALIBRATION_ANGLE_AXIS_EMPTY")
    lo = max(lower, vals[0] - float(margin_deg))
    hi = min(upper, vals[-1] + float(margin_deg))
    step = float(step_deg)
    if step <= 0:
        raise ValueError("CALIBRATION_ANGLE_STEP_INVALID")
    start = max(lower, math.floor(lo / step) * step)
    stop = min(upper, math.ceil(hi / step) * step)
    grid = []
    x = start
    while x <= stop + step * 1e-9:
        grid.append(round(float(x), 6))
        x += step
    # Guarantee bracketing even when bounds land outside numeric loop rounding.
    if grid[0] > vals[0]:
        grid.insert(0, round(max(lower, vals[0]), 6))
    if grid[-1] < vals[-1]:
        grid.append(round(min(upper, vals[-1]), 6))
    return sorted(set(grid))


def plan_liquid_directional_calibration_domain(
    *, foundation: pd.DataFrame, readiness: pd.DataFrame,
    angular_margin_deg: float = 2.0,
    relative_azimuth_margin_deg: float = 5.0,
    angular_step_deg: float = 2.0,
    relative_azimuth_step_deg: float = 2.5,
) -> dict[str, Any]:
    """Create a reproducible liquid-only calibration-domain specification.

    The domain is derived only from real Tier-2-ready evidence supplied by the
    caller.  No synthetic target is introduced.  Standard candidate COT/r_eff
    knots are merely interpolation-grid design points that bracket the observed
    evidence.
    """
    t = select_liquid_calibration_targets(foundation=foundation, readiness=readiness)
    if t.empty:
        raise ValueError("NO_REAL_TIER2_READY_LIQUID_TARGETS_FOR_CALIBRATION_DOMAIN")

    cot_lo = pd.to_numeric(t["cot_lower_bound"], errors="coerce")
    cot_hi = pd.to_numeric(t["cot_upper_bound"], errors="coerce")
    cot_min = float(pd.concat([cot_lo, cot_hi]).min())
    cot_max = float(pd.concat([cot_lo, cot_hi]).max())
    reff_min, reff_max = _range_from_series(t["effective_radius_um"])
    t0_min, t0_max = _range_from_series(t["solar_zenith_deg"])
    tv_min, tv_max = _range_from_series(t["view_zenith_deg"])
    daz_min, daz_max = _range_from_series(t["relative_azimuth_deg"])

    cot_grid = _subset_bracketing_knots(DEFAULT_COT_KNOTS, cot_min, cot_max, guard_knots=1)
    reff_grid = _subset_bracketing_knots(DEFAULT_REFF_KNOTS_UM, reff_min, reff_max, guard_knots=1)
    theta0_grid = _adaptive_angle_knots(
        t["solar_zenith_deg"], margin_deg=angular_margin_deg, step_deg=angular_step_deg,
    )
    thetav_grid = _adaptive_angle_knots(
        t["view_zenith_deg"], margin_deg=angular_margin_deg, step_deg=angular_step_deg,
    )
    relaz_grid = _adaptive_angle_knots(
        t["relative_azimuth_deg"], margin_deg=relative_azimuth_margin_deg,
        step_deg=relative_azimuth_step_deg,
    )

    job_count = (
        1 * len(SIX_BAND_WAVELENGTHS_NM) * len(cot_grid) * len(reff_grid)
        * len(theta0_grid) * len(thetav_grid) * len(relaz_grid)
    )
    return {
        "contract": DOMAIN_CONTRACT,
        "pipeline_contract": PIPELINE_CONTRACT,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_target_state": "REAL_TIER2_READY_LIQUID_TARGET",
        "source_target_count": int(len(t)),
        "phases": ["LIQUID"],
        "wavelengths_nm": [int(x) for x in SIX_BAND_WAVELENGTHS_NM],
        "cot": cot_grid,
        "effective_radius_um": reff_grid,
        "solar_zenith_deg": theta0_grid,
        "view_zenith_deg": thetav_grid,
        "relative_azimuth_deg": relaz_grid,
        "observed_domain": {
            "cot": [cot_min, cot_max],
            "effective_radius_um": [reff_min, reff_max],
            "solar_zenith_deg": [t0_min, t0_max],
            "view_zenith_deg": [tv_min, tv_max],
            "relative_azimuth_deg": [daz_min, daz_max],
        },
        "grid_design": {
            "cot_knots_source": "PHYSICS_DESIGN_KNOTS_BRACKETING_REAL_TARGETS",
            "reff_knots_source": "PHYSICS_DESIGN_KNOTS_BRACKETING_REAL_TARGETS",
            "angular_margin_deg": float(angular_margin_deg),
            "relative_azimuth_margin_deg": float(relative_azimuth_margin_deg),
            "angular_step_deg": float(angular_step_deg),
            "relative_azimuth_step_deg": float(relative_azimuth_step_deg),
            "cloud_thickness_is_interpolation_axis": False,
            "cloud_thickness_role": "EVIDENCE_AND_FUTURE_SENSITIVITY_STUDY_ONLY",
        },
        "planned_job_count": int(job_count),
        "interpolation_axes": list(DIRECTIONAL_INTERPOLATION_AXES),
        "geometry_convention": DIRECTIONAL_GEOMETRY_CONVENTION,
        "response_definition": DIRECTIONAL_RESPONSE_DEFINITION,
        "response_units": DIRECTIONAL_RESPONSE_UNITS,
    }


def _uvspec_umu_from_cloud_to_observer_view_zenith(view_zenith_deg: float) -> float:
    return geometry_to_uvspec(90.0, float(view_zenith_deg), 180.0).umu


def build_libradtran_mystic_solver_recipe(
    *,
    libRadtran_version: str = "UNRESOLVED_EXTERNAL_RUNTIME",
    photons_per_job: int = 1_000_000,
    atmosphere_profile: str = "REQUIRES_VALIDATED_GEOMETRY_PROFILE",
    cloud_optics_source: str = "LIBRADTRAN_WATER_MIE_INTERPOLATE",
    phase_function_source: str = "FULL_MIE_PHASE_FUNCTION",
    effective_variance: str = "LIBRADTRAN_MIE_TABLE_PROVENANCE_REQUIRED",
    reference_cloud_base_km: float = 5.0,
    reference_cloud_top_km: float = 6.0,
    maximum_mc_relative_error: float = 0.02,
    maximum_mc_absolute_error: float = 0.01,
) -> dict[str, Any]:
    if int(photons_per_job) <= 0:
        raise ValueError("MYSTIC_PHOTON_COUNT_INVALID")
    if not (float(reference_cloud_top_km) > float(reference_cloud_base_km) >= 0):
        raise ValueError("REFERENCE_CLOUD_VERTICAL_GEOMETRY_INVALID")
    if float(maximum_mc_relative_error) < 0 or float(maximum_mc_absolute_error) < 0:
        raise ValueError("MYSTIC_QC_THRESHOLD_INVALID")
    return {
        "contract": SOLVER_RECIPE_CONTRACT,
        "pipeline_contract": PIPELINE_CONTRACT,
        "solver_adapter_contract": MYSTIC_ADAPTER_CONTRACT,
        "solver_family": "LIBRADTRAN_UVSPEC_MYSTIC",
        "solver_version": str(libRadtran_version),
        "rte_solver": "mystic",
        "spherical_geometry": "mc_spherical 1D",
        "variance_reduction": "mc_vroom",
        "multiple_scattering_enabled": True,
        "photons_per_job": int(photons_per_job),
        "minimum_photon_count": int(photons_per_job),
        "maximum_mc_relative_error": float(maximum_mc_relative_error),
        "maximum_mc_absolute_error": float(maximum_mc_absolute_error),
        "atmosphere_profile": str(atmosphere_profile),
        "cloud_optics_source": str(cloud_optics_source),
        "phase_function_source": str(phase_function_source),
        "effective_variance": str(effective_variance),
        "incident_irradiance_reference": INCIDENT_IRRADIANCE_REFERENCE,
        "atmospheric_coupling": ATMOSPHERIC_COUPLING,
        "surface_boundary": SURFACE_BOUNDARY,
        "calibration_scope": CALIBRATION_SCOPE,
        "reference_cloud_base_km": float(reference_cloud_base_km),
        "reference_cloud_top_km": float(reference_cloud_top_km),
        "source_normalization": INCIDENT_IRRADIANCE_REFERENCE,
        "response_definition": DIRECTIONAL_RESPONSE_DEFINITION,
        "response_units": DIRECTIONAL_RESPONSE_UNITS,
        "geometry_convention": DIRECTIONAL_GEOMETRY_CONVENTION,
        "geometry_mapping": {
            "sza": "solar_zenith_deg",
            "phi0_deg": 0.0,
            "umu": "-cos(view_zenith_deg)",
            "phi_deg": "relative_azimuth_deg",
            "scattering_angle": "DERIVED_DIAGNOSTIC_ONLY",
        },
        "cloud_thickness_role": "NOT_A_PRODUCTION_INTERPOLATION_AXIS_PENDING_SENSITIVITY_VALIDATION",
        "production_execution_state": "EXTERNAL_SOLVER_REQUIRED",
    }


def uvspec_template_text() -> str:
    return """# Taiwan Firecloud PhysicsCore R5.7.23
# Genuine liquid-cloud full-directional calibration template.
# MUST NOT be interpreted as a completed production LUT.
# Each concrete input is rendered by tier2_libradtran_mystic_adapter.py.
# atmosphere_file <VALIDATED_ATMOSPHERE_PROFILE>

rte_solver mystic
mc_spherical 1D
mc_vroom
wc_properties mie interpolate
# cloud-only: no_rayleigh / no_absorption mol / albedo 0 are mandatory in rendered jobs
"""


def build_external_job_table(domain_spec: dict[str, Any], *, solver_recipe: dict[str, Any]) -> pd.DataFrame:
    if str(domain_spec.get("contract", "")) != DOMAIN_CONTRACT:
        raise ValueError("LIQUID_CALIBRATION_DOMAIN_CONTRACT_MISMATCH")
    if list(domain_spec.get("phases", [])) != ["LIQUID"]:
        raise ValueError("R5.7.23_FIRST_PRODUCTION_CALIBRATION_MUST_BE_LIQUID_ONLY")
    if str(solver_recipe.get("contract", "")) != SOLVER_RECIPE_CONTRACT:
        raise ValueError("MYSTIC_SOLVER_RECIPE_CONTRACT_MISMATCH")
    solver = str(solver_recipe.get("solver_family", "")).upper()
    if solver not in DIRECTIONAL_SUPPORTED_SOLVER_FAMILIES:
        raise ValueError("DIRECTIONAL_SOLVER_NOT_FULL_HEMISPHERE_APPROVED")
    jobs = build_directional_calibration_jobs(domain_spec, solver_family=solver)
    jobs = jobs.copy()
    jobs["uvspec_sza_deg"] = jobs["solar_zenith_deg"].astype(float)
    jobs["uvspec_phi0_deg"] = 0.0
    jobs["uvspec_umu"] = jobs["view_zenith_deg"].map(_uvspec_umu_from_cloud_to_observer_view_zenith)
    jobs["uvspec_phi_deg"] = jobs["relative_azimuth_deg"].astype(float)
    jobs["mc_photons"] = int(solver_recipe["photons_per_job"])
    jobs["solver_recipe_contract"] = SOLVER_RECIPE_CONTRACT
    jobs["result_contract"] = RESULT_CONTRACT
    jobs["adapter_contract"] = MYSTIC_ADAPTER_CONTRACT
    jobs["incident_irradiance_reference"] = INCIDENT_IRRADIANCE_REFERENCE
    jobs["atmospheric_coupling"] = ATMOSPHERIC_COUPLING
    jobs["surface_boundary"] = SURFACE_BOUNDARY
    jobs["reference_cloud_base_km"] = float(solver_recipe["reference_cloud_base_km"])
    jobs["reference_cloud_top_km"] = float(solver_recipe["reference_cloud_top_km"])
    jobs["execution_state"] = "PENDING_EXTERNAL_LIBRADTRAN_MYSTIC"
    return jobs


def write_external_calibration_bundle(
    output_dir: str | Path,
    *,
    domain_spec: dict[str, Any],
    solver_recipe: dict[str, Any],
) -> dict[str, Any]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    jobs = build_external_job_table(domain_spec, solver_recipe=solver_recipe)
    jobs_path = out / "tier2_liquid_directional_calibration_jobs.csv"
    domain_path = out / "tier2_liquid_directional_domain_spec.json"
    recipe_path = out / "tier2_libradtran_mystic_solver_recipe.json"
    template_path = out / "uvspec_mystic_spherical_template.inp"
    result_schema_path = out / "tier2_external_results_required_schema.csv"
    manifest_path = out / "tier2_liquid_directional_calibration_bundle_manifest.json"

    jobs_bytes = jobs.to_csv(index=False, lineterminator="\n").encode("utf-8")
    jobs_path.write_bytes(jobs_bytes)
    domain_path.write_text(json.dumps(domain_spec, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    recipe_path.write_text(json.dumps(solver_recipe, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    template_path.write_text(uvspec_template_text(), encoding="utf-8")
    pd.DataFrame(columns=EXTERNAL_RESULT_REQUIRED_COLUMNS).to_csv(result_schema_path, index=False)

    domain_sha256 = canonical_domain_spec_sha256(domain_spec)
    manifest = {
        "contract": PIPELINE_CONTRACT,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "production_lut_state": "NOT_YET_GENERATED_EXTERNAL_RT_REQUIRED",
        "job_count": int(len(jobs)),
        "jobs_sha256": hashlib.sha256(jobs_bytes).hexdigest(),
        "domain_contract": DOMAIN_CONTRACT,
        "solver_recipe_contract": SOLVER_RECIPE_CONTRACT,
        "result_contract": RESULT_CONTRACT,
        "solver_adapter_contract": MYSTIC_ADAPTER_CONTRACT,
        "domain_spec_sha256": domain_sha256,
        "incident_irradiance_reference": INCIDENT_IRRADIANCE_REFERENCE,
        "atmospheric_coupling": ATMOSPHERIC_COUPLING,
        "surface_boundary": SURFACE_BOUNDARY,
        "calibration_contract_after_external_qc": DIRECTIONAL_CALIBRATION_CONTRACT,
        "files": {
            "jobs": jobs_path.name,
            "domain": domain_path.name,
            "solver_recipe": recipe_path.name,
            "uvspec_template": template_path.name,
            "required_result_schema": result_schema_path.name,
        },
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "state": "EXTERNAL_CALIBRATION_JOB_BUNDLE_READY",
        "output_dir": str(out),
        "job_count": int(len(jobs)),
        "jobs_sha256": manifest["jobs_sha256"],
        "manifest_path": str(manifest_path),
        "production_lut_generated": False,
        "pipeline_contract": PIPELINE_CONTRACT,
    }


def validate_external_rt_results(
    jobs: pd.DataFrame,
    results: pd.DataFrame,
    *,
    max_mc_relative_sigma: float = 0.02,
    max_mc_absolute_sigma: float = 0.01,
    minimum_photon_count: int = 1,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if jobs is None or jobs.empty:
        errors.append("CALIBRATION_JOBS_EMPTY")
    if results is None or results.empty:
        errors.append("EXTERNAL_RT_RESULTS_EMPTY")
        return CalibrationResultAudit(
            False, "EXTERNAL_RT_RESULTS_INVALID", tuple(errors), tuple(warnings),
            int(len(jobs)) if jobs is not None else 0, 0, 0, None,
        ).as_dict()
    missing = [c for c in EXTERNAL_RESULT_REQUIRED_COLUMNS if c not in results.columns]
    if missing:
        errors.append("EXTERNAL_RT_RESULTS_MISSING_COLUMNS:" + ",".join(missing))
        return CalibrationResultAudit(
            False, "EXTERNAL_RT_RESULTS_INVALID", tuple(errors), tuple(warnings),
            int(len(jobs)) if jobs is not None else 0, int(len(results)), 0, None,
        ).as_dict()

    r = results.copy()
    if r["job_id"].astype(str).duplicated().any():
        errors.append("EXTERNAL_RT_RESULTS_DUPLICATE_JOB_ID")
    expected = set(jobs["job_id"].astype(str)) if jobs is not None and not jobs.empty else set()
    got = set(r["job_id"].astype(str))
    missing_jobs = expected - got
    extra_jobs = got - expected
    if missing_jobs:
        errors.append(f"EXTERNAL_RT_RESULTS_INCOMPLETE_JOB_SET:{len(missing_jobs)}")
    if extra_jobs:
        errors.append(f"EXTERNAL_RT_RESULTS_UNKNOWN_JOB_SET:{len(extra_jobs)}")

    for c in ("response_factor", "response_factor_std", "mc_absolute_sigma", "mc_relative_sigma", "photon_count", "solver_exit_code"):
        r[c] = pd.to_numeric(r[c], errors="coerce")
    if r[["response_factor", "response_factor_std", "mc_absolute_sigma", "mc_relative_sigma", "photon_count", "solver_exit_code"]].isna().any().any():
        errors.append("EXTERNAL_RT_RESULTS_NON_NUMERIC_OR_MISSING_QC")
    if (r["response_factor"] < 0).any(): errors.append("EXTERNAL_RT_RESULTS_NEGATIVE_RESPONSE")
    if (r[["response_factor_std", "mc_absolute_sigma", "mc_relative_sigma"]] < 0).any().any(): errors.append("EXTERNAL_RT_RESULTS_NEGATIVE_MC_SIGMA")
    max_sigma = float(r["mc_relative_sigma"].max()) if r["mc_relative_sigma"].notna().any() else None
    max_abs = float(r["mc_absolute_sigma"].max()) if r["mc_absolute_sigma"].notna().any() else None
    if max_sigma is not None and max_sigma > float(max_mc_relative_sigma): errors.append("EXTERNAL_RT_RESULTS_MC_CONVERGENCE_FAILED")
    if max_abs is not None and max_abs > float(max_mc_absolute_sigma): errors.append("EXTERNAL_RT_RESULTS_MC_ABSOLUTE_CONVERGENCE_FAILED")
    if (r["photon_count"] < int(minimum_photon_count)).any(): errors.append("EXTERNAL_RT_RESULTS_PHOTON_COUNT_BELOW_MINIMUM")
    if not r["sample_qc_state"].astype(str).str.upper().eq("PASS").all(): errors.append("EXTERNAL_RT_RESULTS_SAMPLE_QC_NOT_PASS")
    if not r["solver_run_id"].astype(str).str.strip().ne("").all(): errors.append("EXTERNAL_RT_RESULTS_SOLVER_RUN_ID_MISSING")
    if not r["adapter_contract"].astype(str).eq(MYSTIC_ADAPTER_CONTRACT).all(): errors.append("EXTERNAL_RT_RESULTS_ADAPTER_CONTRACT_MISMATCH")
    if not r["solver_exit_code"].fillna(-999).eq(0).all():
        errors.append("EXTERNAL_RT_RESULTS_SOLVER_EXIT_NONZERO")
    if not r["result_contract"].astype(str).eq(RESULT_CONTRACT).all():
        errors.append("EXTERNAL_RT_RESULT_CONTRACT_MISMATCH")
    solvers = {str(x).upper() for x in r["solver_family"].astype(str)}
    if len(solvers) != 1 or not solvers.issubset(DIRECTIONAL_SUPPORTED_SOLVER_FAMILIES):
        errors.append("EXTERNAL_RT_RESULTS_SOLVER_FAMILY_INVALID_OR_MIXED")
    versions = {str(x).strip() for x in r["solver_version"].astype(str)}
    if len(versions) != 1 or not next(iter(versions), ""):
        errors.append("EXTERNAL_RT_RESULTS_SOLVER_VERSION_INVALID_OR_MIXED")

    pass_mask = (
        r["response_factor"].ge(0)
        & r["response_factor_std"].ge(0)
        & r["mc_relative_sigma"].between(0, float(max_mc_relative_sigma), inclusive="both")
        & r["mc_absolute_sigma"].between(0, float(max_mc_absolute_sigma), inclusive="both")
        & r["photon_count"].ge(int(minimum_photon_count))
        & r["sample_qc_state"].astype(str).str.upper().eq("PASS")
        & r["solver_exit_code"].eq(0)
        & r["result_contract"].astype(str).eq(RESULT_CONTRACT)
        & r["adapter_contract"].astype(str).eq(MYSTIC_ADAPTER_CONTRACT)
    )
    audit = CalibrationResultAudit(
        ok=not errors,
        state="EXTERNAL_RT_RESULTS_QC_PASS" if not errors else "EXTERNAL_RT_RESULTS_INVALID",
        errors=tuple(errors), warnings=tuple(warnings),
        expected_job_count=int(len(expected)), result_row_count=int(len(r)),
        passed_row_count=int(pass_mask.sum()), max_mc_relative_sigma=max_sigma,
    ).as_dict()
    return audit


def build_production_lut_from_external_results(
    *,
    jobs: pd.DataFrame,
    results: pd.DataFrame,
    metadata: dict[str, Any],
    max_mc_relative_sigma: float = 0.02,
    max_mc_absolute_sigma: float = 0.01,
    minimum_photon_count: int = 1,
    domain_spec: dict[str, Any] | None = None,
) -> tuple[bytes, bytes, dict[str, Any]]:
    """Build a production package only from a complete external RT result set."""
    audit = validate_external_rt_results(
        jobs, results, max_mc_relative_sigma=max_mc_relative_sigma,
        max_mc_absolute_sigma=max_mc_absolute_sigma, minimum_photon_count=minimum_photon_count,
    )
    if not audit.get("ok", False):
        raise ValueError(";".join(audit.get("errors", [])) or "EXTERNAL_RT_RESULTS_QC_FAILED")

    if jobs["phase"].map(_phase).nunique() != 1 or jobs["phase"].map(_phase).iloc[0] != "LIQUID":
        raise ValueError("R5.7.23_PRODUCTION_BUILD_REQUIRES_LIQUID_ONLY_JOB_GRID")

    rcols = ["job_id", "response_factor", "response_factor_std", "photon_count", "sample_qc_state", "solver_run_id"]
    merged = jobs.merge(results[rcols], on="job_id", how="left", validate="one_to_one")
    sample_cols = [
        "phase", "wavelength_nm", "cot", "effective_radius_um",
        "solar_zenith_deg", "view_zenith_deg", "relative_azimuth_deg",
        "response_factor", "response_factor_std", "photon_count", "sample_qc_state", "solver_run_id",
    ]
    samples = merged[sample_cols].copy()

    enriched = dict(metadata)
    enriched.setdefault("calibration_contract", DIRECTIONAL_CALIBRATION_CONTRACT)
    enriched.setdefault("calibration_state", "CALIBRATED")
    enriched.setdefault("qc_state", "PASS")
    enriched.setdefault("solver_family", str(results["solver_family"].iloc[0]).upper())
    enriched.setdefault("solver_version", str(results["solver_version"].iloc[0]))
    enriched.setdefault("multiple_scattering_enabled", True)
    enriched.setdefault("response_definition", DIRECTIONAL_RESPONSE_DEFINITION)
    enriched.setdefault("response_units", DIRECTIONAL_RESPONSE_UNITS)
    enriched.setdefault("geometry_convention", DIRECTIONAL_GEOMETRY_CONVENTION)
    enriched.setdefault("directional_hemisphere_support", "FULL_0_180")
    enriched.setdefault("solver_adapter_contract", MYSTIC_ADAPTER_CONTRACT)
    enriched.setdefault("incident_irradiance_reference", INCIDENT_IRRADIANCE_REFERENCE)
    enriched.setdefault("atmospheric_coupling", ATMOSPHERIC_COUPLING)
    enriched.setdefault("surface_boundary", SURFACE_BOUNDARY)
    enriched.setdefault("reference_cloud_base_km", float(jobs["reference_cloud_base_km"].iloc[0]) if "reference_cloud_base_km" in jobs else 5.0)
    enriched.setdefault("reference_cloud_top_km", float(jobs["reference_cloud_top_km"].iloc[0]) if "reference_cloud_top_km" in jobs else 6.0)
    enriched.setdefault("minimum_photon_count", int(minimum_photon_count))
    enriched.setdefault("maximum_mc_relative_error", float(max_mc_relative_sigma))
    enriched.setdefault("maximum_mc_absolute_error", float(max_mc_absolute_sigma))
    enriched.setdefault("calibration_scope", CALIBRATION_SCOPE)
    if domain_spec is not None:
        enriched.setdefault("domain_spec_sha256", canonical_domain_spec_sha256(domain_spec))
    if not str(enriched.get("domain_spec_sha256", "")).strip():
        raise ValueError("DIRECTIONAL_DOMAIN_SPEC_SHA256_REQUIRED_FOR_PRODUCTION_BUILD")
    enriched["external_result_contract"] = RESULT_CONTRACT
    enriched["calibration_pipeline_contract"] = PIPELINE_CONTRACT
    enriched["max_mc_relative_sigma_observed"] = audit.get("max_mc_relative_sigma")

    csv_bytes, manifest_bytes, package_audit = build_directional_calibration_package(samples, enriched)
    package_audit = dict(package_audit)
    package_audit.update({
        "pipeline_contract": PIPELINE_CONTRACT,
        "external_result_contract": RESULT_CONTRACT,
        "external_result_qc_state": audit.get("state"),
        "max_mc_relative_sigma_observed": audit.get("max_mc_relative_sigma"),
        "synthetic_response_used": False,
    })
    return csv_bytes, manifest_bytes, package_audit
