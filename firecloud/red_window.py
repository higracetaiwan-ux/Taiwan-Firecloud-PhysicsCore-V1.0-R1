"""PhysicsCore V1.0-R5.4 spectral red-window evolution diagnostics.

Frozen semantics:
- Penumbra/Earth-shadow geometry remains an independent track (F_sun).
- Spectral RT remains an independent track (T_lambda / resolved CloudBase radiance).
- This module only joins those already-computed tracks for diagnostics; it does
  not use geometry to synthesize radiance and it does not define a single
  Physics Score or a calibrated firecloud threshold.
- Brightness, Redness and Effective Illuminated Area keep separate peak windows.
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd


def _role(distance_km: float) -> str:
    try:
        d = float(distance_km)
    except Exception:
        return "UNKNOWN_DISTANCE_ROLE"
    if not math.isfinite(d) or d < 0:
        return "UNKNOWN_DISTANCE_ROLE"
    if d <= 40.0:
        return "PRIMARY_CANVAS_0_40KM"
    if d <= 100.0:
        return "SECONDARY_CANVAS_40_100KM"
    return "HORIZON_RESIDUAL_100PLUS_DIAGNOSTIC_ONLY"


def _finite_series(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan)


def build_canvas_spectral_evolution(canvas_radiance: pd.DataFrame, canvas_penumbra: pd.DataFrame) -> pd.DataFrame:
    """Build per-Canvas angle evolution while keeping geometry and RT separate."""
    if canvas_radiance is None or canvas_radiance.empty:
        return pd.DataFrame()
    r = canvas_radiance.copy()
    keys = [k for k in ("time", "solar_altitude_deg", "canvas_id", "cloud_layer_id") if k in r.columns]
    if canvas_penumbra is not None and not canvas_penumbra.empty:
        pcols = [c for c in [
            "time", "solar_altitude_deg", "canvas_id", "cloud_layer_id", "direct_solar_fraction",
            "penumbra_geometry_state", "red_base_illumination_resolved", "red_light_reaches_cloudbase",
            "red_650nm_transmission", "red_700nm_transmission", "red_750nm_transmission",
        ] if c in canvas_penumbra.columns]
        p = canvas_penumbra[pcols].copy()
        mkeys = [k for k in keys if k in p.columns]
        if mkeys:
            r = r.merge(p, how="left", on=mkeys, suffixes=("", "_penumbra"))

    r["distance_km"] = _finite_series(r.get("distance_km", pd.Series(np.nan, index=r.index)))
    r["canvas_distance_role"] = r["distance_km"].map(_role)
    r["direct_solar_fraction"] = _finite_series(r.get("direct_solar_fraction", pd.Series(np.nan, index=r.index)))
    r["brightness"] = _finite_series(r.get("brightness", pd.Series(np.nan, index=r.index)))
    r["redness"] = _finite_series(r.get("redness", pd.Series(np.nan, index=r.index)))
    r["effective_illuminated_area_fraction"] = _finite_series(r.get("effective_illuminated_area_fraction", pd.Series(np.nan, index=r.index)))
    r["warm_red_fraction_650_750"] = _finite_series(r.get("warm_red_fraction_650_750", pd.Series(np.nan, index=r.index)))
    r["deep_red_tail_fraction_750"] = _finite_series(r.get("deep_red_tail_fraction_750", pd.Series(np.nan, index=r.index)))

    status = r.get("response_status", pd.Series("", index=r.index)).astype(str)
    r["spectral_rt_response_resolved"] = status.eq("READY_TIER1_UNCALIBRATED")
    r["spectral_response_state"] = np.where(
        r["spectral_rt_response_resolved"], "RESOLVED_UNCALIBRATED_SPECTRAL_RESPONSE",
        np.where(r["direct_solar_fraction"].fillna(0.0) <= 0.0, "GEOMETRIC_EARTH_SHADOW",
                 "SPECTRAL_RT_OR_TARGET_OPTICS_UNRESOLVED")
    )

    # Independent peaks only. No combined score and no best-angle collapse.
    group_cols = [c for c in ["canvas_id", "cloud_layer_id", "distance_km"] if c in r.columns]
    r["brightness_peak_for_canvas"] = False
    r["redness_peak_for_canvas"] = False
    r["area_peak_for_canvas"] = False
    r["warm_red_fraction_peak_for_canvas"] = False
    if group_cols:
        for _, idx in r.groupby(group_cols, dropna=False).groups.items():
            ii = list(idx)
            sub = r.loc[ii]
            resolved = sub["spectral_rt_response_resolved"].fillna(False)
            for col, outcol in [
                ("brightness", "brightness_peak_for_canvas"),
                ("redness", "redness_peak_for_canvas"),
                ("effective_illuminated_area_fraction", "area_peak_for_canvas"),
                ("warm_red_fraction_650_750", "warm_red_fraction_peak_for_canvas"),
            ]:
                vals = pd.to_numeric(sub.loc[resolved, col], errors="coerce").dropna()
                if not vals.empty:
                    vmax = float(vals.max())
                    hit = sub.index[resolved & pd.to_numeric(sub[col], errors="coerce").eq(vmax)]
                    r.loc[hit, outcol] = True

    r["red_window_note"] = (
        "GEOMETRY_AND_SPECTRAL_RT_SEPARATE;NO_F_SUN_TO_RADIANCE_SYNTHESIS;"
        "BRIGHTNESS_REDNESS_AREA_PEAKS_SEPARATE;NO_SINGLE_BEST_ANGLE;UNCALIBRATED"
    )
    return r


def build_canvas_peak_windows(evolution: pd.DataFrame) -> pd.DataFrame:
    """Summarize independent B/R/A peak angles by photography distance role.

    A peak is reported only when that dimension is spectrally/physically resolved.
    Missing RT remains Missing.
    """
    if evolution is None or evolution.empty:
        return pd.DataFrame()
    rows = []
    for role, g in evolution.groupby("canvas_distance_role", dropna=False, sort=False):
        g = g.copy()
        angles = sorted(pd.to_numeric(g.get("solar_altitude_deg"), errors="coerce").dropna().unique(), reverse=True)
        for metric, flag in [
            ("brightness", "brightness_peak_for_canvas"),
            ("redness", "redness_peak_for_canvas"),
            ("effective_illuminated_area_fraction", "area_peak_for_canvas"),
            ("warm_red_fraction_650_750", "warm_red_fraction_peak_for_canvas"),
        ]:
            resolved = g[g["spectral_rt_response_resolved"].fillna(False) & pd.to_numeric(g[metric], errors="coerce").notna()]
            if resolved.empty:
                rows.append({
                    "canvas_distance_role": role,
                    "dimension": metric,
                    "resolved_canvas_angle_rows": 0,
                    "peak_angle_min_deg": np.nan,
                    "peak_angle_max_deg": np.nan,
                    "peak_angle_values_deg": "",
                    "window_state": "MISSING_SPECTRAL_RT",
                    "evaluated_solar_altitudes_deg": ";".join(f"{a:g}" for a in angles),
                    "note": "INDEPENDENT_DIMENSION_PEAK;NO_SINGLE_FORMATION_SCORE;NO_GEOMETRY_PROMOTION",
                })
                continue
            peaks = g[g[flag].fillna(False)]
            pa = sorted(pd.to_numeric(peaks.get("solar_altitude_deg"), errors="coerce").dropna().unique())
            rows.append({
                "canvas_distance_role": role,
                "dimension": metric,
                "resolved_canvas_angle_rows": int(len(resolved)),
                "peak_angle_min_deg": float(min(pa)) if pa else np.nan,
                "peak_angle_max_deg": float(max(pa)) if pa else np.nan,
                "peak_angle_values_deg": ";".join(f"{a:g}" for a in pa),
                "window_state": "RESOLVED_UNCALIBRATED" if pa else "RESOLVED_NO_PEAK_FOUND",
                "evaluated_solar_altitudes_deg": ";".join(f"{a:g}" for a in angles),
                "note": "INDEPENDENT_DIMENSION_PEAK;NO_SINGLE_FORMATION_SCORE;NO_GEOMETRY_PROMOTION",
            })
    return pd.DataFrame(rows)
