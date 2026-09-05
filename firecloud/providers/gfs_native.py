"""Operational NOAA GFS native-cloud GRIB2 provider for Taiwan Firecloud V8.1.2.

Downloads a small NOMADS 0.25° GRIB2 subset around the Firecloud route and decodes
pressure-level CLWMR/ICMR/TCDC/TMP/RH/HGT with ecCodes. Missing native fields remain
missing; this module never derives condensate from RH or low/mid/high cloud cover.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import importlib.util, math, os, tempfile
import numpy as np
import pandas as pd
import requests

NATIVE_PROVIDER_NAME = "NOAA_GFS_0P25_NOMADS_GRIB2_CLWMR_ICMR"
NOMADS_FILTER_URL = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl"
GFS_NATIVE_SHORTNAMES = {
    "CLWMR":"cloud_liquid_water_kgkg", "ICMR":"cloud_ice_water_kgkg",
    "TCDC":"cloud_fraction", "TMP":"temperature_k",
    "RH":"relative_humidity_pct", "HGT":"geopotential_height_m",
}
DEFAULT_PRESSURE_LEVELS_HPA = (1000,975,950,925,900,850,800,750,700,650,600,550,500,450,400,350,300,250,200,150,100,70,50,30)


def decoder_available() -> bool:
    return importlib.util.find_spec("eccodes") is not None


def native_provider_status() -> dict:
    return {
        "provider": NATIVE_PROVIDER_NAME,
        "decoder_available": decoder_available(),
        "native_fields": list(GFS_NATIVE_SHORTNAMES),
        "transport": "NCEP_NOMADS_GRIB_FILTER",
        "grid": "GFS_0P25",
        "fallback_policy": "EXPLICIT_OPEN_METEO_PRESSURE_PROFILE; NEVER RH_AS_NATIVE_CONDENSATE",
    }


def _utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def resolve_run_and_lead(valid_time: datetime, now_utc: datetime | None = None) -> tuple[datetime,int]:
    """Resolve a likely-available GFS cycle and nearest 3-hour forecast lead.

    Operational latency is conservatively treated as 5 h. For future targets the
    latest likely-published cycle is used; for past targets a cycle no later than
    the target is used. Forecast lead is rounded to the nearest 3 h.
    """
    target = _utc(valid_time)
    now = _utc(now_utc or datetime.now(timezone.utc))
    anchor = min(target, now - timedelta(hours=5))
    cycle_hour = max(h for h in (0,6,12,18) if h <= anchor.hour)
    run = anchor.replace(hour=cycle_hour, minute=0, second=0, microsecond=0)
    lead = int(round((target-run).total_seconds()/3600/3)*3)
    if lead < 0:
        run -= timedelta(hours=6); lead = int(round((target-run).total_seconds()/3600/3)*3)
    if lead > 384:
        raise ValueError(f"GFS target is outside supported forecast horizon: f{lead:03d}")
    return run, lead


def build_nomads_request(run: datetime, lead_hour: int, bbox: tuple[float,float,float,float],
                         pressure_levels_hpa=DEFAULT_PRESSURE_LEVELS_HPA) -> tuple[str,dict]:
    left, right, bottom, top = bbox
    params = {
        "file": f"gfs.t{run:%H}z.pgrb2.0p25.f{lead_hour:03d}",
        "dir": f"/gfs.{run:%Y%m%d}/{run:%H}/atmos",
        "subregion": "",
        "leftlon": f"{left:.3f}", "rightlon": f"{right:.3f}",
        "bottomlat": f"{bottom:.3f}", "toplat": f"{top:.3f}",
    }
    for v in GFS_NATIVE_SHORTNAMES: params[f"var_{v}"] = "on"
    for p in pressure_levels_hpa: params[f"lev_{int(p)}_mb"] = "on"
    return NOMADS_FILTER_URL, params


def route_bbox(points: list[dict], margin_deg: float=0.5) -> tuple[float,float,float,float]:
    lats=[float(p['lat']) for p in points]; lons=[float(p['lon']) for p in points]
    return (min(lons)-margin_deg, max(lons)+margin_deg, min(lats)-margin_deg, max(lats)+margin_deg)


def download_native_subset(points: list[dict], valid_time: datetime, cache_dir: str|Path|None=None,
                           session: requests.Session|None=None) -> tuple[Path,dict]:
    if not decoder_available():
        raise RuntimeError("ecCodes decoder is not available; native GFS fetch skipped before network download")
    run, lead = resolve_run_and_lead(valid_time)
    bbox = route_bbox(points)
    url, params = build_nomads_request(run, lead, bbox)
    cache = Path(cache_dir or Path(tempfile.gettempdir())/"taiwan_firecloud_gfs")
    cache.mkdir(parents=True, exist_ok=True)
    out = cache/f"gfs_{run:%Y%m%d%H}_f{lead:03d}_{abs(hash(tuple(round(x,2) for x in bbox)))%10**8}.grib2"
    if not out.exists() or out.stat().st_size < 1000:
        s=session or requests.Session()
        r=s.get(url, params=params, timeout=(8, 35))
        r.raise_for_status()
        ctype=(r.headers.get('content-type') or '').lower()
        if len(r.content)<1000 or b'GRIB' not in r.content[:32]:
            raise RuntimeError(f"NOMADS did not return GRIB2 ({len(r.content)} bytes, {ctype})")
        out.write_bytes(r.content)
    meta={"gfs_run_utc":run.isoformat(),"gfs_forecast_hour":lead,"gfs_valid_time_utc":(run+timedelta(hours=lead)).isoformat(),"gfs_bbox":bbox,"gfs_file":out.name}
    return out,meta


def _shortname(raw: str) -> str:
    r=raw.lower()
    return {"clwmr":"CLWMR","icmr":"ICMR","tcc":"TCDC","tcdc":"TCDC","t":"TMP","tmp":"TMP","r":"RH","rh":"RH","gh":"HGT","hgt":"HGT"}.get(r, raw.upper())


def decode_grib_to_route(grib_path: str|Path, points: list[dict], pressure_levels_hpa=DEFAULT_PRESSURE_LEVELS_HPA) -> pd.DataFrame:
    if not decoder_available():
        raise RuntimeError("ecCodes decoder is not installed; install the 'eccodes' Python package")
    from eccodes import codes_grib_new_from_file, codes_get, codes_get_array, codes_release
    wanted=set(float(p) for p in pressure_levels_hpa)
    recs={p['point_id']:{"point_id":p['point_id'],"distance_km":p['distance_km'],"direction_offset_deg":p['direction_offset_deg'],"lat":p['lat'],"lon":p['lon'],"native_profile_source":NATIVE_PROVIDER_NAME} for p in points}
    nearest_idx=None; grid_signature=None
    with open(grib_path,'rb') as f:
        while True:
            gid=codes_grib_new_from_file(f)
            if gid is None: break
            try:
                typ=str(codes_get(gid,'typeOfLevel'))
                if typ not in ('isobaricInhPa','isobaricInPa'): continue
                level=float(codes_get(gid,'level'))
                if typ=='isobaricInPa': level/=100.0
                if level not in wanted: continue
                sn=_shortname(str(codes_get(gid,'shortName')))
                if sn not in GFS_NATIVE_SHORTNAMES: continue
                vals=np.asarray(codes_get_array(gid,'values'),dtype=float)
                lats=np.asarray(codes_get_array(gid,'latitudes'),dtype=float)
                lons=np.asarray(codes_get_array(gid,'longitudes'),dtype=float)
                lons=np.where(lons>180,lons-360,lons)
                sig=(len(vals),round(float(lats[0]),4),round(float(lons[0]),4))
                if nearest_idx is None or sig!=grid_signature:
                    nearest_idx=[]
                    for p in points:
                        # small NOMADS subset: Euclidean lat/lon nearest is sufficient at 0.25° grid
                        d2=(lats-float(p['lat']))**2 + ((lons-float(p['lon']))*math.cos(math.radians(float(p['lat']))))**2
                        nearest_idx.append(int(np.nanargmin(d2)))
                    grid_signature=sig
                keybase=GFS_NATIVE_SHORTNAMES[sn]
                for p,idx in zip(points,nearest_idx):
                    v=float(vals[idx])
                    if sn=='TCDC': v=v/100.0 if v>1.0 else v
                    recs[p['point_id']][f"{keybase}_{int(level)}hPa"]=v
            finally:
                codes_release(gid)
    return pd.DataFrame(recs.values())


def fetch_route_native(points: list[dict], valid_time: datetime, cache_dir: str|Path|None=None) -> tuple[pd.DataFrame,dict]:
    """End-to-end NOMADS download + ecCodes decode for one event time."""
    path,meta=download_native_subset(points,valid_time,cache_dir=cache_dir)
    df=decode_grib_to_route(path,points)
    meta.update({"native_rows":len(df),"native_decoder":"eccodes","native_status":"OK"})
    return df,meta


def merge_native_into_snapshot(snapshot: pd.DataFrame, native: pd.DataFrame) -> pd.DataFrame:
    """Merge native GFS state and backfill the canonical pressure-profile contract.

    V8.4.11.1 makes NOAA GFS the primary thermodynamic pressure-profile source.
    Open-Meteo remains the lightweight operational/surface provider and a
    deferred pressure-profile fallback only when GFS is unavailable.  Canonical
    column names are backfilled from native GRIB without overwriting a real
    provider value that is already present.
    """
    if snapshot.empty or native.empty:
        return snapshot.copy()
    n=native.drop(columns=[c for c in ['distance_km','direction_offset_deg','lat','lon'] if c in native.columns],errors='ignore')
    out=snapshot.merge(n,on='point_id',how='left')
    out['pressure_profile_primary_source'] = NATIVE_PROVIDER_NAME
    for p in DEFAULT_PRESSURE_LEVELS_HPA:
        mapping = {
            f'temperature_{p}hPa': f'temperature_k_{p}hPa',
            f'relative_humidity_{p}hPa': f'relative_humidity_pct_{p}hPa',
            f'geopotential_height_{p}hPa': f'geopotential_height_m_{p}hPa',
        }
        for canonical, native_col in mapping.items():
            if native_col not in out.columns:
                continue
            if canonical not in out.columns:
                out[canonical] = np.nan
            can = pd.to_numeric(out[canonical], errors='coerce')
            nat = pd.to_numeric(out[native_col], errors='coerce')
            out[canonical] = can.where(can.notna(), nat)
        native_cc=f'cloud_fraction_{p}hPa'
        canonical_cc=f'cloud_cover_{p}hPa'
        if native_cc in out.columns:
            if canonical_cc not in out.columns:
                out[canonical_cc]=np.nan
            can=pd.to_numeric(out[canonical_cc],errors='coerce')
            nat=pd.to_numeric(out[native_cc],errors='coerce')
            # Native decoder stores cloud fraction in 0..1. Canonical Open-Meteo
            # pressure cloud cover uses percent. Preserve values that are already
            # present and convert only the native fallback.
            nat_pct=np.where(nat.notna(), np.where(nat<=1.0+1e-9, nat*100.0, nat), np.nan)
            out[canonical_cc]=can.where(can.notna(), pd.Series(nat_pct,index=out.index))
    return out
