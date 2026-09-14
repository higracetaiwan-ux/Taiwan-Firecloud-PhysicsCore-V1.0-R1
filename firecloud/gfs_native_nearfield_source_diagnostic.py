from __future__ import annotations

"""Diagnostic-only attribution of near-field NOAA GFS native cloud source levels.

R5.7.41.3.4.10.9.6
--------------------
This module inspects the already-decoded pressure-level fields that feed the
native cloud-volume builder. It exists to distinguish three very different
situations without changing any PhysicsCore decision:

* provider/source pressure-level condensate is exactly zero;
* source condensate is positive but below the native geometric-envelope threshold;
* source condensate is present at/above the threshold and may be lost later.

Hard contract: diagnostic only; no RH/CF -> condensate synthesis, no tau/COT
synthesis, no Formation/Viewing/Glow promotion, and no provider request.
"""

import numpy as np
import pandas as pd

from .native_cloud import NATIVE_CONDENSATE_THRESHOLD_KGKG
from .providers.gfs_native import DEFAULT_PRESSURE_LEVELS_HPA


POINT_COLUMNS = [
    "analysis_time", "solar_altitude_deg", "point_id", "direction_offset_deg",
    "distance_km", "distance_band", "pressure_hpa", "altitude_agl_km",
    "cloud_liquid_water_kgkg", "cloud_ice_water_kgkg", "total_cloud_condensate_kgkg",
    "cloud_fraction", "relative_humidity_pct", "temperature_k",
    "source_condensate_state", "source_cloud_fraction_state",
    "native_envelope_threshold_kgkg", "gfs_run_utc", "gfs_forecast_hour",
    "gfs_target_time_utc", "gfs_valid_time_utc", "gfs_valid_time_offset_seconds",
    "gfs_forecast_cadence_policy", "gfs_file", "route_sampling_method",
    "diagnostic_role", "tau_synthesis_allowed", "formation_promotion_allowed",
    "viewing_target_required",
]

SUMMARY_COLUMNS = [
    "analysis_time", "solar_altitude_deg", "direction_offset_deg", "distance_band",
    "route_point_count", "pressure_level_row_count", "low_layer_level_row_count",
    "condensate_nonmissing_count", "condensate_exact_zero_count",
    "condensate_positive_below_threshold_count", "condensate_at_or_above_threshold_count",
    "max_total_cloud_condensate_kgkg", "max_cloud_fraction", "max_relative_humidity_pct",
    "low_layer_max_total_cloud_condensate_kgkg", "low_layer_max_cloud_fraction",
    "source_attribution_state", "gfs_run_utc", "gfs_forecast_hour",
    "gfs_valid_time_utc", "gfs_valid_time_offset_seconds", "diagnostic_role",
    "tau_synthesis_allowed", "formation_promotion_allowed",
]


def _num(v):
    return pd.to_numeric(pd.Series([v]), errors="coerce").iloc[0]


def _distance_band(distance_km: float) -> str | None:
    if not np.isfinite(distance_km):
        return None
    if 0.0 <= distance_km <= 10.0:
        return "NEAR_OBSERVER_0_10KM"
    if 10.0 < distance_km <= 40.0:
        return "PRIMARY_GT10_40KM"
    if 40.0 < distance_km <= 100.0:
        return "EXTENDED_GT40_100KM"
    return None


def _condensate_state(ql, qi) -> tuple[float, str]:
    if pd.isna(ql) or pd.isna(qi):
        return np.nan, "SOURCE_CONDENSATE_MISSING"
    qt = max(0.0, float(ql)) + max(0.0, float(qi))
    if qt == 0.0:
        return 0.0, "SOURCE_CONDENSATE_EXACT_ZERO"
    if qt < NATIVE_CONDENSATE_THRESHOLD_KGKG:
        return qt, "SOURCE_CONDENSATE_POSITIVE_BELOW_ENVELOPE_THRESHOLD"
    return qt, "SOURCE_CONDENSATE_AT_OR_ABOVE_ENVELOPE_THRESHOLD"


def _cf_state(cf) -> str:
    if pd.isna(cf):
        return "SOURCE_CLOUD_FRACTION_MISSING"
    return "SOURCE_CLOUD_FRACTION_EXACT_ZERO" if float(cf) == 0.0 else "SOURCE_CLOUD_FRACTION_POSITIVE"


def build_gfs_native_nearfield_source_levels(
    snapshot: pd.DataFrame,
    *,
    analysis_time=None,
    solar_altitude_deg: float | None = None,
    provider_metadata: dict | None = None,
    max_distance_km: float = 100.0,
    pressure_levels_hpa=DEFAULT_PRESSURE_LEVELS_HPA,
) -> pd.DataFrame:
    """Export decoded pressure-level source evidence before voxel interpolation."""
    if snapshot is None or snapshot.empty:
        return pd.DataFrame(columns=POINT_COLUMNS)
    meta = dict(provider_metadata or {})
    rows: list[dict] = []
    for rec in snapshot.to_dict("records"):
        d = _num(rec.get("distance_km")); off = _num(rec.get("direction_offset_deg"))
        if not np.isfinite(d) or not np.isfinite(off) or d < 0.0 or d > float(max_distance_km):
            continue
        elev = _num(rec.get("model_surface_elevation_m"))
        elev = 0.0 if not np.isfinite(elev) else float(elev)
        for p in pressure_levels_hpa:
            gh = _num(rec.get(f"geopotential_height_{int(p)}hPa"))
            alt = np.nan if not np.isfinite(gh) else (float(gh) - elev) / 1000.0
            ql = _num(rec.get(f"cloud_liquid_water_kgkg_{int(p)}hPa", rec.get(f"cloud_liquid_water_{int(p)}hPa")))
            qi = _num(rec.get(f"cloud_ice_water_kgkg_{int(p)}hPa", rec.get(f"cloud_ice_water_{int(p)}hPa")))
            cf = _num(rec.get(f"cloud_fraction_{int(p)}hPa"))
            rh = _num(rec.get(f"relative_humidity_{int(p)}hPa"))
            tk = _num(rec.get(f"temperature_{int(p)}hPa"))
            qt, qstate = _condensate_state(ql, qi)
            rows.append({
                "analysis_time": analysis_time,
                "solar_altitude_deg": solar_altitude_deg,
                "point_id": str(rec.get("point_id", "")),
                "direction_offset_deg": float(off),
                "distance_km": float(d),
                "distance_band": _distance_band(float(d)),
                "pressure_hpa": float(p),
                "altitude_agl_km": alt,
                "cloud_liquid_water_kgkg": ql,
                "cloud_ice_water_kgkg": qi,
                "total_cloud_condensate_kgkg": qt,
                "cloud_fraction": cf,
                "relative_humidity_pct": rh,
                "temperature_k": tk,
                "source_condensate_state": qstate,
                "source_cloud_fraction_state": _cf_state(cf),
                "native_envelope_threshold_kgkg": float(NATIVE_CONDENSATE_THRESHOLD_KGKG),
                "gfs_run_utc": meta.get("gfs_run_utc"),
                "gfs_forecast_hour": meta.get("gfs_forecast_hour"),
                "gfs_target_time_utc": meta.get("gfs_target_time_utc"),
                "gfs_valid_time_utc": meta.get("gfs_valid_time_utc"),
                "gfs_valid_time_offset_seconds": meta.get("gfs_valid_time_offset_seconds"),
                "gfs_forecast_cadence_policy": meta.get("gfs_forecast_cadence_policy"),
                "gfs_file": meta.get("gfs_file"),
                "route_sampling_method": "NEAREST_GFS_0P25_GRIDPOINT_DECODED_PRESSURE_LEVEL",
                "diagnostic_role": "GFS_NATIVE_NEARFIELD_SOURCE_ATTRIBUTION_ONLY_NO_PHYSICS_PROMOTION",
                "tau_synthesis_allowed": False,
                "formation_promotion_allowed": False,
                "viewing_target_required": False,
            })
    out = pd.DataFrame(rows)
    for c in POINT_COLUMNS:
        if c not in out.columns:
            out[c] = np.nan
    return out.loc[:, POINT_COLUMNS].reset_index(drop=True)


def summarize_gfs_native_nearfield_source_levels(points: pd.DataFrame) -> pd.DataFrame:
    if points is None or points.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    p = points[points["distance_band"].notna()].copy()
    rows: list[dict] = []
    keys = ["analysis_time", "solar_altitude_deg", "direction_offset_deg", "distance_band"]
    for vals, g in p.groupby(keys, dropna=False, sort=True):
        qt = pd.to_numeric(g["total_cloud_condensate_kgkg"], errors="coerce")
        cf = pd.to_numeric(g["cloud_fraction"], errors="coerce")
        rh = pd.to_numeric(g["relative_humidity_pct"], errors="coerce")
        alt = pd.to_numeric(g["altitude_agl_km"], errors="coerce")
        states = g["source_condensate_state"].astype(str)
        max_qt = float(qt.max()) if qt.notna().any() else np.nan
        low_mask = alt.between(0.0, 2.0, inclusive="both")
        low_states = states[low_mask]
        low_qt = qt[low_mask]
        low_cf = cf[low_mask]
        if low_states.eq("SOURCE_CONDENSATE_AT_OR_ABOVE_ENVELOPE_THRESHOLD").any():
            status = "LOW_LAYER_SOURCE_CONDENSATE_PRESENT_AT_OR_ABOVE_THRESHOLD"
        elif low_states.eq("SOURCE_CONDENSATE_POSITIVE_BELOW_ENVELOPE_THRESHOLD").any():
            status = "LOW_LAYER_SOURCE_CONDENSATE_ONLY_BELOW_ENVELOPE_THRESHOLD"
        elif low_qt.notna().any() and low_qt.fillna(0.0).eq(0.0).all():
            status = "LOW_LAYER_SOURCE_NATIVE_PRESSURE_LEVELS_EXACT_ZERO"
        elif not low_mask.any():
            status = "LOW_LAYER_SOURCE_VERTICAL_SUPPORT_UNAVAILABLE"
        else:
            status = "LOW_LAYER_SOURCE_NATIVE_CONDENSATE_MISSING_OR_MIXED_AVAILABILITY"
        row = dict(zip(keys, vals if isinstance(vals, tuple) else (vals,)))
        first = g.iloc[0]
        row.update({
            "route_point_count": int(g["point_id"].astype(str).nunique()),
            "pressure_level_row_count": int(len(g)),
            "low_layer_level_row_count": int((alt.between(0.0, 2.0, inclusive="both")).sum()),
            "condensate_nonmissing_count": int(qt.notna().sum()),
            "condensate_exact_zero_count": int(states.eq("SOURCE_CONDENSATE_EXACT_ZERO").sum()),
            "condensate_positive_below_threshold_count": int(states.eq("SOURCE_CONDENSATE_POSITIVE_BELOW_ENVELOPE_THRESHOLD").sum()),
            "condensate_at_or_above_threshold_count": int(states.eq("SOURCE_CONDENSATE_AT_OR_ABOVE_ENVELOPE_THRESHOLD").sum()),
            "max_total_cloud_condensate_kgkg": max_qt,
            "max_cloud_fraction": float(cf.max()) if cf.notna().any() else np.nan,
            "max_relative_humidity_pct": float(rh.max()) if rh.notna().any() else np.nan,
            "low_layer_max_total_cloud_condensate_kgkg": float(low_qt.max()) if low_qt.notna().any() else np.nan,
            "low_layer_max_cloud_fraction": float(low_cf.max()) if low_cf.notna().any() else np.nan,
            "source_attribution_state": status,
            "gfs_run_utc": first.get("gfs_run_utc"),
            "gfs_forecast_hour": first.get("gfs_forecast_hour"),
            "gfs_valid_time_utc": first.get("gfs_valid_time_utc"),
            "gfs_valid_time_offset_seconds": first.get("gfs_valid_time_offset_seconds"),
            "diagnostic_role": "GFS_NATIVE_NEARFIELD_SOURCE_ATTRIBUTION_ONLY_NO_PHYSICS_PROMOTION",
            "tau_synthesis_allowed": False,
            "formation_promotion_allowed": False,
        })
        rows.append(row)
    out = pd.DataFrame(rows)
    for c in SUMMARY_COLUMNS:
        if c not in out.columns:
            out[c] = np.nan
    return out.loc[:, SUMMARY_COLUMNS].reset_index(drop=True)
