"""R5.7.39.1 GFS pgrb2b Canvas optical-truth probe provider hotfix.

This provider is intentionally diagnostic-only. It acquires the intermediate
isobaric levels from the NOAA GFS ``pgrb2b.0p25`` product inside the 0--100 km
Canvas domain so that a coarse main-pressure-level ``CF_CLOUD_CONDENSATE_ZERO``
state can be audited against additional *native* CLWMR/ICMR samples.

Hard contract
-------------
* no RH -> condensate;
* no cloud-fraction -> COT;
* no interpolation/extrapolation of CLWMR/ICMR;
* no change to Formation or target-COT readiness in R5.7.39;
* Missing remains Missing.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import json
import math
import os
import pickle
import tempfile

import numpy as np
import pandas as pd
import requests

from .gfs_native import decoder_available, resolve_run_and_lead, route_bbox
from ..native_cloud import NATIVE_CONDENSATE_THRESHOLD_KGKG
from ..runtime_hardening import atomic_write_bytes, stamp_cache_artifact, cache_provenance

PROVIDER_NAME = "NOAA_GFS_0P25_PGRB2B_CANVAS_OPTICAL_PROBE"
PROVIDER_SCHEMA_VERSION = "R5.7.39.1_GFS_PGRB2B_CANVAS_OPTICAL_PROBE_V1"
NOMADS_FILTER_URL = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25b.pl"

# pgrb2b provides the pressure levels that sit between the main pgrb2 levels.
# The probe is restricted to the tropospheric Canvas-relevant subset. 70 hPa is
# already present in the primary request and is therefore not duplicated here.
SUPPLEMENT_PRESSURE_LEVELS_HPA = (
    125, 175, 225, 275, 325, 375, 425, 475, 525,
    575, 625, 675, 725, 775, 825, 875, 925,
)
PROBE_SHORTNAMES = {
    "CLWMR": "cloud_liquid_water_kgkg",
    "ICMR": "cloud_ice_water_kgkg",
    "TCDC": "cloud_fraction",
    "TMP": "temperature_k",
    "HGT": "geopotential_height_m",
}


def _shortname(raw: str) -> str:
    r = str(raw).lower()
    return {
        "clwmr": "CLWMR", "icmr": "ICMR", "tcc": "TCDC", "tcdc": "TCDC",
        "t": "TMP", "tmp": "TMP", "gh": "HGT", "hgt": "HGT",
    }.get(r, str(raw).upper())


def build_nomads_request(run: datetime, lead_hour: int, bbox: tuple[float, float, float, float]):
    left, right, bottom, top = bbox
    params = {
        "file": f"gfs.t{run:%H}z.pgrb2b.0p25.f{int(lead_hour):03d}",
        "dir": f"/gfs.{run:%Y%m%d}/{run:%H}/atmos",
        "subregion": "",
        "leftlon": f"{left:.3f}", "rightlon": f"{right:.3f}",
        "bottomlat": f"{bottom:.3f}", "toplat": f"{top:.3f}",
    }
    for v in PROBE_SHORTNAMES:
        params[f"var_{v}"] = "on"
    for p in SUPPLEMENT_PRESSURE_LEVELS_HPA:
        params[f"lev_{int(p)}_mb"] = "on"
    return NOMADS_FILTER_URL, params


def _request_fingerprint(params: dict) -> str:
    payload = {
        "schema": PROVIDER_SCHEMA_VERSION,
        "file": params.get("file"), "dir": params.get("dir"),
        "bbox": [params.get(k) for k in ("leftlon", "rightlon", "bottomlat", "toplat")],
        "vars": sorted(PROBE_SHORTNAMES),
        "levels": list(SUPPLEMENT_PRESSURE_LEVELS_HPA),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:18]


def _probe_points(points: list[dict]) -> list[dict]:
    out = []
    for p in points:
        try:
            d = float(p.get("distance_km"))
        except Exception:
            continue
        if 0.0 <= d <= 100.0 + 1e-9:
            out.append(dict(p))
    return out


def _cache_dir(cache_dir=None) -> Path:
    configured = str(os.getenv("FIRECLOUD_GFS_PGRB2B_CACHE_DIR", "") or "").strip()
    p = Path(cache_dir or configured or Path(tempfile.gettempdir()) / "taiwan_firecloud_gfs_pgrb2b")
    p.mkdir(parents=True, exist_ok=True)
    return p


def download_probe_subset(points: list[dict], valid_time: datetime, *, cache_dir=None, session=None):
    pts = _probe_points(points)
    if not pts:
        raise RuntimeError("No 0-100 km Canvas-domain route points for GFS pgrb2b optical probe")
    if not decoder_available():
        raise RuntimeError("ecCodes decoder is not available")
    run, lead = resolve_run_and_lead(valid_time)
    bbox = route_bbox(pts, margin_deg=0.35)
    url, params = build_nomads_request(run, lead, bbox)
    fp = _request_fingerprint(params)
    out = _cache_dir(cache_dir) / f"gfs_pgrb2b_{run:%Y%m%d%H}_f{lead:03d}_{fp}.grib2"
    audit = []
    if out.exists() and out.stat().st_size >= 1000:
        prov = cache_provenance(out, provider=PROVIDER_NAME, role="RAW_GRIB", cache_status="CACHE_HIT")
        audit.append({"action": "CACHE_USE", "status": "CACHE_HIT", "cache_file": out.name, "bytes": out.stat().st_size, **{k:v for k,v in prov.items() if str(k).startswith("cache_") or k in {"current_job_id","current_run_mode"}}})
    else:
        s = session or requests.Session()
        r = s.get(url, params=params, timeout=(8, 35))
        r.raise_for_status()
        if len(r.content) < 1000 or b"GRIB" not in r.content[:32]:
            raise RuntimeError(f"NOMADS pgrb2b did not return GRIB2 ({len(r.content)} bytes)")
        atomic_write_bytes(out, r.content)
        stamp_cache_artifact(out, provider=PROVIDER_NAME, role="RAW_GRIB", schema=PROVIDER_SCHEMA_VERSION, qc_state="CACHE_READY")
        prov = cache_provenance(out, provider=PROVIDER_NAME, role="RAW_GRIB", cache_status="DOWNLOAD")
        audit.append({"action": "DOWNLOAD", "status": "DOWNLOADED", "cache_file": out.name, "bytes": len(r.content), "http_status": getattr(r, "status_code", None), **{k:v for k,v in prov.items() if str(k).startswith("cache_") or k in {"current_job_id","current_run_mode"}}})
    meta = {
        "provider": PROVIDER_NAME,
        "provider_schema_version": PROVIDER_SCHEMA_VERSION,
        "gfs_run_utc": run.isoformat(), "gfs_forecast_hour": int(lead),
        "gfs_valid_time_utc": (run + timedelta(hours=lead)).isoformat(),
        "gfs_file": out.name, "gfs_bbox": bbox,
        "requested_pressure_levels_hpa": list(SUPPLEMENT_PRESSURE_LEVELS_HPA),
        "requested_variables": sorted(PROBE_SHORTNAMES),
        "route_point_count": len(pts), "request_audit": audit,
        "probe_contract": "DIRECT_NATIVE_INTERMEDIATE_PRESSURE_LEVEL_EVIDENCE_ONLY;NO_FORMATION_PROMOTION",
    }
    return out, meta


def decode_probe_to_route(grib_path: str | Path, points: list[dict]) -> pd.DataFrame:
    pts = _probe_points(points)
    if not pts:
        return pd.DataFrame()
    if not decoder_available():
        raise RuntimeError("ecCodes decoder is not installed")
    from eccodes import codes_grib_new_from_file, codes_get, codes_get_array, codes_release
    wanted = set(float(x) for x in SUPPLEMENT_PRESSURE_LEVELS_HPA)
    recs = {
        str(p["point_id"]): {
            "point_id": str(p["point_id"]), "distance_km": float(p["distance_km"]),
            "direction_offset_deg": float(p["direction_offset_deg"]),
            "lat": float(p["lat"]), "lon": float(p["lon"]),
            "surface_elevation_m": p.get("surface_elevation_m", p.get("model_surface_elevation_m", np.nan)),
            "probe_source": PROVIDER_NAME,
        } for p in pts
    }
    nearest = None; sig0 = None
    with open(grib_path, "rb") as fh:
        while True:
            gid = codes_grib_new_from_file(fh)
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
                sn = _shortname(codes_get(gid, "shortName"))
                if sn not in PROBE_SHORTNAMES:
                    continue
                vals = np.asarray(codes_get_array(gid, "values"), dtype=float)
                lats = np.asarray(codes_get_array(gid, "latitudes"), dtype=float)
                lons = np.asarray(codes_get_array(gid, "longitudes"), dtype=float)
                lons = np.where(lons > 180.0, lons - 360.0, lons)
                sig = (len(vals), round(float(lats[0]),4), round(float(lons[0]),4))
                if nearest is None or sig != sig0:
                    nearest = []
                    for p in pts:
                        d2 = (lats-float(p["lat"]))**2 + ((lons-float(p["lon"]))*math.cos(math.radians(float(p["lat"]))))**2
                        nearest.append(int(np.nanargmin(d2)))
                    sig0 = sig
                base = PROBE_SHORTNAMES[sn]
                for p, idx in zip(pts, nearest):
                    v = float(vals[idx])
                    if sn == "TCDC":
                        v = v / 100.0 if v > 1.0 + 1e-9 else v
                    recs[str(p["point_id"])][f"{base}_{int(level)}hPa"] = v
            finally:
                codes_release(gid)
    return pd.DataFrame(recs.values())


def _decoded_cache_path(grib_path: Path, points: list[dict]) -> Path:
    sig = hashlib.sha256("|".join(
        f"{p.get('point_id')}:{p.get('distance_km')}:{p.get('direction_offset_deg')}" for p in _probe_points(points)
    ).encode()).hexdigest()[:16]
    d = grib_path.parent / "decoded_route"; d.mkdir(parents=True, exist_ok=True)
    return d / f"{grib_path.stem}_{sig}.pkl"


def fetch_route_canvas_optical_probe(points: list[dict], valid_time: datetime, *, cache_dir=None, session=None):
    path, meta = download_probe_subset(points, valid_time, cache_dir=cache_dir, session=session)
    cp = _decoded_cache_path(Path(path), points)
    df = None
    try:
        if cp.exists() and cp.stat().st_size > 0:
            with cp.open("rb") as fh:
                obj = pickle.load(fh)
            if isinstance(obj, pd.DataFrame):
                df = obj.copy(); meta["decoded_route_cache_status"] = "HIT"
    except Exception:
        df = None
    if df is None:
        df = decode_probe_to_route(path, points)
        try:
            tmp = cp.with_name(f".{cp.name}.tmp")
            with tmp.open("wb") as fh:
                pickle.dump(df, fh, protocol=pickle.HIGHEST_PROTOCOL)
                fh.flush(); os.fsync(fh.fileno())
            os.replace(tmp, cp)
            stamp_cache_artifact(cp, provider=PROVIDER_NAME, role="DECODED_ROUTE", schema=PROVIDER_SCHEMA_VERSION, qc_state="CACHE_READY")
        except Exception:
            pass
        meta["decoded_route_cache_status"] = "MISS_WRITE"
    meta["decoded_route_rows"] = int(len(df))
    meta["status"] = "READY" if not df.empty else "NO_ROUTE_VALUES"
    return df, meta


def build_canvas_probe_evidence(scene, canvases, probe_route: pd.DataFrame, *, valid_time=None, solar_altitude_deg=None) -> pd.DataFrame:
    """Map direct pgrb2b intermediate-level samples into fixed primary Canvas geometry.

    This function does not resolve target COT. It only states whether extra native
    pressure levels inside the primary Canvas vertical envelope carry positive,
    zero, conflicting, or missing condensate evidence.
    """
    if probe_route is None or probe_route.empty:
        return pd.DataFrame()
    by_key = {}
    for _, r in probe_route.iterrows():
        try:
            by_key[(round(float(r["direction_offset_deg"]),6), round(float(r["distance_km"]),6))] = r
        except Exception:
            continue
    layer_by_id = {str(x.layer_id): x for x in getattr(scene, "layers", ())}
    rows = []
    for c in canvases:
        layer = layer_by_id.get(str(c.cloud_layer_id))
        if layer is None:
            continue
        r = by_key.get((round(float(layer.direction_offset_deg),6), round(float(layer.distance_km),6)))
        if r is None:
            continue
        elev = r.get("surface_elevation_m", np.nan)
        try: elev = float(elev)
        except Exception: elev = np.nan
        for p in SUPPLEMENT_PRESSURE_LEVELS_HPA:
            gh = r.get(f"geopotential_height_m_{p}hPa", np.nan)
            t = r.get(f"temperature_k_{p}hPa", np.nan)
            ql = r.get(f"cloud_liquid_water_kgkg_{p}hPa", np.nan)
            qi = r.get(f"cloud_ice_water_kgkg_{p}hPa", np.nan)
            cf = r.get(f"cloud_fraction_{p}hPa", np.nan)
            if not (pd.notna(gh) and math.isfinite(float(gh)) and math.isfinite(elev)):
                continue
            z = (float(gh)-elev)/1000.0
            if z < float(layer.z_base_km)-1e-9 or z > float(layer.z_top_km)+1e-9:
                continue
            q_known = pd.notna(ql) and pd.notna(qi) and math.isfinite(float(ql)) and math.isfinite(float(qi))
            if q_known:
                qt = max(0.0,float(ql)) + max(0.0,float(qi))
                positive = qt >= NATIVE_CONDENSATE_THRESHOLD_KGKG
                qstate = "POSITIVE" if positive else "ZERO"
            else:
                qt = np.nan; positive = False; qstate = "MISSING"
            try:
                f = float(cf); f = f/100.0 if f > 1.0+1e-9 else f
                f = max(0.0,min(1.0,f))
                geom_cloud = f > 0.01
            except Exception:
                f = np.nan; geom_cloud = None
            if qstate == "MISSING": consistency = "OPTICS_MISSING"
            elif geom_cloud is True and qstate == "ZERO": consistency = "CF_CLOUD_CONDENSATE_ZERO"
            elif geom_cloud is False and qstate == "POSITIVE": consistency = "CONDENSATE_CLOUD_CF_LOW"
            elif qstate == "POSITIVE": consistency = "NATIVE_CONDENSATE_POSITIVE"
            else: consistency = "NATIVE_CONDENSATE_ZERO"
            rows.append({
                "time": valid_time,
                "solar_altitude_deg": float(solar_altitude_deg) if solar_altitude_deg is not None else np.nan,
                "canvas_id": c.canvas_id, "cloud_layer_id": c.cloud_layer_id,
                "direction_offset_deg": float(layer.direction_offset_deg), "distance_km": float(layer.distance_km),
                "target_z_base_km": float(layer.z_base_km), "target_z_top_km": float(layer.z_top_km),
                "probe_pressure_hpa": float(p), "probe_altitude_agl_km": float(z),
                "probe_temperature_k": float(t) if pd.notna(t) and math.isfinite(float(t)) else np.nan,
                "probe_cloud_fraction": f,
                "probe_cloud_liquid_water_kgkg": float(ql) if q_known else np.nan,
                "probe_cloud_ice_water_kgkg": float(qi) if q_known else np.nan,
                "probe_total_condensate_kgkg": qt,
                "probe_condensate_state": qstate,
                "probe_evidence_consistency": consistency,
                "probe_positive_condensate": bool(positive),
                "probe_source": PROVIDER_NAME,
                "probe_contract": "DIRECT_NATIVE_PGRB2B_INTERMEDIATE_LEVEL_ONLY;NO_TARGET_COT_PROMOTION;NO_CF_RH_TO_COT",
            })
    return pd.DataFrame(rows)


def summarize_canvas_probe_evidence(table: pd.DataFrame) -> pd.DataFrame:
    if table is None or table.empty:
        return pd.DataFrame()
    rows=[]
    for (tm, ang), g in table.groupby(["time","solar_altitude_deg"], dropna=False, sort=False):
        by_canvas = g.groupby("canvas_id", sort=False)
        any_pos = by_canvas["probe_positive_condensate"].any()
        any_conf = by_canvas["probe_evidence_consistency"].apply(lambda s: s.astype(str).isin(["CF_CLOUD_CONDENSATE_ZERO","CONDENSATE_CLOUD_CF_LOW"]).any())
        missing = by_canvas["probe_condensate_state"].apply(lambda s: s.astype(str).eq("MISSING").any())
        rows.append({
            "time": tm, "solar_altitude_deg": ang,
            "canvas_count_with_probe_levels": int(by_canvas.ngroups),
            "canvas_with_positive_supplement_condensate_count": int(any_pos.sum()),
            "canvas_with_probe_internal_conflict_count": int(any_conf.sum()),
            "canvas_with_probe_missing_condensate_count": int(missing.sum()),
            "probe_level_row_count": int(len(g)),
            "positive_probe_level_count": int(g["probe_positive_condensate"].astype(bool).sum()),
            "probe_contract": "R5.7.39_DIAGNOSTIC_ONLY_NO_FORMATION_PROMOTION",
        })
    return pd.DataFrame(rows)
