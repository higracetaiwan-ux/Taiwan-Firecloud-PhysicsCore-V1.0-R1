"""PhysicsCore V1.0-R5.5.2 DWD ICON Global native cloud-microphysics provider.

R5.5.2 closes the ICON-global unstructured-grid decoder gap without fabricating
cloud optics. DWD ICON Global GRIB2 carries field values on the native triangular
grid but does not carry per-cell latitude/longitude coordinates. DWD publishes
precomputed nearest-neighbour CDO remap weights separately; this provider uses
those weights only to map each route point to the corresponding native ICON
source-cell address, then reads the native QC/QI/T/P/FI value directly from the
GRIB value array.

Scientific boundaries
---------------------
* Forecast-native QC/QI only; no RH/CF/geometry/satellite -> COT conversion.
* Missing/decode/grid-map failure != zero condensate.
* Secondary optics are exact forecast-model evidence only when the required
  native microphysics + T/P/FI layer geometry are all available.
* The remap weights are a spatial locator, not an optical interpolation model.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path
import bz2
import hashlib
import math
import os
import tarfile
import tempfile
from typing import Iterable

import numpy as np
import pandas as pd
import requests

from ..cloud_optics import condensate_extinction_m1, DEFAULT_LIQUID_REFF_UM, DEFAULT_ICE_REFF_UM

PROVIDER_NAME = "DWD_ICON_GLOBAL_NATIVE_CLOUD_MICROPHYSICS"
PROVIDER_SCHEMA_VERSION = "R5.5.2_ICON_GLOBAL_NATIVE_CLOUD_V2"
BASE_URL = "https://opendata.dwd.de/weather/nwp/icon/grib"
REMAP_BUNDLE_URL = "https://opendata.dwd.de/weather/lib/cdo/ICON_GLOBAL2WORLD_025_EASY.tar.bz2"
REMAP_WEIGHTS_NAME = "weights_icogl2world_025.nc"
REMAP_GRID_NAME = "target_grid_world_025.txt"
# DWD target_grid_world_025.txt contract (CDO lonlat grid)
TARGET_XSIZE = 1440
TARGET_YSIZE = 721
TARGET_XFIRST = 0.0
TARGET_XINC = 0.25
TARGET_YFIRST = -90.0
TARGET_YINC = 0.25

G0 = 9.80665
R_D = 287.05
_RUNTIME_CACHE: dict[tuple, tuple[pd.DataFrame, dict, pd.DataFrame]] = {}
_ROUTE_SOURCE_MAP_CACHE: dict[tuple, tuple[dict[str, dict], dict]] = {}
_WEIGHT_MAP_CACHE: dict[tuple, np.ndarray] = {}


def decoder_available() -> bool:
    try:
        import eccodes  # noqa: F401
        return True
    except Exception:
        return False


def remap_reader_available() -> bool:
    try:
        from scipy.io import netcdf_file  # noqa: F401
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


def _remap_dir() -> Path:
    raw = os.getenv("FIRECLOUD_DWD_ICON_REMAP_DIR", "").strip()
    p = Path(raw).expanduser() if raw else _cache_dir() / "remap"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _configured_weights_path() -> Path | None:
    raw = os.getenv("FIRECLOUD_DWD_ICON_WEIGHTS_PATH", "").strip()
    if not raw:
        return None
    p = Path(raw).expanduser()
    return p if p.exists() and p.stat().st_size > 0 else None


def provider_status() -> dict:
    wp = _configured_weights_path() or (_remap_dir() / REMAP_WEIGHTS_NAME)
    return {
        "provider": PROVIDER_NAME,
        "provider_schema_version": PROVIDER_SCHEMA_VERSION,
        "decoder_available": decoder_available(),
        "remap_reader_available": remap_reader_available(),
        "network_enabled": network_enabled(),
        "source_mode": "DWD_OPEN_DATA_ICON_GLOBAL_MODEL_LEVEL",
        "grid_locator_mode": "DWD_CDO_GNN_SOURCE_ADDRESS_FROM_ICON_GLOBAL2WORLD_025_EASY",
        "cache_dir": str(_cache_dir()),
        "remap_weights_path": str(wp),
        "remap_weights_present": bool(wp.exists() and wp.stat().st_size > 0),
    }


def _floor_cycle(t: datetime) -> datetime:
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    else:
        t = t.astimezone(timezone.utc)
    return t.replace(hour=(t.hour // 6) * 6, minute=0, second=0, microsecond=0)


def resolve_run_and_lead(valid_time: datetime, now_utc: datetime | None = None) -> tuple[datetime, int]:
    """Choose latest likely-published 6-hour ICON run and integer forecast lead."""
    vt = valid_time.replace(tzinfo=timezone.utc) if valid_time.tzinfo is None else valid_time.astimezone(timezone.utc)
    now = now_utc or datetime.now(timezone.utc)
    latest_available = _floor_cycle(now - timedelta(hours=3))
    run = min(latest_available, _floor_cycle(vt))
    lead = int(round((vt - run).total_seconds() / 3600.0))
    if lead < 0:
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
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    return _cache_dir() / f"{h}_{name[:-4]}"


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


def _ensure_remap_assets(timeout_s: float = 60.0) -> tuple[Path | None, dict]:
    """Ensure DWD nearest-neighbour CDO weights are locally available.

    The 44 MB EASY bundle is preferred over the ~938 MB full ICON grid.  A direct
    FIRECLOUD_DWD_ICON_WEIGHTS_PATH override is supported for offline deployment.
    """
    configured = _configured_weights_path()
    if configured is not None:
        return configured, {"stage":"GRID_MAPPING","status":"CONFIGURED_WEIGHTS","weights_path":str(configured),"url":None}
    dest = _remap_dir() / REMAP_WEIGHTS_NAME
    if dest.exists() and dest.stat().st_size > 0:
        return dest, {"stage":"GRID_MAPPING","status":"CACHE_HIT","weights_path":str(dest),"url":REMAP_BUNDLE_URL}
    if not network_enabled():
        return None, {"stage":"GRID_MAPPING","status":"NETWORK_DISABLED","weights_path":str(dest),"url":REMAP_BUNDLE_URL}
    bundle_override = os.getenv("FIRECLOUD_DWD_ICON_REMAP_BUNDLE_PATH", "").strip()
    tmp_bundle: Path | None = None
    remove_tmp = False
    try:
        if bundle_override:
            tmp_bundle = Path(bundle_override).expanduser()
            if not tmp_bundle.exists():
                return None, {"stage":"GRID_MAPPING","status":"CONFIGURED_BUNDLE_MISSING","weights_path":str(dest),"url":None}
        else:
            fd, name = tempfile.mkstemp(prefix="icon_remap_", suffix=".tar.bz2", dir=str(_remap_dir()))
            os.close(fd); tmp_bundle = Path(name); remove_tmp = True
            with requests.get(REMAP_BUNDLE_URL, stream=True, timeout=timeout_s) as r:
                if r.status_code != 200:
                    return None, {"stage":"GRID_MAPPING","status":f"HTTP_{r.status_code}","weights_path":str(dest),"url":REMAP_BUNDLE_URL}
                with open(tmp_bundle, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
        with tarfile.open(tmp_bundle, mode="r:bz2") as tf:
            member = next((m for m in tf.getmembers() if Path(m.name).name == REMAP_WEIGHTS_NAME and m.isfile()), None)
            if member is None:
                return None, {"stage":"GRID_MAPPING","status":"WEIGHTS_MEMBER_MISSING","weights_path":str(dest),"url":REMAP_BUNDLE_URL}
            src = tf.extractfile(member)
            if src is None:
                return None, {"stage":"GRID_MAPPING","status":"WEIGHTS_EXTRACT_FAILED","weights_path":str(dest),"url":REMAP_BUNDLE_URL}
            fd, name = tempfile.mkstemp(prefix="weights_", suffix=".nc", dir=str(_remap_dir()))
            os.close(fd); tmpw = Path(name)
            with open(tmpw, "wb") as out:
                while True:
                    buf = src.read(1024*1024)
                    if not buf: break
                    out.write(buf)
            if tmpw.stat().st_size <= 0:
                tmpw.unlink(missing_ok=True)
                return None, {"stage":"GRID_MAPPING","status":"WEIGHTS_EMPTY","weights_path":str(dest),"url":REMAP_BUNDLE_URL}
            tmpw.replace(dest)
        return dest, {"stage":"GRID_MAPPING","status":"DOWNLOADED_AND_EXTRACTED","weights_path":str(dest),"url":REMAP_BUNDLE_URL,"bytes":int(dest.stat().st_size)}
    except Exception as exc:
        return None, {"stage":"GRID_MAPPING","status":"GRID_MAPPING_FAILED","weights_path":str(dest),"url":REMAP_BUNDLE_URL,"error":f"{type(exc).__name__}: {exc}"}
    finally:
        if remove_tmp and tmp_bundle is not None and tmp_bundle.exists():
            try: tmp_bundle.unlink()
            except Exception: pass


def _read_nn_source_map(weights_path: Path) -> np.ndarray:
    """Read CDO gennn src/dst address arrays into a dense dst->src lookup.

    CDO/SCRIP addresses are 1-based. Returned native source indices are 0-based
    and can index ecCodes ``values`` directly.
    """
    key=(str(weights_path.resolve()), int(weights_path.stat().st_size), int(weights_path.stat().st_mtime_ns))
    if key in _WEIGHT_MAP_CACHE:
        return _WEIGHT_MAP_CACHE[key]
    if not remap_reader_available():
        raise RuntimeError("scipy NetCDF reader unavailable for DWD remap weights")
    from scipy.io import netcdf_file
    with netcdf_file(str(weights_path), mode="r", mmap=False) as nc:
        names=set(nc.variables)
        if "src_address" not in names or "dst_address" not in names:
            raise RuntimeError(f"CDO weights missing src_address/dst_address; variables={sorted(names)[:20]}")
        src=np.asarray(nc.variables["src_address"].data, dtype=np.int64).reshape(-1)
        dst=np.asarray(nc.variables["dst_address"].data, dtype=np.int64).reshape(-1)
    if src.size == 0 or dst.size == 0 or src.size != dst.size:
        raise RuntimeError("invalid CDO nearest-neighbour address arrays")
    good=(src > 0) & (dst > 0)
    src=src[good]; dst=dst[good]
    max_dst=max(int(dst.max()), TARGET_XSIZE*TARGET_YSIZE)
    lookup=np.full(max_dst, -1, dtype=np.int64)
    # gennn normally has one link per destination. If duplicates occur, the first
    # valid source address is retained; this remains a locator, not an averaging step.
    for s,d in zip(src,dst):
        j=int(d)-1
        if lookup[j] < 0:
            lookup[j]=int(s)-1
    _WEIGHT_MAP_CACHE.clear()
    _WEIGHT_MAP_CACHE[key]=lookup
    return lookup


def _target_grid_cell(lat: float, lon: float) -> tuple[int, float, float]:
    lat=max(-90.0,min(90.0,float(lat)))
    lon=float(lon) % 360.0
    ix=int(round((lon-TARGET_XFIRST)/TARGET_XINC)) % TARGET_XSIZE
    iy=int(round((lat-TARGET_YFIRST)/TARGET_YINC))
    iy=max(0,min(TARGET_YSIZE-1,iy))
    cell_lon=TARGET_XFIRST + ix*TARGET_XINC
    cell_lat=TARGET_YFIRST + iy*TARGET_YINC
    # CDO/SCRIP destination address: x fastest, 1-based.
    dst_address=iy*TARGET_XSIZE + ix + 1
    return int(dst_address), float(cell_lat), float(cell_lon)


def _route_source_index_map(points: list[dict], timeout_s: float = 60.0) -> tuple[dict[str, dict], dict]:
    route_sig=tuple((str(p.get("point_id")),round(float(p.get("lat",0)),6),round(float(p.get("lon",0)),6)) for p in points)
    weights, meta=_ensure_remap_assets(timeout_s=timeout_s)
    if weights is None:
        raise RuntimeError(meta.get("error") or meta.get("status") or "DWD remap weights unavailable")
    key=(str(weights.resolve()), int(weights.stat().st_size), route_sig)
    if key in _ROUTE_SOURCE_MAP_CACHE:
        mapping,m0=_ROUTE_SOURCE_MAP_CACHE[key]
        return mapping, {**m0,"status":"GRID_MAPPING_CACHE_HIT"}
    lookup=_read_nn_source_map(weights)
    mapping={}
    unresolved=[]
    for p in points:
        pid=str(p["point_id"])
        dst,glat,glon=_target_grid_cell(float(p["lat"]),float(p["lon"]))
        j=dst-1
        src=int(lookup[j]) if 0 <= j < len(lookup) else -1
        if src < 0:
            unresolved.append(pid); continue
        mapping[pid]={"source_index":src,"dst_address":dst,"target_grid_lat":glat,"target_grid_lon":glon}
    if unresolved:
        raise RuntimeError(f"DWD CDO source-address mapping missing for {len(unresolved)} route points")
    m={**meta,"status":"GRID_MAPPING_READY","route_point_count":len(points),"mapped_route_point_count":len(mapping),"grid_resolution_deg":0.25}
    _ROUTE_SOURCE_MAP_CACHE[key]=(mapping,m)
    return mapping,m


def _decode_nearest(path: Path, points: list[dict], source_map: dict[str, dict] | None = None) -> tuple[pd.DataFrame, dict]:
    if not decoder_available():
        raise RuntimeError("ecCodes decoder unavailable")
    if source_map is None:
        source_map,_=_route_source_index_map(points)
    from eccodes import codes_grib_new_from_file, codes_get, codes_get_array, codes_release
    with open(path, "rb") as f:
        gid = codes_grib_new_from_file(f)
        if gid is None:
            raise RuntimeError("GRIB has no message")
        try:
            vals=np.asarray(codes_get_array(gid,"values"),dtype=float)
            def getstr(key, default=""):
                try: return str(codes_get(gid,key))
                except Exception: return default
            def getint(key, default=-1):
                try: return int(codes_get(gid,key))
                except Exception: return default
            units=getstr("units"); sn=getstr("shortName"); lev=getint("level")
            grid_type=getstr("gridType"); packing=getstr("packingType"); grid_no=getint("numberOfGridUsed")
            rows=[]
            for p in points:
                pid=str(p["point_id"])
                m=source_map.get(pid)
                if m is None:
                    raise RuntimeError(f"route source index missing for {pid}")
                idx=int(m["source_index"])
                if idx < 0 or idx >= len(vals):
                    raise RuntimeError(f"ICON source index {idx} outside GRIB values[0:{len(vals)}]")
                rows.append({
                    "point_id":pid,"distance_km":float(p["distance_km"]),
                    "direction_offset_deg":float(p["direction_offset_deg"]),"lat":float(p["lat"]),"lon":float(p["lon"]),
                    "grid_lat":float(m["target_grid_lat"]),"grid_lon":float(m["target_grid_lon"]),
                    "icon_source_index":idx,"dwd_target_grid_address":int(m["dst_address"]),
                    "value":float(vals[idx]),"model_level":lev,"short_name":sn,"units":units,
                })
            return pd.DataFrame(rows), {
                "short_name":sn,"level":lev,"units":units,"grid_size":int(len(vals)),
                "grid_type":grid_type,"packing_type":packing,"number_of_grid_used":grid_no,
                "grid_locator_mode":"CDO_GNN_SOURCE_ADDRESS",
            }
        finally:
            codes_release(gid)


def _fetch_field(run: datetime, lead: int, level: int, var: str, points: list[dict], timeout_s: float, source_map: dict[str,dict]) -> tuple[pd.DataFrame, dict]:
    url=_url(run,lead,level,var)
    p,meta=_download_decompress(url,timeout_s=timeout_s)
    meta.update({"stage":"FIELD_FETCH","variable":var.upper(),"model_level":int(level),"run":run,"lead_hours":int(lead)})
    if p is None:
        return pd.DataFrame(),meta
    try:
        df,dm=_decode_nearest(p,points,source_map=source_map)
        meta.update(dm); meta["status"] = "OK_" + meta.get("status","READY")
        return df,meta
    except Exception as exc:
        meta["status"]="FIELD_DECODE_FAILED"; meta["error"]=f"{type(exc).__name__}: {exc}"
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
    if not remap_reader_available():
        meta["status"]="REMAP_READER_UNAVAILABLE"; return pd.DataFrame(),meta,pd.DataFrame()
    timeout=float(os.getenv("FIRECLOUD_DWD_ICON_TIMEOUT_S","20"))
    # R5.5.2: resolve route->native source address once, before any QC/QI flood.
    try:
        source_map,gmeta=_route_source_index_map(points,timeout_s=max(30.0,timeout))
        audit.append(gmeta)
        meta.update({"grid_mapping_status":gmeta.get("status"),"grid_mapping_route_point_count":len(source_map)})
    except Exception as exc:
        meta["status"]="GRID_MAPPING_FAILED"; meta["error"]=f"{type(exc).__name__}: {exc}"
        audit.append({"stage":"GRID_MAPPING","status":"GRID_MAPPING_FAILED","error":meta["error"]})
        return pd.DataFrame(),meta,pd.DataFrame(audit)

    run,lead=resolve_run_and_lead(valid_time)
    meta.update({"run":run,"lead_hours":lead})
    if lead < 0 or lead > 180:
        meta["status"]="LEAD_OUT_OF_RANGE"; return pd.DataFrame(),meta,pd.DataFrame(audit)
    levels=_model_levels(); workers=max(1,min(12,int(os.getenv("FIRECLOUD_DWD_ICON_WORKERS","8"))))
    qc={}; qi={}; decoded_pairs=set()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        fut={ex.submit(_fetch_field,run,lead,lev,var,points,timeout,source_map):(lev,var) for lev in levels for var in ("QC","QI")}
        for f in as_completed(fut):
            lev,var=fut[f]
            try: df,m=f.result()
            except Exception as exc: df,m=pd.DataFrame(),{"stage":"FIELD_FETCH","status":"FAILED","variable":var,"model_level":lev,"error":f"{type(exc).__name__}: {exc}"}
            audit.append(m)
            if not df.empty:
                (qc if var=="QC" else qi)[lev]=df; decoded_pairs.add((lev,var))
    positive=_positive_condensate_levels(qc,qi)
    expected_pairs=len(levels)*2
    decoded_count=len(decoded_pairs)
    meta.update({
        "probed_level_count":len(levels),"positive_condensate_level_count":len(positive),"positive_levels":positive,
        "condensate_field_expected_count":expected_pairs,"condensate_field_decoded_count":decoded_count,
        "condensate_field_completeness":decoded_count/expected_pairs if expected_pairs else 0.0,
    })
    if not positive:
        if decoded_count == expected_pairs:
            meta["status"]="NATIVE_MICROPHYSICS_PRESENT_NO_POSITIVE_CLOUD_OPTICS"
            audit.append({"stage":"CONDENSATE_AGGREGATE","status":"ZERO_CONDENSATE","decoded_field_count":decoded_count,"expected_field_count":expected_pairs})
        elif decoded_count == 0:
            meta["status"]="NATIVE_MICROPHYSICS_UNRESOLVED"
            audit.append({"stage":"CONDENSATE_AGGREGATE","status":"MICROPHYSICS_UNRESOLVED","decoded_field_count":0,"expected_field_count":expected_pairs})
        else:
            meta["status"]="NATIVE_MICROPHYSICS_PARTIAL_UNRESOLVED"
            audit.append({"stage":"CONDENSATE_AGGREGATE","status":"MICROPHYSICS_PARTIAL_UNRESOLVED","decoded_field_count":decoded_count,"expected_field_count":expected_pairs})
        return pd.DataFrame(),meta,pd.DataFrame(audit)
    audit.append({"stage":"CONDENSATE_AGGREGATE","status":"POSITIVE_CONDENSATE","positive_level_count":len(positive),"decoded_field_count":decoded_count,"expected_field_count":expected_pairs})

    needed_fi=sorted(set(x for lev in positive for x in (lev-1,lev,lev+1) if 1<=x<=120))
    fields: dict[str,dict[int,pd.DataFrame]]={"T":{},"P":{},"FI":{}}
    tasks=[(lev,"T") for lev in positive]+[(lev,"P") for lev in positive]+[(lev,"FI") for lev in needed_fi]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        fut={ex.submit(_fetch_field,run,lead,lev,var,points,timeout,source_map):(lev,var) for lev,var in tasks}
        for f in as_completed(fut):
            lev,var=fut[f]
            try: df,m=f.result()
            except Exception as exc: df,m=pd.DataFrame(),{"stage":"FIELD_FETCH","status":"FAILED","variable":var,"model_level":lev,"error":f"{type(exc).__name__}: {exc}"}
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
    if prof.empty:
        meta["status"]="POSITIVE_CONDENSATE_GEOMETRY_INCOMPLETE"
    elif decoded_count < expected_pairs:
        meta["status"]="PARTIAL_NATIVE_MICROPHYSICS_WITH_RESOLVED_POSITIVE_OPTICS"
    else:
        meta["status"]="FULL_NATIVE_MICROPHYSICS"
    return prof,meta,pd.DataFrame(audit)


def build_secondary_optics_from_profiles(profiles: pd.DataFrame, valid_time: datetime | None=None) -> pd.DataFrame:
    if profiles is None or profiles.empty: return pd.DataFrame()
    rows=[]
    for _,r in profiles.iterrows():
        ql=float(r["qc_kgkg"]); qi=float(r["qi_kgkg"]); t=float(r["temperature_k"]); ph=float(r["pressure_hpa"])
        z0=float(r["layer_bottom_msl_km"]); z1=float(r["layer_top_msl_km"])
        if not all(math.isfinite(v) for v in (ql,qi,t,ph,z0,z1)) or not z1>z0: continue
        rho=ph*100.0/(R_D*t); lwc=ql*rho*1000.0; iwc=qi*rho*1000.0
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
