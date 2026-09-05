"""PhysicsCore V1.0-R5.2.1 finite-solar-disk penumbra + red illumination diagnostics.

No arbitrary 'effective red height' is invented. Geometry supplies H_any,
H_center, H_full and F_sun. Spectral path/base-illumination evidence supplies
whether 650/700/750 nm actually reaches CloudBase.
"""
from __future__ import annotations
import math
import pandas as pd
from .geometry import finite_solar_disk_penumbra_heights_km, direct_solar_fraction_g0

RED_BANDS=(650,700,750)
CORE_DISTANCES_KM=tuple([float(x) for x in range(0, 45, 5)] + [float(x) for x in range(50, 101, 10)])


def build_earth_shadow_penumbra_matrix(solar_altitudes_deg, *, distances_km=CORE_DISTANCES_KM) -> pd.DataFrame:
    rows=[]
    for a in solar_altitudes_deg:
        for d in distances_km:
            h=finite_solar_disk_penumbra_heights_km(float(d),float(a))
            rows.append({
                "solar_altitude_deg":float(a),"distance_km":float(d),**h,
                "geometry_mode":"G0_FINITE_SOLAR_DISK",
                "sampling_regime":"0-40KM_5KM;40-100KM_10KM",
                "sampling_step_is_cloud_width":False,
                "note":"H_CENTER_IS_TRADITIONAL_EARTH_SHADOW_DIAGNOSTIC;H_ANY_TO_H_FULL_IS_PENUMBRA_TRANSITION;DISTANCE_GRID_FOLLOWS_SHARED_ADAPTIVE_HORIZONTAL_SAMPLING",
            })
    return pd.DataFrame(rows)


def build_canvas_penumbra_red_illumination(canvases: pd.DataFrame, spectral_paths: pd.DataFrame, cloud_base_illumination: pd.DataFrame) -> pd.DataFrame:
    if canvases is None or canvases.empty:
        return pd.DataFrame()
    sp=spectral_paths if spectral_paths is not None else pd.DataFrame()
    cb=cloud_base_illumination if cloud_base_illumination is not None else pd.DataFrame()
    rows=[]
    for _,c in canvases.iterrows():
        cid=str(c.get("canvas_id")); d=float(c.get("distance_km")); a=float(c.get("solar_altitude_deg")); z=float(c.get("cloud_base_altitude_km"))
        h=finite_solar_disk_penumbra_heights_km(d,a)
        fs=float(direct_solar_fraction_g0(d,z,a))
        if fs<=0: geom="FULL_UMBRA"
        elif fs>=1: geom="FULL_SOLAR_DISK"
        else: geom="PENUMBRA_PARTIAL_SOLAR_DISK"
        spp=sp[sp.get("canvas_id",pd.Series(dtype=str)).astype(str).eq(cid)] if not sp.empty and "canvas_id" in sp else pd.DataFrame()
        transmissions={}
        for wl in RED_BANDS:
            q=spp[pd.to_numeric(spp.get("wavelength_nm",pd.Series(dtype=float)),errors="coerce").eq(float(wl))] if not spp.empty else pd.DataFrame()
            vals=pd.to_numeric(q.get("transmission",pd.Series(dtype=float)),errors="coerce").dropna()
            transmissions[wl]=float(vals.iloc[0]) if not vals.empty else float("nan")
        cbb=cb[cb.get("canvas_id",pd.Series(dtype=str)).astype(str).eq(cid)] if not cb.empty and "canvas_id" in cb else pd.DataFrame()
        base={wl:float("nan") for wl in RED_BANDS}
        if not cbb.empty:
            rr=cbb.iloc[0]
            for wl in RED_BANDS:
                v=pd.to_numeric(pd.Series([rr.get(f"relative_base_illumination_{wl}nm")]),errors="coerce").iloc[0]
                base[wl]=float(v) if pd.notna(v) else float("nan")
        red_path_resolved=all(math.isfinite(transmissions[w]) for w in RED_BANDS)
        red_base_resolved=all(math.isfinite(base[w]) for w in RED_BANDS)
        red_reaches=bool(red_base_resolved and any(base[w]>0.0 for w in RED_BANDS))
        if fs<=0:
            state="FULL_UMBRA_NO_DIRECT_RED"
        elif not red_path_resolved:
            state="PENUMBRA_OR_SUNLIT_RED_PATH_UNRESOLVED"
        elif not red_base_resolved:
            state="RED_CLOUDBASE_IRRADIANCE_UNRESOLVED"
        elif red_reaches:
            state="RED_LIGHT_REACHES_CLOUDBASE"
        else:
            state="RED_LIGHT_NOT_REACHING_CLOUDBASE"
        rows.append({
            "solar_altitude_deg":a,"canvas_id":cid,"cloud_layer_id":c.get("cloud_layer_id"),"distance_km":d,"cloud_base_altitude_km":z,
            **h,"cloudbase_clearance_above_h_any_km":z-h["h_any_sun_km"],"cloudbase_clearance_above_h_center_km":z-h["h_solar_center_km"],"cloudbase_clearance_above_h_full_km":z-h["h_full_solar_disk_km"],
            "direct_solar_fraction":fs,"solar_disk_geometry_state":geom,
            "transmission_650nm":transmissions[650],"transmission_700nm":transmissions[700],"transmission_750nm":transmissions[750],
            "relative_base_illumination_650nm":base[650],"relative_base_illumination_700nm":base[700],"relative_base_illumination_750nm":base[750],
            "red_path_resolved":red_path_resolved,"red_base_illumination_resolved":red_base_resolved,"red_light_reaches_cloudbase":red_reaches,
            "penumbra_red_illumination_state":state,
            "note":"NO_FIXED_EFFECTIVE_RED_HEIGHT;FORMATION_USES_F_SUN_TIMES_SPECTRAL_SUN_TO_CLOUDBASE_TRANSMISSION",
        })
    return pd.DataFrame(rows)
