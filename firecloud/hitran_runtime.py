from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

COEFFICIENT_FILENAME = "firecloud_600_750nm_band_coefficients.csv"
MANIFEST_FILENAME = "firecloud_600_750nm_band_coefficients.manifest.json"
REQUIRED_GASES = ("H2O", "O3", "O2")
REQUIRED_WAVELENGTHS_NM = (600.0, 650.0, 700.0, 750.0)
EXTENDED_WAVELENGTHS_NM = (575.0, 600.0, 650.0, 700.0, 750.0)
SIX_BAND_WAVELENGTHS_NM = (550.0, 575.0, 600.0, 650.0, 700.0, 750.0)
REQUIRED_TEMPERATURES_K = (220.0, 250.0, 280.0, 293.0)
REQUIRED_PRESSURES_HPA = (100.0, 300.0, 500.0, 700.0, 900.0, 1000.0)
EXPECTED_ROWS = (
    len(REQUIRED_GASES)
    * len(REQUIRED_WAVELENGTHS_NM)
    * len(REQUIRED_TEMPERATURES_K)
    * len(REQUIRED_PRESSURES_HPA)
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_runtime_lut_bytes(csv_bytes: bytes, manifest_bytes: bytes | None = None) -> dict[str, Any]:
    """Strictly validate the Firecloud production runtime LUT.

    This validates the *derived* spectroscopy table only. Raw HITRAN line lists are
    intentionally not required at runtime and are never copied by this helper.
    """
    result: dict[str, Any] = {
        "ok": False,
        "expected_rows": EXPECTED_ROWS,
        "rows": 0,
        "sha256": _sha256_bytes(csv_bytes),
        "errors": [],
        "warnings": [],
    }
    try:
        import io
        df = pd.read_csv(io.BytesIO(csv_bytes))
    except Exception as exc:
        result["errors"].append(f"CSV_READ_FAILED:{type(exc).__name__}:{exc}")
        return result

    result["rows"] = int(len(df))
    required = {
        "wavelength_nm", "gas", "sigma_cm2_molecule",
        "temperature_k", "pressure_hpa", "spectroscopy_source",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        result["errors"].append("MISSING_COLUMNS:" + ",".join(missing))
        return result

    work = df.copy()
    work["gas"] = work["gas"].astype(str).str.upper().str.strip()
    for col in ("wavelength_nm", "sigma_cm2_molecule", "temperature_k", "pressure_hpa"):
        work[col] = pd.to_numeric(work[col], errors="coerce")

    has_575 = bool(np.isclose(work["wavelength_nm"], 575.0, equal_nan=False).any())
    has_550 = bool(np.isclose(work["wavelength_nm"], 550.0, equal_nan=False).any())
    active_wavelengths = SIX_BAND_WAVELENGTHS_NM if (has_550 and has_575) else (EXTENDED_WAVELENGTHS_NM if has_575 else REQUIRED_WAVELENGTHS_NM)
    expected_rows = len(REQUIRED_GASES) * len(active_wavelengths) * len(REQUIRED_TEMPERATURES_K) * len(REQUIRED_PRESSURES_HPA)
    result["expected_rows"] = expected_rows
    result["active_wavelengths_nm"] = list(active_wavelengths)
    if len(work) != expected_rows:
        result["errors"].append(f"ROW_COUNT_MISMATCH:{len(work)}!={expected_rows}")

    sigma = work["sigma_cm2_molecule"].to_numpy(float)
    if not np.isfinite(sigma).all() or (sigma < 0).any():
        result["errors"].append("SIGMA_NONFINITE_OR_NEGATIVE")

    sources = sorted({str(v).strip() for v in work["spectroscopy_source"].dropna() if str(v).strip()})
    result["spectroscopy_sources"] = sources
    provenance_by_gas = {}
    src_upper = work["spectroscopy_source"].astype(str).str.upper()
    for gas in ("H2O", "O2"):
        m = work["gas"].eq(gas)
        provenance_by_gas[gas] = bool(m.any()) and bool(src_upper[m].str.contains("HITRAN", regex=False).all())
    m = work["gas"].eq("O3")
    provenance_by_gas["O3"] = bool(m.any()) and bool(src_upper[m].str.contains("SERDYUCHENKO_GORSHELEV", regex=False).all())
    result["spectroscopy_provenance_by_gas"] = provenance_by_gas
    if not all(provenance_by_gas.values()):
        result["errors"].append("HYBRID_PROVENANCE_INVALID")

    expected = {
        (g, wl, t, p)
        for g in REQUIRED_GASES
        for wl in active_wavelengths
        for t in REQUIRED_TEMPERATURES_K
        for p in REQUIRED_PRESSURES_HPA
    }
    actual = {
        (str(r.gas), float(r.wavelength_nm), float(r.temperature_k), float(r.pressure_hpa))
        for r in work.itertuples(index=False)
        if str(r.gas) in REQUIRED_GASES
        and np.isfinite(float(r.wavelength_nm))
        and np.isfinite(float(r.temperature_k))
        and np.isfinite(float(r.pressure_hpa))
    }
    missing_states = sorted(expected - actual)
    extra_states = sorted(actual - expected)
    if missing_states:
        result["errors"].append(f"GRID_STATES_MISSING:{len(missing_states)}")
    if extra_states:
        result["errors"].append(f"GRID_STATES_EXTRA:{len(extra_states)}")

    # Detect duplicates separately; a set comparison alone would hide them.
    key_cols = ["gas", "wavelength_nm", "temperature_k", "pressure_hpa"]
    duplicate_count = int(work.duplicated(key_cols, keep=False).sum())
    result["duplicate_rows"] = duplicate_count
    if duplicate_count:
        result["errors"].append(f"DUPLICATE_GRID_ROWS:{duplicate_count}")

    manifest = None
    if manifest_bytes:
        try:
            manifest = json.loads(manifest_bytes.decode("utf-8"))
        except Exception as exc:
            result["errors"].append(f"MANIFEST_READ_FAILED:{type(exc).__name__}:{exc}")
        if isinstance(manifest, dict):
            msha = str(manifest.get("sha256", "")).strip().lower()
            if msha and msha != result["sha256"].lower():
                result["errors"].append("MANIFEST_SHA256_MISMATCH")
            mrows = manifest.get("rows")
            if mrows is not None:
                try:
                    if int(mrows) != len(work):
                        result["errors"].append("MANIFEST_ROW_COUNT_MISMATCH")
                except Exception:
                    result["errors"].append("MANIFEST_ROW_COUNT_INVALID")
            mwls = manifest.get("wavelengths_nm")
            if mwls is not None:
                try:
                    if sorted(float(x) for x in mwls) != sorted(float(x) for x in active_wavelengths):
                        result["errors"].append("MANIFEST_WAVELENGTH_GRID_MISMATCH")
                except Exception:
                    result["errors"].append("MANIFEST_WAVELENGTH_GRID_INVALID")
            result["manifest_version"] = str(manifest.get("version", ""))
    else:
        result["warnings"].append("MANIFEST_NOT_SUPPLIED")

    result["temperature_values_k"] = sorted({float(x) for x in work["temperature_k"].dropna()})
    result["pressure_values_hpa"] = sorted({float(x) for x in work["pressure_hpa"].dropna()})
    result["wavelength_values_nm"] = sorted({float(x) for x in work["wavelength_nm"].dropna()})
    result["gases"] = sorted({str(x) for x in work["gas"].dropna()})
    result["ok"] = not result["errors"]
    return result


def install_runtime_lut(
    csv_bytes: bytes,
    manifest_bytes: bytes | None,
    runtime_dir: str | Path,
) -> dict[str, Any]:
    """Validate then atomically install the derived LUT into a runtime directory."""
    audit = validate_runtime_lut_bytes(csv_bytes, manifest_bytes)
    if not audit.get("ok"):
        return audit
    runtime = Path(runtime_dir).expanduser().resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    csv_path = runtime / COEFFICIENT_FILENAME
    tmp_csv = runtime / (COEFFICIENT_FILENAME + ".tmp")
    tmp_csv.write_bytes(csv_bytes)
    tmp_csv.replace(csv_path)

    if manifest_bytes:
        manifest_path = runtime / MANIFEST_FILENAME
        tmp_manifest = runtime / (MANIFEST_FILENAME + ".tmp")
        tmp_manifest.write_bytes(manifest_bytes)
        tmp_manifest.replace(manifest_path)
    else:
        # Create a minimal deployment manifest for this validated derived table.
        manifest = {
            "format": "Taiwan Firecloud Hybrid Gas Spectroscopy diagnostic-band LUT",
            "version": "PhysicsCore-V1.0-R4.8.1-runtime-import",
            "coefficient_file": COEFFICIENT_FILENAME,
            "sha256": audit["sha256"],
            "rows": audit["rows"],
            "gases": list(REQUIRED_GASES),
            "wavelengths_nm": [int(x) for x in audit.get("active_wavelengths_nm", REQUIRED_WAVELENGTHS_NM)],
            "temperatures_k": list(REQUIRED_TEMPERATURES_K),
            "pressures_hpa": list(REQUIRED_PRESSURES_HPA),
            "spectroscopy_sources": {"H2O":"HITRAN","O2":"HITRAN","O3":"Serdyuchenko-Gorshelev XSC"},
            "note": "Derived coefficient LUT only; raw HITRAN transition data and O3 source spectra are not included.",
        }
        (runtime / MANIFEST_FILENAME).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    audit["installed_path"] = str(csv_path)
    audit["installed_manifest_path"] = str(runtime / MANIFEST_FILENAME)
    return audit


def copy_built_lut_to_runtime(build_db: str | Path, runtime_dir: str | Path) -> dict[str, Any]:
    """Promote a locally built LUT into runtime storage after strict validation."""
    build_db = Path(build_db).expanduser().resolve()
    csv_path = build_db / COEFFICIENT_FILENAME
    manifest_path = build_db / MANIFEST_FILENAME
    if not csv_path.is_file():
        return {"ok": False, "errors": ["BUILT_LUT_MISSING"], "rows": 0, "expected_rows": EXPECTED_ROWS}
    csv_bytes = csv_path.read_bytes()
    manifest_bytes = manifest_path.read_bytes() if manifest_path.is_file() else None
    return install_runtime_lut(csv_bytes, manifest_bytes, runtime_dir)
