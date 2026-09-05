from __future__ import annotations
from datetime import datetime
import hashlib, json, math, os, time
from pathlib import Path
import requests
import pandas as pd

API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
HOURLY_VARS = ["aerosol_optical_depth"]


def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i+n]


def _cache_dir() -> Path:
    raw=os.getenv("FIRECLOUD_OPENMETEO_AQ_CACHE_DIR","").strip()
    return Path(raw).expanduser() if raw else Path(__file__).resolve().parents[2]/".cache"/"openmeteo_air_quality"


def _cache_ttl_seconds():
    try: return max(0.0,float(os.getenv("FIRECLOUD_OPENMETEO_CACHE_TTL_SECONDS","1800")))
    except Exception: return 1800.0


def _key(params):
    payload=json.dumps({"url":API_URL,"params":params},sort_keys=True,separators=(",",":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _load(k):
    p=_cache_dir()/f"{k}.json"
    try:
        if not p.exists(): return None
        ttl=_cache_ttl_seconds()
        if ttl>0 and time.time()-p.stat().st_mtime>ttl: return None
        return json.loads(p.read_text())
    except Exception: return None


def _save(k,data):
    try:
        d=_cache_dir(); d.mkdir(parents=True,exist_ok=True)
        t=d/f".{k}.tmp"; t.write_text(json.dumps(data)); t.replace(d/f"{k}.json")
    except Exception: pass


def _dedupe(points):
    unique=[]; members=[]; idx={}
    for p in points:
        k=(round(float(p["lat"]),8),round(float(p["lon"]),8))
        if k not in idx:
            idx[k]=len(unique); unique.append(p); members.append([p])
        else: members[idx[k]].append(p)
    return unique,members


def _get(session,params,max_attempts=5):
    last=None
    for i in range(max_attempts):
        r=session.get(API_URL,params=params,timeout=(8,30)); last=r
        if r.status_code!=429:
            r.raise_for_status(); return r
        if i==max_attempts-1: break
        ra=r.headers.get("Retry-After")
        try: wait=float(ra) if ra is not None else min(60.0,4.0*(2**i))
        except Exception: wait=min(60.0,4.0*(2**i))
        time.sleep(max(2.0,wait))
    last.raise_for_status()


def fetch_route_aerosol(points: list[dict], start: datetime, end: datetime, timezone: str = "Asia/Taipei") -> pd.DataFrame:
    """Open-Meteo/CAMS AOD550 fallback only, with persistent cache and de-duplication."""
    frames=[]; audit=[]; session=requests.Session(); unique,members=_dedupe(points)
    pairs=list(zip(unique,members))
    for bi,bp in enumerate(_chunks(pairs,40)):
        batch=[x[0] for x in bp]; groups=[x[1] for x in bp]
        params={"latitude":",".join(str(p["lat"]) for p in batch),"longitude":",".join(str(p["lon"]) for p in batch),
                "hourly":",".join(HOURLY_VARS),"timezone":timezone,"start_date":start.date().isoformat(),"end_date":end.date().isoformat()}
        k=_key(params); data=_load(k); cs="HIT" if data is not None else "MISS"
        if data is None:
            data=_get(session,params).json(); _save(k,data)
        audit.append({"provider":"OPEN_METEO_AIR_QUALITY","batch_index":bi,"cache_status":cs,"cache_key":k,
                      "queried_unique_locations":len(batch),"logical_route_points":sum(len(g) for g in groups),
                      "deduplicated_locations_saved":sum(len(g) for g in groups)-len(batch)})
        locs=data if isinstance(data,list) else [data]
        for group,loc in zip(groups,locs):
            hourly=loc.get("hourly",{}); times=hourly.get("time",[]); vals=hourly.get("aerosol_optical_depth")
            base=pd.DataFrame({"time":pd.to_datetime(times)}); base["aod550"]=vals if vals is not None else math.nan
            base["aerosol_provider"]="OPEN_METEO_AIR_QUALITY_CAMS"; base["aerosol_source_variable"]="aerosol_optical_depth"; base["aerosol_wavelength_nm"]=550.0
            for p in group:
                df=base.copy()
                for kk in ("point_id","distance_km","direction_offset_deg","lat","lon"): df[kk]=p[kk]
                frames.append(df)
        if bi < math.ceil(len(pairs)/40)-1 and cs!="HIT": time.sleep(2.0)
    out=pd.concat(frames,ignore_index=True) if frames else pd.DataFrame(); out.attrs["api_request_audit"]=audit
    return out


def interpolate_route_aerosol_at_time(hourly_df: pd.DataFrame, when: datetime) -> pd.DataFrame:
    if hourly_df.empty: return hourly_df.copy()
    target=pd.Timestamp(when.replace(tzinfo=None)); rows=[]
    for _pid,g in hourly_df.groupby("point_id",sort=False):
        g=g.sort_values("time"); before=g[g.time<=target].tail(1); after=g[g.time>=target].head(1)
        if before.empty and after.empty: continue
        if before.empty: row=after.iloc[0].copy()
        elif after.empty: row=before.iloc[0].copy()
        else:
            a,b=before.iloc[0],after.iloc[0]; row=a.copy(); spectral_cols=[c for c in ("aod550","aod645","aod670","aod800") if c in g.columns]
            if a.time==b.time:
                for c in spectral_cols: row[c]=a[c]
            else:
                w=(target-a.time).total_seconds()/(b.time-a.time).total_seconds()
                for c in spectral_cols: row[c]=math.nan if pd.isna(a[c]) or pd.isna(b[c]) else float(a[c])+w*(float(b[c])-float(a[c]))
        row["time"]=target; rows.append(row)
    return pd.DataFrame(rows)
