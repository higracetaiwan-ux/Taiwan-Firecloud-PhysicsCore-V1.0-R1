from __future__ import annotations
import math
import numpy as np
import pandas as pd

from .shared_geometry.vertical import VerticalIndexPlan

# Native condensate thresholds are deliberately very small: model cloud water/ice
# mixing ratios are kg/kg. This threshold is only used to define a geometric
# cloud envelope; the actual condensate values remain continuous.
NATIVE_CONDENSATE_THRESHOLD_KGKG = 1.0e-7
R_D = 287.05


def _interp_pair(z, a, b, key):
    za, zb = a['altitude_agl_km'], b['altitude_agl_km']
    va, vb = a.get(key, np.nan), b.get(key, np.nan)
    if pd.isna(va) or pd.isna(vb) or zb == za:
        return np.nan if pd.isna(va) else float(va)
    w = (z-za)/(zb-za)
    return float(va) + w*(float(vb)-float(va))


def native_levels_from_row(row: pd.Series, pressure_levels_hpa) -> list[dict]:
    """Extract native cloud microphysics on pressure levels.

    Canonical fields per level: cloud_liquid_water_kgkg_<p>hPa, cloud_ice_water_kgkg_<p>hPa,
    cloud_fraction_<p>hPa, temperature_<p>hPa, relative_humidity_<p>hPa,
    geopotential_height_<p>hPa. Missing native fields remain NaN.
    """
    elev = row.get('model_surface_elevation_m', np.nan)
    elev = 0.0 if pd.isna(elev) else float(elev)
    out=[]
    for p in pressure_levels_hpa:
        gh=row.get(f'geopotential_height_{p}hPa', np.nan)
        if pd.isna(gh):
            continue
        z=(float(gh)-elev)/1000.0
        if z < -0.25 or z > 20.0:
            continue
        out.append({
            'pressure_hpa':float(p), 'altitude_agl_km':max(0.0,z),
            'cloud_fraction':row.get(f'cloud_fraction_{p}hPa', np.nan),
            'cloud_liquid_water_kgkg':row.get(f'cloud_liquid_water_kgkg_{p}hPa', row.get(f'cloud_liquid_water_{p}hPa', np.nan)),
            'cloud_ice_water_kgkg':row.get(f'cloud_ice_water_kgkg_{p}hPa', row.get(f'cloud_ice_water_{p}hPa', np.nan)),
            'temperature_k':row.get(f'temperature_{p}hPa', np.nan),
            'relative_humidity_pct':row.get(f'relative_humidity_{p}hPa', np.nan),
        })
    return sorted(out,key=lambda x:x['altitude_agl_km'])


def build_native_cloud_volume(route_at_time: pd.DataFrame, pressure_levels_hpa, altitude_centers_km, step_km: float):
    """Interpolate native condensate fields onto the Firecloud AGL voxel lattice.

    Returns (voxels, columns). No RH->cloud or low/mid/high reconstruction is used.
    A voxel is physically supported only where both bracketing native model levels
    have geopotential height. Condensate Missing is never converted to zero.
    """
    rows=[]
    for _,r in route_at_time.iterrows():
        pts=native_levels_from_row(r, pressure_levels_hpa)
        d=float(r['distance_km']); off=float(r['direction_offset_deg'])
        alts=np.array([x['altitude_agl_km'] for x in pts]) if pts else np.array([])
        vplan = VerticalIndexPlan.from_heights(alts) if len(pts) >= 2 else None
        for z in altitude_centers_km:
            z=float(z); rec={'direction_offset_deg':off,'distance_km':d,'voxel_center_km':z,
                'voxel_bottom_km':z-step_km/2,'voxel_top_km':z+step_km/2,
                'native_microphysics_supported':False,'native_profile_source':r.get('native_profile_source','UNAVAILABLE')}
            if len(pts)<2 or z<alts.min() or z>alts.max():
                rec.update({'cloud_fraction':np.nan,'cloud_liquid_water_kgkg':np.nan,'cloud_ice_water_kgkg':np.nan,
                    'total_cloud_condensate_kgkg':np.nan,'cloud_phase':'UNKNOWN','air_density_kgm3':np.nan,
                    'liquid_water_content_gm3':np.nan,'ice_water_content_gm3':np.nan,'native_quality':'OUTSIDE_NATIVE_SUPPORT'})
                rows.append(rec); continue
            lo_arr, hi_arr = vplan.bracket_indices(np.asarray([z], dtype=float))
            lo, hi = int(lo_arr[0]), int(hi_arr[0])
            if lo==hi and hi+1<len(pts): hi+=1
            a,b=pts[lo],pts[hi]
            vals={k:_interp_pair(z,a,b,k) for k in ['cloud_fraction','cloud_liquid_water_kgkg','cloud_ice_water_kgkg','temperature_k','relative_humidity_pct','pressure_hpa']}
            ql,qi=vals['cloud_liquid_water_kgkg'],vals['cloud_ice_water_kgkg']
            qt=np.nan if pd.isna(ql) or pd.isna(qi) else max(0.0,ql)+max(0.0,qi)
            p=vals['pressure_hpa']; t=vals['temperature_k']
            rho=np.nan if pd.isna(p) or pd.isna(t) or t<=0 else (p*100.0)/(R_D*t)
            lwc=np.nan if pd.isna(rho) or pd.isna(ql) else max(0.0,ql)*rho*1000.0
            iwc=np.nan if pd.isna(rho) or pd.isna(qi) else max(0.0,qi)*rho*1000.0
            if pd.isna(ql) or pd.isna(qi): phase='UNKNOWN'
            elif ql < NATIVE_CONDENSATE_THRESHOLD_KGKG and qi < NATIVE_CONDENSATE_THRESHOLD_KGKG: phase='CLEAR'
            elif ql >= NATIVE_CONDENSATE_THRESHOLD_KGKG and qi >= NATIVE_CONDENSATE_THRESHOLD_KGKG: phase='MIXED'
            elif qi >= NATIVE_CONDENSATE_THRESHOLD_KGKG: phase='ICE'
            else: phase='LIQUID'
            rec.update(vals); rec.update({'total_cloud_condensate_kgkg':qt,'cloud_phase':phase,'air_density_kgm3':rho,
                'liquid_water_content_gm3':lwc,'ice_water_content_gm3':iwc,
                'native_microphysics_supported':not(pd.isna(ql) or pd.isna(qi)),
                'native_quality':'NATIVE_CONDENSATE_INTERPOLATED' if not(pd.isna(ql) or pd.isna(qi)) else 'MISSING_NATIVE_CONDENSATE'})
            rows.append(rec)
    vox=pd.DataFrame(rows)
    cols=[]
    if not vox.empty:
        for (off,d),g in vox.groupby(['direction_offset_deg','distance_km'],sort=False):
            known=g[g['total_cloud_condensate_kgkg'].notna()]
            cloudy=known[known['total_cloud_condensate_kgkg']>=NATIVE_CONDENSATE_THRESHOLD_KGKG]
            base=top=thick=np.nan
            if not cloudy.empty:
                base=float(cloudy['voxel_bottom_km'].min()); top=float(cloudy['voxel_top_km'].max()); thick=top-base
            lwp=(known['liquid_water_content_gm3']*step_km).sum(min_count=1) # g/m3 * km (diagnostic)
            iwp=(known['ice_water_content_gm3']*step_km).sum(min_count=1)
            cols.append({'direction_offset_deg':float(off),'distance_km':float(d),'native_cloud_base_km':base,
                'native_cloud_top_km':top,'native_cloud_thickness_km':thick,'native_vertical_completeness':float(g['native_microphysics_supported'].mean()),
                'liquid_water_path_proxy_gm3_km':lwp,'ice_water_path_proxy_gm3_km':iwp,
                'boundary_quality':'NATIVE_CONDENSATE_THRESHOLD'})
    return vox,pd.DataFrame(cols)
