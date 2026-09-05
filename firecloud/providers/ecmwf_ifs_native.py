"""PhysicsCore V1.0-R5.2 ECMWF IFS native cloud-microphysics provider.

The provider is deliberately fail-closed.  It consumes a *forecast* IFS GRIB
containing model-level CLWC/CIWC/CC/T/Q plus hybrid coefficients and surface
pressure/geopotential, reconstructs model-level AGL geometry, and derives a
visible-band vertical cloud optical depth from native condensate using the same
explicit effective-radius assumptions used by PhysicsCore's GFS native bridge.

No cloud fraction, RH, cloud-base geometry, satellite image, or rain rate is
converted into COT.  If the required native fields or hybrid geometry are not
present, the provider returns no exact secondary optical evidence.

Deployment source discovery (in priority order):
  1. FIRECLOUD_ECMWF_IFS_GRIB_PATH: exact local/mounted GRIB path.
  2. FIRECLOUD_ECMWF_IFS_GRIB_DIR: directory searched for a file whose name
     contains YYYYMMDDHH and/or the valid-time stamp.

A network acquisition layer is intentionally not guessed here: ECMWF access
entitlements and product catalogues differ by deployment.  The GRIB decoder and
physics bridge are fully operational once an entitled forecast file is present.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import math
import os
import re
from typing import Iterable

import numpy as np
import pandas as pd

from ..cloud_optics import condensate_extinction_m1, DEFAULT_LIQUID_REFF_UM, DEFAULT_ICE_REFF_UM

PROVIDER_NAME = "ECMWF_IFS_NATIVE_CLOUD_MICROPHYSICS"
PROVIDER_SCHEMA_VERSION = "R5.1_IFS_NATIVE_CLOUD_V1"
REQUIRED_HYBRID_FIELDS = ("clwc", "ciwc", "cc", "t", "q")
OPTIONAL_HYBRID_FIELDS = ("crwc", "cswc")
R_D = 287.05
G0 = 9.80665


def decoder_available() -> bool:
    try:
        import eccodes  # noqa: F401
        return True
    except Exception:
        return False


def provider_status() -> dict:
    p = resolve_configured_grib_path(None)
    return {
        "provider": PROVIDER_NAME,
        "provider_schema_version": PROVIDER_SCHEMA_VERSION,
        "decoder_available": decoder_available(),
        "configured_local_grib": str(p) if p else "",
        "source_mode": "LOCAL_OR_MOUNTED_ENTITLED_IFS_GRIB",
    }


def resolve_configured_grib_path(valid_time: datetime | None) -> Path | None:
    raw = os.getenv("FIRECLOUD_ECMWF_IFS_GRIB_PATH", "").strip()
    if raw:
        p = Path(raw).expanduser()
        if p.exists() and p.is_file():
            return p
    d_raw = os.getenv("FIRECLOUD_ECMWF_IFS_GRIB_DIR", "").strip()
    if not d_raw:
        return None
    d = Path(d_raw).expanduser()
    if not d.exists() or not d.is_dir():
        return None
    files = sorted([p for p in d.iterdir() if p.is_file() and p.suffix.lower() in {".grib", ".grib2", ".grb", ".grb2"}])
    if not files:
        return None
    if valid_time is None:
        return files[-1]
    stamps = [valid_time.strftime("%Y%m%d%H"), valid_time.strftime("%Y%m%dT%H"), valid_time.strftime("%Y%m%d_%H")]
    exact = [p for p in files if any(s in p.name for s in stamps)]
    return exact[-1] if exact else files[-1]


def _short_name(raw: str) -> str:
    x = str(raw or "").strip().lower()
    aliases = {
        "clwc":"clwc", "246":"clwc", "ciwc":"ciwc", "247":"ciwc", "cc":"cc", "248":"cc",
        "t":"t", "130":"t", "q":"q", "133":"q", "crwc":"crwc", "75":"crwc", "cswc":"cswc", "76":"cswc",
        "lnsp":"lnsp", "152":"lnsp", "sp":"sp", "134":"sp", "z":"z", "129":"z", "gh":"gh", "156":"gh",
    }
    return aliases.get(x, x)


def _nearest_indices(lats: np.ndarray, lons: np.ndarray, points: list[dict]) -> list[int]:
    lons = np.where(lons > 180.0, lons - 360.0, lons)
    out=[]
    for p in points:
        lat=float(p["lat"]); lon=float(p["lon"])
        d2=(lats-lat)**2 + ((lons-lon)*math.cos(math.radians(lat)))**2
        out.append(int(np.nanargmin(d2)))
    return out


def grib_inventory(path: str | Path) -> pd.DataFrame:
    if not decoder_available():
        return pd.DataFrame()
    from eccodes import codes_grib_new_from_file, codes_get, codes_release
    counts={}
    with open(path,"rb") as f:
        while True:
            gid=codes_grib_new_from_file(f)
            if gid is None: break
            try:
                try: sn=_short_name(codes_get(gid,"shortName"))
                except Exception: sn=""
                try: typ=str(codes_get(gid,"typeOfLevel"))
                except Exception: typ=""
                try: lev=int(codes_get(gid,"level"))
                except Exception: lev=-1
                try: units=str(codes_get(gid,"units"))
                except Exception: units=""
                counts[(sn,typ,lev,units)]=counts.get((sn,typ,lev,units),0)+1
            finally:
                codes_release(gid)
    return pd.DataFrame([{"shortName":k[0],"typeOfLevel":k[1],"level":k[2],"units":k[3],"message_count":v} for k,v in counts.items()])


def decode_ifs_hybrid_profiles(path: str | Path, points: list[dict]) -> tuple[pd.DataFrame, dict]:
    """Decode IFS hybrid model levels and reconstruct pressure/AGL height.

    Returns a long profile frame with one row per route point × model level.
    Hybrid A/B half-level coefficients are read from GRIB key ``pv``.  Heights
    are hydrostatically integrated from the surface using model T/Q.
    """
    if not decoder_available():
        raise RuntimeError("ecCodes decoder unavailable")
    from eccodes import codes_grib_new_from_file, codes_get, codes_get_array, codes_release

    points=list(points)
    values={p["point_id"]:{} for p in points}
    surface={p["point_id"]:{"lnsp":np.nan,"sp":np.nan,"z":np.nan,"gh":np.nan} for p in points}
    pv=None; nearest=None; grid_sig=None; hybrid_levels=set(); field_levels={k:set() for k in REQUIRED_HYBRID_FIELDS+OPTIONAL_HYBRID_FIELDS}
    with open(path,"rb") as f:
        while True:
            gid=codes_grib_new_from_file(f)
            if gid is None: break
            try:
                try: sn=_short_name(codes_get(gid,"shortName"))
                except Exception: continue
                if sn not in set(REQUIRED_HYBRID_FIELDS+OPTIONAL_HYBRID_FIELDS+("lnsp","sp","z","gh")):
                    continue
                try: typ=str(codes_get(gid,"typeOfLevel"))
                except Exception: typ=""
                try: level=int(codes_get(gid,"level"))
                except Exception: level=-1
                vals=np.asarray(codes_get_array(gid,"values"),dtype=float)
                lats=np.asarray(codes_get_array(gid,"latitudes"),dtype=float)
                lons=np.asarray(codes_get_array(gid,"longitudes"),dtype=float)
                sig=(len(vals),round(float(lats[0]),4),round(float(lons[0]),4))
                if nearest is None or sig!=grid_sig:
                    nearest=_nearest_indices(lats,lons,points); grid_sig=sig
                if typ in {"hybrid","hybridLayer","generalVertical"} and sn in set(REQUIRED_HYBRID_FIELDS+OPTIONAL_HYBRID_FIELDS):
                    hybrid_levels.add(level); field_levels.setdefault(sn,set()).add(level)
                    if pv is None:
                        try:
                            x=np.asarray(codes_get_array(gid,"pv"),dtype=float)
                            if x.size>=4: pv=x
                        except Exception:
                            pass
                    for p,idx in zip(points,nearest):
                        values[p["point_id"]].setdefault(level,{})[sn]=float(vals[idx])
                elif sn in {"lnsp","sp","z","gh"}:
                    for p,idx in zip(points,nearest):
                        surface[p["point_id"]][sn]=float(vals[idx])
            finally:
                codes_release(gid)

    meta={
        "provider":PROVIDER_NAME,
        "provider_schema_version":PROVIDER_SCHEMA_VERSION,
        "grib_path":str(path),
        "hybrid_level_count":len(hybrid_levels),
        "field_level_counts":{k:len(v) for k,v in field_levels.items()},
        "hybrid_coefficients_present":bool(pv is not None),
    }
    if pv is None or len(hybrid_levels)<2:
        meta["status"]="MISSING_HYBRID_GEOMETRY"
        return pd.DataFrame(),meta
    nlev=max(hybrid_levels)
    if pv.size != 2*(nlev+1):
        meta["status"]="HYBRID_COEFFICIENT_SIZE_MISMATCH"
        meta["pv_size"]=int(pv.size); meta["expected_pv_size"]=int(2*(nlev+1))
        return pd.DataFrame(),meta
    a=pv[:nlev+1]; b=pv[nlev+1:]
    rows=[]
    for p in points:
        pid=p["point_id"]; s=surface[pid]
        sp=float(s["sp"]) if math.isfinite(float(s["sp"])) else (math.exp(float(s["lnsp"])) if math.isfinite(float(s["lnsp"])) else np.nan)
        if not math.isfinite(sp) or sp<=0:
            continue
        zsurf_m=(float(s["gh"]) if math.isfinite(float(s["gh"])) else (float(s["z"])/G0 if math.isfinite(float(s["z"])) else 0.0))
        ph=a+b*sp
        level_recs=[]
        # IFS level number increases downward; integrate from bottom to top.
        z_half_lower=zsurf_m
        for lev in range(nlev,0,-1):
            rec=values[pid].get(lev,{})
            if not all(k in rec and math.isfinite(float(rec[k])) for k in ("t","q")):
                continue
            p_lower=max(1.0,float(ph[lev])); p_upper=max(0.1,float(ph[lev-1])); p_full=max(0.1,0.5*(p_lower+p_upper))
            tv=float(rec["t"])*(1.0+0.61*max(0.0,float(rec["q"])))
            dz_full=R_D*tv/G0*math.log(p_lower/p_full)
            z_full=z_half_lower+dz_full
            dz_layer=R_D*tv/G0*math.log(p_lower/p_upper)
            z_half_upper=z_half_lower+dz_layer
            rr={
                "point_id":pid,"distance_km":float(p["distance_km"]),"direction_offset_deg":float(p["direction_offset_deg"]),
                "lat":float(p["lat"]),"lon":float(p["lon"]),"model_level":lev,
                "pressure_hpa":p_full/100.0,"altitude_msl_km":z_full/1000.0,
                "altitude_agl_km":max(0.0,(z_full-zsurf_m)/1000.0),"layer_bottom_agl_km":max(0.0,(z_half_lower-zsurf_m)/1000.0),
                "layer_top_agl_km":max(0.0,(z_half_upper-zsurf_m)/1000.0),"temperature_k":float(rec["t"]),"specific_humidity_kgkg":float(rec["q"]),
                "clwc_kgkg":rec.get("clwc",np.nan),"ciwc_kgkg":rec.get("ciwc",np.nan),"cloud_fraction":rec.get("cc",np.nan),
                "crwc_kgkg":rec.get("crwc",np.nan),"cswc_kgkg":rec.get("cswc",np.nan),
                "surface_pressure_pa":sp,"surface_height_m":zsurf_m,
            }
            level_recs.append(rr); z_half_lower=z_half_upper
        rows.extend(level_recs)
    out=pd.DataFrame(rows)
    missing=[k for k in REQUIRED_HYBRID_FIELDS if field_levels.get(k,set())!=hybrid_levels]
    meta["missing_full_level_fields"]=missing
    meta["status"]="FULL_NATIVE_MICROPHYSICS" if not missing and not out.empty else ("PARTIAL_NATIVE_MICROPHYSICS" if not out.empty else "NO_ROUTE_PROFILE")
    return out,meta


def build_secondary_optics_from_profiles(profiles: pd.DataFrame, valid_time: datetime | None=None) -> pd.DataFrame:
    """Convert native IFS condensate layers into secondary Target optical evidence."""
    if profiles is None or profiles.empty:
        return pd.DataFrame()
    rows=[]
    for _,r in profiles.iterrows():
        ql=r.get("clwc_kgkg",np.nan); qi=r.get("ciwc_kgkg",np.nan); t=r.get("temperature_k",np.nan); p=r.get("pressure_hpa",np.nan)
        if not all(math.isfinite(float(v)) for v in (ql,qi,t,p)) or float(t)<=0 or float(p)<=0:
            continue
        rho=float(p)*100.0/(R_D*float(t))
        lwc=max(0.0,float(ql))*rho*1000.0; iwc=max(0.0,float(qi))*rho*1000.0
        cf=r.get("cloud_fraction",np.nan)
        ext=condensate_extinction_m1(lwc,iwc,cf,DEFAULT_LIQUID_REFF_UM,DEFAULT_ICE_REFF_UM)
        z0=float(r.get("layer_bottom_agl_km",np.nan)); z1=float(r.get("layer_top_agl_km",np.nan))
        if not (math.isfinite(z0) and math.isfinite(z1) and z1>z0):
            continue
        beta=ext.get("total_extinction_m1",np.nan)
        if not math.isfinite(float(beta)):
            continue
        cot=max(0.0,float(beta)*(z1-z0)*1000.0)
        # Exact optical evidence requires native condensate to be positive; a
        # zero-condensate model layer is not promoted into a cloud optical layer.
        if max(0.0,float(ql))+max(0.0,float(qi)) <= 1.0e-8 or cot<=0.0:
            continue
        if float(qi)>1e-8 and float(ql)>1e-8: phase="MIXED"
        elif float(qi)>1e-8: phase="ICE"
        else: phase="LIQUID"
        reff = DEFAULT_ICE_REFF_UM if phase=="ICE" else (0.5*(DEFAULT_LIQUID_REFF_UM+DEFAULT_ICE_REFF_UM) if phase=="MIXED" else DEFAULT_LIQUID_REFF_UM)
        rows.append({
            "provider":"ECMWF","model":"IFS","source_kind":"FORECAST_MODEL_NATIVE_OPTICS",
            "valid_time":valid_time,"direction_offset_deg":float(r["direction_offset_deg"]),"distance_km":float(r["distance_km"]),
            "z_base_km":z0,"z_top_km":z1,"cot":cot,"effective_radius_um":reff,"phase":phase,
            "optical_evidence":"FULL","provenance":"IFS_NATIVE_CLWC_CIWC_DERIVED_COT_ASSUMED_REFF",
            "status":"OK","cloud_fraction":cf,"clwc_kgkg":float(ql),"ciwc_kgkg":float(qi),
            "model_level":int(r.get("model_level",-1)),"pressure_hpa":float(p),
            "assumed_liquid_reff_um":DEFAULT_LIQUID_REFF_UM,"assumed_ice_reff_um":DEFAULT_ICE_REFF_UM,
            "cloud_optical_model":"NATIVE_CONDENSATE_GEOMETRIC_OPTICS_ASSUMED_REFF",
        })
    return pd.DataFrame(rows)


def fetch_route_secondary_target_optics(points: list[dict], valid_time: datetime) -> tuple[pd.DataFrame, dict]:
    """Resolve configured IFS forecast GRIB and return exact secondary optics."""
    meta={**provider_status(),"valid_time":valid_time,"status":"UNAVAILABLE"}
    p=resolve_configured_grib_path(valid_time)
    if p is None:
        meta["status"]="NO_CONFIGURED_IFS_GRIB"
        meta["note"]="Set FIRECLOUD_ECMWF_IFS_GRIB_PATH or FIRECLOUD_ECMWF_IFS_GRIB_DIR; no fallback fabrication."
        return pd.DataFrame(),meta
    try:
        prof,dm=decode_ifs_hybrid_profiles(p,points)
        meta.update(dm)
        optics=build_secondary_optics_from_profiles(prof,valid_time)
        meta["secondary_optical_record_count"]=int(len(optics))
        meta["profile_row_count"]=int(len(prof))
        if optics.empty and meta.get("status")=="FULL_NATIVE_MICROPHYSICS":
            meta["status"]="NATIVE_MICROPHYSICS_PRESENT_NO_POSITIVE_CLOUD_OPTICS"
        return optics,meta
    except Exception as exc:
        meta["status"]="FAILED"
        meta["error"]=f"{type(exc).__name__}: {exc}"
        return pd.DataFrame(),meta
