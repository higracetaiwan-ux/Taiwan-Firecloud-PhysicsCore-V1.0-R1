from __future__ import annotations

"""Observer near-field cloud-environment diagnostics.

R5.7.41.3.4.10.9.3
---------------------
This module intentionally does *not* participate in Formation, Viewing target
selection, optical-depth synthesis, or Photography Decision.  It preserves the
already available exact-time route low/mid/high cloud-cover fields alongside
GFS native-condensate cloud-column evidence so a CASE can represent an
observer environment even when there is no formed Canvas target.

Hard contract:
* diagnostic only;
* Missing != Clear != Zero;
* coarse cloud cover is never converted into tau/COT;
* native-column absence is reported as absence-at-native-threshold, not clear sky;
* no Formation/Viewing/Glow state is promoted or rewritten.
"""

from typing import Iterable

import numpy as np
import pandas as pd


POINT_COLUMNS = [
    "time",
    "solar_altitude_deg",
    "point_id",
    "direction_offset_deg",
    "distance_km",
    "canvas_domain_role",
    "near_observer_0_10km",
    "cloud_cover_low_pct",
    "cloud_cover_mid_pct",
    "cloud_cover_high_pct",
    "visibility_m",
    "relative_humidity_2m_pct",
    "precipitation",
    "native_cloud_base_km",
    "native_cloud_top_km",
    "native_cloud_thickness_km",
    "native_vertical_completeness",
    "native_liquid_water_path_proxy_gm3_km",
    "native_ice_water_path_proxy_gm3_km",
    "coarse_low_cloud_state",
    "native_column_state",
    "native_low_cloud_geometry_state",
    "coarse_native_low_cloud_relation",
    "diagnostic_role",
    "tau_synthesis_allowed",
    "formation_promotion_allowed",
    "viewing_target_required",
]

SUMMARY_COLUMNS = [
    "time",
    "solar_altitude_deg",
    "direction_offset_deg",
    "distance_band",
    "point_count",
    "coarse_low_cloud_valid_count",
    "coarse_low_cloud_mean_pct",
    "coarse_low_cloud_max_pct",
    "coarse_low_cloud_nonzero_point_count",
    "native_low_cloud_geometry_point_count",
    "native_no_cloud_column_at_threshold_point_count",
    "native_unavailable_point_count",
    "coarse_nonzero_native_no_column_point_count",
    "visibility_min_m",
    "relative_humidity_2m_max_pct",
    "precipitation_max",
    "diagnostic_status",
    "diagnostic_role",
    "tau_synthesis_allowed",
    "formation_promotion_allowed",
]


def _num(frame: pd.DataFrame, name: str) -> pd.Series:
    if name not in frame.columns:
        return pd.Series(np.nan, index=frame.index, dtype=float)
    return pd.to_numeric(frame[name], errors="coerce")


def _bool_false_series(index) -> pd.Series:
    return pd.Series(False, index=index, dtype=bool)


def _canvas_domain_role(distance_km: float) -> str:
    if not np.isfinite(distance_km):
        return "DISTANCE_UNKNOWN"
    if 0.0 <= distance_km <= 40.0:
        return "PRIMARY_0_40KM"
    if 40.0 < distance_km <= 100.0:
        return "EXTENDED_GT40_100KM"
    return "OUTSIDE_0_100KM"


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


def _native_key_frame(native_cloud_columns: pd.DataFrame) -> pd.DataFrame:
    """Return one native-column row per angle/direction/distance.

    Native cloud columns normally already contain exactly one row for every
    sampled route point.  ``drop_duplicates(..., keep='last')`` is only a
    defensive export-normalization step and does not alter any physics.
    """
    if native_cloud_columns is None or native_cloud_columns.empty:
        return pd.DataFrame()
    n = native_cloud_columns.copy()
    for c in ("solar_altitude_deg", "direction_offset_deg", "distance_km"):
        if c not in n.columns:
            n[c] = np.nan
        n[c] = pd.to_numeric(n[c], errors="coerce")
    keys = ["solar_altitude_deg", "direction_offset_deg", "distance_km"]
    n = n.drop_duplicates(subset=keys, keep="last").copy()
    keep = keys + [c for c in (
        "native_cloud_base_km",
        "native_cloud_top_km",
        "native_cloud_thickness_km",
        "native_vertical_completeness",
        "liquid_water_path_proxy_gm3_km",
        "ice_water_path_proxy_gm3_km",
        "boundary_quality",
    ) if c in n.columns]
    return n.loc[:, keep]


def build_observer_nearfield_cloud_environment(
    route_snapshots: pd.DataFrame,
    native_cloud_columns: pd.DataFrame,
    *,
    max_distance_km: float = 100.0,
) -> pd.DataFrame:
    """Build point-level observer-environment evidence for 0--100 km.

    ``route_snapshots`` is the already interpolated exact-time route snapshot
    used by Viewing/Glow.  No new provider request and no optical inference is
    performed here.
    """
    if route_snapshots is None or route_snapshots.empty:
        return pd.DataFrame(columns=POINT_COLUMNS)

    r = route_snapshots.copy()
    for c in ("solar_altitude_deg", "direction_offset_deg", "distance_km"):
        if c not in r.columns:
            r[c] = np.nan
        r[c] = pd.to_numeric(r[c], errors="coerce")

    r = r[r["distance_km"].between(0.0, float(max_distance_km), inclusive="both")].copy()
    if r.empty:
        return pd.DataFrame(columns=POINT_COLUMNS)

    # Keep exactly the source fields needed for observer-environment evidence.
    base = pd.DataFrame(index=r.index)
    base["time"] = r["time"] if "time" in r.columns else pd.NaT
    base["solar_altitude_deg"] = r["solar_altitude_deg"]
    base["point_id"] = r["point_id"].astype(str) if "point_id" in r.columns else ""
    base["direction_offset_deg"] = r["direction_offset_deg"]
    base["distance_km"] = r["distance_km"]
    base["cloud_cover_low_pct"] = _num(r, "cloud_cover_low")
    base["cloud_cover_mid_pct"] = _num(r, "cloud_cover_mid")
    base["cloud_cover_high_pct"] = _num(r, "cloud_cover_high")
    base["visibility_m"] = _num(r, "visibility")
    base["relative_humidity_2m_pct"] = _num(r, "relative_humidity_2m")
    base["precipitation"] = _num(r, "precipitation")

    n = _native_key_frame(native_cloud_columns)
    if not n.empty:
        rename = {
            "liquid_water_path_proxy_gm3_km": "native_liquid_water_path_proxy_gm3_km",
            "ice_water_path_proxy_gm3_km": "native_ice_water_path_proxy_gm3_km",
        }
        n = n.rename(columns=rename)
        base = base.merge(
            n,
            how="left",
            on=["solar_altitude_deg", "direction_offset_deg", "distance_km"],
            sort=False,
            indicator="_native_merge_state",
        )
    else:
        base["_native_merge_state"] = "left_only"

    # Normalize optional native fields while retaining Missing as NaN.
    for c in (
        "native_cloud_base_km",
        "native_cloud_top_km",
        "native_cloud_thickness_km",
        "native_vertical_completeness",
        "native_liquid_water_path_proxy_gm3_km",
        "native_ice_water_path_proxy_gm3_km",
    ):
        if c not in base.columns:
            base[c] = np.nan
        base[c] = pd.to_numeric(base[c], errors="coerce")

    base["canvas_domain_role"] = base["distance_km"].map(_canvas_domain_role)
    base["near_observer_0_10km"] = base["distance_km"].between(0.0, 10.0, inclusive="both")

    coarse = base["cloud_cover_low_pct"]
    base["coarse_low_cloud_state"] = np.where(
        coarse.isna(),
        "MISSING",
        np.where(coarse.gt(0.0), "NONZERO_COARSE_LOW_CLOUD", "EXACT_ZERO_COARSE_LOW_CLOUD"),
    )

    merged = base["_native_merge_state"].astype(str).eq("both")
    nbase = base["native_cloud_base_km"]
    ntop = base["native_cloud_top_km"]
    geometry = merged & nbase.notna() & ntop.notna()
    low_geometry = geometry & nbase.le(2.0) & ntop.ge(0.0)
    nonlow_geometry = geometry & ~low_geometry
    native_no_geometry = merged & ~geometry

    base["native_column_state"] = np.select(
        [~merged, geometry, native_no_geometry],
        ["NATIVE_COLUMN_UNAVAILABLE", "NATIVE_CLOUD_COLUMN_PRESENT", "NATIVE_NO_CLOUD_COLUMN_AT_THRESHOLD"],
        default="NATIVE_COLUMN_UNAVAILABLE",
    )
    base["native_low_cloud_geometry_state"] = np.select(
        [~merged, low_geometry, nonlow_geometry, native_no_geometry],
        [
            "NATIVE_EVIDENCE_UNAVAILABLE",
            "NATIVE_LOW_CLOUD_GEOMETRY_PRESENT",
            "NATIVE_CLOUD_GEOMETRY_ABOVE_LOW_LAYER",
            "NATIVE_NO_CLOUD_COLUMN_AT_THRESHOLD",
        ],
        default="NATIVE_EVIDENCE_UNAVAILABLE",
    )

    coarse_nonzero = coarse.gt(0.0) & coarse.notna()
    coarse_zero = coarse.eq(0.0) & coarse.notna()
    coarse_missing = coarse.isna()
    base["coarse_native_low_cloud_relation"] = np.select(
        [
            coarse_missing,
            coarse_nonzero & low_geometry,
            coarse_nonzero & native_no_geometry,
            coarse_nonzero & ~merged,
            coarse_nonzero & nonlow_geometry,
            coarse_zero & low_geometry,
            coarse_zero & native_no_geometry,
            coarse_zero & ~merged,
        ],
        [
            "COARSE_LOW_CLOUD_MISSING",
            "COARSE_AND_NATIVE_LOW_CLOUD",
            "COARSE_LOW_CLOUD_NATIVE_NO_COLUMN_AT_THRESHOLD",
            "COARSE_LOW_CLOUD_NATIVE_UNAVAILABLE",
            "COARSE_LOW_CLOUD_NATIVE_GEOMETRY_NOT_LOW",
            "NATIVE_LOW_CLOUD_COARSE_EXACT_ZERO",
            "COARSE_EXACT_ZERO_NATIVE_NO_COLUMN_AT_THRESHOLD",
            "COARSE_EXACT_ZERO_NATIVE_UNAVAILABLE",
        ],
        default="DIAGNOSTIC_RELATION_UNRESOLVED",
    )

    base["diagnostic_role"] = "OBSERVER_ENVIRONMENT_ONLY_NO_FORMATION_PROMOTION"
    base["tau_synthesis_allowed"] = False
    base["formation_promotion_allowed"] = False
    base["viewing_target_required"] = False
    base = base.drop(columns=["_native_merge_state"], errors="ignore")

    for c in POINT_COLUMNS:
        if c not in base.columns:
            base[c] = np.nan
    return base.loc[:, POINT_COLUMNS].reset_index(drop=True)


def summarize_observer_nearfield_cloud_environment(points: pd.DataFrame) -> pd.DataFrame:
    """Summarize observer environment without creating a physical score."""
    if points is None or points.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)

    p = points.copy()
    p["_distance_band"] = pd.to_numeric(p["distance_km"], errors="coerce").map(_distance_band)
    p = p[p["_distance_band"].notna()].copy()
    if p.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)

    rows: list[dict] = []
    group_cols = ["time", "solar_altitude_deg", "direction_offset_deg", "_distance_band"]
    for (time_v, alt_v, dir_v, band), g in p.groupby(group_cols, dropna=False, sort=False):
        low = pd.to_numeric(g["cloud_cover_low_pct"], errors="coerce")
        vis = pd.to_numeric(g["visibility_m"], errors="coerce")
        rh = pd.to_numeric(g["relative_humidity_2m_pct"], errors="coerce")
        precip = pd.to_numeric(g["precipitation"], errors="coerce")
        native_low = g["native_low_cloud_geometry_state"].astype(str).eq("NATIVE_LOW_CLOUD_GEOMETRY_PRESENT")
        native_none = g["native_low_cloud_geometry_state"].astype(str).eq("NATIVE_NO_CLOUD_COLUMN_AT_THRESHOLD")
        native_unavail = g["native_low_cloud_geometry_state"].astype(str).eq("NATIVE_EVIDENCE_UNAVAILABLE")
        coarse_nonzero = low.notna() & low.gt(0.0)
        mismatch = g["coarse_native_low_cloud_relation"].astype(str).eq("COARSE_LOW_CLOUD_NATIVE_NO_COLUMN_AT_THRESHOLD")

        if coarse_nonzero.any() and native_low.any():
            status = "COARSE_AND_NATIVE_LOW_CLOUD_EVIDENCE"
        elif coarse_nonzero.any() and mismatch.any() and not native_low.any():
            status = "COARSE_LOW_CLOUD_PRESENT_NATIVE_3D_NOT_RECONSTRUCTED"
        elif coarse_nonzero.any() and native_unavail.any() and not native_low.any():
            status = "COARSE_LOW_CLOUD_PRESENT_NATIVE_EVIDENCE_UNAVAILABLE"
        elif low.isna().all():
            status = "COARSE_LOW_CLOUD_MISSING"
        elif low.eq(0.0).all() and not native_low.any():
            status = "NO_LOW_CLOUD_EVIDENCE_IN_AVAILABLE_FIELDS"
        elif native_low.any():
            status = "NATIVE_LOW_CLOUD_PRESENT_COARSE_WEAK_OR_ZERO"
        else:
            status = "MIXED_OR_UNRESOLVED_OBSERVER_ENVIRONMENT"

        rows.append({
            "time": time_v,
            "solar_altitude_deg": alt_v,
            "direction_offset_deg": dir_v,
            "distance_band": band,
            "point_count": int(len(g)),
            "coarse_low_cloud_valid_count": int(low.notna().sum()),
            "coarse_low_cloud_mean_pct": float(low.mean()) if low.notna().any() else np.nan,
            "coarse_low_cloud_max_pct": float(low.max()) if low.notna().any() else np.nan,
            "coarse_low_cloud_nonzero_point_count": int(coarse_nonzero.sum()),
            "native_low_cloud_geometry_point_count": int(native_low.sum()),
            "native_no_cloud_column_at_threshold_point_count": int(native_none.sum()),
            "native_unavailable_point_count": int(native_unavail.sum()),
            "coarse_nonzero_native_no_column_point_count": int(mismatch.sum()),
            "visibility_min_m": float(vis.min()) if vis.notna().any() else np.nan,
            "relative_humidity_2m_max_pct": float(rh.max()) if rh.notna().any() else np.nan,
            "precipitation_max": float(precip.max()) if precip.notna().any() else np.nan,
            "diagnostic_status": status,
            "diagnostic_role": "OBSERVER_ENVIRONMENT_ONLY_NO_FORMATION_PROMOTION",
            "tau_synthesis_allowed": False,
            "formation_promotion_allowed": False,
        })

    out = pd.DataFrame(rows)
    for c in SUMMARY_COLUMNS:
        if c not in out.columns:
            out[c] = np.nan
    return out.loc[:, SUMMARY_COLUMNS].reset_index(drop=True)
