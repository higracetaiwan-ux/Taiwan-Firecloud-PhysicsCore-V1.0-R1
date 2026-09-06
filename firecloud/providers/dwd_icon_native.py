"""PhysicsCore V1.0-R5.5.1 DWD ICON Global native cloud-microphysics provider.

Purpose
-------
Provide a *real, public, forecast-native* secondary Target-Canvas optical
source when entitled ECMWF IFS model-level GRIB is not configured.

The provider reads DWD ICON Global model-level QC/QI and only if condensate is
actually positive does it fetch the matching T/P/FI geometry needed to derive
visible-band cloud optical depth.  It never converts RH, cloud cover, geometry,
satellite observations, or surface rain into COT.

Network source
--------------
DWD Open Data, ICON global deterministic GRIB2/BZip2 tree:
  https://opendata.dwd.de/weather/nwp/icon/grib/<cycle>/<var>/

Operational safeguards
----------------------
* fail closed: download/decoder/schema failures -> Missing
* route-scoped nearest-grid extraction only after each GRIB is downloaded
* two-stage fetch: probe QC/QI first, then fetch T/P/FI only for positive layers
* persistent file cache so repeated angle evaluations do not redownload data
* default vertical probe 55..108, approximately the 18..1.4 km tropospheric
  band over low terrain; exact layer AGL geometry comes from FI when available
* no model-level spacing is interpreted as cloud thickness
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path
import bz2
import hashlib
import math
import os
import tempfile
from typing import Iterable

import numpy as np
import pandas as pd
import requests

from ..cloud_optics import condensate_extinction_m1, DEFAULT_LIQUID_REFF_UM, DEFAULT_ICE_REFF_UM

PROVIDER_NAME = "DWD_ICON_GLOBAL_NATIVE_CLOUD_MICROPHYSICS"
PROVIDER_SCHEMA_VERSION = "R5.5_ICON_GLOBAL_NATIVE_CLOUD_V1"
BASE_URL = "https://opendata.dwd.de/weather/nwp/icon/grib"
G0 = 9.80665
R_D = 287.05
_RUNTIME_CACHE: dict[tuple, tuple[pd.DataFrame, dict, pd.DataFrame]] = {}


def decoder_available() -> bool:
    try:
        import eccodes  # noqa: F401
        return True
    except Exception:
        return False


def network_enabled() -> bool:
    raw = os.getenv("FIRECLOUD_DWD_ICON_SECONDARY_ENABLED", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _cache_dir() -> Path:
    raw = os.getenv("FIRECLOUD_DWD_ICON_CACHE_DIR", "").strip()
    p = Path(raw).expanduser() if raw else Path(".firecloud_cache") / "dwd_icon_secondary"
    p.mkdir(parents=True, exist_ok=True)
    return p


def provider_status() -> dict:
    return {
        "provider": PROVIDER_NAME,
        "provider_schema_version": PROVIDER_SCHEMA_VERSION,
        "decoder_available": decoder_available(),
        "network_enabled": network_enabled(),
        "source_mode": "DWD_OPEN_DATA_ICON_GLOBAL_MODEL_LEVEL",
        "cache_dir": str(_cache_dir()),
    }


def _floor_cycle(t: datetime) -> datetime:
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    else:
        t = t.astimezone(timezone.utc)
    return t.replace(hour=(t.hour // 6) * 6, minute=0, second=0, microsecond=0)


def resolve_run_and_lead(valid_time: datetime, now_utc: datetime | None = None) -> tuple[datetime, int]:
    """Choose latest likely-published 6-hour ICON run and integer forecast lead."""
    if valid_time.tzinfo is None:
        vt = valid_time.replace(tzinfo=timezone.utc)
    else:
        vt = valid_time.astimezone(timezone.utc)
    now = now_utc or datetime.now(timezone.utc)
    # Conservative 3 h dissemination latency.  Do not choose a cycle after the valid time.
    latest_available = _floor_cycle(now - timedelta(hours=3))
    run = min(latest_available, _floor_cycle(vt))
    # If event is much farther ahead, the latest available run is still correct.
    lead = int(round((vt - run).total_seconds() / 3600.0))
    if lead < 0:
        # Retrospective request: use the cycle at/before valid time.
        run = _floor_cycle(vt)
        lead = int(round((vt - run).total_seconds() / 3600.0))
    return run, lead


def _model_levels() -> list[int]:
    raw = os.getenv("FIRECLOUD_DWD_ICON_MODEL_LEVELS", "").strip()
    if raw:
        out=[]
        for token in raw.split(","):
            token=token.strip()
            if not token:
                continue
            if "-" in token:
                a,b=token.split("-",1)
                out.extend(range(int(a), int(b)+1))
            else:
                out.append(int(token))
        return sorted(set(x for x in out if 1 <= x <= 120))
    # Approx. 18 km down to 1.4 km, based on DWD ICON standard-level geometry.
    return list(range(55, 109))


def _url(run: datetime, lead: int, level: int, var: str) -> str:
    cycle = run.strftime("%H")
    stamp = run.strftime("%Y%m%d%H")
    v = var.lower()
    return (
        f"{BASE_URL}/{cycle}/{v}/"
        f"icon_global_icosahedral_model-level_{stamp}_{int(lead):03d}_{int(level)}_{var.upper()}.grib2.bz2"
    )


def _cache_path(url: str) -> Path:
    name = url.rsplit("/", 1)[-1]
    # URL-derived filename is stable and readable; hash guards pathological length/collision.
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    return _cache_dir() / f"{h}_{name[:-4]}"  # decompressed .grib2


def _download_decompress(url: str, timeout_s: float = 20.0) -> tuple[Path | None, dict]:
    dest = _cache_path(url)
    if dest.exists() and dest.stat().st_size > 0:
        return dest, {"url":url,"status":"CACHE_HIT","bytes":int(dest.stat().st_size)}
    tmp = None
    try:
        r = requests.get(url, timeout=timeout_s)
        if r.status_code != 200:
            return None, {"url":url,"status":f"HTTP_{r.status_code}","bytes":0}
        raw = bz2.decompress(r.content)
        if not raw:
            return None, {"url":url,"status":"EMPTY_BZ2","bytes":0}
        fd, tmpname = tempfile.mkstemp(prefix="icon_", suffix=".grib2", dir=str(dest.parent))
        os.close(fd); tmp = Path(tmpname)
        tmp.write_bytes(raw)
        tmp.replace(dest)
        return dest, {"url":url,"status":"DOWNLOADED","bytes":int(len(raw))}
    except Exception as exc:
        return None, {"url":url,"status":"FAILED","error":f"{type(exc).__name__}: {exc}","bytes":0}
    finally:
        if tmp is not None and tmp.exists():
            try: tmp.unlink()
            except Exception: pass


def _decode_nearest(path: Path, points: list[dict]) -> tuple[pd.DataFrame, dict]:
    if not decoder_available():
        raise RuntimeError("ecCodes decoder unavailable")
    from eccodes import codes_grib_new_from_file, codes_get, codes_get_array, codes_release
    with open(path, "rb") as f:
        gid = codes_grib_new_from_file(f)
        if gid is None:
            raise RuntimeError("GRIB has no message")
        try:
            vals=np.asarray(codes_get_array(gid,"values"),dtype=float)
            lats=np.asarray(codes_get_array(gid,"latitudes"),dtype=float)
            lons=np.asarray(codes_get_array(gid,"longitudes"),dtype=float)
            lons=np.where(lons>180.0,lons-360.0,lons)
            try: units=str(codes_get(gid,"units"))
            except Exception: units=""
            try: sn=str(codes_get(gid,"shortName"))
            except Exception: sn=""
            try: lev=int(codes_get(gid,"level"))
            except Exception: lev=-1
            rows=[]
            for p in points:
                lat=float(p["lat"]); lon=float(p["lon"])
                d2=(lats-lat)**2 + ((lons-lon)*math.cos(math.radians(lat)))**2
                idx=int(np.nanargmin(d2))
                rows.append({
                    "point_id":p["point_id"],"distance_km":float(p["distance_km"]),
                    "direction_offset_deg":float(p["direction_offset_deg"]),"lat":lat,"lon":lon,
                    "grid_lat":float(lats[idx]),"grid_lon":float(lons[idx]),"value":float(vals[idx]),
                    "model_level":lev,"short_name":sn,"units":units,
                })
            return pd.DataFrame(rows), {"short_name":sn,"level":lev,"units":units,"grid_size":int(len(vals))}
        finally:
            codes_release(gid)


def _fetch_field(run: datetime, lead: int, level: int, var: str, points: list[dict], timeout_s: float) -> tuple[pd.DataFrame, dict]:
    url=_url(run,lead,level,var)
    p,meta=_download_decompress(url,timeout_s=timeout_s)
    meta.update({"variable":var.upper(),"model_level":int(level),"run":run,"lead_hours":int(lead)})
    if p is None:
        return pd.DataFrame(),meta
    try:
        df,dm=_decode_nearest(p,points)
        meta.update(dm); meta["status"] = "OK_" + meta.get("status","READY")
        return df,meta
    except Exception as exc:
        meta["status"]="DECODE_FAILED"; meta["error"]=f"{type(exc).__name__}: {exc}"
        return pd.DataFrame(),meta


def _positive_condensate_levels(qc: dict[int,pd.DataFrame], qi: dict[int,pd.DataFrame], threshold: float=1e-10) -> list[int]:
    out=[]
    for lev in sorted(set(qc)|set(qi)):
        vals=[]
        for m in (qc,qi):
            d=m.get(lev)
            if d is not None and not d.empty:
                vals.extend(pd.to_numeric(d["value"],errors="coerce").dropna().tolist())
        if vals and max(max(0.0,float(x)) for x in vals) > threshold:
            out.append(int(lev))
    return out


def fetch_icon_route_profiles(points: list[dict], valid_time: datetime) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """Fetch native ICON QC/QI and exact local model-level geometry for route points."""
    meta={**provider_status(),"valid_time":valid_time,"status":"UNAVAILABLE"}
    audit=[]
    if not network_enabled():
        meta["status"]="NETWORK_DISABLED"; return pd.DataFrame(),meta,pd.DataFrame()
    if not decoder_available():
        meta["status"]="DECODER_UNAVAILABLE"; return pd.DataFrame(),meta,pd.DataFrame()
    run,lead=resolve_run_and_lead(valid_time)
    meta.update({"run":run,"lead_hours":lead})
    if lead < 0 or lead > 180:
        meta["status"]="LEAD_OUT_OF_RANGE"; return pd.DataFrame(),meta,pd.DataFrame()
    levels=_model_levels(); timeout=float(os.getenv("FIRECLOUD_DWD_ICON_TIMEOUT_S","20")); workers=max(1,min(12,int(os.getenv("FIRECLOUD_DWD_ICON_WORKERS","8"))))
    qc={}; qi={}
    # Stage A: native condensate probe.
    with ThreadPoolExecutor(max_workers=workers) as ex:
        fut={ex.submit(_fetch_field,run,lead,lev,var,points,timeout):(lev,var) for lev in levels for var in ("QC","QI")}
        for f in as_completed(fut):
            lev,var=fut[f]
            try: df,m=f.result()
            except Exception as exc: df,m=pd.DataFrame(),{"status":"FAILED","error":f"{type(exc).__name__}: {exc}"}
            audit.append(m)
            if not df.empty:
                (qc if var=="QC" else qi)[lev]=df
    positive=_positive_condensate_levels(qc,qi)
    meta["probed_level_count"]=len(levels); meta["positive_condensate_level_count"]=len(positive); meta["positive_levels"]=positive
    if not positive:
        meta["status"]="NATIVE_MICROPHYSICS_PRESENT_NO_POSITIVE_CLOUD_OPTICS"
        return pd.DataFrame(),meta,pd.DataFrame(audit)

    # Stage B: fetch exact forecast T/P/FI only for layers where QC/QI is positive.
    needed_fi=sorted(set(x for lev in positive for x in (lev-1,lev,lev+1) if 1<=x<=120))
    fields: dict[str,dict[int,pd.DataFrame]]={"T":{},"P":{},"FI":{}}
    tasks=[(lev,"T") for lev in positive]+[(lev,"P") for lev in positive]+[(lev,"FI") for lev in needed_fi]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        fut={ex.submit(_fetch_field,run,lead,lev,var,points,timeout):(lev,var) for lev,var in tasks}
        for f in as_completed(fut):
            lev,var=fut[f]
            try: df,m=f.result()
            except Exception as exc: df,m=pd.DataFrame(),{"status":"FAILED","error":f"{type(exc).__name__}: {exc}"}
            audit.append(m)
            if not df.empty: fields[var][lev]=df

    def asmap(d: pd.DataFrame | None) -> dict[str,float]:
        if d is None or d.empty: return {}
        return {str(r.point_id):float(r.value) for r in d.itertuples(index=False)}
    rows=[]
    for lev in positive:
        maps={
            "qc":asmap(qc.get(lev)),"qi":asmap(qi.get(lev)),"t":asmap(fields["T"].get(lev)),
            "p":asmap(fields["P"].get(lev)),"fi":asmap(fields["FI"].get(lev)),
            "fim1":asmap(fields["FI"].get(lev-1)),"fip1":asmap(fields["FI"].get(lev+1)),
        }
        for pnt in points:
            pid=str(pnt["point_id"])
            ql=maps["qc"].get(pid,np.nan); ice=maps["qi"].get(pid,np.nan)
            if not (math.isfinite(ql) or math.isfinite(ice)): continue
            ql=max(0.0,float(ql)) if math.isfinite(ql) else 0.0; ice=max(0.0,float(ice)) if math.isfinite(ice) else 0.0
            if ql+ice<=1e-10: continue
            temp=maps["t"].get(pid,np.nan); pres=maps["p"].get(pid,np.nan); fi=maps["fi"].get(pid,np.nan)
            fim1=maps["fim1"].get(pid,np.nan); fip1=maps["fip1"].get(pid,np.nan)
            # P is expected in Pa.  FI is geopotential m2/s2.
            if not all(math.isfinite(float(v)) for v in (temp,pres,fi,fim1,fip1)) or temp<=0 or pres<=0:
                continue
            z=float(fi)/G0/1000.0; za=float(fim1)/G0/1000.0; zb=float(fip1)/G0/1000.0
            z0=min(0.5*(za+z),0.5*(z+zb)); z1=max(0.5*(za+z),0.5*(z+zb))
            if not z1>z0: continue
            rows.append({
                "point_id":pid,"distance_km":float(pnt["distance_km"]),"direction_offset_deg":float(pnt["direction_offset_deg"]),
                "lat":float(pnt["lat"]),"lon":float(pnt["lon"]),"model_level":int(lev),
                "pressure_hpa":float(pres)/100.0,"temperature_k":float(temp),
                "altitude_msl_km":z,"layer_bottom_msl_km":z0,"layer_top_msl_km":z1,
                "qc_kgkg":ql,"qi_kgkg":ice,
            })
    prof=pd.DataFrame(rows)
    meta["profile_row_count"]=int(len(prof))
    meta["status"]="FULL_NATIVE_MICROPHYSICS" if not prof.empty else "POSITIVE_CONDENSATE_GEOMETRY_INCOMPLETE"
    return prof,meta,pd.DataFrame(audit)


def build_secondary_optics_from_profiles(profiles: pd.DataFrame, valid_time: datetime | None=None) -> pd.DataFrame:
    if profiles is None or profiles.empty: return pd.DataFrame()
    rows=[]
    for _,r in profiles.iterrows():
        ql=float(r["qc_kgkg"]); qi=float(r["qi_kgkg"]); t=float(r["temperature_k"]); ph=float(r["pressure_hpa"])
        z0=float(r["layer_bottom_msl_km"]); z1=float(r["layer_top_msl_km"])
        if not all(math.isfinite(v) for v in (ql,qi,t,ph,z0,z1)) or not z1>z0: continue
        rho=ph*100.0/(R_D*t); lwc=ql*rho*1000.0; iwc=qi*rho*1000.0
        # ICON QC/QI are grid-cell mean condensate.  Cloud-fraction conversion is deliberately not used.
        ext=condensate_extinction_m1(lwc,iwc,np.nan,DEFAULT_LIQUID_REFF_UM,DEFAULT_ICE_REFF_UM)
        beta=ext.get("total_extinction_m1",np.nan)
        if not math.isfinite(float(beta)) or float(beta)<=0: continue
        cot=float(beta)*(z1-z0)*1000.0
        if cot<=0: continue
        phase="MIXED" if ql>1e-10 and qi>1e-10 else ("ICE" if qi>1e-10 else "LIQUID")
        reff=DEFAULT_ICE_REFF_UM if phase=="ICE" else (0.5*(DEFAULT_LIQUID_REFF_UM+DEFAULT_ICE_REFF_UM) if phase=="MIXED" else DEFAULT_LIQUID_REFF_UM)
        rows.append({
            "provider":"DWD","model":"ICON_GLOBAL","source_kind":"FORECAST_MODEL_NATIVE_OPTICS","valid_time":valid_time,
            "direction_offset_deg":float(r["direction_offset_deg"]),"distance_km":float(r["distance_km"]),
            "z_base_km":z0,"z_top_km":z1,"cot":cot,"effective_radius_um":reff,"phase":phase,
            "optical_evidence":"FULL","provenance":"DWD_ICON_GLOBAL_NATIVE_QC_QI_FI_T_P_DERIVED_COT_ASSUMED_REFF",
            "status":"OK","qc_kgkg":ql,"qi_kgkg":qi,"model_level":int(r["model_level"]),"pressure_hpa":ph,
            "assumed_liquid_reff_um":DEFAULT_LIQUID_REFF_UM,"assumed_ice_reff_um":DEFAULT_ICE_REFF_UM,
            "cloud_optical_model":"NATIVE_CONDENSATE_GEOMETRIC_OPTICS_ASSUMED_REFF",
            "sampling_distance_is_cloud_width":False,
        })
    return pd.DataFrame(rows)


def fetch_route_secondary_target_optics(points: list[dict], valid_time: datetime) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    meta={**provider_status(),"valid_time":valid_time,"status":"UNAVAILABLE"}
    try:
        run,lead=resolve_run_and_lead(valid_time)
        route_sig=tuple((str(p.get("point_id")), round(float(p.get("lat",0.0)),5), round(float(p.get("lon",0.0)),5)) for p in points)
        key=(run.strftime("%Y%m%d%H"),int(lead),route_sig,tuple(_model_levels()))
        if key in _RUNTIME_CACHE:
            optics0,meta0,audit0=_RUNTIME_CACHE[key]
            optics=optics0.copy(); audit=audit0.copy(); meta={**meta0,"valid_time":valid_time,"runtime_cache_status":"HIT"}
            if not optics.empty: optics["valid_time"]=valid_time
            return optics,meta,audit
        prof,dm,audit=fetch_icon_route_profiles(points,valid_time)
        meta.update(dm)
        optics=build_secondary_optics_from_profiles(prof,valid_time)
        meta["secondary_optical_record_count"]=int(len(optics)); meta["runtime_cache_status"]="MISS"
        _RUNTIME_CACHE[key]=(optics.copy(),dict(meta),audit.copy())
        return optics,meta,audit
    except Exception as exc:
        meta["status"]="FAILED"; meta["error"]=f"{type(exc).__name__}: {exc}"
        return pd.DataFrame(),meta,pd.DataFrame()
