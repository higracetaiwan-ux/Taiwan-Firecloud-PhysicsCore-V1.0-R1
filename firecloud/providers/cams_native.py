"""Optional CAMS native 3-D aerosol-extinction provider for Taiwan Firecloud V8.3.3.

This provider is deliberately credential-gated. It retrieves CAMS global atmospheric
composition forecast aerosol extinction coefficient at 532 nm on pressure levels and
maps the gridded 3-D field to the Firecloud Sun-direction route. No synthetic aerosol
profile is created here.

The ADS API requires a valid Copernicus/ECMWF API configuration (typically ~/.cdsapirc).
If credentials, the cdsapi client, or decodable data are unavailable, the caller must
keep the native 3-D aerosol field Missing and may retain the V8.3.2 column-AOD profile
reconstruction only as a separately labelled fallback diagnostic.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import importlib.util
import math
import os
import tempfile
import hashlib
import subprocess
import sys
import json
import gc
import signal
import time
import pickle
import uuid
import re
import numpy as np
import pandas as pd

DATASET = "cams-global-atmospheric-composition-forecasts"
PROVIDER_NAME = "CAMS_GLOBAL_FORECAST_NATIVE_3D_AEROSOL_EXTINCTION_532NM"
OZONE_PROVIDER_NAME = "CAMS_GLOBAL_FORECAST_NATIVE_3D_OZONE_PRESSURE_LEVELS"
DEFAULT_PRESSURE_LEVELS_HPA = (1000, 950, 925, 900, 850, 800, 700, 600, 500, 400, 300, 250, 200, 150, 100, 70, 50, 30)


def decoder_available() -> bool:
    return importlib.util.find_spec("eccodes") is not None


def api_client_available() -> bool:
    return importlib.util.find_spec("cdsapi") is not None


def _credential_env() -> tuple[str | None, str | None, str]:
    """Resolve deployment credentials without exposing the secret value.

    Priority is ADS-specific env vars, then generic CDSAPI vars.  The ADS URL
    defaults to the official Atmosphere Data Store endpoint when an ADS key is
    supplied.  ~/.cdsapirc remains fully supported for local deployments.
    """
    ads_key = (os.getenv("ADS_API_KEY") or "").strip()
    if ads_key:
        url = (os.getenv("ADS_API_URL") or "https://ads.atmosphere.copernicus.eu/api").strip()
        return url, ads_key, "ADS_ENV"
    cds_key = (os.getenv("CDSAPI_KEY") or "").strip()
    if cds_key:
        url = (os.getenv("CDSAPI_URL") or os.getenv("ADS_API_URL") or "https://ads.atmosphere.copernicus.eu/api").strip()
        return url, cds_key, "CDSAPI_ENV"
    return None, None, ""


def credentials_configured() -> bool:
    if Path.home().joinpath(".cdsapirc").exists():
        return True
    _url, key, _source = _credential_env()
    return bool(key)


def credential_source() -> str:
    if Path.home().joinpath(".cdsapirc").exists():
        return "HOME_CDSAPIRC"
    _url, key, source = _credential_env()
    return source if key else "NOT_CONFIGURED"


def _make_cdsapi_client():
    """Create a cdsapi client from ~/.cdsapirc or deployment environment.

    This avoids relying on cdsapi to interpret custom environment variable
    names.  Secrets are never included in returned metadata or CASE outputs.
    """
    import cdsapi
    url, key, _source = _credential_env()
    if key:
        return cdsapi.Client(url=url, key=key)
    return cdsapi.Client()


def native_aerosol_provider_status() -> dict:
    return {
        "provider": PROVIDER_NAME,
        "dataset": DATASET,
        "api_client_available": api_client_available(),
        "decoder_available": decoder_available(),
        "credentials_configured": credentials_configured(),
        "credential_source": credential_source(),
        "native_variable": "aerosol_extinction_coefficient_at_532_nm",
        "ozone_retrieval_policy": "INDEPENDENT_REQUEST",
        "native_units": "m-1",
        "vertical_coordinate": "pressure_levels",
        "fallback_policy": "V8.3.2_COLUMN_AOD_PROFILE_RECONSTRUCTION_KEPT_SEPARATE",
    }




def native_ozone_provider_status() -> dict:
    """Status for the real CAMS pressure-level ozone profile used by V8.4.1.

    Ozone is co-retrieved with the native aerosol/geopotential pressure-level
    subset so the event does not pay a second ADS download for the same run/lead.
    """
    return {
        "provider": OZONE_PROVIDER_NAME,
        "dataset": DATASET,
        "api_client_available": api_client_available(),
        "decoder_available": decoder_available(),
        "credentials_configured": credentials_configured(),
        "credential_source": credential_source(),
        "native_variable": "ozone",
        "native_units": "kg kg-1",
        "vertical_coordinate": "pressure_levels",
        "profile_policy": "REAL_CAMS_PRESSURE_LEVELS_ONLY_NO_FIXED_300DU_NO_SYNTHETIC_O3_PROFILE",
        "retrieval_policy": "INDEPENDENT_REQUEST",
    }

def _utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def resolve_cams_run_and_lead(valid_time: datetime, now_utc: datetime | None = None) -> tuple[datetime, int]:
    """Resolve an operationally available CAMS 00/12 UTC run and nearest 3-hour lead.

    CAMS global forecasts are nominally delivered about 10 h after cycle time
    (00 UTC by 10 UTC; 12 UTC by 22 UTC).  Earlier PhysicsCore releases used
    an 8 h availability assumption, which could select a not-yet-published run
    and trigger ADS HTTP 400 ``invalid combination`` for every Dynamic tile.

    ``FIRECLOUD_CAMS_AVAILABILITY_LAG_HOURS`` is configurable for deployments;
    the default 10.25 h adds a small safety margin while keeping the previous
    cycle scientifically valid for the requested forecast valid time.
    """
    target = _utc(valid_time)
    now = _utc(now_utc or datetime.now(timezone.utc))
    try:
        lag_hours = float(os.getenv("FIRECLOUD_CAMS_AVAILABILITY_LAG_HOURS", "10.25"))
    except Exception:
        lag_hours = 10.25
    lag_hours = max(10.0, lag_hours)

    # Never select a cycle newer than the latest one expected to be delivered,
    # and never select a run later than the target valid time itself.
    anchor = min(target, now - timedelta(hours=lag_hours))
    cycle = 12 if anchor.hour >= 12 else 0
    run = anchor.replace(hour=cycle, minute=0, second=0, microsecond=0)
    lead = int(round((target - run).total_seconds() / 3600.0 / 3.0) * 3)
    if lead < 0:
        run -= timedelta(hours=12)
        lead = int(round((target - run).total_seconds() / 3600.0 / 3.0) * 3)
    if lead > 120:
        raise ValueError(f"CAMS target outside 5-day forecast horizon: +{lead} h")
    return run, lead


def route_bbox(points: list[dict], margin_deg: float = 0.6) -> list[float]:
    lats = [float(p["lat"]) for p in points]
    lons = [float(p["lon"]) for p in points]
    # ADS area order is North, West, South, East.
    return [max(lats) + margin_deg, min(lons) - margin_deg, min(lats) - margin_deg, max(lons) + margin_deg]


def _base_request(points: list[dict], valid_time: datetime) -> tuple[dict, dict]:
    run, lead = resolve_cams_run_and_lead(valid_time)
    request = {
        "date": run.strftime("%Y-%m-%d"),
        "time": run.strftime("%H:%M"),
        "leadtime_hour": str(int(lead)),
        "type": "forecast",
        "area": route_bbox(points),
        "data_format": "grib",
    }
    meta = {
        "cams_run_utc": run.isoformat(),
        "cams_forecast_hour": int(lead),
        "cams_valid_time_utc": (run + timedelta(hours=lead)).isoformat(),
        "cams_area_nwse": request["area"],
    }
    return request, meta


def build_ads_native_aerosol_request(points: list[dict], valid_time: datetime, pressure_levels_hpa=DEFAULT_PRESSURE_LEVELS_HPA) -> tuple[dict, dict]:
    """Independent CAMS multi-level request for native 532-nm aerosol extinction.

    Official CAMS CDS/API variable name: aerosol_extinction_coefficient_532nm.
    Multi-level fields are requested only at 3-hourly forecast leads.
    """
    request, meta = _base_request(points, valid_time)
    request.update({
        "variable": ["aerosol_extinction_coefficient_532nm", "geopotential"],
        "pressure_level": [str(int(p)) for p in pressure_levels_hpa],
    })
    meta["request_role"] = "NATIVE_AEROSOL_532NM_PRESSURE_LEVEL"
    return request, meta


def build_ads_ozone_request(points: list[dict], valid_time: datetime, pressure_levels_hpa=DEFAULT_PRESSURE_LEVELS_HPA) -> tuple[dict, dict]:
    """Independent CAMS multi-level request for real pressure-level ozone."""
    request, meta = _base_request(points, valid_time)
    request.update({
        "variable": ["ozone", "geopotential"],
        "pressure_level": [str(int(p)) for p in pressure_levels_hpa],
    })
    meta["request_role"] = "O3_PRESSURE_LEVEL"
    return request, meta


def build_ads_request(points: list[dict], valid_time: datetime, pressure_levels_hpa=DEFAULT_PRESSURE_LEVELS_HPA) -> tuple[dict, dict]:
    """Backward-compatible alias for the native aerosol pressure-level contract."""
    return build_ads_native_aerosol_request(points, valid_time, pressure_levels_hpa)


def _default_cache_dir() -> Path:
    """Return a process-persistent CAMS cache location.

    The path can be pinned by FIRECLOUD_CAMS_CACHE_DIR.  Otherwise use the
    user's cache directory instead of tempfile so repeated Streamlit analyses
    in the same deployment can reuse already completed ADS retrievals.
    """
    configured = (os.getenv("FIRECLOUD_CAMS_CACHE_DIR") or "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".cache" / "taiwan_firecloud" / "cams"


def _request_cache_path(prefix: str, meta: dict, points: list[dict], cache_dir: str | Path | None = None) -> Path:
    cache = Path(cache_dir).expanduser() if cache_dir else _default_cache_dir()
    cache.mkdir(parents=True, exist_ok=True)
    # Python's built-in hash() is randomized per interpreter process and cannot
    # name a persistent cache.  Use a deterministic SHA-256 signature instead.
    signature_source = "|".join([
        str(meta.get("cams_run_utc", "")),
        str(int(meta.get("cams_forecast_hour", 0))),
        str(prefix),
        ",".join(f"{x:.2f}" for x in route_bbox(points)),
    ])
    sig = hashlib.sha256(signature_source.encode("utf-8")).hexdigest()[:16]
    return cache / f"cams_{prefix}_{str(meta.get('cams_run_utc',''))[:13].replace(':','')}_f{int(meta.get('cams_forecast_hour',0)):03d}_{sig}.grib"


def _retrieve_request(points: list[dict], valid_time: datetime, role: str, request_builder, cache_dir: str | Path | None = None) -> tuple[Path, dict]:
    if not api_client_available():
        raise RuntimeError("cdsapi is not installed; CAMS fetch skipped")
    if not decoder_available():
        raise RuntimeError("ecCodes is not installed; CAMS fetch skipped")
    if not credentials_configured():
        raise RuntimeError("CAMS ADS credentials are not configured (~/.cdsapirc or API key environment)")
    request, meta = request_builder(points, valid_time)
    out = _request_cache_path(role.lower(), meta, points, cache_dir)
    audit = {
        "request_role": role,
        "dataset": DATASET,
        "date": request.get("date"),
        "time": request.get("time"),
        "leadtime_hour": request.get("leadtime_hour"),
        "type": request.get("type"),
        "variable": "|".join(request.get("variable", []) if isinstance(request.get("variable"), list) else [str(request.get("variable", ""))]),
        "pressure_level": "|".join(request.get("pressure_level", []) if isinstance(request.get("pressure_level"), list) else ([str(request.get("pressure_level"))] if request.get("pressure_level") is not None else [])),
        "area_nwse": str(request.get("area")),
        "status": "CACHE_HIT" if out.exists() and out.stat().st_size >= 1000 else "REQUESTING",
        "error": "",
    }
    try:
        if not out.exists() or out.stat().st_size < 1000:
            _make_cdsapi_client().retrieve(DATASET, request, str(out))
            audit["status"] = "OK"
        if not out.exists() or out.stat().st_size < 1000:
            raise RuntimeError("CAMS ADS retrieval did not produce a valid GRIB file")
    except Exception as exc:
        audit["status"] = "FAILED"
        audit["error"] = f"{type(exc).__name__}: {exc}"
        meta["request_audit"] = audit
        raise RuntimeError(audit["error"]) from exc
    meta["cams_file"] = out.name
    meta["request_audit"] = audit
    return out, meta


def download_native_subset(points: list[dict], valid_time: datetime, cache_dir: str | Path | None = None) -> tuple[Path, dict]:
    return _retrieve_request(points, valid_time, "NATIVE_AEROSOL_532NM_PRESSURE_LEVEL", build_ads_native_aerosol_request, cache_dir)


def download_ozone_subset(points: list[dict], valid_time: datetime, cache_dir: str | Path | None = None) -> tuple[Path, dict]:
    return _retrieve_request(points, valid_time, "O3_PRESSURE_LEVEL", build_ads_ozone_request, cache_dir)

def _message_identity(gid, codes_get) -> dict:
    out = {}
    for key in ("shortName", "name", "paramId", "units", "typeOfLevel", "level"):
        try:
            out[key] = codes_get(gid, key)
        except Exception:
            out[key] = None
    return out


def _norm(v) -> str:
    return str(v or "").strip().lower()


def _is_ext532(gid, codes_get) -> bool:
    ident = _message_identity(gid, codes_get)
    short = _norm(ident.get("shortName"))
    name = _norm(ident.get("name"))
    joined = f"{short} {name}"
    # Accept explicit 532-nm aerosol-extinction names/shortNames only.  Do not
    # infer a parameter from unrelated aerosol fields; unknown CAMS encodings
    # are archived by the GRIB inventory for audit instead.
    if short in {"aerext532", "aerext", "aermrext532"}:
        return True
    return "aerosol" in joined and "extinction" in joined and "532" in joined


def _is_ozone(gid, codes_get) -> bool:
    ident = _message_identity(gid, codes_get)
    short = _norm(ident.get("shortName"))
    name = _norm(ident.get("name"))
    if short in {"o3", "go3", "ozone"}:
        return True
    return "ozone" in name and "column" not in name


def _is_geopotential(gid, codes_get) -> bool:
    ident = _message_identity(gid, codes_get)
    short = _norm(ident.get("shortName"))
    name = _norm(ident.get("name"))
    return short in {"z", "gh"} or "geopotential" in name


def inspect_grib_message_inventory(grib_path: str | Path) -> pd.DataFrame:
    """Return a deduplicated, non-secret inventory of GRIB message identities.

    This is diagnostic evidence for CAMS schema changes.  It never contains the
    ADS token, request headers, or raw field values.
    """
    if not decoder_available():
        raise RuntimeError("ecCodes decoder unavailable")
    from eccodes import codes_grib_new_from_file, codes_get, codes_release
    rows = []
    with open(grib_path, "rb") as f:
        while True:
            gid = codes_grib_new_from_file(f)
            if gid is None:
                break
            try:
                ident = _message_identity(gid, codes_get)
                rows.append({
                    "shortName": ident.get("shortName"),
                    "name": ident.get("name"),
                    "paramId": ident.get("paramId"),
                    "units": ident.get("units"),
                    "typeOfLevel": ident.get("typeOfLevel"),
                    "level": ident.get("level"),
                    "recognized_ext532": bool(_is_ext532(gid, codes_get)),
                    "recognized_ozone": bool(_is_ozone(gid, codes_get)),
                    "recognized_geopotential": bool(_is_geopotential(gid, codes_get)),
                })
            finally:
                codes_release(gid)
    if not rows:
        return pd.DataFrame(columns=["shortName","name","paramId","units","typeOfLevel","level","recognized_ext532","recognized_ozone","recognized_geopotential"])
    return pd.DataFrame(rows).drop_duplicates().reset_index(drop=True)


def decode_grib_to_route(grib_path: str | Path, points: list[dict], pressure_levels_hpa=DEFAULT_PRESSURE_LEVELS_HPA) -> pd.DataFrame:
    if not decoder_available():
        raise RuntimeError("ecCodes decoder unavailable")
    from eccodes import codes_grib_new_from_file, codes_get, codes_get_array, codes_release

    wanted = set(float(p) for p in pressure_levels_hpa)
    recs = {
        p["point_id"]: {
            "point_id": p["point_id"], "distance_km": p["distance_km"],
            "direction_offset_deg": p["direction_offset_deg"], "lat": p["lat"], "lon": p["lon"],
            "cams_native_aerosol_source": PROVIDER_NAME,
        }
        for p in points
    }
    nearest_idx = None
    grid_signature = None
    with open(grib_path, "rb") as f:
        while True:
            gid = codes_grib_new_from_file(f)
            if gid is None:
                break
            try:
                typ = str(codes_get(gid, "typeOfLevel"))
                if typ not in ("isobaricInhPa", "isobaricInPa"):
                    continue
                level = float(codes_get(gid, "level"))
                if typ == "isobaricInPa":
                    level /= 100.0
                if level not in wanted:
                    continue
                is_ext = _is_ext532(gid, codes_get)
                is_geo = _is_geopotential(gid, codes_get)
                is_o3 = _is_ozone(gid, codes_get)
                if not (is_ext or is_geo or is_o3):
                    continue
                vals = np.asarray(codes_get_array(gid, "values"), dtype=float)
                lats = np.asarray(codes_get_array(gid, "latitudes"), dtype=float)
                lons = np.asarray(codes_get_array(gid, "longitudes"), dtype=float)
                lons = np.where(lons > 180, lons - 360, lons)
                sig = (len(vals), round(float(lats[0]), 4), round(float(lons[0]), 4))
                if nearest_idx is None or sig != grid_signature:
                    nearest_idx = []
                    for p in points:
                        d2 = (lats - float(p["lat"])) ** 2 + ((lons - float(p["lon"])) * math.cos(math.radians(float(p["lat"])))) ** 2
                        nearest_idx.append(int(np.nanargmin(d2)))
                    grid_signature = sig
                for p, idx in zip(points, nearest_idx):
                    v = float(vals[idx])
                    if is_ext:
                        recs[p["point_id"]][f"cams_aerext532_m1_{int(level)}hPa"] = max(0.0, v) if np.isfinite(v) else np.nan
                    if is_o3:
                        recs[p["point_id"]][f"cams_ozone_kgkg_{int(level)}hPa"] = max(0.0, v) if np.isfinite(v) else np.nan
                    if is_geo:
                        # GRIB geopotential (m2 s-2) is converted to approximate geopotential height.
                        try:
                            units = str(codes_get(gid, "units")).lower()
                        except Exception:
                            units = ""
                        if "m2" in units or "m^2" in units or "s-2" in units:
                            v = v / 9.80665
                        recs[p["point_id"]][f"cams_geopotential_height_m_{int(level)}hPa"] = v
            finally:
                codes_release(gid)
    return pd.DataFrame(recs.values())


def fetch_route_native_aerosol(points: list[dict], valid_time: datetime, cache_dir: str | Path | None = None) -> tuple[pd.DataFrame, dict]:
    path, meta = download_native_subset(points, valid_time, cache_dir=cache_dir)
    df = decode_grib_to_route(path, points)
    ext_cols = [c for c in df.columns if c.startswith("cams_aerext532_m1_")]
    o3_cols = [c for c in df.columns if c.startswith("cams_ozone_kgkg_")]
    try:
        inv = inspect_grib_message_inventory(path)
        meta["grib_message_inventory"] = inv.to_dict(orient="records")
        meta["grib_message_inventory_count"] = int(len(inv))
    except Exception as exc:
        meta["grib_message_inventory"] = []
        meta["grib_inventory_error"] = f"{type(exc).__name__}: {exc}"
    meta.update({
        "native_aerosol_rows": len(df),
        "native_aerosol_levels_decoded": len(ext_cols),
        "native_aerosol_status": "OK" if ext_cols else "MISSING",
        "native_aerosol_error": "" if ext_cols else "CAMS_PRESSURE_LEVEL_AEROSOL_EXTINCTION_532NM_NOT_FOUND_IN_GRIB",
        "native_ozone_rows": len(df),
        "native_ozone_levels_decoded": len(o3_cols),
        "native_ozone_status": "OK" if o3_cols else "MISSING",
        "native_ozone_error": "" if o3_cols else "CAMS_PRESSURE_LEVEL_OZONE_NOT_FOUND_IN_GRIB",
    })
    # V8.4.1.2: aerosol and ozone are independent decode outcomes.  A missing
    # aerosol-extinction message must never discard a valid ozone profile.
    return df, meta

SPECTRAL_AOD_VARIABLES = {
    550: "total_aerosol_optical_depth_550nm",
    645: "total_aerosol_optical_depth_645nm",
    670: "total_aerosol_optical_depth_670nm",
    800: "total_aerosol_optical_depth_800nm",
}


def build_ads_spectral_aod_request(points: list[dict], valid_time: datetime) -> tuple[dict, dict]:
    run, lead = resolve_cams_run_and_lead(valid_time)
    request = {
        "variable": list(SPECTRAL_AOD_VARIABLES.values()),
        "date": run.strftime("%Y-%m-%d"),
        "time": run.strftime("%H:%M"),
        "leadtime_hour": str(int(lead)),
        "type": "forecast",
        "area": route_bbox(points),
        "data_format": "grib",
    }
    return request, {"cams_run_utc": run.isoformat(), "cams_forecast_hour": int(lead), "request_role": "SPECTRAL_COLUMN_AOD"}


def _aod_wavelength_from_message(gid, codes_get) -> int | None:
    vals=[]
    for key in ("shortName", "name"):
        try: vals.append(str(codes_get(gid,key)).lower())
        except Exception: pass
    s=" ".join(vals)
    if "aerosol" not in s or "optical depth" not in s:
        return None
    for wl in SPECTRAL_AOD_VARIABLES:
        if str(wl) in s:
            return wl
    return None


def decode_grib_spectral_aod_to_route(grib_path: str | Path, points: list[dict]) -> pd.DataFrame:
    if not decoder_available():
        raise RuntimeError("ecCodes decoder unavailable")
    from eccodes import codes_grib_new_from_file, codes_get, codes_get_array, codes_release
    recs={p["point_id"]:{"point_id":p["point_id"]} for p in points}
    nearest_idx=None; grid_signature=None
    with open(grib_path,"rb") as f:
        while True:
            gid=codes_grib_new_from_file(f)
            if gid is None: break
            try:
                wl=_aod_wavelength_from_message(gid,codes_get)
                if wl is None: continue
                vals=np.asarray(codes_get_array(gid,"values"),dtype=float)
                lats=np.asarray(codes_get_array(gid,"latitudes"),dtype=float)
                lons=np.asarray(codes_get_array(gid,"longitudes"),dtype=float)
                lons=np.where(lons>180,lons-360,lons)
                sig=(len(vals),round(float(lats[0]),4),round(float(lons[0]),4))
                if nearest_idx is None or sig!=grid_signature:
                    nearest_idx=[]
                    for p in points:
                        d2=(lats-float(p["lat"]))**2 + ((lons-float(p["lon"]))*math.cos(math.radians(float(p["lat"]))))**2
                        nearest_idx.append(int(np.nanargmin(d2)))
                    grid_signature=sig
                for p,idx in zip(points,nearest_idx):
                    v=float(vals[idx]); recs[p["point_id"]][f"aod{wl}"]=max(0.0,v) if np.isfinite(v) else np.nan
            finally:
                codes_release(gid)
    return pd.DataFrame(recs.values())


def _decode_ozone_only(grib_path: str | Path, points: list[dict], pressure_levels_hpa=DEFAULT_PRESSURE_LEVELS_HPA) -> pd.DataFrame:
    df = decode_grib_to_route(grib_path, points, pressure_levels_hpa)
    keep = [c for c in df.columns if c in {"point_id","distance_km","direction_offset_deg","lat","lon"} or c.startswith("cams_ozone_kgkg_") or c.startswith("cams_geopotential_height_m_")]
    return df[keep].copy() if keep else pd.DataFrame()


def _merge_on_point(base: pd.DataFrame, extra: pd.DataFrame) -> pd.DataFrame:
    if base is None or base.empty:
        return extra.copy() if extra is not None else pd.DataFrame()
    if extra is None or extra.empty:
        return base.copy()
    dup = [c for c in extra.columns if c != "point_id" and c in base.columns]
    return base.merge(extra.drop(columns=dup, errors="ignore"), on="point_id", how="outer")


def _audit_row_from_exception(role: str, valid_time: datetime, exc: Exception) -> dict:
    return {"request_role": role, "valid_time": _utc(valid_time).isoformat(), "status": "FAILED", "error": f"{type(exc).__name__}: {exc}"}


def fetch_route_native_aerosol_bundle(points: list[dict], valid_time: datetime, cache_dir: str | Path | None = None) -> tuple[pd.DataFrame, dict]:
    """V8.4.1.3: three fully independent CAMS retrieval contracts.

    A) pressure-level O3 + geopotential
    B) pressure-level aerosol extinction 532 nm + geopotential
    C) single-level/column spectral AOD 550/645/670/800 nm

    A failure in one role never changes the success state of another role.
    """
    base_meta = {**native_aerosol_provider_status(), **{f"ozone_{k}":v for k,v in native_ozone_provider_status().items() if k not in {"provider","dataset"}}}
    meta = dict(base_meta)
    request_audit=[]
    inventory_rows=[]
    merged=pd.DataFrame()

    # B: native aerosol pressure-level request.
    try:
        path, ameta = download_native_subset(points, valid_time, cache_dir=cache_dir)
        request_audit.append(ameta.get("request_audit", {}))
        adf = decode_grib_to_route(path, points)
        a_cols=[c for c in adf.columns if c.startswith("cams_aerext532_m1_")]
        merged=_merge_on_point(merged, adf[[c for c in adf.columns if c in {"point_id","distance_km","direction_offset_deg","lat","lon","cams_native_aerosol_source"} or c.startswith("cams_aerext532_m1_") or c.startswith("cams_geopotential_height_m_")]])
        inv=inspect_grib_message_inventory(path);
        if not inv.empty:
            inv=inv.copy(); inv["request_role"]="NATIVE_AEROSOL_532NM_PRESSURE_LEVEL"; inventory_rows.append(inv)
        meta.update({"native_aerosol_status":"OK" if a_cols else "MISSING","native_aerosol_error":"" if a_cols else "CAMS_PRESSURE_LEVEL_AEROSOL_EXTINCTION_532NM_NOT_FOUND_IN_GRIB","native_aerosol_levels_decoded":len(a_cols),"native_aerosol_rows":len(adf)})
    except Exception as exc:
        request_audit.append(_audit_row_from_exception("NATIVE_AEROSOL_532NM_PRESSURE_LEVEL", valid_time, exc))
        meta.update({"native_aerosol_status":"FAILED","native_aerosol_error":f"{type(exc).__name__}: {exc}","native_aerosol_levels_decoded":0,"native_aerosol_rows":0})

    # A: ozone pressure-level request -- entirely independent of aerosol.
    try:
        path, ometa = download_ozone_subset(points, valid_time, cache_dir=cache_dir)
        request_audit.append(ometa.get("request_audit", {}))
        odf=_decode_ozone_only(path, points)
        o_cols=[c for c in odf.columns if c.startswith("cams_ozone_kgkg_")]
        merged=_merge_on_point(merged, odf)
        inv=inspect_grib_message_inventory(path)
        if not inv.empty:
            inv=inv.copy(); inv["request_role"]="O3_PRESSURE_LEVEL"; inventory_rows.append(inv)
        meta.update({"native_ozone_status":"OK" if o_cols else "MISSING","native_ozone_error":"" if o_cols else "CAMS_PRESSURE_LEVEL_OZONE_NOT_FOUND_IN_GRIB","native_ozone_levels_decoded":len(o_cols),"native_ozone_rows":len(odf)})
    except Exception as exc:
        request_audit.append(_audit_row_from_exception("O3_PRESSURE_LEVEL", valid_time, exc))
        meta.update({"native_ozone_status":"FAILED","native_ozone_error":f"{type(exc).__name__}: {exc}","native_ozone_levels_decoded":0,"native_ozone_rows":0})

    # C: spectral total-column AOD request. No pressure_level is ever attached.
    try:
        request, smeta = build_ads_spectral_aod_request(points, valid_time)
        out = _request_cache_path("spectral_column_aod", smeta, points, cache_dir)
        audit={"request_role":"SPECTRAL_COLUMN_AOD","dataset":DATASET,"date":request.get("date"),"time":request.get("time"),"leadtime_hour":request.get("leadtime_hour"),"type":request.get("type"),"variable":"|".join(request.get("variable",[])),"pressure_level":"","area_nwse":str(request.get("area")),"status":"CACHE_HIT" if out.exists() and out.stat().st_size>=1000 else "REQUESTING","error":""}
        if not out.exists() or out.stat().st_size<1000:
            _make_cdsapi_client().retrieve(DATASET,request,str(out)); audit["status"]="OK"
        if not out.exists() or out.stat().st_size<1000:
            raise RuntimeError("CAMS spectral AOD retrieval did not produce a valid GRIB file")
        sdf=decode_grib_spectral_aod_to_route(out,points)
        merged=_merge_on_point(merged,sdf)
        have=[c for c in ("aod550","aod645","aod670","aod800") if c in merged and merged[c].notna().any()]
        meta.update({"cams_spectral_aod_status":"OK" if len(have)>=2 else "INCOMPLETE","cams_spectral_aod_columns":have,"cams_spectral_aod_error":"" if len(have)>=2 else "CAMS_SPECTRAL_AOD_INCOMPLETE"})
        request_audit.append(audit)
        try:
            inv=inspect_grib_message_inventory(out)
            if not inv.empty:
                inv=inv.copy(); inv["request_role"]="SPECTRAL_COLUMN_AOD"; inventory_rows.append(inv)
        except Exception:
            pass
    except Exception as exc:
        request_audit.append(_audit_row_from_exception("SPECTRAL_COLUMN_AOD", valid_time, exc))
        meta.update({"cams_spectral_aod_status":"FAILED","cams_spectral_aod_columns":[],"cams_spectral_aod_error":f"{type(exc).__name__}: {exc}"})

    meta["cams_request_audit"] = request_audit
    if inventory_rows:
        inv=pd.concat(inventory_rows,ignore_index=True).drop_duplicates().reset_index(drop=True)
        meta["grib_message_inventory"]=inv.to_dict(orient="records")
        meta["grib_message_inventory_count"]=int(len(inv))
    else:
        meta["grib_message_inventory"]=[]
        meta["grib_message_inventory_count"]=0
    return merged, meta



# V8.4.2.2 persistent-cache + retrieval-grace hotfix -------------------------------
# cdsapi.retrieve() may block for minutes while ADS queues a job.  Threads cannot
# reliably cancel that blocking call, so each independent CAMS role runs in its own
# child process.  The parent enforces a real wall-clock deadline and terminates a
# stalled child.  Missing/timeout remains Missing; no zero-value substitution occurs.

def _write_cams_worker_result(result_path: str | Path, payload: dict) -> None:
    """Atomically persist one CAMS child result on local disk.

    V8.4.10.4 deliberately avoids multiprocessing.Queue for DataFrame payloads.
    A Queue timeout only bounds the wait for the first pipe bytes; once a large
    pickle starts crossing the pipe, recv_bytes/unpickle can block the parent and
    freeze both the heartbeat and the wall-clock watchdog.  File-backed IPC keeps
    the entire network/decode/serialization phase inside the killable child.
    """
    result_path = Path(result_path)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = result_path.with_suffix(result_path.suffix + ".tmp")
    with tmp.open("wb") as fh:
        pickle.dump(payload, fh, protocol=pickle.HIGHEST_PROTOCOL)
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except Exception:
            pass
    os.replace(tmp, result_path)


def _read_cams_worker_result(result_path: str | Path) -> dict:
    result_path = Path(result_path)
    with result_path.open("rb") as fh:
        payload = pickle.load(fh)
    if not isinstance(payload, dict):
        raise TypeError(f"CAMS worker payload must be dict, got {type(payload).__name__}")
    return payload


def _checkpoint_tail(path: str | Path | None, max_chars: int = 4000) -> str:
    if not path:
        return ""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")[-max_chars:]
    except Exception:
        return ""


def _write_cams_worker_checkpoint(role: str, status: str, *, elapsed_seconds: float = 0.0,
                                  pid: int | None = None, exit_code: int | None = None,
                                  error: str = "", request_path: str | Path | None = None,
                                  result_path: str | Path | None = None,
                                  stdout_path: str | Path | None = None,
                                  stderr_path: str | Path | None = None) -> None:
    """Persist a tiny worker heartbeat outside Streamlit session state.

    The parent UI can be restarted while an ADS child is being launched or
    waited on.  The old job journal only received the initial ``RUNNING 0s``
    callback, which made a restart indistinguishable from a frozen worker.
    This best-effort file contains no credentials or scientific payload.
    """
    try:
        state_dir = Path(os.getenv("FIRECLOUD_STATE_DIR", ".firecloud_state")).expanduser()
        state_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "role": str(role), "status": str(status),
            "elapsed_seconds": round(float(elapsed_seconds), 3),
            "pid": int(pid) if pid is not None else None,
            "exit_code": int(exit_code) if exit_code is not None else None,
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            "error": str(error or ""),
            "request_path": str(request_path) if request_path else "",
            "result_path": str(result_path) if result_path else "",
            "stdout_path": str(stdout_path) if stdout_path else "",
            "stderr_path": str(stderr_path) if stderr_path else "",
            "stderr_tail": _checkpoint_tail(stderr_path),
        }
        # Keep a latest aggregate checkpoint for the existing UI, and also a
        # role-specific durable checkpoint.  The latter is required when two
        # unique CAMS forecast times are prefetched concurrently: otherwise the
        # last writer would erase the PID/exit/stderr evidence of the other
        # worker.
        safe_role = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(role)).strip("_") or "unknown"
        worker_token = ""
        if request_path:
            try:
                worker_token = re.sub(r"[^A-Za-z0-9_.-]+", "_", Path(request_path).parent.name)
            except Exception:
                worker_token = ""
        targets = [state_dir / "cams_worker_checkpoint.json",
                   state_dir / f"cams_worker_checkpoint_{safe_role}{('_' + worker_token) if worker_token else ''}.json"]
        raw = json.dumps(payload, ensure_ascii=False, indent=2)
        for path in targets:
            tmp = path.with_suffix(path.suffix + f".{os.getpid()}.{uuid.uuid4().hex}.tmp")
            tmp.write_text(raw, encoding="utf-8")
            os.replace(tmp, path)
    except Exception:
        # Diagnostics must never block the provider or physics pipeline.
        pass


def _cams_role_worker(result_path: str, role: str, points: list[dict], valid_time: datetime, cache_dir):
    try:
        # All three CAMS roles use the same external worker contract.  Perform
        # the dependency/credential check before constructing a request so a
        # missing local runtime component cannot turn into a misleading ADS
        # wait (or trigger dozens of pointless adaptive children).
        if not api_client_available():
            _write_cams_worker_result(result_path, {
                "role": role, "status": "FAILED", "df": pd.DataFrame(),
                "meta": {}, "inventory": [],
                "error": "CAMS_PREFLIGHT_CDSAPI_UNAVAILABLE",
            })
            return
        if not decoder_available():
            _write_cams_worker_result(result_path, {
                "role": role, "status": "FAILED", "df": pd.DataFrame(),
                "meta": {}, "inventory": [],
                "error": "CAMS_PREFLIGHT_ECCODES_UNAVAILABLE",
            })
            return
        if not credentials_configured():
            _write_cams_worker_result(result_path, {
                "role": role, "status": "FAILED", "df": pd.DataFrame(),
                "meta": {}, "inventory": [],
                "error": "CAMS_PREFLIGHT_ADS_CREDENTIALS_MISSING",
            })
            return
        if role == "NATIVE_AEROSOL_532NM_PRESSURE_LEVEL":
            path, meta = download_native_subset(points, valid_time, cache_dir=cache_dir)
            df = decode_grib_to_route(path, points)
            keep = [c for c in df.columns if c in {"point_id","distance_km","direction_offset_deg","lat","lon","cams_native_aerosol_source"} or c.startswith("cams_aerext532_m1_") or c.startswith("cams_geopotential_height_m_")]
            df = df[keep].copy()
            cols = [c for c in df.columns if c.startswith("cams_aerext532_m1_")]
            inv = inspect_grib_message_inventory(path)
            _write_cams_worker_result(result_path, {"role": role, "status": "OK" if cols else "MISSING", "df": df,
                              "meta": meta, "levels": len(cols), "rows": len(df),
                              "inventory": inv.to_dict(orient="records") if not inv.empty else [],
                              "error": "" if cols else "CAMS_PRESSURE_LEVEL_AEROSOL_EXTINCTION_532NM_NOT_FOUND_IN_GRIB"})
            return
        if role == "O3_PRESSURE_LEVEL":
            path, meta = download_ozone_subset(points, valid_time, cache_dir=cache_dir)
            df = _decode_ozone_only(path, points)
            cols = [c for c in df.columns if c.startswith("cams_ozone_kgkg_")]
            inv = inspect_grib_message_inventory(path)
            _write_cams_worker_result(result_path, {"role": role, "status": "OK" if cols else "MISSING", "df": df,
                              "meta": meta, "levels": len(cols), "rows": len(df),
                              "inventory": inv.to_dict(orient="records") if not inv.empty else [],
                              "error": "" if cols else "CAMS_PRESSURE_LEVEL_OZONE_NOT_FOUND_IN_GRIB"})
            return
        if role == "SPECTRAL_COLUMN_AOD":
            request, smeta = build_ads_spectral_aod_request(points, valid_time)
            out = _request_cache_path("spectral_column_aod", smeta, points, cache_dir)
            audit={"request_role":role,"dataset":DATASET,"date":request.get("date"),"time":request.get("time"),
                   "leadtime_hour":request.get("leadtime_hour"),"type":request.get("type"),
                   "variable":"|".join(request.get("variable",[])),"pressure_level":"",
                   "area_nwse":str(request.get("area")),
                   "status":"CACHE_HIT" if out.exists() and out.stat().st_size>=1000 else "REQUESTING","error":""}
            if not out.exists() or out.stat().st_size < 1000:
                _make_cdsapi_client().retrieve(DATASET, request, str(out)); audit["status"]="OK"
            if not out.exists() or out.stat().st_size < 1000:
                raise RuntimeError("CAMS spectral AOD retrieval did not produce a valid GRIB file")
            df=decode_grib_spectral_aod_to_route(out, points)
            have=[c for c in ("aod550","aod645","aod670","aod800") if c in df and df[c].notna().any()]
            inv=inspect_grib_message_inventory(out)
            smeta["request_audit"] = audit
            _write_cams_worker_result(result_path, {"role": role, "status": "OK" if len(have)>=2 else "INCOMPLETE", "df": df,
                              "meta": smeta, "columns": have, "rows": len(df),
                              "inventory": inv.to_dict(orient="records") if not inv.empty else [],
                              "error": "" if len(have)>=2 else "CAMS_SPECTRAL_AOD_INCOMPLETE"})
            return
        raise ValueError(f"Unknown CAMS role: {role}")
    except Exception as exc:
        payload={"role": role, "status": "FAILED", "df": pd.DataFrame(), "meta": {},
                 "inventory": [], "error": f"{type(exc).__name__}: {exc}"}
        try:
            _write_cams_worker_result(result_path, payload)
        except Exception:
            # Parent will convert an exited child without a readable result file
            # into CAMS_CHILD_EXITED_WITHOUT_RESULT.
            pass


def _run_cams_role_isolated(role: str, points: list[dict], valid_time: datetime,
                            cache_dir: str | Path | None = None,
                            deadline_seconds: float = 90.0,
                            heartbeat_callback=None) -> dict:
    """Run one CAMS ADS role in a dedicated *external* Python worker.

    V8.4.10.5 removes ``multiprocessing.spawn`` from the Streamlit process.
    On Streamlit, Python's spawn bootstrap can reconstruct the main application
    module in every child and substantially increase transient memory pressure.
    A deployment may then restart the Streamlit process itself, which presents
    to the user as a heartbeat that freezes and the whole page returning to its
    initial state.  The external worker imports only the CAMS provider stack and
    communicates through small request JSON + atomic result pickle files.

    The parent only polls ``Popen`` liveness, so the heartbeat and wall-clock
    deadline remain under the Streamlit process' control.  A timeout terminates
    the whole worker process group; Missing remains Missing.
    """
    deadline_seconds=max(0.2,float(deadline_seconds))
    try:
        heartbeat_seconds=max(0.5,float(os.getenv("FIRECLOUD_CAMS_HEARTBEAT_SECONDS","5")))
    except Exception:
        heartbeat_seconds=5.0

    started=time.monotonic(); res=None

    # Reclaim cyclic garbage before temporarily adding a CAMS worker process.
    # This is a reliability measure only; it does not alter any scientific data.
    try:
        gc.collect()
    except Exception:
        pass

    # Keep the IPC directory under the persistent state root.  A Streamlit
    # rerun can destroy Python objects and temporary directories while the
    # detached analysis worker is still running; durable paths are required to
    # inspect stderr/result files after that interruption.
    state_root = Path(os.getenv("FIRECLOUD_STATE_DIR", ".firecloud_state")).expanduser()
    ipc_dir = state_root / "cams_workers" / uuid.uuid4().hex
    ipc_dir.mkdir(parents=True, exist_ok=True)
    request_path = result_path = stdout_path = stderr_path = None
    proc = None
    try:
        request_path=ipc_dir/"request.json"
        result_path=ipc_dir/"result.pkl"
        stdout_path=ipc_dir/"worker.stdout.log"
        stderr_path=ipc_dir/"worker.stderr.log"
        request_payload={
            "role": str(role),
            "points": points,
            "valid_time": valid_time.isoformat(),
            "cache_dir": None if cache_dir is None else str(Path(cache_dir).expanduser()),
        }
        request_path.write_text(json.dumps(request_payload, ensure_ascii=False), encoding="utf-8")
        cmd=[sys.executable, "-m", "firecloud.providers.cams_worker", str(request_path), str(result_path)]
        env=os.environ.copy()
        env.setdefault("PYTHONUNBUFFERED","1")
        proc=None
        observed_returncode=None

        def _stop_worker(force: bool = False):
            nonlocal proc
            if proc is None or proc.poll() is not None:
                return
            try:
                if os.name == "posix":
                    os.killpg(proc.pid, signal.SIGTERM)
                else:
                    proc.terminate()
            except Exception:
                try: proc.terminate()
                except Exception: pass
            try:
                proc.wait(timeout=1.5 if force else 0.5)
                return
            except Exception:
                pass
            try:
                if os.name == "posix":
                    os.killpg(proc.pid, signal.SIGKILL)
                else:
                    proc.kill()
            except Exception:
                try: proc.kill()
                except Exception: pass
            try: proc.wait(timeout=1.0)
            except Exception: pass

        try:
            with stdout_path.open("wb") as out_fh, stderr_path.open("wb") as err_fh:
                _write_cams_worker_checkpoint(
                    role, "O3_WORKER_STARTING" if role == "O3_PRESSURE_LEVEL" else "CAMS_WORKER_STARTING",
                    request_path=request_path, result_path=result_path,
                    stdout_path=stdout_path, stderr_path=stderr_path,
                )
                proc=subprocess.Popen(
                    cmd,
                    stdout=out_fh,
                    stderr=err_fh,
                    env=env,
                    cwd=str(Path(__file__).resolve().parents[2]),
                    start_new_session=(os.name == "posix"),
                )
                _write_cams_worker_checkpoint(
                    role, "STARTED", pid=proc.pid, request_path=request_path,
                    result_path=result_path, stdout_path=stdout_path, stderr_path=stderr_path,
                )
                if heartbeat_callback:
                    try: heartbeat_callback(role,"RUNNING",0.0)
                    except Exception: pass

                # Do not use Popen.wait(timeout=...) as the heartbeat clock.
                # On some hosted Streamlit/Python combinations we observed the
                # parent freezing inside wait() even though a timeout was
                # supplied, leaving the UI stuck forever at RUNNING 0s.
                # Poll liveness non-blockingly and drive the deadline from the
                # parent's monotonic clock instead.
                next_heartbeat = time.monotonic() + heartbeat_seconds
                poll_sleep = min(0.5, max(0.1, heartbeat_seconds / 10.0))
                while True:
                    now = time.monotonic()
                    elapsed = now - started
                    remaining = deadline_seconds - elapsed
                    if remaining <= 0:
                        timeout_error = "O3_ADS_TIMEOUT" if role == "O3_PRESSURE_LEVEL" else f"CAMS_ADS_WALLCLOCK_DEADLINE_EXCEEDED_{deadline_seconds:.0f}S"
                        res={"role":role,"status":"TIMEOUT_DEFERRED","df":pd.DataFrame(),"meta":{},"inventory":[],
                             "error":timeout_error}
                        _stop_worker(force=True)
                        observed_returncode = proc.poll()
                        _write_cams_worker_checkpoint(role, "O3_ADS_TIMEOUT" if role == "O3_PRESSURE_LEVEL" else "CAMS_ADS_TIMEOUT",
                                                      elapsed_seconds=elapsed, pid=proc.pid,
                                                      exit_code=observed_returncode, error=res["error"],
                                                      request_path=request_path, result_path=result_path,
                                                      stdout_path=stdout_path, stderr_path=stderr_path)
                        break

                    rc = proc.poll()
                    if rc is not None:
                        observed_returncode = rc
                        break

                    if now >= next_heartbeat:
                        _write_cams_worker_checkpoint(role, "RUNNING",
                                                      elapsed_seconds=elapsed, pid=proc.pid,
                                                      request_path=request_path, result_path=result_path,
                                                      stdout_path=stdout_path, stderr_path=stderr_path)
                        if heartbeat_callback:
                            try: heartbeat_callback(role,"RUNNING",elapsed)
                            except Exception: pass
                        # Schedule from 'now' so a delayed callback cannot cause
                        # a rapid burst of catch-up callbacks.
                        next_heartbeat = now + heartbeat_seconds

                    time.sleep(min(poll_sleep, max(0.05, remaining)))

                # Process exited.
                if res is None:
                    if result_path.exists() and result_path.stat().st_size > 0:
                        try:
                            res=_read_cams_worker_result(result_path)
                        except Exception as exc:
                            res={"role":role,"status":"FAILED","df":pd.DataFrame(),"meta":{},"inventory":[],
                                 "error":f"CAMS_WORKER_RESULT_READ_FAILED: {type(exc).__name__}: {exc}"}
                    else:
                        err_tail=""
                        try:
                            err_tail=stderr_path.read_text(encoding="utf-8",errors="replace")[-1500:].replace("\n"," | ")
                        except Exception:
                            pass
                        # Use the value returned by poll().  proc.returncode
                        # can still be None in the narrow interval before the
                        # child is reaped, which previously erased the real
                        # worker failure code from every CAMS audit row.
                        rc_text = observed_returncode if observed_returncode is not None else proc.poll()
                        out_tail=""
                        try:
                            out_tail=stdout_path.read_text(encoding="utf-8",errors="replace")[-1500:].replace("\n"," | ")
                        except Exception:
                            pass
                        detail=""
                        if err_tail: detail += f": stderr={err_tail}"
                        if out_tail: detail += f": stdout={out_tail}"
                        res={"role":role,"status":"FAILED","df":pd.DataFrame(),"meta":{},"inventory":[],
                             "error":f"CAMS_EXTERNAL_WORKER_EXITED_WITHOUT_RESULT_EXITCODE_{rc_text}" + detail}
                        _write_cams_worker_checkpoint(role, "FAILED",
                                                      elapsed_seconds=time.monotonic()-started,
                                                      pid=proc.pid, exit_code=rc_text,
                                                      error=res["error"])
                if res is not None:
                    result_status = str(res.get("status", "FAILED")).upper()
                    result_elapsed = time.monotonic() - started
                    if result_status in {"OK", "CACHE_HIT"}:
                        _write_cams_worker_checkpoint(
                            role, "COMPLETED", elapsed_seconds=result_elapsed,
                            pid=proc.pid, exit_code=observed_returncode,
                            request_path=request_path, result_path=result_path,
                            stdout_path=stdout_path, stderr_path=stderr_path)
                    elif result_status not in {"TIMEOUT_DEFERRED"}:
                        # A child can return a valid result envelope whose status
                        # is FAILED/INCOMPLETE/MISSING (for example preflight or
                        # a GRIB missing the requested field).  Keep the durable
                        # checkpoint aligned with that envelope; otherwise a
                        # later app restart falsely reports STARTED/RUNNING.
                        _write_cams_worker_checkpoint(
                            role, "FAILED", elapsed_seconds=result_elapsed,
                            pid=proc.pid, exit_code=observed_returncode,
                            error=str(res.get("error", "") or result_status),
                            request_path=request_path, result_path=result_path,
                            stdout_path=stdout_path, stderr_path=stderr_path)
        except Exception as exc:
            res={"role":role,"status":"FAILED","df":pd.DataFrame(),"meta":{},"inventory":[],
                 "error":f"CAMS_EXTERNAL_WORKER_START_OR_WATCHDOG_FAILED: {type(exc).__name__}: {exc}"}
            rc = proc.poll() if proc is not None else None
            _write_cams_worker_checkpoint(
                role, "FAILED", elapsed_seconds=time.monotonic()-started,
                pid=proc.pid if proc is not None else None, exit_code=rc,
                error=res["error"], request_path=request_path, result_path=result_path,
                stdout_path=stdout_path, stderr_path=stderr_path)
        finally:
            _stop_worker(force=str((res or {}).get("status","")).upper() in {"TIMEOUT_DEFERRED","FAILED"})
    except Exception as exc:
        res={"role":role,"status":"FAILED","df":pd.DataFrame(),"meta":{},"inventory":[],
             "error":f"CAMS_EXTERNAL_WORKER_UNHANDLED: {type(exc).__name__}: {exc}"}
        _write_cams_worker_checkpoint(
            role, "FAILED", elapsed_seconds=time.monotonic()-started,
            pid=proc.pid if proc is not None else None,
            exit_code=proc.poll() if proc is not None else None,
            error=res["error"], request_path=request_path, result_path=result_path,
            stdout_path=stdout_path, stderr_path=stderr_path)

    if res is None:
        res={"role":role,"status":"FAILED","df":pd.DataFrame(),"meta":{},"inventory":[],
             "error":"CAMS_ROLE_RETURNED_NO_RESULT"}
    res["elapsed_seconds"]=time.monotonic()-started
    res["ipc_mode"]="EXTERNAL_SUBPROCESS_FILE_BACKED_ATOMIC_PICKLE"
    res["worker_mode"]="PYTHON_MODULE_SUBPROCESS_NO_STREAMLIT_SPAWN"
    return res

def _is_retryable_cams_failure(res: dict) -> bool:
    status=str(res.get("status","")).upper()
    err=str(res.get("error","") or "").lower()
    if status in {"OK","CACHE_HIT"}:
        return False
    # A timeout means the remote ADS job may still be alive even after the local
    # child is terminated.  Do not immediately duplicate it.
    if status=="TIMEOUT_DEFERRED":
        return False
    # Permanent request-contract failures should not be hammered repeatedly.
    permanent=("400 client error" in err or "invalid combination" in err or
               "outside 5-day forecast horizon" in err or "not found in grib" in err)
    if permanent:
        return False
    return status in {"FAILED","INCOMPLETE","MISSING"}


def _fetch_route_native_aerosol_bundle_single_tile(points: list[dict], valid_time: datetime,
                                                    cache_dir: str | Path | None = None,
                                                    deadline_seconds: float | None = None,
                                                    progress_callback=None) -> tuple[pd.DataFrame, dict]:
    """Fetch the three CAMS chains with a conservative serial ADS scheduler.

    V8.4.10.5 retains one ADS job at a time and runs each role in an external Python module worker,
    avoiding multiprocessing.spawn of the Streamlit main application.  The previous parallel mode could saturate the
    ADS queue: one tile would succeed, the next three roles would all hit the
    90 s local deadline together, and subsequent tiles would fail while remote
    jobs were still queued.  Completeness is preferred over throughput here.

    Successful role results are never re-requested.  Only a prompt, retryable
    failure is retried once.  TIMEOUT_DEFERRED is *not* immediately retried.
    """
    if deadline_seconds is None:
        try:
            deadline_seconds=float(os.getenv("FIRECLOUD_CAMS_DEADLINE_SECONDS","90"))
        except Exception:
            deadline_seconds=90.0
    deadline_seconds=max(0.2,float(deadline_seconds))
    spectral_role="SPECTRAL_COLUMN_AOD"
    roles=["O3_PRESSURE_LEVEL",spectral_role,"NATIVE_AEROSOL_532NM_PRESSURE_LEVEL"]
    base_meta={**native_aerosol_provider_status(), **{f"ozone_{k}":v for k,v in native_ozone_provider_status().items() if k not in {"provider","dataset"}}}
    meta=dict(base_meta)
    meta["cams_prefetch_policy"]="PERSISTENT_CACHE_FIRST_SERIAL_FILE_IPC_ADS_ROLES_WITH_BOUNDED_RETRY"
    meta["cams_scheduler_mode"]="SERIAL_EXTERNAL_SUBPROCESS_FILE_IPC_ROLES"
    meta["cams_cache_dir"]=str(Path(cache_dir).expanduser() if cache_dir else _default_cache_dir())
    meta["cams_prefetch_deadline_seconds"]=deadline_seconds
    try:
        role_gap=max(0.0,float(os.getenv("FIRECLOUD_CAMS_INTER_ROLE_GAP_SECONDS","2.5")))
    except Exception:
        role_gap=2.5
    # Keep synthetic short-deadline tests and explicit low-latency deployments
    # bounded; production 90 s deadlines retain the configured 2.5 s gap.
    role_gap=min(role_gap, max(0.0, deadline_seconds*0.25))
    try:
        retry_backoff=max(0.0,float(os.getenv("FIRECLOUD_CAMS_RETRY_BACKOFF_SECONDS","8")))
    except Exception:
        retry_backoff=8.0
    try:
        generic_retry_count=max(0,int(os.getenv("FIRECLOUD_CAMS_ROLE_RETRY_COUNT","1")))
    except Exception:
        generic_retry_count=1
    try:
        timeout_cooldown=max(0.0,float(os.getenv("FIRECLOUD_CAMS_TIMEOUT_COOLDOWN_SECONDS","15")))
    except Exception:
        timeout_cooldown=15.0
    timeout_cooldown=min(timeout_cooldown, max(0.0, deadline_seconds*0.25))

    role_results={}
    for idx,role in enumerate(roles):
        if idx and role_gap:
            time.sleep(role_gap)
        res=_run_cams_role_isolated(role,points,valid_time,cache_dir,deadline_seconds, heartbeat_callback=progress_callback)
        if progress_callback:
            try: progress_callback(role,res.get("status","FAILED"),res.get("elapsed_seconds",0.0))
            except Exception: pass

        initial_status=str(res.get("status","")); initial_error=str(res.get("error","") or "")
        initial_elapsed=float(res.get("elapsed_seconds",0.0) or 0.0)
        retry_deadline=deadline_seconds
        if role == spectral_role:
            try:
                retry_count=max(0,int(os.getenv("FIRECLOUD_CAMS_SPECTRAL_RETRY_COUNT",str(generic_retry_count))))
            except Exception:
                retry_count=generic_retry_count
            try:
                retry_deadline=max(0.2,float(os.getenv("FIRECLOUD_CAMS_SPECTRAL_RETRY_DEADLINE_SECONDS",str(deadline_seconds))))
            except Exception:
                retry_deadline=deadline_seconds
        else:
            retry_count=generic_retry_count
        attempts=0
        while attempts < retry_count and _is_retryable_cams_failure(res):
            attempts += 1
            if retry_backoff: time.sleep(retry_backoff)
            if progress_callback:
                def _retry_progress(_r, _s, _e):
                    return progress_callback(str(_r)+"_RETRY", _s, _e)
            else:
                _retry_progress=None
            rr=_run_cams_role_isolated(role,points,valid_time,cache_dir,retry_deadline, heartbeat_callback=_retry_progress)
            rr["retry_attempted"]=True; rr["retry_count"]=attempts
            rr["initial_status"]=initial_status; rr["initial_error"]=initial_error
            rr["initial_elapsed_seconds"]=initial_elapsed
            res=rr
            if progress_callback:
                try: progress_callback(role+"_RETRY",res.get("status","FAILED"),res.get("elapsed_seconds",0.0))
                except Exception: pass
            if str(res.get("status","")).upper()=="OK":
                break

        if str(res.get("status","")).upper()=="TIMEOUT_DEFERRED" and timeout_cooldown:
            # Remote ADS jobs may outlive the terminated local process.  A short
            # cooldown before submitting the next role prevents an immediate
            # cascade of queued requests.
            time.sleep(timeout_cooldown)
        role_results[role]=res

    merged=pd.DataFrame(); request_audit=[]; inventory_rows=[]
    for role in roles:
        res=role_results[role]; rdf=res.get("df")
        if isinstance(rdf,pd.DataFrame) and not rdf.empty:
            merged=_merge_on_point(merged,rdf)
        rmeta=res.get("meta") or {}; audit=dict(rmeta.get("request_audit") or {})
        if not audit:
            audit={"request_role":role,"valid_time":_utc(valid_time).isoformat()}
        audit.update({"final_status":res.get("status","FAILED"),
                      "elapsed_seconds":round(float(res.get("elapsed_seconds",0.0)),3),
                      "timeout":str(res.get("status","")).upper()=="TIMEOUT_DEFERRED",
                      "cache_hit":str(audit.get("status","")).upper()=="CACHE_HIT",
                      "scheduler_mode":"SERIAL_EXTERNAL_SUBPROCESS_FILE_IPC_ROLES",
                      "ipc_mode":res.get("ipc_mode","EXTERNAL_SUBPROCESS_FILE_BACKED_ATOMIC_PICKLE"),
                      "worker_mode":res.get("worker_mode","PYTHON_MODULE_SUBPROCESS_NO_STREAMLIT_SPAWN"),
                      "retry_attempted":bool(res.get("retry_attempted",False)),
                      "retry_count":int(res.get("retry_count",0) or 0),
                      "initial_status":res.get("initial_status",""),
                      "initial_error":res.get("initial_error",""),
                      "initial_elapsed_seconds":round(float(res.get("initial_elapsed_seconds",0.0) or 0.0),3),
                      "error":res.get("error","")})
        request_audit.append(audit)
        inv=res.get("inventory") or []
        if inv:
            idf=pd.DataFrame(inv); idf["request_role"]=role; inventory_rows.append(idf)
        if role=="NATIVE_AEROSOL_532NM_PRESSURE_LEVEL":
            meta.update({"native_aerosol_status":res.get("status","FAILED"),"native_aerosol_error":res.get("error",""),
                         "native_aerosol_levels_decoded":int(res.get("levels",0) or 0),"native_aerosol_rows":int(res.get("rows",0) or 0)})
        elif role=="O3_PRESSURE_LEVEL":
            meta.update({"native_ozone_status":res.get("status","FAILED"),"native_ozone_error":res.get("error",""),
                         "native_ozone_levels_decoded":int(res.get("levels",0) or 0),"native_ozone_rows":int(res.get("rows",0) or 0)})
        else:
            meta.update({"cams_spectral_aod_status":res.get("status","FAILED"),"cams_spectral_aod_columns":res.get("columns",[]),
                         "cams_spectral_aod_error":res.get("error","")})
    meta["cams_request_audit"]=request_audit
    meta["cams_role_elapsed_seconds"]={r:round(float(role_results[r].get("elapsed_seconds",0.0)),3) for r in roles}
    if inventory_rows:
        inv=pd.concat(inventory_rows,ignore_index=True).drop_duplicates().reset_index(drop=True)
        meta["grib_message_inventory"]=inv.to_dict(orient="records"); meta["grib_message_inventory_count"]=int(len(inv))
    else:
        meta["grib_message_inventory"]=[]; meta["grib_message_inventory_count"]=0
    return merged,meta

def split_cams_route_tiles(points: list[dict], max_distance_span_km: float | None = None) -> list[list[dict]]:
    """Split a long Dynamic RT route into provider-safe CAMS request tiles.

    Dynamic physics geometry is not truncated.  Tiling only changes how the
    provider is queried.  All direction offsets at the same route-distance band
    stay in the same tile so the merged route state remains deterministic.
    """
    if not points:
        return []
    if max_distance_span_km is None:
        try:
            max_distance_span_km = float(os.getenv("FIRECLOUD_CAMS_TILE_SPAN_KM", "320"))
        except Exception:
            max_distance_span_km = 320.0
    max_distance_span_km = max(80.0, float(max_distance_span_km))
    ordered = sorted(points, key=lambda x: (float(x.get("distance_km", 0.0)), float(x.get("direction_offset_deg", 0.0))))
    dists = sorted({float(p.get("distance_km", 0.0)) for p in ordered})
    if not dists:
        return [ordered]
    # Keep compact routes in the already validated single-request contract.
    if max(dists) - min(dists) <= max_distance_span_km + 1e-9:
        return [ordered]
    tiles=[]
    start=min(dists)
    maxd=max(dists)
    while start <= maxd + 1e-9:
        end=start + max_distance_span_km
        tile=[p for p in ordered if start-1e-9 <= float(p.get("distance_km",0.0)) <= end+1e-9]
        if tile:
            tiles.append(tile)
        # Advance without overlap. Each logical point is queried once.
        start=end + 1e-6
    return tiles


def _merge_tile_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    frames=[f for f in frames if isinstance(f,pd.DataFrame) and not f.empty]
    if not frames:
        return pd.DataFrame()
    out=pd.concat(frames, ignore_index=True, sort=False)
    if "point_id" in out.columns:
        out=out.drop_duplicates(subset=["point_id"], keep="first")
    sort_cols=[c for c in ("direction_offset_deg","distance_km") if c in out.columns]
    return out.sort_values(sort_cols).reset_index(drop=True) if sort_cols else out.reset_index(drop=True)



def _role_frame_status_ok(res: dict) -> bool:
    return str((res or {}).get("status", "")).upper() in {"OK", "CACHE_HIT"} and isinstance((res or {}).get("df"), pd.DataFrame) and not (res or {}).get("df").empty


def _split_points_by_distance_midpoint(points: list[dict]) -> list[list[dict]]:
    """Split a route segment into two non-overlapping distance subtiles.

    All direction offsets at a given logical distance stay together.  This is
    used only after a provider request fails; the physical Dynamic RT route is
    never shortened or resampled.
    """
    if not points:
        return []
    ordered = sorted(points, key=lambda x: (float(x.get("distance_km", 0.0)), float(x.get("direction_offset_deg", 0.0))))
    dists = sorted({float(p.get("distance_km", 0.0)) for p in ordered})
    if len(dists) <= 1:
        return [ordered]
    mid = len(dists) // 2
    left_d = set(dists[:mid])
    right_d = set(dists[mid:])
    left = [p for p in ordered if float(p.get("distance_km", 0.0)) in left_d]
    right = [p for p in ordered if float(p.get("distance_km", 0.0)) in right_d]
    return [x for x in (left, right) if x]


def _fetch_cams_role_adaptive(points: list[dict], valid_time: datetime, role: str,
                              cache_dir: str | Path | None = None,
                              deadline_seconds: float | None = None,
                              progress_callback=None,
                              max_depth: int | None = None,
                              min_span_km: float | None = None,
                              label_prefix: str = "") -> tuple[pd.DataFrame, list[dict], list[dict], dict]:
    """Fetch one CAMS role using whole-route-first adaptive subdivision.

    V8.4.11 replaces proactive 4-tile × 3-role scheduling with a request planner:
    try the largest scientifically valid route area first, then subdivide only
    the failing role/segment.  Successful parent/child requests are persisted in
    the existing deterministic cache and are never re-requested during the same
    analysis.  Missing children remain Missing; no spatial fabrication occurs.
    """
    if deadline_seconds is None:
        try: deadline_seconds=float(os.getenv("FIRECLOUD_CAMS_DEADLINE_SECONDS","90"))
        except Exception: deadline_seconds=90.0
    deadline_seconds=max(0.2,float(deadline_seconds))
    if max_depth is None:
        try: max_depth=max(0,int(os.getenv("FIRECLOUD_CAMS_ADAPTIVE_MAX_DEPTH","3")))
        except Exception: max_depth=3
    if min_span_km is None:
        try: min_span_km=max(20.0,float(os.getenv("FIRECLOUD_CAMS_ADAPTIVE_MIN_SPAN_KM","120")))
        except Exception: min_span_km=120.0

    audits=[]; inventories=[]; frames=[]
    stats={"requests":0,"successful_requests":0,"failed_requests":0,"adaptive_splits":0,"max_depth_reached":0}

    def recurse(seg: list[dict], depth: int, node: str):
        if not seg:
            return
        d0=min(float(p.get("distance_km",0.0)) for p in seg)
        d1=max(float(p.get("distance_km",0.0)) for p in seg)
        span=max(0.0,d1-d0)
        display=(label_prefix + node + ":" + role) if (label_prefix or node) else role
        def hb(_r,_s,_e):
            if progress_callback:
                try: progress_callback(display, _s, _e)
                except Exception: pass
        res=_run_cams_role_isolated(role,seg,valid_time,cache_dir,deadline_seconds,heartbeat_callback=hb)
        stats["requests"] += 1
        ok=_role_frame_status_ok(res)
        if ok: stats["successful_requests"] += 1
        else: stats["failed_requests"] += 1
        if progress_callback:
            try: progress_callback(display,res.get("status","FAILED"),res.get("elapsed_seconds",0.0))
            except Exception: pass

        meta=res.get("meta") or {}; audit=dict(meta.get("request_audit") or {})
        if not audit:
            audit={"request_role":role,"valid_time":_utc(valid_time).isoformat()}
        audit.update({
            "final_status":res.get("status","FAILED"),
            "elapsed_seconds":round(float(res.get("elapsed_seconds",0.0) or 0.0),3),
            "timeout":str(res.get("status","")).upper()=="TIMEOUT_DEFERRED",
            "cache_hit":str(audit.get("status","")).upper()=="CACHE_HIT",
            "scheduler_mode":"WHOLE_ROUTE_FIRST_ADAPTIVE_SUBTILING",
            "ipc_mode":res.get("ipc_mode","EXTERNAL_SUBPROCESS_FILE_BACKED_ATOMIC_PICKLE"),
            "worker_mode":res.get("worker_mode","PYTHON_MODULE_SUBPROCESS_NO_STREAMLIT_SPAWN"),
            "adaptive_depth":depth,
            "adaptive_node":node,
            "distance_start_km":d0,
            "distance_end_km":d1,
            "distance_span_km":span,
            "logical_points":len(seg),
            "bbox_nwse":route_bbox(seg),
            "error":res.get("error","")
        })
        audits.append(audit)
        for inv in res.get("inventory") or []:
            row=dict(inv); row.update({"request_role":role,"adaptive_depth":depth,"adaptive_node":node,
                                       "distance_start_km":d0,"distance_end_km":d1})
            inventories.append(row)
        if ok:
            frames.append(res["df"])
            return

        # A worker-level failure is independent of geographic extent.  Splitting
        # the same invalid runtime/request contract only multiplies failures and
        # can make one event spend several minutes producing no new information.
        worker_error = str(res.get("error", "") or "")
        if worker_error.startswith(("CAMS_PREFLIGHT_", "CAMS_EXTERNAL_WORKER_", "CAMS_WORKER_")):
            return

        # A timeout may represent a remote ADS job still running.  Do not create
        # duplicate children immediately in that case.  The missing segment stays
        # auditable and can be completed on the next resumed run/cache pass.
        if str(res.get("status","")).upper()=="TIMEOUT_DEFERRED":
            return
        if depth >= max_depth or span <= min_span_km + 1e-9 or len({float(p.get("distance_km",0.0)) for p in seg}) <= 2:
            stats["max_depth_reached"] = max(stats["max_depth_reached"], depth)
            return
        children=_split_points_by_distance_midpoint(seg)
        if len(children) < 2:
            return
        stats["adaptive_splits"] += 1
        for j,child in enumerate(children):
            recurse(child, depth+1, f"{node}.{j+1}" if node else str(j+1))

    recurse(points,0,"ROOT")
    return _merge_tile_frames(frames), audits, inventories, stats


def fetch_route_native_aerosol_bundle_timed(points: list[dict], valid_time: datetime,
                                             cache_dir: str | Path | None = None,
                                             deadline_seconds: float | None = None,
                                             progress_callback=None) -> tuple[pd.DataFrame, dict]:
    """V8.4.11 CAMS Request Planner: whole-route-first, split only on failure.

    Previous releases proactively split the Dynamic route into four 320-km tiles
    and fetched three independent roles for every tile and both time slices.  A
    cold run therefore required up to 24 serial ADS jobs before retries.  This
    planner keeps the same native CAMS variables and physical route, but starts
    with one request per role/time slice.  Only the role/segment that actually
    fails is subdivided.  Successful results are merged on logical point_id.
    """
    if not points:
        return pd.DataFrame(), {"cams_request_planner":"WHOLE_ROUTE_FIRST_ADAPTIVE_SUBTILING","cams_route_requested_points":0,
                                "cams_route_returned_points":0,"cams_route_point_completeness":0.0}
    roles=["O3_PRESSURE_LEVEL","SPECTRAL_COLUMN_AOD","NATIVE_AEROSOL_532NM_PRESSURE_LEVEL"]
    merged=pd.DataFrame(); all_audits=[]; all_inventory=[]; planner_rows=[]
    role_statuses={}; role_stats={}
    try:
        role_gap=max(0.0,float(os.getenv("FIRECLOUD_CAMS_INTER_ROLE_GAP_SECONDS","1.0")))
    except Exception:
        role_gap=1.0

    for i,role in enumerate(roles):
        if i and role_gap:
            time.sleep(role_gap)
        rdf,audits,inventory,stats=_fetch_cams_role_adaptive(
            points, valid_time, role, cache_dir, deadline_seconds,
            progress_callback=progress_callback,
            label_prefix="ADAPTIVE:"
        )
        merged=_merge_on_point(merged,rdf) if not rdf.empty else merged
        all_audits.extend(audits); all_inventory.extend(inventory); role_stats[role]=stats
        req_ids={str(p.get("point_id")) for p in points}
        got_ids=set(rdf.get("point_id",pd.Series(dtype=str)).astype(str)) if isinstance(rdf,pd.DataFrame) and not rdf.empty else set()
        cov=(len(req_ids & got_ids)/len(req_ids)) if req_ids else 0.0
        if cov>=0.999: status="OK"
        elif cov>0: status="PARTIAL"
        else: status="FAILED"
        role_statuses[role]=status
        planner_rows.append({"request_role":role,"status":status,"route_point_completeness":cov,**stats})

    meta={**native_aerosol_provider_status(),
          "cams_prefetch_policy":"WHOLE_ROUTE_FIRST_ADAPTIVE_SUBTILING+PERSISTENT_CACHE+EXTERNAL_WORKER",
          "cams_scheduler_mode":"WHOLE_ROUTE_FIRST_ADAPTIVE_SUBTILING",
          "cams_request_planner":"WHOLE_ROUTE_FIRST_ADAPTIVE_SUBTILING",
          "cams_tiling_enabled":True,
          "cams_tile_count":sum(int(x.get("requests",0)) for x in role_stats.values()),
          "cams_tile_span_km":None,
          "cams_request_audit":all_audits,
          "grib_message_inventory":all_inventory,
          "grib_message_inventory_count":len(all_inventory),
          "cams_planner_audit":planner_rows,
          "native_aerosol_status":role_statuses.get("NATIVE_AEROSOL_532NM_PRESSURE_LEVEL","MISSING"),
          "native_ozone_status":role_statuses.get("O3_PRESSURE_LEVEL","MISSING"),
          "cams_spectral_aod_status":role_statuses.get("SPECTRAL_COLUMN_AOD","MISSING")}

    # Build an adaptive segment audit from every leaf/attempt.  This keeps the
    # existing CASE cams_tile_audit.csv useful without implying fixed 320-km tiles.
    tile_rows=[]
    for a in all_audits:
        tile_rows.append({
            "tile_index":a.get("adaptive_node","ROOT"),
            "tile_count":len(all_audits),
            "request_role":a.get("request_role",""),
            "adaptive_depth":a.get("adaptive_depth",0),
            "distance_start_km":a.get("distance_start_km"),
            "distance_end_km":a.get("distance_end_km"),
            "logical_points":a.get("logical_points"),
            "bbox_nwse":a.get("bbox_nwse"),
            "final_status":a.get("final_status",a.get("status","")),
            "bundle_error":a.get("error","")
        })
    meta["cams_tile_audit"]=tile_rows

    requested_ids={str(p.get("point_id")) for p in points}
    returned_ids=set(merged.get("point_id",pd.Series(dtype=str)).astype(str)) if not merged.empty else set()
    meta["cams_route_requested_points"]=len(requested_ids)
    meta["cams_route_returned_points"]=len(returned_ids & requested_ids)
    meta["cams_route_point_completeness"]=(len(returned_ids & requested_ids)/len(requested_ids)) if requested_ids else 0.0
    return merged,meta
