"""PhysicsCore V1.0-R5.7 forecast-native 3-D precipitation-path optics.

Scientific contract
-------------------
* Surface precipitation rate never becomes optical depth.
* tau_precip is resolved only from forecast-native hydrometeor mass fields
  (GFS RWMR/SNMR/GRLE today; provider-neutral canonical names are used).
* Missing hydrometeor volume != zero hydrometeor volume.
* Visible-band large-particle extinction is a Tier-1 optical model with explicit
  assumed effective particle radii/densities; it is not a retrieval from rain rate.
* Sun->CloudBase and Cloud->Observer remain separate path integrations.
"""
from __future__ import annotations
import math
import re
import numpy as np
import pandas as pd

from .contracts import SIX_BAND_WAVELENGTHS_NM
from .geometry import ray_altitude_km_at_surface_distance

R_D = 287.05
Q_EXT_VISIBLE = 2.0
# Deliberately explicit Tier-1 assumptions. Large precipitation particles are
# approximately grey across 550-750 nm compared with molecular/aerosol effects.
HYDROMETEOR_MICROPHYSICS = {
    "rain": {"prefix":"rain_water_kgkg_", "radius_um":500.0, "density_kgm3":1000.0},
    "snow": {"prefix":"snow_water_kgkg_", "radius_um":300.0, "density_kgm3":100.0},
    "graupel": {"prefix":"graupel_kgkg_", "radius_um":700.0, "density_kgm3":400.0},
}


def _finite(v):
    try:
        x=float(v); return x if math.isfinite(x) else None
    except Exception:
        return None


def _mass_extinction_m2kg(radius_um: float, density_kgm3: float) -> float:
    r=max(1e-9,float(radius_um)*1e-6)
    rho=max(1e-9,float(density_kgm3))
    return 3.0*Q_EXT_VISIBLE/(4.0*rho*r)


def _pressure_levels_from_columns(df: pd.DataFrame) -> list[int]:
    levels=set()
    for c in df.columns:
        for cfg in HYDROMETEOR_MICROPHYSICS.values():
            m=re.fullmatch(re.escape(cfg["prefix"])+r"(\d+)hPa",str(c))
            if m: levels.add(int(m.group(1)))
    return sorted(levels, reverse=True)


def _support_bounds(distances: list[float], i: int) -> tuple[float,float]:
    d=float(distances[i])
    left=0.0 if i==0 else 0.5*(float(distances[i-1])+d)
    right=d if i==len(distances)-1 else 0.5*(d+float(distances[i+1]))
    return max(0.0,left), max(left,right)


def _layer_bounds_from_heights(heights: dict[int,float], level: int) -> tuple[float,float] | None:
    if level not in heights or not math.isfinite(float(heights[level])):
        return None
    levs=sorted((p for p,z in heights.items() if math.isfinite(float(z))), reverse=True)
    if level not in levs: return None
    j=levs.index(level); z=float(heights[level])
    if len(levs)<2: return None
    if j==0:
        z2=float(heights[levs[j+1]]); dz=abs(z2-z); return max(0.0,z-0.5*dz), z+0.5*dz
    if j==len(levs)-1:
        z1=float(heights[levs[j-1]]); dz=abs(z-z1); return max(0.0,z-0.5*dz), z+0.5*dz
    za=float(heights[levs[j-1]]); zb=float(heights[levs[j+1]])
    return min(0.5*(za+z),0.5*(z+zb)), max(0.5*(za+z),0.5*(z+zb))


def _prepare_native_hydrometeor_cells(route_snapshot: pd.DataFrame) -> tuple[dict[float,list[dict]], dict]:
    """Build provider-neutral route cells carrying true 3-D hydrometeor volume."""
    if route_snapshot is None or route_snapshot.empty:
        return {}, {"status":"NO_ROUTE_SNAPSHOT","field_completeness":0.0}
    levels=_pressure_levels_from_columns(route_snapshot)
    if not levels:
        return {}, {"status":"NATIVE_HYDROMETEOR_FIELDS_MISSING","field_completeness":0.0}
    cells_by_dir={}; available_fields=0; possible_fields=0; nonzero=0
    for direction,gdir in route_snapshot.groupby("direction_offset_deg",dropna=False):
        try: direction=float(direction)
        except Exception: continue
        gdir=gdir.copy(); gdir["distance_km"]=pd.to_numeric(gdir["distance_km"],errors="coerce")
        gdir=gdir[gdir["distance_km"].notna()].sort_values("distance_km")
        distances=sorted(gdir["distance_km"].astype(float).unique())
        for i,d in enumerate(distances):
            rr=gdir[(gdir["distance_km"]-d).abs()<1e-8]
            if rr.empty: continue
            r=rr.iloc[0]; s0,s1=_support_bounds(distances,i)
            heights={}
            for p in levels:
                z=_finite(r.get(f"geopotential_height_{p}hPa"))
                if z is None: z=_finite(r.get(f"geopotential_height_m_{p}hPa"))
                if z is not None: heights[p]=z/1000.0
            for p in levels:
                bounds=_layer_bounds_from_heights(heights,p)
                if bounds is None: continue
                z0,z1=bounds
                if not z1>z0: continue
                temp=_finite(r.get(f"temperature_{p}hPa"))
                if temp is None: temp=_finite(r.get(f"temperature_k_{p}hPa"))
                if temp is None or temp<=0: continue
                rho_air=float(p)*100.0/(R_D*temp)
                ext=0.0; field_seen=False; all_seen=True; qvals={}
                for kind,cfg in HYDROMETEOR_MICROPHYSICS.items():
                    col=f"{cfg['prefix']}{p}hPa"; possible_fields+=1
                    q=_finite(r.get(col))
                    if q is None:
                        all_seen=False; qvals[kind]=None; continue
                    available_fields+=1; field_seen=True; q=max(0.0,q); qvals[kind]=q
                    if q>0: nonzero+=1
                    mass_density=q*rho_air
                    ext += mass_density*_mass_extinction_m2kg(cfg["radius_um"],cfg["density_kgm3"])
                if not field_seen: continue
                cells_by_dir.setdefault(direction,[]).append({
                    "distance_km":d,"support_start_km":s0,"support_end_km":s1,
                    "pressure_hpa":p,"z_base_km":z0,"z_top_km":z1,
                    "temperature_k":temp,"air_density_kgm3":rho_air,
                    "extinction_m1":ext,"all_hydrometeor_fields_resolved":bool(all_seen),
                    **{f"{k}_kgkg":v for k,v in qvals.items()},
                })
    comp=available_fields/max(1,possible_fields)
    status="NATIVE_HYDROMETEOR_VOLUME_READY" if cells_by_dir else "NATIVE_HYDROMETEOR_GEOMETRY_UNRESOLVED"
    return cells_by_dir,{"status":status,"field_completeness":float(comp),"nonzero_value_count":int(nonzero),"pressure_level_count":len(levels)}


def _integrate_sun_path(canvas, cells: list[dict], solar_altitude_deg: float, earth_radius_km: float) -> tuple[float|None,int,int,float]:
    """Integrate large-particle extinction through native hydrometeor cells."""
    if not cells: return None,0,0,0.0
    tau=0.0; hit=0; unresolved=0; path_km=0.0
    td=float(canvas.distance_km); tz=float(canvas.cloud_base_altitude_km)
    for c in cells:
        if float(c["support_end_km"]) < td-1e-9: continue
        a=max(td,float(c["support_start_km"])); b=float(c["support_end_km"])
        if b<=a+1e-9: continue
        xm=0.5*(a+b)
        za=ray_altitude_km_at_surface_distance(td,tz,a,solar_altitude_deg,earth_radius_km)
        zm=ray_altitude_km_at_surface_distance(td,tz,xm,solar_altitude_deg,earth_radius_km)
        zb=ray_altitude_km_at_surface_distance(td,tz,b,solar_altitude_deg,earth_radius_km)
        if any(v is None or not math.isfinite(float(v)) for v in (za,zm,zb)): continue
        lo=float(c["z_base_km"]); hi=float(c["z_top_km"])
        if max(za,zm,zb)<lo or min(za,zm,zb)>hi: continue
        hit+=1
        if not bool(c["all_hydrometeor_fields_resolved"]): unresolved+=1
        # deterministic 17-point path occupancy through the cell
        xs=np.linspace(a,b,17); zz=np.array([ray_altitude_km_at_surface_distance(td,tz,float(x),solar_altitude_deg,earth_radius_km) for x in xs],dtype=float)
        inside=np.isfinite(zz)&(zz>=lo)&(zz<=hi)
        seg=0.0
        for j in range(len(xs)-1):
            if inside[j] or inside[j+1]:
                frac=1.0 if inside[j] and inside[j+1] else 0.5
                seg += frac*math.hypot((xs[j+1]-xs[j])*1000.0,(zz[j+1]-zz[j])*1000.0)
        if seg>0:
            path_km += seg/1000.0
            tau += max(0.0,float(c["extinction_m1"]))*seg
    if hit==0:
        # Native volume exists along this transect and no cell intersects the ray:
        # zero is a resolved geometric result only when every relevant field is present.
        relevant=[c for c in cells if float(c["support_end_km"])>=td-1e-9]
        if relevant and all(bool(c["all_hydrometeor_fields_resolved"]) for c in relevant):
            return 0.0,0,0,0.0
        return None,0,len(relevant),0.0
    if unresolved:
        return None,hit,unresolved,path_km
    return float(tau),hit,0,path_km


def build_precipitation_path_evidence(canvases, route_snapshot: pd.DataFrame | None = None, *, valid_time=None,
                                      path_optics: pd.DataFrame | None = None, solar_altitude_deg: float | None=None,
                                      earth_radius_km: float=6371.0) -> pd.DataFrame:
    rows=[]
    precip_present=False; max_rate=None; surface_field_available=False
    if route_snapshot is not None and not route_snapshot.empty:
        for col in ("precipitation","precipitation_mm","rain","rain_mm"):
            if col in route_snapshot.columns:
                vals=pd.to_numeric(route_snapshot[col],errors="coerce")
                if vals.notna().any():
                    surface_field_available=True; max_rate=float(vals.max()); precip_present=max_rate>0.0; break
    explicit = path_optics if path_optics is not None else pd.DataFrame()
    cells_by_dir,volume_meta=_prepare_native_hydrometeor_cells(route_snapshot if route_snapshot is not None else pd.DataFrame())
    for c in canvases:
        rec={
            "time":valid_time,"canvas_id":c.canvas_id,
            "surface_precipitation_field_available":bool(surface_field_available),
            "surface_precipitation_evidence":bool(precip_present),
            "max_surface_precipitation_rate":max_rate,
            "geometry_resolved_3d":False,"optical_evidence":"MISSING","role":"UNKNOWN",
            "native_hydrometeor_volume_status":volume_meta.get("status"),
            "native_hydrometeor_field_completeness":volume_meta.get("field_completeness",0.0),
            "native_hydrometeor_nonzero_value_count":volume_meta.get("nonzero_value_count",0),
            "hydrometeor_optical_model":"LARGE_PARTICLE_GREY_EXTINCTION_TIER1_QEXT2_ASSUMED_REFF",
            "status":"PRECIPITATION_VOLUME_UNRESOLVED",
            "reason":"NATIVE_3D_HYDROMETEOR_VOLUME_REQUIRED;SURFACE_RATE_NOT_USED_FOR_TAU",
        }
        q=pd.DataFrame()
        if not explicit.empty and "canvas_id" in explicit.columns:
            q=explicit[explicit["canvas_id"].astype(str)==str(c.canvas_id)]
        if not q.empty:
            prow=q.iloc[0]; rec["geometry_resolved_3d"]=bool(prow.get("geometry_resolved_3d",True)); known=0
            for wl in SIX_BAND_WAVELENGTHS_NM:
                v=_finite(prow.get(f"tau_precip_{int(wl)}nm",prow.get(f"precipitation_optical_depth_{int(wl)}nm")))
                rec[f"tau_precip_{int(wl)}nm"]=v; known += int(v is not None)
            if known==len(SIX_BAND_WAVELENGTHS_NM):
                rec.update({"status":"PRECIPITATION_OPTICS_RESOLVED","optical_evidence":"FULL","role":str(prow.get("role","ILLUMINATION_BLOCKER")),"reason":"EXPLICIT_PATH_RESOLVED_HYDROMETEOR_OPTICS"})
            elif known:
                rec.update({"status":"PRECIPITATION_OPTICS_PARTIAL","optical_evidence":"PARTIAL_OPTICS","role":str(prow.get("role","ILLUMINATION_BLOCKER")),"reason":"PARTIAL_PATH_RESOLVED_HYDROMETEOR_OPTICS"})
            rows.append(rec); continue
        if solar_altitude_deg is None:
            rows.append(rec); continue
        direction=None
        # direction is encoded in Canvas->CloudLayer in runtime IDs; preserve no-guess fallback
        try:
            s=str(c.cloud_layer_id); direction=float(s.split("_d",1)[0][3:]) if s.startswith("dir") else None
        except Exception: direction=None
        cells=cells_by_dir.get(float(direction),[]) if direction is not None else []
        tau,hits,unresolved,path_km=_integrate_sun_path(c,cells,float(solar_altitude_deg),float(earth_radius_km))
        rec["hydrometeor_intersection_count"]=int(hits); rec["hydrometeor_unresolved_intersection_count"]=int(unresolved); rec["hydrometeor_slant_path_km"]=float(path_km)
        if tau is not None:
            rec["geometry_resolved_3d"]=True; rec["optical_evidence"]="FULL"; rec["role"]="ILLUMINATION_BLOCKER"
            rec["status"]="PRECIPITATION_OPTICS_RESOLVED"; rec["reason"]="FORECAST_NATIVE_3D_RWMR_SNMR_GRLE_PATH_INTEGRATION"
            for wl in SIX_BAND_WAVELENGTHS_NM: rec[f"tau_precip_{int(wl)}nm"]=float(tau)
        elif cells:
            rec["geometry_resolved_3d"]=True; rec["status"]="PRECIPITATION_OPTICS_PARTIAL"; rec["optical_evidence"]="PARTIAL_OPTICS"
            rec["reason"]="NATIVE_HYDROMETEOR_VOLUME_PARTIAL_OR_INTERSECTION_OPTICS_UNRESOLVED"
        rows.append(rec)
    return pd.DataFrame(rows)


def _observer_los_height_km(target_distance_km: float, target_height_km: float, distance_km: float, earth_radius_km: float=6371.0) -> float:
    dt=max(1e-9,float(target_distance_km)); d=min(max(0.0,float(distance_km)),dt); r=float(earth_radius_km)
    target_tangent=float(target_height_km)-dt*dt/(2.0*r)
    line_tangent=(d/dt)*target_tangent
    ground_tangent=-(d*d)/(2.0*r)
    return line_tangent-ground_tangent


def build_viewing_precipitation_evidence(viewing_targets: pd.DataFrame, route_snapshot: pd.DataFrame | None, *, earth_radius_km: float=6371.0) -> pd.DataFrame:
    """Cloud->Observer native-hydrometeor extinction, independent of Formation."""
    cols=["time","solar_altitude_deg","canvas_id","view_precipitation_status","view_precipitation_path_km","view_precipitation_intersection_count",*[f"view_tau_precip_{int(w)}nm" for w in SIX_BAND_WAVELENGTHS_NM],"note"]
    if viewing_targets is None or viewing_targets.empty:
        return pd.DataFrame(columns=cols)
    cells_by_dir,meta=_prepare_native_hydrometeor_cells(route_snapshot if route_snapshot is not None else pd.DataFrame())
    rows=[]
    for _,r in viewing_targets.iterrows():
        if not bool(r.get("photographic_target_eligible",False)):
            continue
        dt=_finite(r.get("target_distance_km")); zb=_finite(r.get("target_base_km")); zt=_finite(r.get("target_top_km")); direction=_finite(r.get("direction_offset_deg"))
        base={"time":r.get("time"),"solar_altitude_deg":r.get("solar_altitude_deg"),"canvas_id":r.get("canvas_id")}
        if None in (dt,zb,zt,direction) or dt<=0 or zt<=zb:
            rows.append({**base,"view_precipitation_status":"VIEW_PRECIPITATION_GEOMETRY_UNRESOLVED","view_precipitation_path_km":np.nan,"view_precipitation_intersection_count":0,"note":"FORMATION_UNCHANGED;VIEWING_ONLY"}); continue
        hs=0.5*(zb+zt); tau=0.0; hits=0; unresolved=0; path_km=0.0
        cells=cells_by_dir.get(float(direction),[])
        for c in cells:
            a=max(0.0,float(c["support_start_km"])); b=min(float(dt),float(c["support_end_km"]))
            if b<=a+1e-9: continue
            lo=float(c["z_base_km"]); hi=float(c["z_top_km"])
            xs=np.linspace(a,b,17); zz=np.array([_observer_los_height_km(dt,hs,float(x),earth_radius_km) for x in xs],dtype=float)
            inside=np.isfinite(zz)&(zz>=lo)&(zz<=hi)
            if not inside.any(): continue
            hits+=1
            if not bool(c["all_hydrometeor_fields_resolved"]): unresolved+=1
            seg=0.0
            for j in range(len(xs)-1):
                if inside[j] or inside[j+1]:
                    frac=1.0 if inside[j] and inside[j+1] else 0.5
                    seg += frac*math.hypot((xs[j+1]-xs[j])*1000.0,(zz[j+1]-zz[j])*1000.0)
            if seg>0:
                path_km += seg/1000.0; tau += max(0.0,float(c["extinction_m1"]))*seg
        if not cells:
            status="VIEW_PRECIPITATION_VOLUME_UNRESOLVED"; val=None
        elif unresolved:
            status="VIEW_PRECIPITATION_OPTICS_PARTIAL"; val=None
        else:
            status="VIEW_PRECIPITATION_OPTICS_RESOLVED"; val=float(tau)
        rec={**base,"view_precipitation_status":status,"view_precipitation_path_km":path_km,"view_precipitation_intersection_count":hits,"note":"FORECAST_NATIVE_3D_HYDROMETEOR_VIEW_PATH;NO_SURFACE_RATE_TO_TAU;LARGE_PARTICLE_GREY_TIER1"}
        for wl in SIX_BAND_WAVELENGTHS_NM: rec[f"view_tau_precip_{int(wl)}nm"]=val
        rows.append(rec)
    return pd.DataFrame(rows,columns=cols)
