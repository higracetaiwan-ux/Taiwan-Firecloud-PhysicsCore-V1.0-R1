"""R4.4 Cloud Optical Validation audit helpers.

Validation reports evidence availability and whether the native-condensate
slant-RT bridge was exercised.  It does not manufacture missing condensate,
cloud optical depth, horizontal cloud width, or calibration thresholds.
"""
from __future__ import annotations

import pandas as pd


def build_cloud_optical_validation_table(
    *,
    cloud_layers: pd.DataFrame,
    canvases: pd.DataFrame,
    horizontal_support: pd.DataFrame,
    intersections: pd.DataFrame,
) -> pd.DataFrame:
    angles = set()
    for df in (cloud_layers, canvases, horizontal_support, intersections):
        if df is not None and not df.empty and "solar_altitude_deg" in df.columns:
            angles.update(pd.to_numeric(df["solar_altitude_deg"], errors="coerce").dropna().astype(float).tolist())
    rows = []
    for angle in sorted(angles, reverse=True):
        def sub(df):
            if df is None or df.empty or "solar_altitude_deg" not in df.columns:
                return pd.DataFrame()
            return df[pd.to_numeric(df["solar_altitude_deg"], errors="coerce").eq(float(angle))].copy()
        cl = sub(cloud_layers); ca = sub(canvases); hs = sub(horizontal_support); ix = sub(intersections)
        optical = cl[~cl.get("optical_evidence", pd.Series(index=cl.index, dtype=str)).astype(str).isin(["GEOMETRY_ONLY", "MISSING", "UNKNOWN", ""])] if not cl.empty else pd.DataFrame()
        cot = pd.to_numeric(cl.get("cot", pd.Series(index=cl.index, dtype=float)), errors="coerce") if not cl.empty else pd.Series(dtype=float)
        condensate_positive = cl[cot.notna() & (cot > 0)] if not cl.empty else pd.DataFrame()
        resolved_support = hs[hs.get("horizontal_support_resolved", pd.Series(index=hs.index, dtype=bool)).astype(str).str.lower().isin(["true", "1"])] if not hs.empty else pd.DataFrame()
        slant_status = ix.get("slant_optics_status", pd.Series(index=ix.index, dtype=str)).astype(str) if not ix.empty else pd.Series(dtype=str)
        resolved_slant = ix[slant_status.eq("RESOLVED_NATIVE_CONDENSATE_SLANT_RT")] if not ix.empty else pd.DataFrame()
        target_ready = 0
        if not ca.empty and not cl.empty and "cloud_layer_id" in ca.columns and "layer_id" in cl.columns:
            ready_ids = set(optical.get("layer_id", pd.Series(dtype=str)).astype(str))
            target_ready = int(ca["cloud_layer_id"].astype(str).isin(ready_ids).sum())
        if len(condensate_positive) > 0 and len(resolved_slant) > 0:
            state = "CONDENSATE_POSITIVE_SLANT_RT_VALIDATED"
        elif len(condensate_positive) > 0:
            state = "CONDENSATE_POSITIVE_HORIZONTAL_SUPPORT_NOT_RESOLVED"
        else:
            state = "NO_NATIVE_CONDENSATE_OPTICAL_EVIDENCE"
        rows.append({
            "solar_altitude_deg": float(angle),
            "cloud_layer_count": int(len(cl)),
            "native_optical_layer_count": int(len(optical)),
            "condensate_positive_layer_count": int(len(condensate_positive)),
            "target_canvas_count": int(len(ca)),
            "target_canvas_with_native_optics_count": int(target_ready),
            "horizontal_support_candidate_count": int(len(hs)),
            "horizontal_support_resolved_count": int(len(resolved_support)),
            "resolved_native_condensate_slant_intersection_count": int(len(resolved_slant)),
            "validation_state": state,
            "validation_note": "NO_RH_OR_CLOUD_FRACTION_COT_SYNTHESIS;SAMPLING_STEP_IS_NOT_CLOUD_WIDTH",
        })
    return pd.DataFrame(rows)
