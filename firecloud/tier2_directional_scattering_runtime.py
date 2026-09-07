from __future__ import annotations
"""R5.7.22 production runtime for full-directional Tier-2 cloud-scattering LUTs."""

import hashlib
import io
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd

from .contracts import SIX_BAND_WAVELENGTHS_NM
from .tier2_directional_scattering_calibration import (
    DIRECTIONAL_RUNTIME_CONTRACT,
    DIRECTIONAL_CALIBRATION_CONTRACT,
    DIRECTIONAL_GEOMETRY_CONVENTION,
    DIRECTIONAL_INTERPOLATION_AXES,
    validate_directional_scattering_lut,
    validate_directional_calibration_metadata,
)

LUT_FILENAME = "tier2_directional_scattering_lut.csv"
MANIFEST_FILENAME = "tier2_directional_scattering_lut_manifest.json"
SUPPORTED_PHASES = {"LIQUID", "ICE", "MIXED"}
MANIFEST_REQUIRED_FIELDS = [
    "contract", "lut_version", "calibration_state", "calibration_id",
    "calibration_source", "calibration_date", "required_wavelengths_nm",
    "supported_phases", "csv_sha256", "calibration_contract", "qc_state",
    "solver_family", "solver_version", "cloud_optics_source", "phase_function_source",
    "multiple_scattering_enabled", "response_definition", "response_units",
    "geometry_convention", "directional_hemisphere_support", "interpolation_axes",
    "validation_reference",
]


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_runtime_dir() -> Path:
    return _root() / "tier2_directional_scattering_runtime"


def resolve_directional_lut_paths() -> tuple[Path, Path, str]:
    csv_env = os.environ.get("FIRECLOUD_TIER2_DIRECTIONAL_SCATTERING_LUT_PATH", "").strip()
    man_env = os.environ.get("FIRECLOUD_TIER2_DIRECTIONAL_SCATTERING_LUT_MANIFEST_PATH", "").strip()
    if csv_env:
        csv_path = Path(csv_env).expanduser()
        manifest_path = Path(man_env).expanduser() if man_env else csv_path.with_name(MANIFEST_FILENAME)
        return csv_path, manifest_path, "env:FIRECLOUD_TIER2_DIRECTIONAL_SCATTERING_LUT_PATH"
    runtime = default_runtime_dir()
    return runtime / LUT_FILENAME, runtime / MANIFEST_FILENAME, "packaged_directional_runtime"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _phase(v: Any) -> str:
    p = str(v or "").strip().upper()
    return "LIQUID" if p == "WATER" else p


def validate_directional_lut_bytes(csv_bytes: bytes, manifest_bytes: bytes | None) -> dict[str, Any]:
    audit: dict[str, Any] = {
        "ok": False, "state": "DIRECTIONAL_LUT_RUNTIME_INVALID", "errors": [], "warnings": [],
        "rows": 0, "lut_version": "", "calibration_id": "", "csv_sha256": _sha256(csv_bytes or b""),
        "runtime_contract": DIRECTIONAL_RUNTIME_CONTRACT, "solver_eligible": False,
        "production_calibration_state": "NOT_EVALUATED", "geometry_convention": DIRECTIONAL_GEOMETRY_CONVENTION,
    }
    if not csv_bytes:
        audit["errors"].append("DIRECTIONAL_LUT_CSV_EMPTY")
        return audit
    if not manifest_bytes:
        audit["errors"].append("DIRECTIONAL_LUT_MANIFEST_REQUIRED")
        return audit
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except Exception as exc:
        audit["errors"].append(f"DIRECTIONAL_LUT_MANIFEST_JSON_INVALID:{type(exc).__name__}")
        return audit
    missing = [k for k in MANIFEST_REQUIRED_FIELDS if k not in manifest]
    if missing:
        audit["errors"].append("DIRECTIONAL_LUT_MANIFEST_MISSING_FIELDS:" + ",".join(missing))
        return audit
    if str(manifest.get("contract")) != DIRECTIONAL_RUNTIME_CONTRACT:
        audit["errors"].append("DIRECTIONAL_LUT_RUNTIME_CONTRACT_MISMATCH")
    if str(manifest.get("calibration_contract")) != DIRECTIONAL_CALIBRATION_CONTRACT:
        audit["errors"].append("DIRECTIONAL_LUT_CALIBRATION_CONTRACT_MISMATCH")
    if str(manifest.get("geometry_convention")) != DIRECTIONAL_GEOMETRY_CONVENTION:
        audit["errors"].append("DIRECTIONAL_LUT_GEOMETRY_CONVENTION_MISMATCH")
    if list(manifest.get("interpolation_axes", [])) != list(DIRECTIONAL_INTERPOLATION_AXES):
        audit["errors"].append("DIRECTIONAL_LUT_INTERPOLATION_AXES_MISMATCH")
    try:
        wls = sorted(int(x) for x in manifest.get("required_wavelengths_nm", []))
    except Exception:
        wls = []
    if wls != sorted(int(x) for x in SIX_BAND_WAVELENGTHS_NM):
        audit["errors"].append("DIRECTIONAL_LUT_WAVELENGTH_CONTRACT_MISMATCH")
    phases = {_phase(x) for x in manifest.get("supported_phases", [])}
    if not phases or not phases.issubset(SUPPORTED_PHASES):
        audit["errors"].append("DIRECTIONAL_LUT_PHASE_CONTRACT_INVALID")
    if str(manifest.get("csv_sha256", "")).lower() != audit["csv_sha256"]:
        audit["errors"].append("DIRECTIONAL_LUT_CSV_SHA256_MISMATCH")
    try:
        df = pd.read_csv(io.BytesIO(csv_bytes))
    except Exception as exc:
        audit["errors"].append(f"DIRECTIONAL_LUT_CSV_READ_FAILED:{type(exc).__name__}")
        return audit
    base = validate_directional_scattering_lut(df)
    if not base.get("valid", False):
        audit["errors"].append(str(base.get("state", "DIRECTIONAL_LUT_SCHEMA_INVALID")) + ":" + str(base.get("reason", "")))
    if str(manifest.get("lut_version", "")) != str(base.get("lut_version", manifest.get("lut_version", ""))):
        audit["errors"].append("DIRECTIONAL_LUT_VERSION_MANIFEST_TABLE_MISMATCH")
    if set(_phase(x) for x in df.get("phase", pd.Series(dtype=str)).astype(str).unique()) != phases:
        audit["errors"].append("DIRECTIONAL_LUT_PHASE_MANIFEST_TABLE_MISMATCH")
    cal = validate_directional_calibration_metadata(manifest)
    audit["production_calibration_state"] = cal.get("state", "DIRECTIONAL_CALIBRATION_METADATA_INVALID")
    audit["errors"].extend(str(x) for x in cal.get("errors", []))
    audit["warnings"].extend(str(x) for x in cal.get("warnings", []))
    audit.update({
        "rows": int(len(df)), "lut_version": str(manifest.get("lut_version", "")),
        "calibration_id": str(manifest.get("calibration_id", "")),
        "calibration_source": str(manifest.get("calibration_source", "")),
        "calibration_date": str(manifest.get("calibration_date", "")),
        "supported_phases": "/".join(sorted(phases)),
        "calibration_contract": str(manifest.get("calibration_contract", "")),
        "qc_state": str(manifest.get("qc_state", "")),
        "solver_family": str(manifest.get("solver_family", "")),
        "solver_version": str(manifest.get("solver_version", "")),
        "cloud_optics_source": str(manifest.get("cloud_optics_source", "")),
        "phase_function_source": str(manifest.get("phase_function_source", "")),
        "multiple_scattering_enabled": bool(manifest.get("multiple_scattering_enabled", False)),
        "response_definition": str(manifest.get("response_definition", "")),
        "response_units": str(manifest.get("response_units", "")),
        "directional_hemisphere_support": str(manifest.get("directional_hemisphere_support", "")),
        "validation_reference": str(manifest.get("validation_reference", "")),
        "interpolation_axes": "/".join(str(x) for x in manifest.get("interpolation_axes", [])),
        "scattering_angle_role": str(manifest.get("scattering_angle_role", "DERIVED_DIAGNOSTIC_NOT_INTERPOLATION_AXIS")),
        "cloud_thickness_role": str(manifest.get("cloud_thickness_role", "TARGET_GEOMETRY_EVIDENCE_NOT_LUT_INTERPOLATION_AXIS")),
    })
    audit["ok"] = not audit["errors"]
    audit["solver_eligible"] = bool(audit["ok"] and cal.get("ok", False))
    audit["state"] = "CALIBRATED_DIRECTIONAL_LUT_RUNTIME_READY" if audit["ok"] else "DIRECTIONAL_LUT_RUNTIME_INVALID"
    return audit


def load_installed_directional_scattering_lut() -> tuple[pd.DataFrame | None, dict[str, Any]]:
    csv_path, man_path, source = resolve_directional_lut_paths()
    if not csv_path.exists() or not man_path.exists():
        # Migration evidence: an R5.7.19/20 scattering-angle-only LUT may still
        # be installed.  Detect it explicitly but never auto-promote it.
        legacy_csv_env = os.environ.get("FIRECLOUD_TIER2_SCATTERING_LUT_PATH", "").strip()
        legacy_csv = Path(legacy_csv_env).expanduser() if legacy_csv_env else (_root() / "tier2_scattering_runtime" / "tier2_scattering_lut.csv")
        legacy_manifest = legacy_csv.with_name("tier2_scattering_lut_manifest.json")
        if legacy_csv.exists() and legacy_manifest.exists():
            return None, {
                "ok": False, "state": "LEGACY_SCATTERING_ANGLE_LUT_DETECTED_NOT_PRODUCTION_ELIGIBLE",
                "errors": ["R5.7.22_REQUIRES_FULL_DIRECTIONAL_THETA0_THETAV_DELTAPHI_LUT"],
                "warnings": ["LEGACY_LUT_PRESERVED_FOR_HISTORICAL_REGRESSION_ONLY"], "rows": 0,
                "source": "legacy_scattering_runtime_detected", "csv_path": str(legacy_csv),
                "manifest_path": str(legacy_manifest), "runtime_contract": DIRECTIONAL_RUNTIME_CONTRACT,
                "solver_eligible": False, "production_calibration_state": "LEGACY_DIRECTIONAL_CONTRACT_MISSING",
                "geometry_convention": DIRECTIONAL_GEOMETRY_CONVENTION,
            }
        return None, {
            "ok": False, "state": "CALIBRATED_DIRECTIONAL_LUT_NOT_INSTALLED",
            "errors": ["DIRECTIONAL_LUT_CSV_OR_MANIFEST_NOT_FOUND"], "warnings": [], "rows": 0,
            "source": source, "csv_path": str(csv_path), "manifest_path": str(man_path),
            "runtime_contract": DIRECTIONAL_RUNTIME_CONTRACT, "solver_eligible": False,
            "production_calibration_state": "PRODUCTION_DIRECTIONAL_CALIBRATION_NOT_INSTALLED",
            "geometry_convention": DIRECTIONAL_GEOMETRY_CONVENTION,
        }
    csv_bytes = csv_path.read_bytes()
    man_bytes = man_path.read_bytes()
    audit = validate_directional_lut_bytes(csv_bytes, man_bytes)
    audit.update({"source": source, "csv_path": str(csv_path), "manifest_path": str(man_path)})
    if not audit.get("ok", False):
        return None, audit
    return pd.read_csv(io.BytesIO(csv_bytes)), audit


def install_directional_scattering_lut(csv_bytes: bytes, manifest_bytes: bytes, destination: str | Path | None = None) -> dict[str, Any]:
    audit = validate_directional_lut_bytes(csv_bytes, manifest_bytes)
    if not audit.get("ok", False):
        return audit
    dest = Path(destination) if destination is not None else default_runtime_dir()
    dest.mkdir(parents=True, exist_ok=True)
    (dest / LUT_FILENAME).write_bytes(csv_bytes)
    (dest / MANIFEST_FILENAME).write_bytes(manifest_bytes)
    out = dict(audit)
    out.update({"installed": True, "csv_path": str(dest / LUT_FILENAME), "manifest_path": str(dest / MANIFEST_FILENAME)})
    return out
