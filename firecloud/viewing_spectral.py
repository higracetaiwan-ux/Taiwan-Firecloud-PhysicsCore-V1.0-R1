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

VIEWING_SIX_BAND_RT_CONTRACT = "R5.7.29_VIEWING_FULL_SIX_BAND_RT_V1"


def _finite(v):
    try:
        x=float(v); return x if math.isfinite(x) else None
    except Exception:
        return None


def _spectral_aod_from_row(row: pd.Series, wl: int, *, explicit_only: bool = False):
    exact=_finite(row.get(f"aod{wl}"))
    if exact is not None: return max(0.0,exact)
    if explicit_only:
        return None
    a550=_finite(row.get("aod550")); ang=_finite(row.get("angstrom_550_800"))
    if a550 is None or ang is None: return None
    return max(0.0,a550*(float(wl)/550.0)**(-ang))


def _evidence_key(time_value, angle_value, object_id) -> tuple[str, float | None, str]:
    angle=_finite(angle_value)
    return (str(time_value), None if angle is None else round(angle,8), str(object_id))


def _aerosol_temporal_provenance_valid(row: pd.Series) -> tuple[bool,str]:
    """Require the R5.7.28 exact or bounded-real temporal evidence contract."""
    state=str(row.get("spectral_aod_temporal_evidence_state") or "")
    if state == "EXACT_VALID_TIME":
        return True,state
    if state == "REAL_ONE_SIDED_TEMPORAL_FALLBACK":
        offset=_finite(row.get("spectral_aod_time_offset_hours"))
        bound=_finite(row.get("spectral_aod_temporal_bound_hours"))
        if offset is not None and bound is not None and abs(offset)<=bound+1e-9:
            return True,state
        return False,"REAL_TEMPORAL_FALLBACK_OUT_OF_BOUND"
    return False,"SPECTRAL_AOD_TEMPORAL_PROVENANCE_MISSING"


def _interp_aerosol_ext532_with_endpoint(row: pd.Series, z_km: float, lowest_endpoint_tolerance_km: float = 0.0):
    zz=[]; ee=[]
    for c in row.index:
        if not str(c).startswith("cams_aerext532_m1_") or not str(c).endswith("hPa"): continue
        p=str(c).split("_")[-1][:-3]
        z=_finite(row.get(f"cams_geopotential_height_m_{p}hPa")); e=_finite(row.get(c))
        if z is not None and e is not None and e>=0:
            zz.append(z/1000.0); ee.append(e)
    if len(zz)<2: return None,False
    order=np.argsort(zz); z=np.asarray(zz)[order]; e=np.asarray(ee)[order]
    if z_km > z[-1]+1e-9: return None,False
    if z_km < z[0]-1e-9:
        # R5.7.32 Glow-only endpoint robustness. After CAMS geopotential is
        # correctly normalized to metres, an observer-ray midpoint can fall a
        # few metres below the lowest (1000 hPa) pressure surface. A strict,
        # small snap to the nearest *native* lowest-level extinction is allowed
        # only within the explicitly supplied tolerance. This is not AOD
        # reconstruction and does not change the default Viewing contract.
        if lowest_endpoint_tolerance_km > 0.0 and (z[0]-float(z_km)) <= float(lowest_endpoint_tolerance_km)+1e-12:
            return float(e[0]),True
        return None,False
    return float(np.interp(z_km,z,e)),False


def _interp_aerosol_ext532(row: pd.Series, z_km: float):
    value,_ = _interp_aerosol_ext532_with_endpoint(row,z_km,0.0)
    return value


def _route_rows_for_target(df: pd.DataFrame, direction: float, time, angle: float, max_distance: float):
    if df is None or df.empty: return pd.DataFrame()
    q=df.copy()
    if "direction_offset_deg" in q: q=q[(pd.to_numeric(q["direction_offset_deg"],errors="coerce")-direction).abs()<1e-8]
    if "solar_altitude_deg" in q: q=q[(pd.to_numeric(q["solar_altitude_deg"],errors="coerce")-angle).abs()<1e-8]
    if "time" in q and pd.notna(time): q=q[q["time"].astype(str)==str(time)]
    q["distance_km"]=pd.to_numeric(q["distance_km"],errors="coerce")
    return q[q["distance_km"].notna() & (q["distance_km"]<=max_distance+1e-8)].sort_values("distance_km")


def _integrate_view_aerosol(target, aerosol_rows: pd.DataFrame, earth_radius_km: float, *, lowest_endpoint_tolerance_km: float = 0.0):
    dt=float(target["target_distance_km"]); ht=0.5*(float(target["target_base_km"])+float(target["target_top_km"]))
    empty_meta={"required_segment_count":0,"resolved_segment_count":0,"temporal_fallback_segment_count":0,"temporal_missing_segment_count":0,"lowest_endpoint_snap_segment_count":0}
    if aerosol_rows is None or aerosol_rows.empty: return None,"VIEW_AEROSOL_3D_MISSING",0.0,empty_meta
    dists=sorted(aerosol_rows["distance_km"].astype(float).unique())
    if len(dists)<2: return None,"VIEW_AEROSOL_ROUTE_INCOMPLETE",0.0,empty_meta
    taus={int(w):0.0 for w in SIX_BAND_WAVELENGTHS_NM}; used=0; required=0; path_km=0.0; fallback=0; temporal_missing=0; endpoint_snap=0
    for d0,d1 in zip(dists[:-1],dists[1:]):
        if d0>=dt: break
        d1=min(d1,dt)
        if d1<=d0: continue
        required+=1; dm=0.5*(d0+d1); z0=observer_los_height_agl_km(dt,ht,d0,earth_radius_km); z1=observer_los_height_agl_km(dt,ht,d1,earth_radius_km); zm=observer_los_height_agl_km(dt,ht,dm,earth_radius_km)
        row=aerosol_rows[(aerosol_rows["distance_km"]-d0).abs()<1e-8]
        if row.empty: continue
        row=row.iloc[0]
        temporal_ok,temporal_state=_aerosol_temporal_provenance_valid(row)
        if not temporal_ok:
            temporal_missing+=1; continue
        fallback+=int(temporal_state=="REAL_ONE_SIDED_TEMPORAL_FALLBACK")
        ext532,snapped=_interp_aerosol_ext532_with_endpoint(row,zm,lowest_endpoint_tolerance_km)
        endpoint_snap += int(snapped)
        a550=_spectral_aod_from_row(row,550,explicit_only=True)
        if ext532 is None or a550 is None or a550<=0: continue
        path=math.hypot((d1-d0)*1000.0,(z1-z0)*1000.0); path_km+=path/1000.0
        ok=True; local={}
        for wl in SIX_BAND_WAVELENGTHS_NM:
            # Full Viewing RT consumes the explicit six-band payload emitted by
            # the R5.7.28 real multi-wavelength spectral evidence chain.  A
            # local one-band Angstrom reconstruction must not be promoted to
            # full six-band evidence here.
            aw=_spectral_aod_from_row(row,int(wl),explicit_only=True)
            if aw is None: ok=False; break
            local[int(wl)]=ext532*(aw/a550)*path
        if not ok: continue
        used+=1
        for wl,v in local.items(): taus[wl]+=v
    meta={"required_segment_count":required,"resolved_segment_count":used,"temporal_fallback_segment_count":fallback,"temporal_missing_segment_count":temporal_missing,"lowest_endpoint_snap_segment_count":endpoint_snap}
    if required==0 or used<required:
        return taus if used else None,"VIEW_AEROSOL_3D_PARTIAL",path_km,meta
    return taus,"VIEW_AEROSOL_3D_RESOLVED",path_km,meta


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
    """Index COT by time + angle + layer; layer IDs repeat across angles."""
    out={}
    if cloud_layers is not None and not cloud_layers.empty:
        for _,r in cloud_layers.iterrows():
            cot=_finite(r.get("cot")); consistency=str(r.get("evidence_consistency") or "")
            if cot is not None and consistency not in {"CF_CLOUD_CONDENSATE_ZERO","CONDENSATE_CLOUD_CF_LOW"}:
                out[_evidence_key(r.get("time"),r.get("solar_altitude_deg"),r.get("layer_id"))]=(cot,"CLOUD_LAYER_NATIVE_COT")
    if target_optics is not None and not target_optics.empty:
        for _,r in target_optics.iterrows():
            if bool(r.get("target_optics_ready",False)):
                cot=_finite(r.get("target_cot_nominal"))
                if cot is not None:
                    out[_evidence_key(r.get("time"),r.get("solar_altitude_deg"),r.get("cloud_layer_id"))]=(cot,str(r.get("evidence_source") or "TARGET_OPTICS"))
    return out


def _cloud_expected_tau(target, cloud_layers: pd.DataFrame, target_optics: pd.DataFrame, earth_radius_km: float, *, prefiltered_layers=None, cotmap=None, support_cache=None):
    # Rebuild only the actual blocker volumes for the center of the target angular footprint.
    #
    # R5.7.41.3.3 historical-replay hardening:
    # an old/partial provider replay can legitimately yield a headerless empty
    # DataFrame.  Missing cloud-volume evidence must fail closed instead of
    # raising KeyError (and must never be promoted to PATH_CLEAR).
    direction=float(target["direction_offset_deg"]); dt=float(target["target_distance_km"]); ht=0.5*(float(target["target_base_km"])+float(target["target_top_km"]))
    time=target.get("time"); angle=float(target.get("solar_altitude_deg"))
    required_cloud_columns={"direction_offset_deg","distance_km","z_base_km","z_top_km"}
    if cloud_layers is None or cloud_layers.empty:
        return None,0.0,"VIEW_CLOUD_VOLUME_UNRESOLVED",0,""
    if not required_cloud_columns.issubset(set(cloud_layers.columns)):
        return None,0.0,"VIEW_CLOUD_VOLUME_UNRESOLVED",0,""
    cand=prefiltered_layers.copy() if prefiltered_layers is not None else cloud_layers.copy()
    if prefiltered_layers is not None:
        # A supplied group should retain the cloud schema.  If it does not,
        # treat it as missing evidence rather than an empty/clear route.
        if not required_cloud_columns.issubset(set(cand.columns)):
            return None,0.0,"VIEW_CLOUD_VOLUME_UNRESOLVED",0,""
    else:
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
        blockers+=1; bid=str(b.get("layer_id")); cotrec=cotmap.get(_evidence_key(b.get("time"),b.get("solar_altitude_deg"),bid))
        if cotrec is None or cf is None:
            unresolved+=1; continue
        cot,src=cotrec; seg=sampled_segment_path_km(xs,zz,inside)*1000.0
        thick=(bt-bb)*1000.0
        if seg<=0 or thick<=0: continue
        slant_tau=max(0.0,cot)*seg/thick; conditional_tau+=slant_tau; cf=min(1.0,max(0.0,cf)); expected_t *= (1.0-cf)+cf*math.exp(-slant_tau); sources.append(src)
    if blockers==0: return 0.0,0.0,"VIEW_CLOUD_PATH_CLEAR",0,""
    if unresolved: return None,conditional_tau,"VIEW_CLOUD_OPTICS_PARTIAL",blockers,";".join(sorted(str(x) for x in set(sources)))
    eff_tau=-math.log(max(1e-300,expected_t)); return eff_tau,conditional_tau,"VIEW_CLOUD_OPTICS_RESOLVED_OCCUPANCY_EXPECTATION",blockers,";".join(sorted(str(x) for x in set(sources)))


def build_viewing_spectral_extinction(viewing_geometry: pd.DataFrame, cloud_layers: pd.DataFrame, target_optics: pd.DataFrame,
                                      aerosol_snapshots: pd.DataFrame, gas_profiles: pd.DataFrame,
                                      viewing_precipitation: pd.DataFrame | None=None, *, earth_radius_km: float=6371.0, aerosol_lowest_endpoint_tolerance_km: float=0.0) -> pd.DataFrame:
    """Build independent Cloud→Observer six-band extinction.

    R5.7.3 caches route groups, gas RT contexts, exact-COT lookup, and cloud
    support geometry. Numerical formulas and fail-closed semantics are unchanged.
    """
    rows=[]
    if viewing_geometry is None or viewing_geometry.empty: return pd.DataFrame()
    pmap={}
    if viewing_precipitation is not None and not viewing_precipitation.empty:
        pmap={
            _evidence_key(getattr(r,"time",None),getattr(r,"solar_altitude_deg",None),getattr(r,"canvas_id",None)):r
            for r in viewing_precipitation.itertuples(index=False)
        }

    def _key(timev, angv, dirv):
        a=_finite(angv); d=_finite(dirv)
        return (str(timev), None if a is None else round(a,8), None if d is None else round(d,8))
    def _group_route(df):
        out={}
        if df is None or df.empty: return out
        work=df.copy()
        if "solar_altitude_deg" not in work.columns or "direction_offset_deg" not in work.columns or "distance_km" not in work.columns:
            return out
        tser=work.get("time",pd.Series("",index=work.index)).astype(str)
        aser=pd.to_numeric(work["solar_altitude_deg"],errors="coerce").round(8)
        dser=pd.to_numeric(work["direction_offset_deg"],errors="coerce").round(8)
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
        if None in (direction,dt,zb,zt,angle) or dt<=0:
            rec={"time":t.get("time"),"solar_altitude_deg":angle,"canvas_id":t.get("canvas_id"),"cloud_layer_id":t.get("cloud_layer_id"),"direction_offset_deg":direction,"target_distance_km":dt,"target_base_km":zb,"target_top_km":zt,
                 "view_gas_status":"VIEW_GAS_GEOMETRY_UNRESOLVED","view_aerosol_status":"VIEW_AEROSOL_GEOMETRY_UNRESOLVED","view_cloud_status":"VIEW_CLOUD_GEOMETRY_UNRESOLVED","view_cloud_conditional_slant_tau":None,"view_cloud_blocker_count":0,"view_cloud_optical_sources":"","view_gas_path_km":0.0,"view_aerosol_path_km":0.0,
                 "view_precipitation_status":"VIEW_PRECIPITATION_GEOMETRY_UNRESOLVED","view_aerosol_required_segment_count":0,"view_aerosol_resolved_segment_count":0,"view_aerosol_temporal_fallback_segment_count":0,"view_aerosol_temporal_missing_segment_count":0,"view_aerosol_lowest_endpoint_snap_segment_count":0}
            for wl in SIX_BAND_WAVELENGTHS_NM:
                for component in ("gas","aerosol","cloud","precip","total"):
                    rec[f"view_tau_{component}_{int(wl)}nm"]=None
                rec[f"view_transmission_{int(wl)}nm"]=None
                rec[f"view_band_evidence_state_{int(wl)}nm"]="MISSING"
            rec["viewing_spectral_status"]="VIEW_SIX_BAND_RT_UNRESOLVED"
            rec["viewing_missing_components"]="GEOMETRY"
            rec["viewing_resolved_component_count"]=0
            rec["viewing_spectral_contract"]=VIEWING_SIX_BAND_RT_CONTRACT
            rec["note"]="CLOUD_TO_OBSERVER_ONLY;FORMATION_UNCHANGED;LOCAL_OR_INVALID_VIEW_GEOMETRY_FAIL_CLOSED"
            rows.append(rec); continue
        k=_key(t.get("time"),angle,direction)
        ar=aerosol_groups.get(k,pd.DataFrame()); ar=ar[ar["distance_km"].notna() & (ar["distance_km"]<=dt+1e-8)] if not ar.empty else ar
        gr=gas_groups.get(k,pd.DataFrame()); gr=gr[gr["distance_km"].notna() & (gr["distance_km"]<=dt+1e-8)] if not gr.empty else gr
        atau,astatus,apath,ameta=_integrate_view_aerosol(t,ar,earth_radius_km,lowest_endpoint_tolerance_km=aerosol_lowest_endpoint_tolerance_km)
        gtau,gstatus,gpath=_integrate_view_gas(t,gr,earth_radius_km,prepared_context=gas_contexts.get(k))
        cg=cloud_groups.get(k)
        ctau,cconditional,cstatus,blockers,csrc=_cloud_expected_tau(t,cloud_layers,target_optics,earth_radius_km,prefiltered_layers=cg,cotmap=cotmap,support_cache=cloud_support_caches.setdefault(k,{}))
        pr=pmap.get(_evidence_key(t.get("time"),angle,t.get("canvas_id")))
        rec={"time":t.get("time"),"solar_altitude_deg":angle,"canvas_id":t.get("canvas_id"),"cloud_layer_id":t.get("cloud_layer_id"),"direction_offset_deg":direction,"target_distance_km":dt,"target_base_km":zb,"target_top_km":zt,
             "view_gas_status":gstatus,"view_aerosol_status":astatus,"view_cloud_status":cstatus,"view_cloud_conditional_slant_tau":cconditional,"view_cloud_blocker_count":blockers,"view_cloud_optical_sources":csrc,"view_gas_path_km":gpath,"view_aerosol_path_km":apath,
             "view_precipitation_status":getattr(pr,"view_precipitation_status",None) if pr is not None else "VIEW_PRECIPITATION_VOLUME_UNRESOLVED",
             "view_aerosol_required_segment_count":ameta.get("required_segment_count",0),"view_aerosol_resolved_segment_count":ameta.get("resolved_segment_count",0),
             "view_aerosol_temporal_fallback_segment_count":ameta.get("temporal_fallback_segment_count",0),"view_aerosol_temporal_missing_segment_count":ameta.get("temporal_missing_segment_count",0),"view_aerosol_lowest_endpoint_snap_segment_count":ameta.get("lowest_endpoint_snap_segment_count",0)}
        missing=[]
        resolved_components={
            "GAS":gstatus=="VIEW_GAS_RT_RESOLVED",
            "AEROSOL":astatus=="VIEW_AEROSOL_3D_RESOLVED",
            "CLOUD":cstatus in {"VIEW_CLOUD_PATH_CLEAR","VIEW_CLOUD_OPTICS_RESOLVED_OCCUPANCY_EXPECTATION"},
            "PRECIPITATION":rec["view_precipitation_status"]=="VIEW_PRECIPITATION_OPTICS_RESOLVED",
        }
        for wl in SIX_BAND_WAVELENGTHS_NM:
            tg=gtau.get(int(wl)) if gtau is not None else None; ta=atau.get(int(wl)) if atau is not None else None; tc=ctau
            tp=getattr(pr,f"view_tau_precip_{int(wl)}nm",None) if pr is not None else None; tp=_finite(tp)
            rec[f"view_tau_gas_{int(wl)}nm"]=tg; rec[f"view_tau_aerosol_{int(wl)}nm"]=ta; rec[f"view_tau_cloud_{int(wl)}nm"]=tc; rec[f"view_tau_precip_{int(wl)}nm"]=tp
            miss=[]
            if tg is None or not resolved_components["GAS"]: miss.append("GAS")
            if ta is None or not resolved_components["AEROSOL"]: miss.append("AEROSOL")
            if tc is None or not resolved_components["CLOUD"]: miss.append("CLOUD")
            if tp is None or not resolved_components["PRECIPITATION"]: miss.append("PRECIPITATION")
            if miss:
                rec[f"view_tau_total_{int(wl)}nm"]=None; rec[f"view_transmission_{int(wl)}nm"]=None; missing.extend(miss)
                rec[f"view_band_evidence_state_{int(wl)}nm"]="MISSING"
            else:
                total=max(0.0,float(tg+ta+tc+tp)); rec[f"view_tau_total_{int(wl)}nm"]=total; rec[f"view_transmission_{int(wl)}nm"]=math.exp(-total)
                rec[f"view_band_evidence_state_{int(wl)}nm"]="FULL"
        available_component_values=any(
            _finite(rec.get(f"view_tau_{component}_{int(wl)}nm")) is not None
            for component in ("gas","aerosol","cloud","precip") for wl in SIX_BAND_WAVELENGTHS_NM
        )
        rec["viewing_spectral_status"]=("VIEW_FULL_SIX_BAND_RT" if not missing else ("VIEW_PARTIAL_SIX_BAND_RT" if available_component_values else "VIEW_SIX_BAND_RT_UNRESOLVED"))
        rec["viewing_missing_components"]=";".join(sorted(str(x) for x in set(missing)))
        rec["viewing_resolved_component_count"]=int(sum(resolved_components.values()))
        rec["viewing_spectral_contract"]=VIEWING_SIX_BAND_RT_CONTRACT
        rec["note"]="CLOUD_TO_OBSERVER_ONLY;FORMATION_UNCHANGED;NO_SUN_PATH_REUSE;CLOUD_OCCUPANCY_AND_OPTICAL_DEPTH_KEPT_SEPARATE;PARTIAL_COMPONENT_TAU_NEVER_PROMOTED_TO_TOTAL_TRANSMISSION;R5729_TIME_ANGLE_TARGET_EVIDENCE_KEYS"
        rows.append(rec)
    return pd.DataFrame(rows)

def summarize_viewing_spectral_extinction(df: pd.DataFrame) -> pd.DataFrame:
    cols=["time","solar_altitude_deg","photographic_target_count","full_viewing_rt_target_count","partial_viewing_rt_target_count","unresolved_viewing_rt_target_count","viewing_rt_completeness",*[f"mean_view_transmission_{int(w)}nm" for w in SIX_BAND_WAVELENGTHS_NM],*[f"viewing_rt_completeness_{int(w)}nm" for w in SIX_BAND_WAVELENGTHS_NM],"viewing_spectral_state","viewing_missing_components","viewing_spectral_contract"]
    if df is None or df.empty: return pd.DataFrame(columns=cols)
    rows=[]
    for keys,g in df.groupby(["time","solar_altitude_deg"],dropna=False,sort=False):
        full=g["viewing_spectral_status"].astype(str).eq("VIEW_FULL_SIX_BAND_RT")
        partial=g["viewing_spectral_status"].astype(str).eq("VIEW_PARTIAL_SIX_BAND_RT")
        unresolved=~(full|partial)
        rec={"time":keys[0],"solar_altitude_deg":keys[1],"photographic_target_count":len(g),"full_viewing_rt_target_count":int(full.sum()),"partial_viewing_rt_target_count":int(partial.sum()),"unresolved_viewing_rt_target_count":int(unresolved.sum()),"viewing_rt_completeness":float(full.mean()) if len(g) else 0.0}
        for wl in SIX_BAND_WAVELENGTHS_NM:
            band_full=g.get(f"view_band_evidence_state_{int(wl)}nm",pd.Series("MISSING",index=g.index)).astype(str).eq("FULL")
            tr=pd.to_numeric(g.loc[band_full,f"view_transmission_{int(wl)}nm"],errors="coerce") if f"view_transmission_{int(wl)}nm" in g else pd.Series(dtype=float)
            rec[f"mean_view_transmission_{int(wl)}nm"]=float(tr.mean()) if tr.notna().any() else np.nan
            rec[f"viewing_rt_completeness_{int(wl)}nm"]=float(band_full.mean()) if len(g) else 0.0
        rec["viewing_spectral_state"]="VIEW_SPECTRAL_READY" if full.all() and len(g)>0 else ("VIEW_SPECTRAL_PARTIAL" if (full|partial).any() else "VIEW_SPECTRAL_UNRESOLVED")
        missing=set()
        for value in g.get("viewing_missing_components",pd.Series(dtype=str)).fillna("").astype(str):
            missing.update(x for x in value.split(";") if x)
        rec["viewing_missing_components"]=";".join(sorted(missing))
        rec["viewing_spectral_contract"]=VIEWING_SIX_BAND_RT_CONTRACT
        rows.append(rec)
    return pd.DataFrame(rows,columns=cols)


def attach_viewing_spectral_status(viewing_geometry: pd.DataFrame, spectral: pd.DataFrame) -> pd.DataFrame:
    """Attach target RT state without changing any viewing geometry value."""
    if viewing_geometry is None or viewing_geometry.empty:
        return viewing_geometry.copy() if isinstance(viewing_geometry,pd.DataFrame) else pd.DataFrame()
    out=viewing_geometry.copy()
    status_map={}
    if spectral is not None and not spectral.empty:
        for _,r in spectral.iterrows():
            key=(_evidence_key(r.get("time"),r.get("solar_altitude_deg"),r.get("canvas_id")),str(r.get("cloud_layer_id")))
            status_map[key]=str(r.get("viewing_spectral_status") or "VIEW_SIX_BAND_RT_UNRESOLVED")
    states=[]
    for _,r in out.iterrows():
        if not bool(r.get("photographic_target_eligible",False)):
            states.append("VIEW_SPECTRAL_NOT_APPLICABLE_FOREGROUND_BLOCKER")
            continue
        key=(_evidence_key(r.get("time"),r.get("solar_altitude_deg"),r.get("canvas_id")),str(r.get("cloud_layer_id")))
        states.append(status_map.get(key,"VIEW_SIX_BAND_RT_UNRESOLVED"))
    out["viewing_path_spectral_status"]=states
    out["viewing_spectral_contract"]=VIEWING_SIX_BAND_RT_CONTRACT
    return out
