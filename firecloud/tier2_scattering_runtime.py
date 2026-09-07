from __future__ import annotations
"""R5.7.19 calibrated Tier-2 scattering LUT runtime ingestion.

The runtime layer validates scientific provenance and tabular integrity, resolves
an explicitly installed LUT, and exposes a strict load/install API.  It does not
run Tier-2 radiance interpolation; R5.7.19 only determines whether a target lies
inside a complete interpolation domain.
"""

import hashlib
import io
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd

from .contracts import SIX_BAND_WAVELENGTHS_NM
from .tier2_scattering_foundation import validate_scattering_lut

LUT_FILENAME = "tier2_scattering_lut.csv"
MANIFEST_FILENAME = "tier2_scattering_lut_manifest.json"
RUNTIME_CONTRACT = "R5.7.19_TIER2_SCATTERING_LUT_RUNTIME_V1"
SUPPORTED_PHASES = {"LIQUID", "ICE", "MIXED"}

MANIFEST_REQUIRED_FIELDS = [
    "contract",
    "lut_version",
    "calibration_state",
    "calibration_id",
    "calibration_source",
    "calibration_date",
    "required_wavelengths_nm",
    "supported_phases",
    "csv_sha256",
]


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_runtime_dir() -> Path:
    return _root() / "tier2_scattering_runtime"


def resolve_scattering_lut_paths() -> tuple[Path, Path, str]:
    """Resolve CSV + manifest without silently accepting a manifest-less LUT."""
    csv_env = os.environ.get("FIRECLOUD_TIER2_SCATTERING_LUT_PATH", "").strip()
    manifest_env = os.environ.get("FIRECLOUD_TIER2_SCATTERING_LUT_MANIFEST_PATH", "").strip()
    if csv_env:
        csv_path = Path(csv_env).expanduser()
        manifest_path = Path(manifest_env).expanduser() if manifest_env else csv_path.with_name(MANIFEST_FILENAME)
        return csv_path, manifest_path, "env:FIRECLOUD_TIER2_SCATTERING_LUT_PATH"
    runtime = default_runtime_dir()
    return runtime / LUT_FILENAME, runtime / MANIFEST_FILENAME, "packaged_runtime"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalize_phase(value: Any) -> str:
    p = str(value or "").strip().upper()
    if p == "WATER":
        p = "LIQUID"
    return p


def validate_scattering_lut_bytes(csv_bytes: bytes, manifest_bytes: bytes | None) -> dict[str, Any]:
    audit: dict[str, Any] = {
        "ok": False,
        "state": "LUT_RUNTIME_INVALID",
        "errors": [],
        "warnings": [],
        "rows": 0,
        "lut_version": "",
        "calibration_id": "",
        "csv_sha256": _sha256(csv_bytes or b""),
        "runtime_contract": RUNTIME_CONTRACT,
    }
    if not csv_bytes:
        audit["errors"].append("LUT_CSV_EMPTY")
        return audit
    if not manifest_bytes:
        audit["errors"].append("LUT_MANIFEST_REQUIRED")
        return audit
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except Exception as exc:
        audit["errors"].append(f"LUT_MANIFEST_JSON_INVALID:{type(exc).__name__}")
        return audit
    missing_manifest = [k for k in MANIFEST_REQUIRED_FIELDS if k not in manifest]
    if missing_manifest:
        audit["errors"].append("LUT_MANIFEST_MISSING_FIELDS:" + ",".join(missing_manifest))
        return audit
    if str(manifest.get("contract")) != RUNTIME_CONTRACT:
        audit["errors"].append("LUT_MANIFEST_CONTRACT_MISMATCH")
    if str(manifest.get("calibration_state", "")).upper() != "CALIBRATED":
        audit["errors"].append("LUT_MANIFEST_NOT_CALIBRATED")
    expected_wl = [int(x) for x in SIX_BAND_WAVELENGTHS_NM]
    try:
        manifest_wl = sorted(int(x) for x in manifest.get("required_wavelengths_nm", []))
    except Exception:
        manifest_wl = []
    if manifest_wl != sorted(expected_wl):
        audit["errors"].append("LUT_MANIFEST_WAVELENGTH_CONTRACT_MISMATCH")
    phases = {_normalize_phase(x) for x in manifest.get("supported_phases", [])}
    if not phases or not phases.issubset(SUPPORTED_PHASES):
        audit["errors"].append("LUT_MANIFEST_PHASE_CONTRACT_INVALID")
    actual_sha = audit["csv_sha256"]
    if str(manifest.get("csv_sha256", "")).lower() != actual_sha:
        audit["errors"].append("LUT_CSV_SHA256_MISMATCH")
    try:
        df = pd.read_csv(io.BytesIO(csv_bytes))
    except Exception as exc:
        audit["errors"].append(f"LUT_CSV_READ_FAILED:{type(exc).__name__}")
        return audit
    audit["rows"] = int(len(df))
    base = validate_scattering_lut(df)
    audit["foundation_validation_state"] = base.get("state", "UNKNOWN")
    if not base.get("valid", False):
        audit["errors"].append("LUT_FOUNDATION_VALIDATION_FAILED:" + str(base.get("reason", base.get("state", "UNKNOWN"))))
    if "phase" in df.columns:
        normalized = df["phase"].map(_normalize_phase)
        if not set(normalized.unique()).issubset(phases):
            audit["errors"].append("LUT_CSV_PHASE_NOT_DECLARED_IN_MANIFEST")
        df = df.copy()
        df["phase"] = normalized
    if "lut_version" in df.columns:
        versions = set(df["lut_version"].astype(str))
        if versions != {str(manifest.get("lut_version"))}:
            audit["errors"].append("LUT_VERSION_MANIFEST_CSV_MISMATCH")
    # Duplicate coordinates make interpolation ambiguous even if response values match.
    coord_cols = ["phase", "wavelength_nm", "cot", "effective_radius_um", "cloud_thickness_km", "scattering_angle_deg"]
    if all(c in df.columns for c in coord_cols) and df.duplicated(coord_cols, keep=False).any():
        audit["errors"].append("LUT_DUPLICATE_GRID_COORDINATE")
    for field in ("calibration_id", "calibration_source", "calibration_date", "lut_version"):
        if not str(manifest.get(field, "")).strip():
            audit["errors"].append("LUT_MANIFEST_EMPTY_" + field.upper())
    audit["lut_version"] = str(manifest.get("lut_version", ""))
    audit["calibration_id"] = str(manifest.get("calibration_id", ""))
    audit["calibration_source"] = str(manifest.get("calibration_source", ""))
    audit["calibration_date"] = str(manifest.get("calibration_date", ""))
    audit["supported_phases"] = "/".join(sorted(phases))
    audit["ok"] = not audit["errors"]
    audit["state"] = "CALIBRATED_LUT_RUNTIME_READY" if audit["ok"] else "LUT_RUNTIME_INVALID"
    return audit


def install_scattering_lut(csv_bytes: bytes, manifest_bytes: bytes, runtime_dir: str | Path | None = None) -> dict[str, Any]:
    """Validate then atomically install a calibrated LUT and its provenance manifest."""
    audit = validate_scattering_lut_bytes(csv_bytes, manifest_bytes)
    if not audit.get("ok"):
        return audit
    outdir = Path(runtime_dir) if runtime_dir is not None else default_runtime_dir()
    outdir.mkdir(parents=True, exist_ok=True)
    csv_tmp = outdir / (LUT_FILENAME + ".tmp")
    manifest_tmp = outdir / (MANIFEST_FILENAME + ".tmp")
    csv_tmp.write_bytes(csv_bytes)
    manifest_tmp.write_bytes(manifest_bytes)
    os.replace(csv_tmp, outdir / LUT_FILENAME)
    os.replace(manifest_tmp, outdir / MANIFEST_FILENAME)
    audit = dict(audit)
    audit["installed_csv"] = str(outdir / LUT_FILENAME)
    audit["installed_manifest"] = str(outdir / MANIFEST_FILENAME)
    return audit


def load_installed_scattering_lut() -> tuple[pd.DataFrame | None, dict[str, Any]]:
    csv_path, manifest_path, source = resolve_scattering_lut_paths()
    if not csv_path.exists() or not manifest_path.exists():
        return None, {
            "ok": False,
            "state": "CALIBRATED_LUT_NOT_INSTALLED",
            "errors": ["LUT_CSV_OR_MANIFEST_NOT_FOUND"],
            "source": source,
            "csv_path": str(csv_path),
            "manifest_path": str(manifest_path),
            "runtime_contract": RUNTIME_CONTRACT,
        }
    csv_bytes = csv_path.read_bytes()
    manifest_bytes = manifest_path.read_bytes()
    audit = validate_scattering_lut_bytes(csv_bytes, manifest_bytes)
    audit["source"] = source
    audit["csv_path"] = str(csv_path)
    audit["manifest_path"] = str(manifest_path)
    if not audit.get("ok"):
        return None, audit
    df = pd.read_csv(io.BytesIO(csv_bytes))
    df = df.copy()
    df["phase"] = df["phase"].map(_normalize_phase)
    for col in ["wavelength_nm", "cot", "effective_radius_um", "cloud_thickness_km", "scattering_angle_deg", "response_factor"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df, audit
