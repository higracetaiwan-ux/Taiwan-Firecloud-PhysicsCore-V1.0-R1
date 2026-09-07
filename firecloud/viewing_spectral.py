"""PhysicsCore V1.0-R5.7 Cloud->Observer six-band spectral extinction.

This branch is independent of Formation. It integrates the observer viewing path
using real route gas profiles, CAMS native 3-D aerosol extinction when present,
forecast-native cloud optical evidence, and forecast-native hydrometeor optics.
No Sun->CloudBase transmission is reused.
"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd

from .contracts import SIX_BAND_WAVELENGTHS_NM
from .viewing import _projected_support_interval
from .shared_geometry.ray import observer_los_height_agl_km, sample_observer_los_segment, sampled_segment_path_km
from .gas_rt import prepare_gas_rt_context, _interp_fast_profile_state, _sigma_fast, BOLTZMANN


def _finite(v):
    try:
        x=float(v); return x if math.isfinite(x) else None
    except Exception:
        return None


def _spectral_aod_from_row(row: pd.Series, wl: int):
    exact=_finite(row.get(f"aod{wl}"))
    if exact is not None: return max(0.0,exact)
    a550=_finite(row.get("aod550")); ang=_finite(row.get("angstrom_550_800"))
    if a550 is None or ang is None: return None
    return max(0.0,a550*(float(wl)/550.0)**(-ang))


def _interp_aerosol_ext532(row: pd.Series, z_km: float):
    zz=[]; ee=[]
    for c in row.index:
        if not str(c).startswith("cams_aerext532_m1_") or not str(c).endswith("hPa"): continue
        p=str(c).split("_")[-1][:-3]
        z=_finite(row.get(f"cams_geopotential_height_m_{p}hPa")); e=_finite(row.get(c))
        if z is not None and e is not None and e>=0:
            zz.append(z/1000.0); ee.append(e)
    if len(zz)<2: return None
    order=np.argsort(zz); z=np.asarray(zz)[order]; e=np.asarray(ee)[order]
    if z_km < z[0]-1e-9 or z_km > z[-1]+1e-9: return None
    return float(np.interp(z_km,z,e))


def _route_rows_for_target(df: pd.DataFrame, direction: float, time, angle: float, max_distance: float):
    if df is None or df.empty: return pd.DataFrame()
    q=df.copy()
    if "direction_offset_deg" in q: q=q[(pd.to_numeric(q["direction_offset_deg"],errors="coerce")-direction).abs()<1e-8]
    if "solar_altitude_deg" in q: q=q[(pd.to_numeric(q["solar_altitude_deg"],errors="coerce")-angle).abs()<1e-8]
    if "time" in q and pd.notna(time): q=q[q["time"].astype(str)==str(time)]
    q["distance_km"]=pd.to_numeric(q["distance_km"],errors="coerce")
    return q[q["distance_km"].notna() & (q["distance_km"]<=max_distance+1e-8)].sort_values("distance_km")


def _integrate_view_aerosol(target, aerosol_rows: pd.DataFrame, earth_radius_km: float):
    dt=float(target["target_distance_km"]); ht=0.5*(float(target["target_base_km"])+float(target["target_top_km"]))
    if aerosol_rows is None or aerosol_rows.empty: return None,"VIEW_AEROSOL_3D_MISSING",0.0
    dists=sorted(aerosol_rows["distance_km"].astype(float).unique())
    if len(dists)<2: return None,"VIEW_AEROSOL_ROUTE_INCOMPLETE",0.0
    taus={int(w):0.0 for w in SIX_BAND_WAVELENGTHS_NM}; used=0; required=0; path_km=0.0
    for d0,d1 in zip(dists[:-1],dists[1:]):
        if d0>=dt: break
        d1=min(d1,dt)
        if d1<=d0: continue
        required+=1; dm=0.5*(d0+d1); z0=observer_los_height_agl_km(dt,ht,d0,earth_radius_km); z1=observer_los_height_agl_km(dt,ht,d1,earth_radius_km); zm=observer_los_height_agl_km(dt,ht,dm,earth_radius_km)
        row=aerosol_rows[(aerosol_rows["distance_km"]-d0).abs()<1e-8]
        if row.empty: continue
        row=row.iloc[0]; ext532=_interp_aerosol_ext532(row,zm)
        a550=_spectral_aod_from_row(row,550)
        if ext532 is None or a550 is None or a550<=0: continue
        path=math.hypot((d1-d0)*1000.0,(z1-z0)*1000.0); path_km+=path/1000.0
        ok=True; local={}
        for wl in SIX_BAND_WAVELENGTHS_NM:
            aw=_spectral_aod_from_row(row,int(wl))
            if aw is None: ok=False; break
            local[int(wl)]=ext532*(aw/a550)*path
        if not ok: continue
        used+=1
        for wl,v in local.items(): taus[wl]+=v
    if required==0 or used<required:
        return taus if used else None,"VIEW_AEROSOL_3D_PARTIAL",path_km
    return taus,"VIEW_AEROSOL_3D_RESOLVED",path_km


def _integrate_view_gas(target, gas_rows: pd.DataFrame, earth_radius_km: float, prepared_context=None):
    if gas_rows is None or gas_rows.empty: return None,"VIEW_GAS_PROFILE_MISSING",0.0
    ctx=prepared_context if prepared_context is not None else prepare_gas_rt_context(gas_rows)
    if not ctx.valid: return None,"VIEW_GAS_RT_CONTEXT_MISSING",0.0
    direction=float(target["direction_offset_deg"]); dt=float(target["target_distance_km"]); ht=0.5*(float(target["target_base_km"])+float(target["target_top_km"]))
    drec=ctx.prepared_profile.get(direction)
    if drec is None: return None,"VIEW_GAS_DIRECTION_MISSING",0.0
    ds=[float(x) for x in drec["distances"] if float(x)<=dt+1e-8]
    if not ds or ds[0]>1e-6: return None,"VIEW_GAS_OBSERVER_ENDPOINT_MISSING",0.0
    if ds[-1]<dt-1e-8: ds.append(dt)
    taus={int(w):0.0 for w in SIX_BAND_WAVELENGTHS_NM}; used=0; required=0; path_km=0.0
    for d0,d1 in zip(ds[:-1],ds[1:]):
        if d1<=d0: continue
        required+=1; dm=0.5*(d0+d1); z0=observer_los_height_agl_km(dt,ht,d0,earth_radius_km); z1=observer_los_height_agl_km(dt,ht,d1,earth_radius_km); zm=observer_los_height_agl_km(dt,ht,dm,earth_radius_km)
        # Use nearest real route profile at or before segment midpoint.
        near=min(drec["distances"], key=lambda x: abs(float(x)-dm)); rec=drec["profiles"].get(float(near))
        if rec is None: continue
        st=_interp_fast_profile_state(rec,zm)
        if st is None: continue
        tk=float(st["temperature_k"]); ph=float(st["pressure_hpa"]); n_air=ph*100.0/(BOLTZMANN*tk)
        dens={"O2":float(st["o2_mole_fraction"])*n_air,"H2O":float(st["h2o_mole_fraction"])*n_air,"O3":float(st["o3_mole_fraction"])*n_air}
        path=math.hypot((d1-d0)*1000.0,(z1-z0)*1000.0); local={}; ok=True
        for wl in SIX_BAND_WAVELENGTHS_NM:
            total=0.0
            for gas,density in dens.items():
                sig=_sigma_fast(ctx.lut,gas,int(wl),tk,ph)
                if not math.isfinite(float(sig)): ok=False; break
                total += float(sig)*density*path
            if not ok: break
            local[int(wl)]=total
        if not ok: continue
        used+=1; path_km+=path/1000.0
        for wl,v in local.items(): taus[wl]+=v
    if required==0 or used<required:
        return taus if used else None,"VIEW_GAS_RT_PARTIAL",path_km
    return taus,"VIEW_GAS_RT_RESOLVED",path_km


def _exact_cot_map(cloud_layers: pd.DataFrame, target_optics: pd.DataFrame):
    out={}
    if cloud_layers is not None and not cloud_layers.empty:
        for _,r in cloud_layers.iterrows():
            cot=_finite(r.get("cot")); consistency=str(r.get("evidence_consistency") or "")
            if cot is not None and consistency not in {"CF_CLOUD_CONDENSATE_ZERO","CONDENSATE_CLOUD_CF_LOW"}:
                out[str(r.get("layer_id"))]=(cot,"CLOUD_LAYER_NATIVE_COT")
    if target_optics is not None and not target_optics.empty:
        for _,r in target_optics.iterrows():
            if bool(r.get("target_optics_ready",False)):
                cot=_finite(r.get("target_cot_nominal"))
                if cot is not None: out[str(r.get("cloud_layer_id"))]=(cot,str(r.get("evidence_source") or "TARGET_OPTICS"))
    return out


def _cloud_expected_tau(target, cloud_layers: pd.DataFrame, target_optics: pd.DataFrame, earth_radius_km: float, *, prefiltered_layers=None, cotmap=None, support_cache=None):
    # Rebuild only the actual blocker volumes for the center of the target angular footprint.
    direction=float(target["direction_offset_deg"]); dt=float(target["target_distance_km"]); ht=0.5*(float(target["target_base_km"])+float(target["target_top_km"]))
    time=target.get("time"); angle=float(target.get("solar_altitude_deg"))
    cand=prefiltered_layers.copy() if prefiltered_layers is not None else cloud_layers.copy()
    if prefiltered_layers is None:
        if "solar_altitude_deg" in cand: cand=cand[(pd.to_numeric(cand["solar_altitude_deg"],errors="coerce")-angle).abs()<1e-8]
        cand=cand[(pd.to_numeric(cand["direction_offset_deg"],errors="coerce")-direction).abs()<1e-8]
        if "time" in cand and pd.notna(time): cand=cand[cand["time"].astype(str)==str(time)]
    transect=cand.copy(); cand=cand[pd.to_numeric(cand["distance_km"],errors="coerce")<dt-1e-8]
    cotmap=_exact_cot_map(cloud_layers,target_optics) if cotmap is None else cotmap
    support_cache={} if support_cache is None else support_cache
    expected_t=1.0; conditional_tau=0.0; blockers=0; unresolved=0; sources=[]
    for _,b in cand.iterrows():
        bb=_finite(b.get("z_base_km")); bt=_finite(b.get("z_top_km")); cf=_finite(b.get("cloud_fraction"))
        if bb is None or bt is None or bt<=bb: continue
        _sk=str(b.get("layer_id",""))+"@"+str(b.name)
        if _sk not in support_cache: support_cache[_sk]=_projected_support_interval(b,transect)
        s0,s1,_,_=support_cache[_sk]
        if not (math.isfinite(float(s0)) and math.isfinite(float(s1))) or s1<=s0: continue
        xs,zz=sample_observer_los_segment(dt,ht,max(0.0,s0),min(dt,s1),sample_count=25,radius_km=earth_radius_km)
        if len(xs)<2: continue
        inside=np.isfinite(zz)&(zz>=bb)&(zz<=bt)
        if not inside.any(): continue
        blockers+=1; bid=str(b.get("layer_id")); cotrec=cotmap.get(bid)
        if cotrec is None or cf is None:
            unresolved+=1; continue
        cot,src=cotrec; seg=sampled_segment_path_km(xs,zz,inside)*1000.0
        thick=(bt-bb)*1000.0
        if seg<=0 or thick<=0: continue
        slant_tau=max(0.0,cot)*seg/thick; conditional_tau+=slant_tau; cf=min(1.0,max(0.0,cf)); expected_t *= (1.0-cf)+cf*math.exp(-slant_tau); sources.append(src)
    if blockers==0: return 0.0,0.0,"VIEW_CLOUD_PATH_CLEAR",0,""
    if unresolved: return None,conditional_tau,"VIEW_CLOUD_OPTICS_PARTIAL",blockers,";".join(sorted(set(sources)))
    eff_tau=-math.log(max(1e-300,expected_t)); return eff_tau,conditional_tau,"VIEW_CLOUD_OPTICS_RESOLVED_OCCUPANCY_EXPECTATION",blockers,";".join(sorted(set(sources)))


def build_viewing_spectral_extinction(viewing_geometry: pd.DataFrame, cloud_layers: pd.DataFrame, target_optics: pd.DataFrame,
                                      aerosol_snapshots: pd.DataFrame, gas_profiles: pd.DataFrame,
                                      viewing_precipitation: pd.DataFrame | None=None, *, earth_radius_km: float=6371.0) -> pd.DataFrame:
    """Build independent Cloud→Observer six-band extinction.

    R5.7.3 caches route groups, gas RT contexts, exact-COT lookup, and cloud
    support geometry. Numerical formulas and fail-closed semantics are unchanged.
    """
    rows=[]
    if viewing_geometry is None or viewing_geometry.empty: return pd.DataFrame()
    pmap={}
    if viewing_precipitation is not None and not viewing_precipitation.empty:
        pmap={str(r.canvas_id):r for r in viewing_precipitation.itertuples(index=False)}

    def _key(timev, angv, dirv):
        a=_finite(angv); d=_finite(dirv)
        return (str(timev), None if a is None else round(a,8), None if d is None else round(d,8))
    def _group_route(df):
        out={}
        if df is None or df.empty: return out
        work=df.copy()
        tser=work.get("time",pd.Series("",index=work.index)).astype(str)
        aser=pd.to_numeric(work.get("solar_altitude_deg"),errors="coerce").round(8)
        dser=pd.to_numeric(work.get("direction_offset_deg"),errors="coerce").round(8)
        for k,g in work.groupby([tser,aser,dser],dropna=False,sort=False):
            key=(str(k[0]), None if pd.isna(k[1]) else float(k[1]), None if pd.isna(k[2]) else float(k[2]))
            gg=g.copy(); gg["distance_km"]=pd.to_numeric(gg["distance_km"],errors="coerce"); out[key]=gg.sort_values("distance_km")
        return out
    aerosol_groups=_group_route(aerosol_snapshots)
    gas_groups=_group_route(gas_profiles)
    cloud_groups=_group_route(cloud_layers)
    gas_contexts={}
    for k,g in gas_groups.items():
        gas_contexts[k]=prepare_gas_rt_context(g)
    cotmap=_exact_cot_map(cloud_layers,target_optics)
    cloud_support_caches={k:{} for k in cloud_groups}

    for _,t in viewing_geometry.iterrows():
        if not bool(t.get("photographic_target_eligible",False)): continue
        direction=_finite(t.get("direction_offset_deg")); dt=_finite(t.get("target_distance_km")); zb=_finite(t.get("target_base_km")); zt=_finite(t.get("target_top_km")); angle=_finite(t.get("solar_altitude_deg"))
        if None in (direction,dt,zb,zt,angle) or dt<=0: continue
        k=_key(t.get("time"),angle,direction)
        ar=aerosol_groups.get(k,pd.DataFrame()); ar=ar[ar["distance_km"].notna() & (ar["distance_km"]<=dt+1e-8)] if not ar.empty else ar
        gr=gas_groups.get(k,pd.DataFrame()); gr=gr[gr["distance_km"].notna() & (gr["distance_km"]<=dt+1e-8)] if not gr.empty else gr
        atau,astatus,apath=_integrate_view_aerosol(t,ar,earth_radius_km)
        gtau,gstatus,gpath=_integrate_view_gas(t,gr,earth_radius_km,prepared_context=gas_contexts.get(k))
        cg=cloud_groups.get(k)
        ctau,cconditional,cstatus,blockers,csrc=_cloud_expected_tau(t,cloud_layers,target_optics,earth_radius_km,prefiltered_layers=cg,cotmap=cotmap,support_cache=cloud_support_caches.setdefault(k,{}))
        pr=pmap.get(str(t.get("canvas_id")))
        rec={"time":t.get("time"),"solar_altitude_deg":angle,"canvas_id":t.get("canvas_id"),"cloud_layer_id":t.get("cloud_layer_id"),"direction_offset_deg":direction,"target_distance_km":dt,"target_base_km":zb,"target_top_km":zt,
             "view_gas_status":gstatus,"view_aerosol_status":astatus,"view_cloud_status":cstatus,"view_cloud_conditional_slant_tau":cconditional,"view_cloud_blocker_count":blockers,"view_cloud_optical_sources":csrc,"view_gas_path_km":gpath,"view_aerosol_path_km":apath,
             "view_precipitation_status":getattr(pr,"view_precipitation_status",None) if pr is not None else "VIEW_PRECIPITATION_VOLUME_UNRESOLVED"}
        missing=[]
        for wl in SIX_BAND_WAVELENGTHS_NM:
            tg=gtau.get(int(wl)) if gtau is not None else None; ta=atau.get(int(wl)) if atau is not None else None; tc=ctau
            tp=getattr(pr,f"view_tau_precip_{int(wl)}nm",None) if pr is not None else None; tp=_finite(tp)
            rec[f"view_tau_gas_{int(wl)}nm"]=tg; rec[f"view_tau_aerosol_{int(wl)}nm"]=ta; rec[f"view_tau_cloud_{int(wl)}nm"]=tc; rec[f"view_tau_precip_{int(wl)}nm"]=tp
            miss=[]
            if tg is None: miss.append("GAS")
            if ta is None: miss.append("AEROSOL")
            if tc is None: miss.append("CLOUD")
            if tp is None: miss.append("PRECIPITATION")
            if miss:
                rec[f"view_tau_total_{int(wl)}nm"]=None; rec[f"view_transmission_{int(wl)}nm"]=None; missing.extend(miss)
            else:
                total=max(0.0,float(tg+ta+tc+tp)); rec[f"view_tau_total_{int(wl)}nm"]=total; rec[f"view_transmission_{int(wl)}nm"]=math.exp(-total)
        rec["viewing_spectral_status"]="VIEW_FULL_SIX_BAND_RT" if not missing else "VIEW_PARTIAL_SIX_BAND_RT"
        rec["viewing_missing_components"]=";".join(sorted(set(missing)))
        rec["note"]="CLOUD_TO_OBSERVER_ONLY;FORMATION_UNCHANGED;NO_SUN_PATH_REUSE;CLOUD_OCCUPANCY_AND_OPTICAL_DEPTH_KEPT_SEPARATE;R573_CACHED_ROUTE_CONTEXT"
        rows.append(rec)
    return pd.DataFrame(rows)

def summarize_viewing_spectral_extinction(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty: return pd.DataFrame()
    rows=[]
    for keys,g in df.groupby(["time","solar_altitude_deg"],dropna=False,sort=False):
        full=g["viewing_spectral_status"].astype(str).eq("VIEW_FULL_SIX_BAND_RT")
        rec={"time":keys[0],"solar_altitude_deg":keys[1],"photographic_target_count":len(g),"full_viewing_rt_target_count":int(full.sum()),"viewing_rt_completeness":float(full.mean()) if len(g) else 0.0}
        for wl in SIX_BAND_WAVELENGTHS_NM:
            tr=pd.to_numeric(g.get(f"view_transmission_{int(wl)}nm"),errors="coerce")
            rec[f"mean_view_transmission_{int(wl)}nm"]=float(tr.mean()) if tr.notna().any() else np.nan
        rec["viewing_spectral_state"]="VIEW_SPECTRAL_READY" if full.all() and len(g)>0 else ("VIEW_SPECTRAL_PARTIAL" if full.any() else "VIEW_SPECTRAL_UNRESOLVED")
        rows.append(rec)
    return pd.DataFrame(rows)
