"""PhysicsCore V1.0-R5.1 causal Formation gate diagnostics.

Formation is a Sun→CloudBase problem.  This table does not use observer-path
visibility and does not collapse Formation into a score.
"""
from __future__ import annotations
import math
import pandas as pd

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
        above_shadow=bool(geometry_resolved and fs>0.0)

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
        elif not above_shadow:
            state="EARTH_SHADOW_BLOCKED"
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
            "cloud_receives_direct_solar_geometry":above_shadow,"sun_to_cloudbase_red_path_resolved":path_resolved,
            "red_cloudbase_illumination_resolved":red_base_resolved,"red_light_reaches_cloudbase":red_reaches,
            "relative_base_illumination_650nm":red_vals[0] if len(red_vals)>0 else float("nan"),
            "relative_base_illumination_700nm":red_vals[1] if len(red_vals)>1 else float("nan"),
            "relative_base_illumination_750nm":red_vals[2] if len(red_vals)>2 else float("nan"),
            "formation_gate_state":state,
            "note":"FORMATION_ONLY_SUN_TO_CLOUDBASE;VIEWING_PATH_EXCLUDED;F_SUN_FINITE_SOLAR_DISK_NOT_SHADOW_HEIGHT_ONLY",
        })
    return pd.DataFrame(rows)
