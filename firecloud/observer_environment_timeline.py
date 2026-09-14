from __future__ import annotations

"""Observer-environment timeline diagnostics.

R5.7.41.3.4.10.9.4
--------------------
Diagnostic-only time alignment for observer-environment evidence.  This module
extends the R5.7.41.3.4.10.9.3 near-field snapshot into a regular event-relative
time series so field imagery can be compared against the same already-fetched
forecast route data.

Hard contract:
* diagnostic only; never participates in Formation / Viewing / Glow decisions;
* does not extend the PhysicsCore solar-angle calculation below -6 deg;
* coarse cloud cover is never converted into tau/COT;
* native 3D cloud columns are never temporally interpolated;
* native evidence may only be attached as a nearby existing snapshot with its
  explicit timestamp and time delta;
* Missing != Clear != Zero;
* no new provider request is issued.
"""

from dataclasses import dataclass
from datetime import timedelta

import numpy as np
import pandas as pd

from .providers.openmeteo import interpolate_route_at_time


POINT_COLUMNS = [
    "timeline_time",
    "event_time",
    "event_offset_minutes",
    "timeline_step_minutes",
    "timeline_window_role",
    "core_physics_window_state",
    "temporal_interpolation_method",
    "point_id",
    "direction_offset_deg",
    "distance_km",
    "distance_band",
    "cloud_cover_low_pct",
    "cloud_cover_mid_pct",
    "cloud_cover_high_pct",
    "visibility_m",
    "relative_humidity_2m_pct",
    "precipitation",
    "native_reference_time",
    "native_time_delta_seconds",
    "native_time_match_state",
    "native_reference_solar_altitude_deg",
    "native_cloud_base_km",
    "native_cloud_top_km",
    "native_cloud_thickness_km",
    "native_vertical_completeness",
    "native_liquid_water_path_proxy_gm3_km",
    "native_ice_water_path_proxy_gm3_km",
    "native_low_cloud_geometry_state",
    "coarse_native_low_cloud_relation",
    "diagnostic_role",
    "tau_synthesis_allowed",
    "formation_promotion_allowed",
    "viewing_target_required",
    "native_temporal_interpolation_allowed",
]

SUMMARY_COLUMNS = [
    "timeline_time",
    "event_time",
    "event_offset_minutes",
    "timeline_window_role",
    "core_physics_window_state",
    "direction_offset_deg",
    "distance_band",
    "point_count",
    "coarse_low_cloud_valid_count",
    "coarse_low_cloud_mean_pct",
    "coarse_low_cloud_max_pct",
    "coarse_low_cloud_nonzero_point_count",
    "native_time_matched_point_count",
    "native_low_cloud_geometry_point_count",
    "coarse_nonzero_native_no_column_point_count",
    "coarse_nonzero_native_unmatched_point_count",
    "visibility_min_m",
    "relative_humidity_2m_max_pct",
    "precipitation_max",
    "diagnostic_status",
    "diagnostic_role",
    "tau_synthesis_allowed",
    "formation_promotion_allowed",
    "native_temporal_interpolation_allowed",
]


@dataclass(frozen=True)
class TimelineContract:
    start_offset_minutes: int = -60
    end_offset_minutes: int = 30
    step_minutes: int = 5
    native_match_tolerance_seconds: float = 180.0


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


def _event_time_from_contract(event_time_contract: pd.DataFrame) -> pd.Timestamp | None:
    if event_time_contract is None or event_time_contract.empty:
        return None
    e = event_time_contract.copy()
    if "solar_altitude_deg" in e.columns:
        s = pd.to_numeric(e["solar_altitude_deg"], errors="coerce")
        q = e[s.abs().le(1e-9)]
        if not q.empty:
            e = q
    col = "event_local_time" if "event_local_time" in e.columns else "time" if "time" in e.columns else None
    if col is None or e.empty:
        return None
    t = pd.to_datetime(e.iloc[0][col], errors="coerce")
    if pd.isna(t):
        return None
    return pd.Timestamp(t)


def _local_naive(ts: pd.Timestamp) -> pd.Timestamp:
    t = pd.Timestamp(ts)
    if t.tzinfo is not None:
        return t.tz_localize(None)
    return t


def _core_end_time_from_contract(event_time_contract: pd.DataFrame, event_time: pd.Timestamp) -> pd.Timestamp:
    if event_time_contract is None or event_time_contract.empty:
        return event_time
    e = event_time_contract.copy()
    if "solar_altitude_deg" not in e.columns:
        return event_time
    s = pd.to_numeric(e["solar_altitude_deg"], errors="coerce")
    q = e[(s + 6.0).abs().le(1e-9)]
    if q.empty:
        return event_time
    col = "event_local_time" if "event_local_time" in q.columns else "time" if "time" in q.columns else None
    if col is None:
        return event_time
    t = pd.to_datetime(q.iloc[0][col], errors="coerce")
    return pd.Timestamp(t) if not pd.isna(t) else event_time


def _native_groups(native_cloud_columns: pd.DataFrame) -> dict[tuple[float, float], pd.DataFrame]:
    if native_cloud_columns is None or native_cloud_columns.empty:
        return {}
    n = native_cloud_columns.copy()
    for c in ("direction_offset_deg", "distance_km", "solar_altitude_deg"):
        if c not in n.columns:
            n[c] = np.nan
        n[c] = pd.to_numeric(n[c], errors="coerce")
    if "time" not in n.columns:
        return {}
    n["_native_time"] = pd.to_datetime(n["time"], errors="coerce")
    n = n[n["_native_time"].notna()].copy()
    if n.empty:
        return {}
    n["_native_time_naive"] = n["_native_time"].map(_local_naive)
    groups: dict[tuple[float, float], pd.DataFrame] = {}
    for (off, dist), g in n.groupby(["direction_offset_deg", "distance_km"], dropna=False):
        if not np.isfinite(off) or not np.isfinite(dist):
            continue
        groups[(round(float(off), 6), round(float(dist), 6))] = g.sort_values("_native_time_naive").reset_index(drop=True)
    return groups


def _attach_native_nearest(
    row: dict,
    target_time: pd.Timestamp,
    native_groups: dict[tuple[float, float], pd.DataFrame],
    tolerance_seconds: float,
) -> None:
    key = (round(float(row["direction_offset_deg"]), 6), round(float(row["distance_km"]), 6))
    g = native_groups.get(key)
    target_naive = _local_naive(target_time)
    native_fields = [
        "native_cloud_base_km", "native_cloud_top_km", "native_cloud_thickness_km",
        "native_vertical_completeness", "liquid_water_path_proxy_gm3_km",
        "ice_water_path_proxy_gm3_km", "solar_altitude_deg",
    ]
    if g is None or g.empty:
        row.update({
            "native_reference_time": pd.NaT,
            "native_time_delta_seconds": np.nan,
            "native_time_match_state": "NATIVE_TIME_SAMPLE_UNAVAILABLE",
            "native_reference_solar_altitude_deg": np.nan,
            "native_cloud_base_km": np.nan,
            "native_cloud_top_km": np.nan,
            "native_cloud_thickness_km": np.nan,
            "native_vertical_completeness": np.nan,
            "native_liquid_water_path_proxy_gm3_km": np.nan,
            "native_ice_water_path_proxy_gm3_km": np.nan,
        })
        return

    deltas = (g["_native_time_naive"] - target_naive).abs().dt.total_seconds()
    idx = deltas.idxmin()
    delta = float(deltas.loc[idx])
    if not np.isfinite(delta) or delta > float(tolerance_seconds):
        row.update({
            "native_reference_time": pd.NaT,
            "native_time_delta_seconds": delta if np.isfinite(delta) else np.nan,
            "native_time_match_state": "NO_NATIVE_SAMPLE_WITHIN_TIME_TOLERANCE",
            "native_reference_solar_altitude_deg": np.nan,
            "native_cloud_base_km": np.nan,
            "native_cloud_top_km": np.nan,
            "native_cloud_thickness_km": np.nan,
            "native_vertical_completeness": np.nan,
            "native_liquid_water_path_proxy_gm3_km": np.nan,
            "native_ice_water_path_proxy_gm3_km": np.nan,
        })
        return

    q = g.loc[idx]
    row["native_reference_time"] = q.get("time", pd.NaT)
    row["native_time_delta_seconds"] = delta
    row["native_time_match_state"] = "NEAREST_EXISTING_NATIVE_SNAPSHOT_WITHIN_TOLERANCE"
    row["native_reference_solar_altitude_deg"] = pd.to_numeric(pd.Series([q.get("solar_altitude_deg")]), errors="coerce").iloc[0]
    row["native_cloud_base_km"] = pd.to_numeric(pd.Series([q.get("native_cloud_base_km")]), errors="coerce").iloc[0]
    row["native_cloud_top_km"] = pd.to_numeric(pd.Series([q.get("native_cloud_top_km")]), errors="coerce").iloc[0]
    row["native_cloud_thickness_km"] = pd.to_numeric(pd.Series([q.get("native_cloud_thickness_km")]), errors="coerce").iloc[0]
    row["native_vertical_completeness"] = pd.to_numeric(pd.Series([q.get("native_vertical_completeness")]), errors="coerce").iloc[0]
    row["native_liquid_water_path_proxy_gm3_km"] = pd.to_numeric(pd.Series([q.get("liquid_water_path_proxy_gm3_km")]), errors="coerce").iloc[0]
    row["native_ice_water_path_proxy_gm3_km"] = pd.to_numeric(pd.Series([q.get("ice_water_path_proxy_gm3_km")]), errors="coerce").iloc[0]


def _classify_native_relation(row: dict) -> tuple[str, str]:
    coarse = row.get("cloud_cover_low_pct", np.nan)
    try:
        coarse = float(coarse)
    except Exception:
        coarse = np.nan
    matched = row.get("native_time_match_state") == "NEAREST_EXISTING_NATIVE_SNAPSHOT_WITHIN_TOLERANCE"
    base = row.get("native_cloud_base_km", np.nan)
    top = row.get("native_cloud_top_km", np.nan)
    try:
        base = float(base)
    except Exception:
        base = np.nan
    try:
        top = float(top)
    except Exception:
        top = np.nan
    geom = matched and np.isfinite(base) and np.isfinite(top)
    low_geom = bool(geom and base <= 2.0 and top >= 0.0)

    if not matched:
        return "NATIVE_TIME_SAMPLE_UNAVAILABLE_FOR_TIMELINE", (
            "COARSE_LOW_CLOUD_NATIVE_TIME_UNMATCHED" if np.isfinite(coarse) and coarse > 0.0
            else "COARSE_EXACT_ZERO_OR_MISSING_NATIVE_TIME_UNMATCHED"
        )
    if low_geom:
        return "NATIVE_LOW_CLOUD_GEOMETRY_PRESENT", (
            "COARSE_AND_NATIVE_LOW_CLOUD" if np.isfinite(coarse) and coarse > 0.0
            else "NATIVE_LOW_CLOUD_COARSE_EXACT_ZERO_OR_MISSING"
        )
    if geom:
        return "NATIVE_CLOUD_GEOMETRY_ABOVE_LOW_LAYER", (
            "COARSE_LOW_CLOUD_NATIVE_GEOMETRY_NOT_LOW" if np.isfinite(coarse) and coarse > 0.0
            else "COARSE_EXACT_ZERO_OR_MISSING_NATIVE_GEOMETRY_NOT_LOW"
        )
    return "NATIVE_NO_CLOUD_COLUMN_AT_THRESHOLD", (
        "COARSE_LOW_CLOUD_NATIVE_NO_COLUMN_AT_THRESHOLD" if np.isfinite(coarse) and coarse > 0.0
        else "COARSE_EXACT_ZERO_OR_MISSING_NATIVE_NO_COLUMN_AT_THRESHOLD"
    )


def build_observer_environment_timeline(
    hourly_raw: pd.DataFrame,
    event_time_contract: pd.DataFrame,
    native_cloud_columns: pd.DataFrame | None = None,
    *,
    contract: TimelineContract = TimelineContract(),
    max_distance_km: float = 100.0,
) -> pd.DataFrame:
    """Build a regular event-relative observer-environment diagnostic timeline.

    Coarse route fields are interpolated with the existing Open-Meteo route
    interpolation contract.  Native cloud-column evidence is *not* interpolated;
    an already-existing native snapshot is only attached when its timestamp is
    within ``native_match_tolerance_seconds`` of the diagnostic target time.
    """
    if hourly_raw is None or hourly_raw.empty:
        return pd.DataFrame(columns=POINT_COLUMNS)
    event_time = _event_time_from_contract(event_time_contract)
    if event_time is None:
        return pd.DataFrame(columns=POINT_COLUMNS)
    if contract.step_minutes <= 0 or contract.end_offset_minutes < contract.start_offset_minutes:
        return pd.DataFrame(columns=POINT_COLUMNS)

    core_end_time = _core_end_time_from_contract(event_time_contract, event_time)
    native_groups = _native_groups(native_cloud_columns if native_cloud_columns is not None else pd.DataFrame())
    rows: list[dict] = []
    offsets = range(int(contract.start_offset_minutes), int(contract.end_offset_minutes) + 1, int(contract.step_minutes))

    for offset in offsets:
        target = event_time + pd.Timedelta(minutes=int(offset))
        snap = interpolate_route_at_time(hourly_raw, target.to_pydatetime())
        if snap is None or snap.empty:
            continue
        if "distance_km" not in snap.columns:
            continue
        dist = pd.to_numeric(snap["distance_km"], errors="coerce")
        snap = snap[dist.between(0.0, float(max_distance_km), inclusive="both")].copy()
        if snap.empty:
            continue

        for rec in snap.to_dict("records"):
            distance = pd.to_numeric(pd.Series([rec.get("distance_km")]), errors="coerce").iloc[0]
            direction = pd.to_numeric(pd.Series([rec.get("direction_offset_deg")]), errors="coerce").iloc[0]
            if not np.isfinite(distance) or not np.isfinite(direction):
                continue
            row = {
                "timeline_time": target,
                "event_time": event_time,
                "event_offset_minutes": int(offset),
                "timeline_step_minutes": int(contract.step_minutes),
                "timeline_window_role": (
                    "PRE_EVENT" if offset < 0 else "EVENT_TIME" if offset == 0 else "POST_EVENT_DIAGNOSTIC"
                ),
                "core_physics_window_state": (
                    "PRE_CORE_EVENT_DIAGNOSTIC" if target < event_time else
                    "CORE_0_TO_MINUS6_TIME_RANGE" if target <= core_end_time else
                    "POST_MINUS6_DIAGNOSTIC_ONLY"
                ),
                "temporal_interpolation_method": "OPENMETEO_ROUTE_LINEAR_INTERPOLATION_EXISTING_CONTRACT",
                "point_id": str(rec.get("point_id", "")),
                "direction_offset_deg": float(direction),
                "distance_km": float(distance),
                "distance_band": _distance_band(float(distance)),
                "cloud_cover_low_pct": pd.to_numeric(pd.Series([rec.get("cloud_cover_low")]), errors="coerce").iloc[0],
                "cloud_cover_mid_pct": pd.to_numeric(pd.Series([rec.get("cloud_cover_mid")]), errors="coerce").iloc[0],
                "cloud_cover_high_pct": pd.to_numeric(pd.Series([rec.get("cloud_cover_high")]), errors="coerce").iloc[0],
                "visibility_m": pd.to_numeric(pd.Series([rec.get("visibility")]), errors="coerce").iloc[0],
                "relative_humidity_2m_pct": pd.to_numeric(pd.Series([rec.get("relative_humidity_2m")]), errors="coerce").iloc[0],
                "precipitation": pd.to_numeric(pd.Series([rec.get("precipitation")]), errors="coerce").iloc[0],
            }
            _attach_native_nearest(row, target, native_groups, contract.native_match_tolerance_seconds)
            native_state, relation = _classify_native_relation(row)
            row["native_low_cloud_geometry_state"] = native_state
            row["coarse_native_low_cloud_relation"] = relation
            row["diagnostic_role"] = "OBSERVER_ENVIRONMENT_TIMELINE_ONLY_NO_PHYSICS_PROMOTION"
            row["tau_synthesis_allowed"] = False
            row["formation_promotion_allowed"] = False
            row["viewing_target_required"] = False
            row["native_temporal_interpolation_allowed"] = False
            rows.append(row)

    if not rows:
        return pd.DataFrame(columns=POINT_COLUMNS)
    out = pd.DataFrame(rows)
    for c in POINT_COLUMNS:
        if c not in out.columns:
            out[c] = np.nan
    return out.loc[:, POINT_COLUMNS].reset_index(drop=True)


def summarize_observer_environment_timeline(points: pd.DataFrame) -> pd.DataFrame:
    if points is None or points.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    p = points.copy()
    p = p[p["distance_band"].notna()].copy()
    rows: list[dict] = []
    keys = ["timeline_time", "event_time", "event_offset_minutes", "timeline_window_role", "core_physics_window_state", "direction_offset_deg", "distance_band"]
    for vals, g in p.groupby(keys, dropna=False, sort=True):
        low = pd.to_numeric(g["cloud_cover_low_pct"], errors="coerce")
        vis = pd.to_numeric(g["visibility_m"], errors="coerce")
        rh = pd.to_numeric(g["relative_humidity_2m_pct"], errors="coerce")
        pr = pd.to_numeric(g["precipitation"], errors="coerce")
        native_matched = g["native_time_match_state"].astype(str).eq("NEAREST_EXISTING_NATIVE_SNAPSHOT_WITHIN_TOLERANCE")
        native_low = g["native_low_cloud_geometry_state"].astype(str).eq("NATIVE_LOW_CLOUD_GEOMETRY_PRESENT")
        mismatch = g["coarse_native_low_cloud_relation"].astype(str).eq("COARSE_LOW_CLOUD_NATIVE_NO_COLUMN_AT_THRESHOLD")
        unmatched = g["coarse_native_low_cloud_relation"].astype(str).eq("COARSE_LOW_CLOUD_NATIVE_TIME_UNMATCHED")
        if int(mismatch.sum()) > 0:
            status = "COARSE_LOW_CLOUD_PRESENT_NATIVE_3D_NOT_RECONSTRUCTED"
        elif int(unmatched.sum()) > 0:
            status = "COARSE_LOW_CLOUD_PRESENT_NATIVE_TIME_UNMATCHED"
        elif int(native_low.sum()) > 0:
            status = "NATIVE_LOW_CLOUD_GEOMETRY_PRESENT"
        elif low.notna().any() and low.gt(0.0).any():
            status = "COARSE_LOW_CLOUD_PRESENT"
        else:
            status = "NO_NONZERO_COARSE_LOW_CLOUD_IN_AVAILABLE_EVIDENCE"
        row = dict(zip(keys, vals if isinstance(vals, tuple) else (vals,)))
        row.update({
            "point_count": int(len(g)),
            "coarse_low_cloud_valid_count": int(low.notna().sum()),
            "coarse_low_cloud_mean_pct": float(low.mean()) if low.notna().any() else np.nan,
            "coarse_low_cloud_max_pct": float(low.max()) if low.notna().any() else np.nan,
            "coarse_low_cloud_nonzero_point_count": int(low.gt(0.0).sum()),
            "native_time_matched_point_count": int(native_matched.sum()),
            "native_low_cloud_geometry_point_count": int(native_low.sum()),
            "coarse_nonzero_native_no_column_point_count": int(mismatch.sum()),
            "coarse_nonzero_native_unmatched_point_count": int(unmatched.sum()),
            "visibility_min_m": float(vis.min()) if vis.notna().any() else np.nan,
            "relative_humidity_2m_max_pct": float(rh.max()) if rh.notna().any() else np.nan,
            "precipitation_max": float(pr.max()) if pr.notna().any() else np.nan,
            "diagnostic_status": status,
            "diagnostic_role": "OBSERVER_ENVIRONMENT_TIMELINE_ONLY_NO_PHYSICS_PROMOTION",
            "tau_synthesis_allowed": False,
            "formation_promotion_allowed": False,
            "native_temporal_interpolation_allowed": False,
        })
        rows.append(row)
    out = pd.DataFrame(rows)
    for c in SUMMARY_COLUMNS:
        if c not in out.columns:
            out[c] = np.nan
    return out.loc[:, SUMMARY_COLUMNS].reset_index(drop=True)
