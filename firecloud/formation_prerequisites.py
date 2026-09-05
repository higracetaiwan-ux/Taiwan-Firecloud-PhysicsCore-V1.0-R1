"""R4.6 Formation prerequisite diagnostics.

This module is diagnostic only. It never fills missing spectroscopy, precipitation
optics, or target cloud COT.
"""
from __future__ import annotations
import pandas as pd

def build_formation_prerequisite_table(*, spectral_paths: pd.DataFrame, canvas_radiance: pd.DataFrame, formation: pd.DataFrame) -> pd.DataFrame:
    angles=set()
    for df in (spectral_paths, canvas_radiance, formation):
        if df is not None and not df.empty and "solar_altitude_deg" in df.columns:
            angles.update(pd.to_numeric(df["solar_altitude_deg"], errors="coerce").dropna().astype(float).tolist())
    rows=[]
    for a in sorted(angles, reverse=True):
        sp=spectral_paths[pd.to_numeric(spectral_paths.get("solar_altitude_deg"), errors="coerce").eq(a)].copy() if spectral_paths is not None and not spectral_paths.empty else pd.DataFrame()
        cr=canvas_radiance[pd.to_numeric(canvas_radiance.get("solar_altitude_deg"), errors="coerce").eq(a)].copy() if canvas_radiance is not None and not canvas_radiance.empty else pd.DataFrame()
        def wl_count(wl, col):
            q=sp[pd.to_numeric(sp.get("wavelength_nm"), errors="coerce").eq(float(wl))] if not sp.empty else pd.DataFrame()
            return int(pd.to_numeric(q.get(col, pd.Series(dtype=float)), errors="coerce").notna().sum())
        total_canvas=int(cr.get("canvas_id", pd.Series(dtype=str)).astype(str).nunique()) if not cr.empty else 0
        target_ready=int(cr.get("target_optics_ready", pd.Series(dtype=bool)).astype(bool).sum()) if not cr.empty else 0
        target_bounded=int(cr.get("target_optics_bounded", pd.Series(dtype=bool)).astype(bool).sum()) if not cr.empty else 0
        full_paths=int(sp.get("evidence_state", pd.Series(dtype=str)).astype(str).eq("FULL").sum()) if not sp.empty else 0
        precip_resolved=int(pd.to_numeric(sp.get("tau_precip", pd.Series(dtype=float)), errors="coerce").notna().sum()) if not sp.empty else 0
        gas550=wl_count(550,"tau_gas")
        rows.append({
            "solar_altitude_deg":a,
            "canvas_count":total_canvas,
            "target_optics_ready_canvas_count":target_ready,
            "target_optics_bounded_canvas_count":target_bounded,
            "target_optics_ready": bool(total_canvas>0 and target_ready>0),
            "gas_550nm_resolved_path_count":gas550,
            "gas_550nm_ready":bool(gas550>0),
            "precipitation_optics_resolved_path_count":precip_resolved,
            "precipitation_path_ready":bool(precip_resolved>0),
            "full_six_band_optical_path_row_count":full_paths,
            "formation_prerequisite_state": (
                "READY_FOR_SIX_BAND_FORMATION" if target_ready>0 and gas550>0 and precip_resolved>0 and full_paths>0
                else "FORMATION_PREREQUISITES_INCOMPLETE"
            ),
            "missing_prerequisites": ";".join([x for x,ok in [
                ("TARGET_CANVAS_OPTICS",target_ready>0),("550NM_GAS_SPECTROSCOPY",gas550>0),("PRECIPITATION_PATH_OPTICS",precip_resolved>0),("FULL_SIX_BAND_PATH",full_paths>0)] if not ok]),
            "note":"NO_INTERPOLATED_550NM;NO_SURFACE_RAIN_TO_TAU;NO_CLOUD_FRACTION_TO_COT;BOUNDED_TARGET_COT_NOT_PROMOTED_TO_EXACT_FORMATION",
        })
    return pd.DataFrame(rows)
