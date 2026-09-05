"""PhysicsCore V1.0 R3.1 precipitation-path evidence bridge.

This module deliberately does not convert surface precipitation rate into cloud
optical depth.  It exposes whether a 3-D precipitation/hydrometeor path is
resolved; unresolved geometry stays Unknown and propagates only downstream.
"""
from __future__ import annotations
import pandas as pd

def build_precipitation_path_evidence(canvases, route_snapshot: pd.DataFrame | None = None, *, valid_time=None) -> pd.DataFrame:
    rows=[]
    # Surface precipitation is observation/forecast evidence of hydrometeors, but
    # without a vertical volume it cannot establish Sun->CloudBase intersection.
    precip_present=False
    max_rate=None
    if route_snapshot is not None and not route_snapshot.empty:
        for col in ("precipitation", "precipitation_mm", "rain", "rain_mm"):
            if col in route_snapshot.columns:
                vals=pd.to_numeric(route_snapshot[col], errors="coerce")
                if vals.notna().any():
                    max_rate=float(vals.max()); precip_present=max_rate>0.0; break
    for c in canvases:
        rows.append({
            "time": valid_time, "canvas_id": c.canvas_id,
            "status": "PRECIPITATION_VOLUME_UNRESOLVED" if precip_present else "PRECIPITATION_GEOMETRY_MISSING",
            "surface_precipitation_evidence": bool(precip_present),
            "max_surface_precipitation_rate": max_rate,
            "geometry_resolved_3d": False, "optical_evidence": "MISSING",
            "role": "UNKNOWN",
            "reason": "SURFACE_RAIN_RATE_DOES_NOT_DEFINE_3D_PATH_OPTICS" if precip_present else "NO_3D_PRECIPITATION_VOLUME",
        })
    return pd.DataFrame(rows)
