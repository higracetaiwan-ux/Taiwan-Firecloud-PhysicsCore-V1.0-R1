"""Operational NOAA GFS native-cloud GRIB2 provider for Taiwan Firecloud V8.1.2.

Downloads a small NOMADS 0.25° GRIB2 subset around the Firecloud route and decodes
pressure-level CLWMR/ICMR/TCDC/TMP/RH/HGT with ecCodes. Missing native fields remain
missing; this module never derives condensate from RH or low/mid/high cloud cover.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import importlib.util, math, os, tempfile, hashlib, json
import numpy as np
import pandas as pd
import requests

NATIVE_PROVIDER_NAME = "NOAA_GFS_0P25_NOMADS_GRIB2_CLWMR_ICMR"
NOMADS_FILTER_URL = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl"
GFS_PROVIDER_SCHEMA_VERSION = "R4.5_NATIVE_CONDENSATE_V2"
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
        "provider_schema_version": GFS_PROVIDER_SCHEMA_VERSION,
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




def _request_schema_fingerprint(params: dict, pressure_levels_hpa=DEFAULT_PRESSURE_LEVELS_HPA) -> str:
    payload = {
        "schema": GFS_PROVIDER_SCHEMA_VERSION,
        "variables": sorted(GFS_NATIVE_SHORTNAMES.keys()),
        "levels_hpa": [int(x) for x in pressure_levels_hpa],
        "file": params.get("file"),
        "dir": params.get("dir"),
        "leftlon": params.get("leftlon"),
        "rightlon": params.get("rightlon"),
        "bottomlat": params.get("bottomlat"),
        "toplat": params.get("toplat"),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]


def grib_message_inventory(grib_path: str|Path) -> list[dict]:
    """Return a compact ecCodes message inventory for required GFS native fields."""
    if not decoder_available():
        return []
    from eccodes import codes_grib_new_from_file, codes_get, codes_release
    counts = {}
    with open(grib_path, 'rb') as f:
        while True:
            gid = codes_grib_new_from_file(f)
            if gid is None:
                break
            try:
                try: raw_sn = str(codes_get(gid, 'shortName'))
                except Exception: raw_sn = ''
                sn = _shortname(raw_sn)
                try: typ = str(codes_get(gid, 'typeOfLevel'))
                except Exception: typ = ''
                try: level = float(codes_get(gid, 'level'))
                except Exception: level = float('nan')
                if typ == 'isobaricInPa' and math.isfinite(level):
                    level /= 100.0
                try: name = str(codes_get(gid, 'name'))
                except Exception: name = ''
                try: units = str(codes_get(gid, 'units'))
                except Exception: units = ''
                key=(sn,name,typ,level,units)
                counts[key]=counts.get(key,0)+1
            finally:
                codes_release(gid)
    rows=[]
    for (sn,name,typ,level,units),cnt in counts.items():
        rows.append({
            'shortName':sn,'name':name,'typeOfLevel':typ,'level':level,'units':units,
            'message_count':cnt,'recognized_as':GFS_NATIVE_SHORTNAMES.get(sn,''),
        })
    return sorted(rows,key=lambda r:(r['shortName'],str(r['typeOfLevel']),float(r['level']) if isinstance(r['level'],(int,float)) and math.isfinite(r['level']) else 1e9))


def _field_completeness_from_inventory(inventory: list[dict], pressure_levels_hpa=DEFAULT_PRESSURE_LEVELS_HPA) -> list[dict]:
    wanted=set(float(x) for x in pressure_levels_hpa)
    rows=[]
    for sn in GFS_NATIVE_SHORTNAMES:
        levels=set()
        messages=0
        for r in inventory:
            if r.get('shortName') != sn or r.get('typeOfLevel') not in ('isobaricInhPa','isobaricInPa'):
                continue
            try: lev=float(r.get('level'))
            except Exception: continue
            if lev in wanted:
                levels.add(lev); messages += int(r.get('message_count',0) or 0)
        rows.append({
            'field':sn, 'canonical_field':GFS_NATIVE_SHORTNAMES[sn],
            'pressure_level_count':len(levels), 'message_count':messages,
            'required_for_native_condensate':sn in ('CLWMR','ICMR'),
            'status':'READY' if len(levels)>0 else 'MISSING',
        })
    return rows


def _inventory_has_required_condensate(inventory: list[dict]) -> bool:
    comp={r['field']:r for r in _field_completeness_from_inventory(inventory)}
    return comp.get('CLWMR',{}).get('pressure_level_count',0)>0 and comp.get('ICMR',{}).get('pressure_level_count',0)>0

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
    schema_fp=_request_schema_fingerprint(params)
    bbox_fp=hashlib.sha256(json.dumps([round(x,3) for x in bbox]).encode()).hexdigest()[:10]
    out = cache/f"gfs_{run:%Y%m%d%H}_f{lead:03d}_{bbox_fp}_{schema_fp}.grib2"
    audit=[]
    s=session or requests.Session()

    def _download(reason: str):
        r=s.get(url, params=params, timeout=(8, 35))
        r.raise_for_status()
        ctype=(r.headers.get('content-type') or '').lower()
        if len(r.content)<1000 or b'GRIB' not in r.content[:32]:
            raise RuntimeError(f"NOMADS did not return GRIB2 ({len(r.content)} bytes, {ctype})")
        out.write_bytes(r.content)
        audit.append({'action':'DOWNLOAD','reason':reason,'cache_file':out.name,'bytes':len(r.content),'http_status':getattr(r,'status_code',None)})

    cache_status='MISS'
    if out.exists() and out.stat().st_size >= 1000:
        cache_status='HIT'
        inv=grib_message_inventory(out)
        if _inventory_has_required_condensate(inv):
            audit.append({'action':'CACHE_USE','reason':'REQUIRED_FIELDS_VALID','cache_file':out.name,'bytes':out.stat().st_size})
        else:
            cache_status='INVALID_REQUIRED_FIELDS'
            audit.append({'action':'CACHE_INVALID_REQUIRED_FIELDS','reason':'CLWMR_OR_ICMR_MISSING','cache_file':out.name,'bytes':out.stat().st_size})
            try: out.unlink()
            except Exception: pass
            _download('CACHE_INVALID_REQUIRED_FIELDS')
    else:
        _download('CACHE_MISS_OR_TOO_SMALL')

    inventory=grib_message_inventory(out)
    completeness=_field_completeness_from_inventory(inventory)
    condensate_ok=_inventory_has_required_condensate(inventory)
    meta={
        "gfs_run_utc":run.isoformat(),"gfs_forecast_hour":lead,
        "gfs_valid_time_utc":(run+timedelta(hours=lead)).isoformat(),"gfs_bbox":bbox,"gfs_file":out.name,
        "gfs_cache_status":cache_status,"gfs_request_schema_version":GFS_PROVIDER_SCHEMA_VERSION,
        "gfs_request_schema_fingerprint":schema_fp,"gfs_requested_variables":sorted(GFS_NATIVE_SHORTNAMES),
        "gfs_requested_pressure_levels_hpa":[int(x) for x in DEFAULT_PRESSURE_LEVELS_HPA],
        "gfs_grib_message_inventory":inventory,"gfs_native_field_completeness":completeness,
        "gfs_native_request_audit":audit,"gfs_required_condensate_fields_present":condensate_ok,
    }
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
    required_present=bool(meta.get("gfs_required_condensate_fields_present"))
    cl_cols=[c for c in df.columns if c.startswith("cloud_liquid_water_kgkg_")]
    ic_cols=[c for c in df.columns if c.startswith("cloud_ice_water_kgkg_")]
    cl_nonnull=int(df[cl_cols].notna().sum().sum()) if cl_cols else 0
    ic_nonnull=int(df[ic_cols].notna().sum().sum()) if ic_cols else 0
    if not required_present:
        status="MISSING_REQUIRED_CONDENSATE_FIELDS"
    elif cl_nonnull==0 or ic_nonnull==0:
        status="CONDENSATE_FIELDS_DECODED_BUT_NO_ROUTE_VALUES"
    else:
        status="FULL_NATIVE_MICROPHYSICS"
    meta.update({
        "native_rows":len(df),"native_decoder":"eccodes","native_status":status,
        "native_clwmr_nonnull_values":cl_nonnull,"native_icmr_nonnull_values":ic_nonnull,
    })
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
        # R4.5.1: canonical native-condensate contract is explicitly kg/kg.
        # Native ecCodes decode already emits these names; the legacy aliases are
        # accepted only as an input-compatibility fallback for older CASE/replay data.
        for phase_name in ('liquid', 'ice'):
            canonical_q=f'cloud_{phase_name}_water_kgkg_{p}hPa'
            legacy_q=f'cloud_{phase_name}_water_{p}hPa'
            if canonical_q not in out.columns and legacy_q in out.columns:
                out[canonical_q]=pd.to_numeric(out[legacy_q],errors='coerce')
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
