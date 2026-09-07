from __future__ import annotations
"""R5.7.20 Tier-2 scattering calibration package contract.

This module does not synthesize cloud scattering physics.  It converts externally
computed, physically calibrated radiative-transfer samples into the exact CSV +
manifest package consumed by the PhysicsCore runtime, and it emits explicit job
specifications for an external RT solver.

The production contract intentionally distinguishes:
- schema-valid LUT (R5.7.19 ingestion), from
- solver-eligible calibrated LUT (R5.7.20 physical provenance + QC).
"""

import hashlib
import itertools
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

import pandas as pd

from .contracts import SIX_BAND_WAVELENGTHS_NM
from .tier2_scattering_foundation import SCATTERING_LUT_REQUIRED_COLUMNS, validate_scattering_lut

CALIBRATION_CONTRACT = "R5.7.20_TIER2_SCATTERING_CALIBRATION_V1"
RESPONSE_DEFINITION = "TARGET_RADIANCE_PER_UNIT_CLOUD_BASE_INCIDENT_IRRADIANCE"
RESPONSE_UNITS = "SR^-1"
GEOMETRY_CONVENTION = "SCATTERING_ANGLE_0_FORWARD_180_BACKWARD"

# The framework is solver-agnostic, but production calibration must identify a
# physically based RT solver.  Synthetic/regression generators are deliberately
# excluded from this allow-list.
SUPPORTED_SOLVER_FAMILIES = {
    "LIBRADTRAN_UVSPEC_DISORT",
    "LIBRADTRAN_UVSPEC_MYSTIC",
    "DISORT_VALIDATED_EXTERNAL",
    "MONTE_CARLO_VALIDATED_EXTERNAL",
}

CALIBRATION_REQUIRED_FIELDS = [
    "calibration_contract",
    "calibration_state",
    "calibration_id",
    "calibration_source",
    "calibration_date",
    "qc_state",
    "solver_family",
    "solver_version",
    "cloud_optics_source",
    "phase_function_source",
    "multiple_scattering_enabled",
    "response_definition",
    "response_units",
    "geometry_convention",
    "validation_reference",
]

CALIBRATION_JOB_COLUMNS = [
    "job_id", "phase", "wavelength_nm", "cot", "effective_radius_um",
    "cloud_thickness_km", "scattering_angle_deg", "solver_family",
    "response_definition", "response_units", "geometry_convention",
    "calibration_state",
]


def _phase(v: Any) -> str:
    p = str(v or "").strip().upper()
    return "LIQUID" if p == "WATER" else p


def _bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in {"1", "true", "yes", "y"}


def validate_calibration_metadata(meta: dict[str, Any] | None) -> dict[str, Any]:
    meta = dict(meta or {})
    errors: list[str] = []
    warnings: list[str] = []
    missing = [k for k in CALIBRATION_REQUIRED_FIELDS if k not in meta]
    if missing:
        errors.append("CALIBRATION_METADATA_MISSING_FIELDS:" + ",".join(missing))
    if str(meta.get("calibration_contract", "")) != CALIBRATION_CONTRACT:
        errors.append("CALIBRATION_CONTRACT_MISMATCH")
    if str(meta.get("calibration_state", "")).upper() != "CALIBRATED":
        errors.append("CALIBRATION_STATE_NOT_CALIBRATED")
    if str(meta.get("qc_state", "")).upper() != "PASS":
        errors.append("CALIBRATION_QC_NOT_PASS")
    solver = str(meta.get("solver_family", "")).upper()
    if solver not in SUPPORTED_SOLVER_FAMILIES:
        errors.append("CALIBRATION_SOLVER_FAMILY_NOT_PRODUCTION_APPROVED")
    if not str(meta.get("solver_version", "")).strip():
        errors.append("CALIBRATION_SOLVER_VERSION_MISSING")
    if not str(meta.get("cloud_optics_source", "")).strip():
        errors.append("CALIBRATION_CLOUD_OPTICS_SOURCE_MISSING")
    if not str(meta.get("phase_function_source", "")).strip():
        errors.append("CALIBRATION_PHASE_FUNCTION_SOURCE_MISSING")
    if not _bool(meta.get("multiple_scattering_enabled", False)):
        errors.append("CALIBRATION_MULTIPLE_SCATTERING_REQUIRED")
    if str(meta.get("response_definition", "")) != RESPONSE_DEFINITION:
        errors.append("CALIBRATION_RESPONSE_DEFINITION_MISMATCH")
    if str(meta.get("response_units", "")).upper() != RESPONSE_UNITS.upper():
        errors.append("CALIBRATION_RESPONSE_UNITS_MISMATCH")
    if str(meta.get("geometry_convention", "")) != GEOMETRY_CONVENTION:
        errors.append("CALIBRATION_GEOMETRY_CONVENTION_MISMATCH")
    for k in ("calibration_id", "calibration_source", "calibration_date", "validation_reference"):
        if not str(meta.get(k, "")).strip():
            errors.append("CALIBRATION_EMPTY_" + k.upper())
    src = str(meta.get("calibration_source", "")).upper()
    if any(x in src for x in ("SYNTHETIC", "REGRESSION_ONLY", "PLACEHOLDER", "DUMMY")):
        errors.append("CALIBRATION_SYNTHETIC_SOURCE_NOT_PRODUCTION_ELIGIBLE")
    return {
        "ok": not errors,
        "state": "PRODUCTION_CALIBRATION_READY" if not errors else "CALIBRATION_METADATA_INVALID",
        "errors": errors,
        "warnings": warnings,
        "calibration_contract": CALIBRATION_CONTRACT,
        "solver_family": solver,
    }


def _grid_values(spec: dict[str, Any], key: str) -> list[float]:
    vals = spec.get(key, [])
    if not isinstance(vals, (list, tuple)) or not vals:
        raise ValueError(f"GRID_AXIS_EMPTY:{key}")
    out = sorted({float(x) for x in vals})
    return out


def build_calibration_jobs(grid_spec: dict[str, Any], *, solver_family: str) -> pd.DataFrame:
    """Emit explicit external-RT jobs; no response values are fabricated."""
    solver = str(solver_family or "").upper()
    if solver not in SUPPORTED_SOLVER_FAMILIES:
        raise ValueError("SOLVER_FAMILY_NOT_PRODUCTION_APPROVED")
    phases = [_phase(x) for x in grid_spec.get("phases", [])]
    if not phases or any(p not in {"LIQUID", "ICE", "MIXED"} for p in phases):
        raise ValueError("GRID_PHASES_INVALID")
    wls = [int(x) for x in grid_spec.get("wavelengths_nm", list(SIX_BAND_WAVELENGTHS_NM))]
    if sorted(set(wls)) != sorted(int(x) for x in SIX_BAND_WAVELENGTHS_NM):
        raise ValueError("GRID_WAVELENGTHS_MUST_MATCH_FROZEN_SIX_BANDS")
    cot = _grid_values(grid_spec, "cot")
    reff = _grid_values(grid_spec, "effective_radius_um")
    thick = _grid_values(grid_spec, "cloud_thickness_km")
    angle = _grid_values(grid_spec, "scattering_angle_deg")
    rows = []
    i = 0
    for p, wl, c, r, h, a in itertools.product(phases, wls, cot, reff, thick, angle):
        i += 1
        rows.append({
            "job_id": f"T2SCAT-{i:08d}", "phase": p, "wavelength_nm": int(wl),
            "cot": float(c), "effective_radius_um": float(r),
            "cloud_thickness_km": float(h), "scattering_angle_deg": float(a),
            "solver_family": solver, "response_definition": RESPONSE_DEFINITION,
            "response_units": RESPONSE_UNITS, "geometry_convention": GEOMETRY_CONVENTION,
            "calibration_state": "PENDING_EXTERNAL_RT",
        })
    return pd.DataFrame(rows, columns=CALIBRATION_JOB_COLUMNS)


def _assert_complete_tensor_grid(df: pd.DataFrame, supported_phases: Iterable[str]) -> None:
    """Production package must be a complete Cartesian tensor per phase × band."""
    q = df.copy()
    q["phase"] = q["phase"].map(_phase)
    for phase in supported_phases:
        p = q[q["phase"] == _phase(phase)]
        if p.empty:
            raise ValueError(f"CALIBRATION_PHASE_GRID_EMPTY:{phase}")
        for wl in SIX_BAND_WAVELENGTHS_NM:
            g = p[p["wavelength_nm"].astype(int) == int(wl)]
            if g.empty:
                raise ValueError(f"CALIBRATION_WAVELENGTH_GRID_EMPTY:{phase}:{int(wl)}")
            axes = [
                sorted(set(pd.to_numeric(g[c], errors="coerce").dropna().astype(float)))
                for c in ("cot", "effective_radius_um", "cloud_thickness_km", "scattering_angle_deg")
            ]
            expected = 1
            for axis in axes:
                expected *= len(axis)
            if len(g) != expected:
                raise ValueError(f"CALIBRATION_TENSOR_GRID_INCOMPLETE:{phase}:{int(wl)}:{len(g)}/{expected}")


def build_calibration_package(
    samples: pd.DataFrame,
    metadata: dict[str, Any],
    *,
    runtime_contract: str = "R5.7.19_TIER2_SCATTERING_LUT_RUNTIME_V1",
) -> tuple[bytes, bytes, dict[str, Any]]:
    """Build a production-installable CSV + manifest from external RT samples.

    No calibration claim is inferred by this function.  The caller must provide
    explicit production metadata and samples already containing physically
    derived response_factor values.
    """
    ma = validate_calibration_metadata(metadata)
    if not ma["ok"]:
        raise ValueError(";".join(ma["errors"]))
    if samples is None or samples.empty:
        raise ValueError("CALIBRATION_SAMPLES_EMPTY")
    q = samples.copy()
    required_coords = [
        "phase", "wavelength_nm", "cot", "effective_radius_um",
        "cloud_thickness_km", "scattering_angle_deg", "response_factor",
    ]
    missing = [c for c in required_coords if c not in q.columns]
    if missing:
        raise ValueError("CALIBRATION_SAMPLES_MISSING_COLUMNS:" + ",".join(missing))
    q["phase"] = q["phase"].map(_phase)
    q["calibration_state"] = "CALIBRATED"
    q["lut_version"] = str(metadata.get("lut_version", "")).strip()
    if not q["lut_version"].iloc[0]:
        raise ValueError("CALIBRATION_LUT_VERSION_MISSING")
    q = q[SCATTERING_LUT_REQUIRED_COLUMNS].copy()
    base = validate_scattering_lut(q)
    if not base.get("valid", False):
        raise ValueError("CALIBRATION_LUT_SCHEMA_INVALID:" + str(base.get("reason", base.get("state"))))
    phases = sorted(set(q["phase"].astype(str)))
    _assert_complete_tensor_grid(q, phases)
    csv_bytes = q.to_csv(index=False, lineterminator="\n").encode("utf-8")
    manifest = {
        "contract": runtime_contract,
        "lut_version": str(metadata["lut_version"]),
        "calibration_state": "CALIBRATED",
        "calibration_id": str(metadata["calibration_id"]),
        "calibration_source": str(metadata["calibration_source"]),
        "calibration_date": str(metadata["calibration_date"]),
        "required_wavelengths_nm": [int(x) for x in SIX_BAND_WAVELENGTHS_NM],
        "supported_phases": phases,
        "csv_sha256": hashlib.sha256(csv_bytes).hexdigest(),
        "calibration_contract": CALIBRATION_CONTRACT,
        "qc_state": "PASS",
        "solver_family": str(metadata["solver_family"]).upper(),
        "solver_version": str(metadata["solver_version"]),
        "cloud_optics_source": str(metadata["cloud_optics_source"]),
        "phase_function_source": str(metadata["phase_function_source"]),
        "multiple_scattering_enabled": True,
        "response_definition": RESPONSE_DEFINITION,
        "response_units": RESPONSE_UNITS,
        "geometry_convention": GEOMETRY_CONVENTION,
        "validation_reference": str(metadata["validation_reference"]),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    audit = {
        "ok": True, "state": "PRODUCTION_CALIBRATION_PACKAGE_READY",
        "rows": int(len(q)), "lut_version": manifest["lut_version"],
        "calibration_id": manifest["calibration_id"], "csv_sha256": manifest["csv_sha256"],
        "supported_phases": "/".join(phases), "calibration_contract": CALIBRATION_CONTRACT,
    }
    return csv_bytes, manifest_bytes, audit
