"""PhysicsCore V1.0-R4.7 precipitation-path contract.

Surface precipitation rate is not converted to optical depth.  A path may only
become optically resolved when an explicit 3-D/path hydrometeor optical product
is supplied.  This keeps rain as a geometry/path problem rather than a score.
"""
from __future__ import annotations
import pandas as pd
import numpy as np

from .contracts import SIX_BAND_WAVELENGTHS_NM


def _first_numeric(row, names):
    for n in names:
        if n in row.index:
            try:
                v=float(row[n])
                if np.isfinite(v): return v
            except Exception:
                pass
    return None


def build_precipitation_path_evidence(canvases, route_snapshot: pd.DataFrame | None = None, *, valid_time=None, path_optics: pd.DataFrame | None = None) -> pd.DataFrame:
    rows=[]
    precip_present=False; max_rate=None; surface_field_available=False
    if route_snapshot is not None and not route_snapshot.empty:
        for col in ("precipitation","precipitation_mm","rain","rain_mm"):
            if col in route_snapshot.columns:
                vals=pd.to_numeric(route_snapshot[col],errors="coerce")
                if vals.notna().any():
                    surface_field_available=True; max_rate=float(vals.max()); precip_present=max_rate>0.0; break
    explicit = path_optics if path_optics is not None else pd.DataFrame()
    for c in canvases:
        rec={
            "time":valid_time,"canvas_id":c.canvas_id,
            "surface_precipitation_field_available":bool(surface_field_available),
            "surface_precipitation_evidence":bool(precip_present),
            "max_surface_precipitation_rate":max_rate,
            "geometry_resolved_3d":False,"optical_evidence":"MISSING","role":"UNKNOWN",
            "status":"PRECIPITATION_VOLUME_UNRESOLVED" if precip_present else "PRECIPITATION_GEOMETRY_MISSING",
            "reason":"SURFACE_RAIN_RATE_DOES_NOT_DEFINE_3D_PATH_OPTICS" if precip_present else "NO_3D_PRECIPITATION_VOLUME",
        }
        q=pd.DataFrame()
        if not explicit.empty and "canvas_id" in explicit.columns:
            q=explicit[explicit["canvas_id"].astype(str)==str(c.canvas_id)]
        if not q.empty:
            prow=q.iloc[0]
            rec["geometry_resolved_3d"]=bool(prow.get("geometry_resolved_3d",True))
            known=0
            for wl in SIX_BAND_WAVELENGTHS_NM:
                v=_first_numeric(prow,[f"tau_precip_{int(wl)}nm",f"precipitation_optical_depth_{int(wl)}nm"])
                rec[f"tau_precip_{int(wl)}nm"]=v
                known += int(v is not None)
            if known==len(SIX_BAND_WAVELENGTHS_NM):
                rec.update({"status":"PRECIPITATION_OPTICS_RESOLVED","optical_evidence":"FULL","role":str(prow.get("role","ILLUMINATION_BLOCKER")),"reason":"EXPLICIT_PATH_RESOLVED_HYDROMETEOR_OPTICS"})
            elif known:
                rec.update({"status":"PRECIPITATION_OPTICS_PARTIAL","optical_evidence":"PARTIAL_OPTICS","role":str(prow.get("role","ILLUMINATION_BLOCKER")),"reason":"PARTIAL_PATH_RESOLVED_HYDROMETEOR_OPTICS"})
        rows.append(rec)
    return pd.DataFrame(rows)
