from __future__ import annotations

import json
import math
import os
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REQUIRED_WAVELENGTHS_NM = (600, 650, 700, 750)
EXTENDED_WAVELENGTHS_NM = (575, 600, 650, 700, 750)
REQUIRED_GASES = ("H2O", "O3", "O2")
REQUIRED_TEMPERATURES_K = (220.0, 250.0, 280.0, 293.0)
REQUIRED_PRESSURES_HPA = (100.0, 300.0, 500.0, 700.0, 900.0, 1000.0)
COEFFICIENT_FILENAME = "firecloud_600_750nm_band_coefficients.csv"


def _secret_lookup(*keys: str) -> tuple[str | None, str | None]:
    """Read optional Streamlit secrets without making Streamlit a hard dependency.

    Supported forms:
      HITRAN_API_KEY = "..."
      FIRECLOUD_HITRAN_DB = "..."

      [hitran]
      api_key = "..."
      db_path = "..."

    Secret values are never returned in status metadata; only source names are.
    """
    try:
        import streamlit as st  # type: ignore
    except Exception:
        return None, None
    try:
        secrets = st.secrets
    except Exception:
        return None, None

    for key in keys:
        try:
            value = secrets.get(key)
        except Exception:
            value = None
        if value is not None and str(value).strip():
            return str(value).strip(), f"streamlit:{key}"

    try:
        section = secrets.get("hitran")
    except Exception:
        section = None
    if section is not None:
        aliases = {
            "HITRAN_API_KEY": ("api_key", "key", "token"),
            "FIRECLOUD_HITRAN_DB": ("db_path", "database_path", "path"),
            "FIRECLOUD_HITRAN_LUT_PATH": ("lut_path", "runtime_lut_path"),
        }
        for key in keys:
            for alias in aliases.get(key, (key.lower(),)):
                try:
                    value = section.get(alias)
                except Exception:
                    value = None
                if value is not None and str(value).strip():
                    return str(value).strip(), f"streamlit:hitran.{alias}"
    return None, None


def resolve_hitran_api_key() -> tuple[str, str]:
    for env_name in ("HITRAN_API_KEY",):
        value = os.environ.get(env_name, "").strip()
        if value:
            return value, f"env:{env_name}"
    value, source = _secret_lookup("HITRAN_API_KEY")
    return (value or ""), (source or "")


def resolve_hitran_db_path() -> tuple[Path, str]:
    env_value = os.environ.get("FIRECLOUD_HITRAN_DB", "").strip()
    if env_value:
        return Path(env_value).expanduser(), "env:FIRECLOUD_HITRAN_DB"
    value, source = _secret_lookup("FIRECLOUD_HITRAN_DB")
    if value:
        return Path(value).expanduser(), source or "streamlit"
    return Path("hitran_db"), "default:hitran_db"


def resolve_hitran_lut_path() -> tuple[Path, str]:
    """Resolve the production derived-LUT path without requiring raw HITRAN tables.

    Priority: explicit environment/secret path -> packaged hitran_runtime LUT ->
    legacy build database LUT.  This lets deployments persist the derived table in
    the repository while keeping raw HITRAN transition data out of the app.
    """
    env_value = os.environ.get("FIRECLOUD_HITRAN_LUT_PATH", "").strip()
    if env_value:
        return Path(env_value).expanduser(), "env:FIRECLOUD_HITRAN_LUT_PATH"
    value, source = _secret_lookup("FIRECLOUD_HITRAN_LUT_PATH")
    if value:
        return Path(value).expanduser(), source or "streamlit"
    packaged = Path(__file__).resolve().parent.parent / "hitran_runtime" / COEFFICIENT_FILENAME
    if packaged.is_file():
        return packaged, "packaged:hitran_runtime"
    db, db_source = resolve_hitran_db_path()
    return db / COEFFICIENT_FILENAME, f"legacy-db:{db_source}"


def _load_coefficient_path(path: Path) -> tuple[pd.DataFrame, str]:
    if not path.is_file():
        return pd.DataFrame(), "COEFFICIENT_TABLE_MISSING"
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        return pd.DataFrame(), f"COEFFICIENT_TABLE_READ_FAILED:{type(exc).__name__}"
    required_cols = {"wavelength_nm", "gas", "sigma_cm2_molecule"}
    if not required_cols.issubset(df.columns):
        return df, "COEFFICIENT_TABLE_SCHEMA_INCOMPLETE"
    return df, ""


def _load_coefficient_table(db_path: Path) -> tuple[pd.DataFrame, str]:
    path = db_path / COEFFICIENT_FILENAME
    if not path.is_file():
        return pd.DataFrame(), "COEFFICIENT_TABLE_MISSING"
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        return pd.DataFrame(), f"COEFFICIENT_TABLE_READ_FAILED:{type(exc).__name__}"
    required_cols = {"wavelength_nm", "gas", "sigma_cm2_molecule"}
    if not required_cols.issubset(df.columns):
        return df, "COEFFICIENT_TABLE_SCHEMA_INCOMPLETE"
    return df, ""


def inspect_hitran_coefficient_table(db_path: str | Path | None = None) -> dict[str, Any]:
    if db_path is None:
        coeff_path, coeff_source = resolve_hitran_lut_path()
        path = coeff_path.parent
        path_source = coeff_source
        coeff, read_error = _load_coefficient_path(coeff_path)
    else:
        path, path_source = Path(db_path).expanduser(), "explicit"
        coeff_path = path / COEFFICIENT_FILENAME
        coeff, read_error = _load_coefficient_table(path)

    pair_status: dict[str, bool] = {}
    finite_rows = 0
    if not coeff.empty and {"wavelength_nm", "gas", "sigma_cm2_molecule"}.issubset(coeff.columns):
        work = coeff.copy()
        work["gas_norm"] = work["gas"].astype(str).str.upper().str.strip()
        work["wl"] = pd.to_numeric(work["wavelength_nm"], errors="coerce")
        work["sigma"] = pd.to_numeric(work["sigma_cm2_molecule"], errors="coerce")
        finite_rows = int((np.isfinite(work["sigma"]) & (work["sigma"] >= 0)).sum())
        has_575 = bool(np.isclose(work["wl"], 575.0, equal_nan=False).any())
        active_wavelengths = EXTENDED_WAVELENGTHS_NM if has_575 else REQUIRED_WAVELENGTHS_NM
        for gas in REQUIRED_GASES:
            for wl in active_wavelengths:
                mask = (
                    (work["gas_norm"] == gas)
                    & np.isclose(work["wl"], float(wl), equal_nan=False)
                    & np.isfinite(work["sigma"])
                    & (work["sigma"] >= 0)
                )
                pair_status[f"{gas}_{wl}nm"] = bool(mask.any())
    else:
        active_wavelengths = REQUIRED_WAVELENGTHS_NM
        for gas in REQUIRED_GASES:
            for wl in active_wavelengths:
                pair_status[f"{gas}_{wl}nm"] = False

    pair_complete = all(pair_status.values()) if pair_status else False
    provenance_ok = False
    sources: list[str] = []
    provenance_by_gas: dict[str, bool] = {g: False for g in REQUIRED_GASES}
    if not coeff.empty and "spectroscopy_source" in coeff.columns:
        sources = sorted({str(v).strip() for v in coeff["spectroscopy_source"].dropna() if str(v).strip()})
        gas_norm = coeff["gas"].astype(str).str.upper().str.strip() if "gas" in coeff.columns else pd.Series([], dtype=str)
        src_norm = coeff["spectroscopy_source"].astype(str).str.upper()
        for gas in ("H2O", "O2"):
            m = gas_norm.eq(gas)
            provenance_by_gas[gas] = bool(m.any()) and bool(src_norm[m].str.contains("HITRAN", regex=False).all())
        m = gas_norm.eq("O3")
        provenance_by_gas["O3"] = bool(m.any()) and bool(src_norm[m].str.contains("SERDYUCHENKO_GORSHELEV", regex=False).all())
        provenance_ok = all(provenance_by_gas.values())

    tp_grid = {
        "temperature_values_k": [],
        "pressure_values_hpa": [],
        "temperature_count": 0,
        "pressure_count": 0,
    }
    if not coeff.empty:
        if "temperature_k" in coeff.columns:
            vals = sorted({float(v) for v in pd.to_numeric(coeff["temperature_k"], errors="coerce").dropna() if math.isfinite(float(v))})
            tp_grid["temperature_values_k"] = vals
            tp_grid["temperature_count"] = len(vals)
        if "pressure_hpa" in coeff.columns:
            vals = sorted({float(v) for v in pd.to_numeric(coeff["pressure_hpa"], errors="coerce").dropna() if math.isfinite(float(v))})
            tp_grid["pressure_values_hpa"] = vals
            tp_grid["pressure_count"] = len(vals)

    # V8.4.5 requires the complete hybrid 3 × 4 × 4 × 6 grid, not merely one
    # coefficient per gas/wavelength pair. This prevents an old 288-row all-HITRAN
    # O3 LUT or a sparse table from being silently accepted as Hybrid READY.
    grid_complete = False
    if not coeff.empty and {"gas","wavelength_nm","temperature_k","pressure_hpa","sigma_cm2_molecule"}.issubset(coeff.columns):
        keys=set()
        for _,r in coeff.iterrows():
            try:
                g=str(r["gas"]).upper().strip(); wl=float(r["wavelength_nm"]); t=float(r["temperature_k"]); ph=float(r["pressure_hpa"]); sig=float(r["sigma_cm2_molecule"])
            except Exception:
                continue
            if np.isfinite(sig) and sig>=0:
                keys.add((g,wl,t,ph))
        required={(g,float(wl),float(t),float(ph)) for g in REQUIRED_GASES for wl in active_wavelengths for t in REQUIRED_TEMPERATURES_K for ph in REQUIRED_PRESSURES_HPA}
        grid_complete = required.issubset(keys) and len(required)==(360 if len(active_wavelengths)==5 else 288)

    complete = bool(pair_complete and grid_complete and provenance_ok and not read_error)
    reason = ""
    if read_error:
        reason = read_error
    elif not pair_complete:
        reason = "REQUIRED_GAS_WAVELENGTH_PAIRS_MISSING"
    elif not grid_complete:
        reason = f"HYBRID_{len(REQUIRED_GASES)*len(active_wavelengths)*len(REQUIRED_TEMPERATURES_K)*len(REQUIRED_PRESSURES_HPA)}_STATE_GRID_INCOMPLETE"
    elif not provenance_ok:
        reason = "HYBRID_SPECTROSCOPY_PROVENANCE_INVALID"

    return {
        "database_path": str(path),
        "database_path_source": path_source,
        "database_exists": path.is_dir(),
        "coefficient_table_path": str(coeff_path),
        "coefficient_table_source": path_source,
        "coefficient_table_exists": coeff_path.is_file(),
        "coefficient_table_rows": int(len(coeff)),
        "coefficient_table_finite_rows": finite_rows,
        "coefficient_table_complete": complete,
        "coefficient_table_missing_reason": reason,
        "required_gases": list(REQUIRED_GASES),
        "required_wavelengths_nm": list(REQUIRED_WAVELENGTHS_NM),
        "active_wavelengths_nm": list(active_wavelengths),
        "extended_575nm_detected": bool(575 in active_wavelengths),
        "extended_575nm_ready": bool(575 in active_wavelengths and complete),
        "required_pair_status": pair_status,
        "spectroscopy_sources": sources,
        "spectroscopy_provenance_by_gas": provenance_by_gas,
        "hybrid_grid_complete": grid_complete,
        "required_temperatures_k": list(REQUIRED_TEMPERATURES_K),
        "required_pressures_hpa": list(REQUIRED_PRESSURES_HPA),
        **tp_grid,
    }


def hitran_backend_status(db_path: str | Path | None = None) -> dict[str, Any]:
    """Return safe status for Runtime or an explicitly audited build database.

    Normal app calls use the packaged/Runtime LUT resolver. A bootstrap command
    with ``--db`` must pass its explicit directory here; otherwise the packaged
    base LUT can mask a newly built 360-state LUT during the readiness audit.
    """
    try:
        with warnings.catch_warnings():
            # HAPI 1.3.0 contains legacy string escapes. They are harmless
            # upstream SyntaxWarnings and should not pollute analysis stderr.
            warnings.simplefilter("ignore", SyntaxWarning)
            import hapi  # noqa: F401
        hapi_ok = True
        try:
            hapi_version = str(getattr(hapi, "__version__", getattr(hapi, "HAPI_VERSION", "")))
        except Exception:
            hapi_version = ""
    except Exception:
        hapi_ok = False
        hapi_version = ""

    api_key, credential_source = resolve_hitran_api_key()
    status = inspect_hitran_coefficient_table(db_path=db_path)
    status.update(
        {
            "hapi_available": hapi_ok,
            "hapi_version": hapi_version,
            "api_key_configured": bool(api_key),
            "credential_source": credential_source,
            # Runtime full RT consumes the local HITRAN-derived LUT. HAPI itself
            # is a build-time dependency and is not required once the LUT exists.
            "runtime_spectroscopy_ready": bool(status.get("coefficient_table_complete")),
            "extended_runtime_spectroscopy_ready": bool(status.get("extended_575nm_ready")),
        }
    )
    if status["runtime_spectroscopy_ready"]:
        status["gas_rt_status"] = "READY_LOCAL_HITRAN_LUT"
    elif not status.get("database_exists"):
        status["gas_rt_status"] = "LOCAL_HITRAN_DB_REQUIRED"
    elif not status.get("coefficient_table_exists"):
        status["gas_rt_status"] = "HITRAN_COEFFICIENT_LUT_REQUIRED"
    else:
        status["gas_rt_status"] = "HITRAN_COEFFICIENT_LUT_INCOMPLETE"
    return status


def write_status_json(path: str | Path) -> None:
    Path(path).write_text(json.dumps(hitran_backend_status(), ensure_ascii=False, indent=2), encoding="utf-8")
