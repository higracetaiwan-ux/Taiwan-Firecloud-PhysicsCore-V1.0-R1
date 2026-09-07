from __future__ import annotations
"""R5.7.22 full-directional Tier-2 scattering calibration contract.

Production cloud-response LUTs are functions of COT, effective radius and the
full target-local illumination/view geometry (theta0, thetav, Delta-phi).  The
legacy scattering-angle-only contract remains available only for historical
regression and cannot satisfy this production gate.
"""

import hashlib
import itertools
import json
import math
from datetime import datetime, timezone
from typing import Any, Iterable

import pandas as pd

from .contracts import SIX_BAND_WAVELENGTHS_NM

DIRECTIONAL_CALIBRATION_CONTRACT = "R5.7.22_TIER2_DIRECTIONAL_SCATTERING_CALIBRATION_V2"
DIRECTIONAL_RUNTIME_CONTRACT = "R5.7.22_TIER2_DIRECTIONAL_SCATTERING_LUT_RUNTIME_V2"
DIRECTIONAL_RESPONSE_DEFINITION = "TARGET_RADIANCE_PER_UNIT_CLOUD_BASE_INCIDENT_IRRADIANCE"
DIRECTIONAL_RESPONSE_UNITS = "SR^-1"
DIRECTIONAL_GEOMETRY_CONVENTION = "TARGET_LOCAL_ENU_THETA0_THETAV_DELTAPHI_SCATTER_DIAGNOSTIC_V1"
DIRECTIONAL_INTERPOLATION_AXES = [
    "cot", "effective_radius_um", "solar_zenith_deg", "view_zenith_deg", "relative_azimuth_deg"
]

# For the Firecloud geometry theta0/thetav may exceed 90 deg.  Ordinary
# top-of-atmosphere plane-parallel reflection tables are therefore not enough.
DIRECTIONAL_SUPPORTED_SOLVER_FAMILIES = {
    "LIBRADTRAN_UVSPEC_MYSTIC",
    "MONTE_CARLO_VALIDATED_EXTERNAL",
    "SPHERICAL_RT_VALIDATED_EXTERNAL",
}

DIRECTIONAL_LUT_REQUIRED_COLUMNS = [
    "phase", "wavelength_nm", "cot", "effective_radius_um",
    "solar_zenith_deg", "view_zenith_deg", "relative_azimuth_deg",
    "response_factor", "calibration_state", "lut_version",
]

DIRECTIONAL_CALIBRATION_REQUIRED_FIELDS = [
    "calibration_contract", "calibration_state", "calibration_id",
    "calibration_source", "calibration_date", "qc_state", "solver_family",
    "solver_version", "cloud_optics_source", "phase_function_source",
    "multiple_scattering_enabled", "response_definition", "response_units",
    "geometry_convention", "validation_reference", "directional_hemisphere_support",
]

DIRECTIONAL_CALIBRATION_JOB_COLUMNS = [
    "job_id", "phase", "wavelength_nm", "cot", "effective_radius_um",
    "solar_zenith_deg", "view_zenith_deg", "relative_azimuth_deg",
    "scattering_angle_deg_diagnostic", "solver_family", "response_definition",
    "response_units", "geometry_convention", "calibration_state",
]


def _phase(v: Any) -> str:
    p = str(v or "").strip().upper()
    return "LIQUID" if p == "WATER" else p


def _bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in {"1", "true", "yes", "y"}


def directional_scattering_angle_from_angles_deg(theta0_deg: float, thetav_deg: float, relative_azimuth_deg: float) -> float:
    """Derived 0-forward/180-backward scattering angle from full geometry."""
    t0 = math.radians(float(theta0_deg))
    tv = math.radians(float(thetav_deg))
    dp = math.radians(float(relative_azimuth_deg))
    sun_view_dot = math.cos(t0) * math.cos(tv) + math.sin(t0) * math.sin(tv) * math.cos(dp)
    c = max(-1.0, min(1.0, -sun_view_dot))
    return float(math.degrees(math.acos(c)))


def validate_directional_scattering_lut(df: pd.DataFrame | None) -> dict[str, Any]:
    if df is None or df.empty:
        return {"valid": False, "state": "DIRECTIONAL_LUT_MISSING", "reason": "EMPTY_LUT"}
    missing = [c for c in DIRECTIONAL_LUT_REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        legacy_markers = {"scattering_angle_deg", "cloud_thickness_km"}
        if legacy_markers.issubset(set(df.columns)):
            return {
                "valid": False,
                "state": "LEGACY_SCATTERING_ANGLE_LUT_NOT_DIRECTIONAL",
                "reason": "R5.7.22_REQUIRES_THETA0_THETAV_DELTAPHI",
            }
        return {"valid": False, "state": "DIRECTIONAL_LUT_SCHEMA_INVALID", "reason": "MISSING_COLUMNS:" + ",".join(missing)}
    q = df.copy()
    nums = [
        "wavelength_nm", "cot", "effective_radius_um", "solar_zenith_deg",
        "view_zenith_deg", "relative_azimuth_deg", "response_factor",
    ]
    for c in nums:
        q[c] = pd.to_numeric(q[c], errors="coerce")
    if q[nums].isna().any().any():
        return {"valid": False, "state": "DIRECTIONAL_LUT_NUMERIC_INVALID", "reason": "NON_NUMERIC_OR_NONFINITE"}
    if not q["wavelength_nm"].isin(list(SIX_BAND_WAVELENGTHS_NM)).all():
        return {"valid": False, "state": "DIRECTIONAL_LUT_WAVELENGTH_INVALID", "reason": "OUTSIDE_FROZEN_SIX_BANDS"}
    if set(map(int, SIX_BAND_WAVELENGTHS_NM)) - set(q["wavelength_nm"].astype(int).unique()):
        return {"valid": False, "state": "DIRECTIONAL_LUT_WAVELENGTH_INCOMPLETE", "reason": "MISSING_REQUIRED_WAVELENGTH"}
    if (q["cot"] < 0).any() or (q["effective_radius_um"] <= 0).any():
        return {"valid": False, "state": "DIRECTIONAL_LUT_DOMAIN_INVALID", "reason": "NONPHYSICAL_COT_OR_REFF"}
    if ((q["solar_zenith_deg"] < 0) | (q["solar_zenith_deg"] > 180)).any():
        return {"valid": False, "state": "DIRECTIONAL_LUT_DOMAIN_INVALID", "reason": "SOLAR_ZENITH_OUT_OF_RANGE"}
    if ((q["view_zenith_deg"] < 0) | (q["view_zenith_deg"] > 180)).any():
        return {"valid": False, "state": "DIRECTIONAL_LUT_DOMAIN_INVALID", "reason": "VIEW_ZENITH_OUT_OF_RANGE"}
    if ((q["relative_azimuth_deg"] < 0) | (q["relative_azimuth_deg"] > 180)).any():
        return {"valid": False, "state": "DIRECTIONAL_LUT_DOMAIN_INVALID", "reason": "RELATIVE_AZIMUTH_OUT_OF_RANGE"}
    if (q["response_factor"] < 0).any():
        return {"valid": False, "state": "DIRECTIONAL_LUT_RESPONSE_INVALID", "reason": "NEGATIVE_RESPONSE_FACTOR"}
    if not q["calibration_state"].astype(str).str.upper().eq("CALIBRATED").all():
        return {"valid": False, "state": "DIRECTIONAL_LUT_NOT_CALIBRATED", "reason": "CALIBRATION_STATE_NOT_CALIBRATED"}
    phases = {_phase(x) for x in q["phase"]}
    if not phases or not phases.issubset({"LIQUID", "ICE", "MIXED"}):
        return {"valid": False, "state": "DIRECTIONAL_LUT_PHASE_INVALID", "reason": "UNSUPPORTED_PHASE"}
    versions = sorted(set(q["lut_version"].astype(str)))
    if len(versions) != 1:
        return {"valid": False, "state": "DIRECTIONAL_LUT_VERSION_MIXED", "reason": "MULTIPLE_LUT_VERSIONS"}
    coord_cols = ["phase", "wavelength_nm", *DIRECTIONAL_INTERPOLATION_AXES]
    if q.duplicated(coord_cols).any():
        return {"valid": False, "state": "DIRECTIONAL_LUT_COORDINATE_DUPLICATE", "reason": "DUPLICATE_GRID_COORDINATES"}
    return {
        "valid": True,
        "state": "CALIBRATED_DIRECTIONAL_LUT_SCHEMA_READY",
        "reason": "OK",
        "lut_version": versions[0],
        "row_count": int(len(q)),
        "geometry_convention": DIRECTIONAL_GEOMETRY_CONVENTION,
    }


def validate_directional_calibration_metadata(meta: dict[str, Any] | None) -> dict[str, Any]:
    meta = dict(meta or {})
    errors: list[str] = []
    missing = [k for k in DIRECTIONAL_CALIBRATION_REQUIRED_FIELDS if k not in meta]
    if missing:
        errors.append("DIRECTIONAL_CALIBRATION_METADATA_MISSING_FIELDS:" + ",".join(missing))
    if str(meta.get("calibration_contract", "")) != DIRECTIONAL_CALIBRATION_CONTRACT:
        errors.append("DIRECTIONAL_CALIBRATION_CONTRACT_MISMATCH")
    if str(meta.get("calibration_state", "")).upper() != "CALIBRATED":
        errors.append("DIRECTIONAL_CALIBRATION_STATE_NOT_CALIBRATED")
    if str(meta.get("qc_state", "")).upper() != "PASS":
        errors.append("DIRECTIONAL_CALIBRATION_QC_NOT_PASS")
    solver = str(meta.get("solver_family", "")).upper()
    if solver not in DIRECTIONAL_SUPPORTED_SOLVER_FAMILIES:
        errors.append("DIRECTIONAL_SOLVER_NOT_FULL_HEMISPHERE_APPROVED")
    if not str(meta.get("solver_version", "")).strip():
        errors.append("DIRECTIONAL_SOLVER_VERSION_MISSING")
    if not str(meta.get("cloud_optics_source", "")).strip():
        errors.append("DIRECTIONAL_CLOUD_OPTICS_SOURCE_MISSING")
    if not str(meta.get("phase_function_source", "")).strip():
        errors.append("DIRECTIONAL_PHASE_FUNCTION_SOURCE_MISSING")
    if not _bool(meta.get("multiple_scattering_enabled", False)):
        errors.append("DIRECTIONAL_MULTIPLE_SCATTERING_REQUIRED")
    if str(meta.get("response_definition", "")) != DIRECTIONAL_RESPONSE_DEFINITION:
        errors.append("DIRECTIONAL_RESPONSE_DEFINITION_MISMATCH")
    if str(meta.get("response_units", "")).upper() != DIRECTIONAL_RESPONSE_UNITS.upper():
        errors.append("DIRECTIONAL_RESPONSE_UNITS_MISMATCH")
    if str(meta.get("geometry_convention", "")) != DIRECTIONAL_GEOMETRY_CONVENTION:
        errors.append("DIRECTIONAL_GEOMETRY_CONVENTION_MISMATCH")
    if str(meta.get("directional_hemisphere_support", "")).upper() != "FULL_0_180":
        errors.append("DIRECTIONAL_FULL_HEMISPHERE_SUPPORT_REQUIRED")
    for k in ("calibration_id", "calibration_source", "calibration_date", "validation_reference"):
        if not str(meta.get(k, "")).strip():
            errors.append("DIRECTIONAL_CALIBRATION_EMPTY_" + k.upper())
    src = str(meta.get("calibration_source", "")).upper()
    if any(x in src for x in ("SYNTHETIC", "REGRESSION_ONLY", "PLACEHOLDER", "DUMMY")):
        errors.append("DIRECTIONAL_SYNTHETIC_SOURCE_NOT_PRODUCTION_ELIGIBLE")
    return {
        "ok": not errors,
        "state": "PRODUCTION_DIRECTIONAL_CALIBRATION_READY" if not errors else "DIRECTIONAL_CALIBRATION_METADATA_INVALID",
        "errors": errors,
        "warnings": [],
        "calibration_contract": DIRECTIONAL_CALIBRATION_CONTRACT,
        "solver_family": solver,
    }


def _grid_values(spec: dict[str, Any], key: str) -> list[float]:
    vals = spec.get(key, [])
    if not isinstance(vals, (list, tuple)) or not vals:
        raise ValueError(f"GRID_AXIS_EMPTY:{key}")
    return sorted({float(x) for x in vals})


def build_directional_calibration_jobs(grid_spec: dict[str, Any], *, solver_family: str) -> pd.DataFrame:
    solver = str(solver_family or "").upper()
    if solver not in DIRECTIONAL_SUPPORTED_SOLVER_FAMILIES:
        raise ValueError("DIRECTIONAL_SOLVER_NOT_FULL_HEMISPHERE_APPROVED")
    phases = [_phase(x) for x in grid_spec.get("phases", [])]
    if not phases or any(p not in {"LIQUID", "ICE", "MIXED"} for p in phases):
        raise ValueError("GRID_PHASES_INVALID")
    wls = [int(x) for x in grid_spec.get("wavelengths_nm", list(SIX_BAND_WAVELENGTHS_NM))]
    if sorted(set(wls)) != sorted(int(x) for x in SIX_BAND_WAVELENGTHS_NM):
        raise ValueError("GRID_WAVELENGTHS_MUST_MATCH_FROZEN_SIX_BANDS")
    cot = _grid_values(grid_spec, "cot")
    reff = _grid_values(grid_spec, "effective_radius_um")
    theta0 = _grid_values(grid_spec, "solar_zenith_deg")
    thetav = _grid_values(grid_spec, "view_zenith_deg")
    relaz = _grid_values(grid_spec, "relative_azimuth_deg")
    rows = []
    for i, (p, wl, c, r, t0, tv, daz) in enumerate(itertools.product(phases, wls, cot, reff, theta0, thetav, relaz), start=1):
        rows.append({
            "job_id": f"T2DIR-{i:09d}", "phase": p, "wavelength_nm": int(wl),
            "cot": float(c), "effective_radius_um": float(r),
            "solar_zenith_deg": float(t0), "view_zenith_deg": float(tv),
            "relative_azimuth_deg": float(daz),
            "scattering_angle_deg_diagnostic": directional_scattering_angle_from_angles_deg(t0, tv, daz),
            "solver_family": solver, "response_definition": DIRECTIONAL_RESPONSE_DEFINITION,
            "response_units": DIRECTIONAL_RESPONSE_UNITS,
            "geometry_convention": DIRECTIONAL_GEOMETRY_CONVENTION,
            "calibration_state": "PENDING_EXTERNAL_RT",
        })
    return pd.DataFrame(rows, columns=DIRECTIONAL_CALIBRATION_JOB_COLUMNS)


def _assert_complete_directional_tensor(df: pd.DataFrame, phases: Iterable[str]) -> None:
    q = df.copy()
    q["phase"] = q["phase"].map(_phase)
    for phase in phases:
        p = q[q["phase"] == _phase(phase)]
        if p.empty:
            raise ValueError(f"DIRECTIONAL_CALIBRATION_PHASE_GRID_EMPTY:{phase}")
        for wl in SIX_BAND_WAVELENGTHS_NM:
            g = p[p["wavelength_nm"].astype(int) == int(wl)]
            if g.empty:
                raise ValueError(f"DIRECTIONAL_CALIBRATION_WAVELENGTH_GRID_EMPTY:{phase}:{int(wl)}")
            axes = [sorted(set(pd.to_numeric(g[c], errors="coerce").dropna().astype(float))) for c in DIRECTIONAL_INTERPOLATION_AXES]
            expected = math.prod(len(axis) for axis in axes)
            if len(g) != expected:
                raise ValueError(f"DIRECTIONAL_CALIBRATION_TENSOR_GRID_INCOMPLETE:{phase}:{int(wl)}:{len(g)}/{expected}")


def build_directional_calibration_package(
    samples: pd.DataFrame,
    metadata: dict[str, Any],
) -> tuple[bytes, bytes, dict[str, Any]]:
    ma = validate_directional_calibration_metadata(metadata)
    if not ma["ok"]:
        raise ValueError(";".join(ma["errors"]))
    if samples is None or samples.empty:
        raise ValueError("DIRECTIONAL_CALIBRATION_SAMPLES_EMPTY")
    q = samples.copy()
    missing = [c for c in ["phase", "wavelength_nm", *DIRECTIONAL_INTERPOLATION_AXES, "response_factor"] if c not in q.columns]
    if missing:
        raise ValueError("DIRECTIONAL_CALIBRATION_SAMPLES_MISSING_COLUMNS:" + ",".join(missing))
    q["phase"] = q["phase"].map(_phase)
    q["calibration_state"] = "CALIBRATED"
    q["lut_version"] = str(metadata.get("lut_version", "")).strip()
    if not q["lut_version"].iloc[0]:
        raise ValueError("DIRECTIONAL_CALIBRATION_LUT_VERSION_MISSING")
    q = q[DIRECTIONAL_LUT_REQUIRED_COLUMNS].copy()
    base = validate_directional_scattering_lut(q)
    if not base.get("valid", False):
        raise ValueError("DIRECTIONAL_LUT_SCHEMA_INVALID:" + str(base.get("reason", base.get("state"))))
    phases = sorted(set(q["phase"].astype(str)))
    _assert_complete_directional_tensor(q, phases)
    csv_bytes = q.to_csv(index=False, lineterminator="\n").encode("utf-8")
    manifest = {
        "contract": DIRECTIONAL_RUNTIME_CONTRACT,
        "lut_version": str(metadata["lut_version"]),
        "calibration_state": "CALIBRATED",
        "calibration_id": str(metadata["calibration_id"]),
        "calibration_source": str(metadata["calibration_source"]),
        "calibration_date": str(metadata["calibration_date"]),
        "required_wavelengths_nm": [int(x) for x in SIX_BAND_WAVELENGTHS_NM],
        "supported_phases": phases,
        "csv_sha256": hashlib.sha256(csv_bytes).hexdigest(),
        "calibration_contract": DIRECTIONAL_CALIBRATION_CONTRACT,
        "qc_state": "PASS",
        "solver_family": str(metadata["solver_family"]).upper(),
        "solver_version": str(metadata["solver_version"]),
        "cloud_optics_source": str(metadata["cloud_optics_source"]),
        "phase_function_source": str(metadata["phase_function_source"]),
        "multiple_scattering_enabled": True,
        "response_definition": DIRECTIONAL_RESPONSE_DEFINITION,
        "response_units": DIRECTIONAL_RESPONSE_UNITS,
        "geometry_convention": DIRECTIONAL_GEOMETRY_CONVENTION,
        "directional_hemisphere_support": "FULL_0_180",
        "interpolation_axes": list(DIRECTIONAL_INTERPOLATION_AXES),
        "scattering_angle_role": "DERIVED_DIAGNOSTIC_NOT_INTERPOLATION_AXIS",
        "cloud_thickness_role": "TARGET_GEOMETRY_EVIDENCE_NOT_LUT_INTERPOLATION_AXIS",
        "validation_reference": str(metadata["validation_reference"]),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    audit = {
        "ok": True, "state": "PRODUCTION_DIRECTIONAL_CALIBRATION_PACKAGE_READY",
        "rows": int(len(q)), "lut_version": manifest["lut_version"],
        "calibration_id": manifest["calibration_id"], "csv_sha256": manifest["csv_sha256"],
        "supported_phases": "/".join(phases), "calibration_contract": DIRECTIONAL_CALIBRATION_CONTRACT,
    }
    return csv_bytes, manifest_bytes, audit
