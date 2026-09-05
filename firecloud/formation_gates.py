"""PhysicsCore V1.0-R5.2 causal Formation gate diagnostics.

Formation is a Sun→CloudBase problem.  This table does not use observer-path
visibility and does not collapse Formation into a score.
"""
from __future__ import annotations
import math
import pandas as pd
from .geometry import finite_solar_disk_penumbra_heights_km

RED_BANDS=(650.0,700.0,750.0)

def build_formation_gate_table(canvases: pd.DataFrame, direct_solar: pd.DataFrame, cloud_base_illumination: pd.DataFrame, spectral_paths: pd.DataFrame) -> pd.DataFrame:
    if canvases is None or canvases.empty:
        return pd.DataFrame()
    ds=direct_solar if direct_solar is not None else pd.DataFrame()
    cb=cloud_base_illumination if cloud_base_illumination is not None else pd.DataFrame()
    sp=spectral_paths if spectral_paths is not None else pd.DataFrame()
    rows=[]
    for _,c in canvases.iterrows():
        cid=str(c.get("canvas_id")); a=float(c.get("solar_altitude_deg",float("nan")))
        d=ds[ds.get("canvas_id",pd.Series(dtype=str)).astype(str).eq(cid)] if not ds.empty and "canvas_id" in ds else pd.DataFrame()
        fvals=pd.to_numeric(d.get("direct_solar_fraction",pd.Series(dtype=float)),errors="coerce").dropna()
        fs=float(fvals.max()) if not fvals.empty else float("nan")
        geometry_resolved=math.isfinite(fs)
        receives_any_direct_solar=bool(geometry_resolved and fs>0.0)
        distance_km=float(c.get("distance_km", float("nan")))
        cloud_base_km=float(c.get("cloud_base_altitude_km", float("nan")))
        pen=finite_solar_disk_penumbra_heights_km(distance_km, a) if math.isfinite(distance_km) else {"h_any_sun_km":float("nan"),"h_solar_center_km":float("nan"),"h_full_solar_disk_km":float("nan"),"penumbra_vertical_span_km":float("nan"),"solar_angular_radius_deg":float("nan")}
        above_center=bool(math.isfinite(cloud_base_km) and math.isfinite(pen["h_solar_center_km"]) and cloud_base_km>=pen["h_solar_center_km"]-1e-9)
        above_full=bool(math.isfinite(cloud_base_km) and math.isfinite(pen["h_full_solar_disk_km"]) and cloud_base_km>=pen["h_full_solar_disk_km"]-1e-9)

        spp=sp[sp.get("canvas_id",pd.Series(dtype=str)).astype(str).eq(cid)] if not sp.empty and "canvas_id" in sp else pd.DataFrame()
        red=spp[pd.to_numeric(spp.get("wavelength_nm",pd.Series(dtype=float)),errors="coerce").isin(RED_BANDS)] if not spp.empty else pd.DataFrame()
        red_t=pd.to_numeric(red.get("transmission",pd.Series(dtype=float)),errors="coerce").dropna()
        path_resolved=bool(len(red)>=len(RED_BANDS) and len(red_t)>=len(RED_BANDS))

        cbb=cb[cb.get("canvas_id",pd.Series(dtype=str)).astype(str).eq(cid)] if not cb.empty and "canvas_id" in cb else pd.DataFrame()
        red_vals=[]
        if not cbb.empty:
            rr=cbb.iloc[0]
            for wl in RED_BANDS:
                v=pd.to_numeric(pd.Series([rr.get(f"relative_base_illumination_{int(wl)}nm")]),errors="coerce").iloc[0]
                if pd.notna(v): red_vals.append(float(v))
        red_base_resolved=bool(len(red_vals)==len(RED_BANDS))
        red_reaches=bool(red_base_resolved and any(v>0.0 for v in red_vals))

        if not geometry_resolved:
            state="EARTH_SHADOW_GEOMETRY_UNRESOLVED"
        elif not receives_any_direct_solar:
            state="FULL_UMBRA_EARTH_OCCULTED"
        elif not path_resolved:
            state="SUN_TO_CLOUDBASE_PATH_OPTICS_UNRESOLVED"
        elif not red_base_resolved:
            state="RED_CLOUDBASE_ILLUMINATION_UNRESOLVED"
        elif not red_reaches:
            state="RED_LIGHT_NOT_REACHING_CLOUDBASE"
        else:
            state="CLOUD_BASE_RED_ILLUMINATION_RESOLVED"
        rows.append({
            "solar_altitude_deg":a,"canvas_id":cid,"cloud_layer_id":c.get("cloud_layer_id"),
            "cloud_exists":True,"direct_solar_fraction":fs,"earth_shadow_geometry_resolved":geometry_resolved,
            "h_any_sun_km":pen["h_any_sun_km"],"h_solar_center_km":pen["h_solar_center_km"],"h_full_solar_disk_km":pen["h_full_solar_disk_km"],
            "penumbra_vertical_span_km":pen["penumbra_vertical_span_km"],
            "cloudbase_above_center_shadow_height":above_center,"cloudbase_above_full_disk_height":above_full,
            "cloud_receives_direct_solar_geometry":receives_any_direct_solar,"sun_to_cloudbase_red_path_resolved":path_resolved,
            "red_cloudbase_illumination_resolved":red_base_resolved,"red_light_reaches_cloudbase":red_reaches,
            "relative_base_illumination_650nm":red_vals[0] if len(red_vals)>0 else float("nan"),
            "relative_base_illumination_700nm":red_vals[1] if len(red_vals)>1 else float("nan"),
            "relative_base_illumination_750nm":red_vals[2] if len(red_vals)>2 else float("nan"),
            "formation_gate_state":state,
            "note":"FORMATION_ONLY_SUN_TO_CLOUDBASE;VIEWING_PATH_EXCLUDED;FINITE_SOLAR_DISK_PENUMBRA;H_CENTER_DIAGNOSTIC_ONLY;FORMATION_USES_F_SUN_AND_SPECTRAL_PATH",
        })
    return pd.DataFrame(rows)
