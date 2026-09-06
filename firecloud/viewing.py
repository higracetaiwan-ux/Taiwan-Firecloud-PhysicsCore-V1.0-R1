"""PhysicsCore V1.0-R5.6 Cloud→Observer viewing geometry.

This module is deliberately independent of Formation.  It answers only whether
an existing target cloud is geometrically visible from the observer through
nearer forecast cloud layers.  It does not change F_sun, Sun→CloudBase RT, or
whether the target cloud was illuminated.

R5.6 is a Tier-1 geometry/occupancy branch.  It does NOT claim full spectral
Cloud→Observer transmission.  ``view_obstruction_fraction_proxy`` is a cloud-
occupancy proxy derived from intervening cloud fraction at line-of-sight
intersections and is explicitly not optical depth.
"""
from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd

EARTH_RADIUS_KM = 6371.0


def _finite(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None


def _los_height_agl_km(target_distance_km: float, target_height_agl_km: float,
                       blocker_distance_km: float, earth_radius_km: float = EARTH_RADIUS_KM) -> float:
    """Approximate curved-Earth LOS height above local ground at blocker range.

    The observer is treated as 0 km AGL.  For 0–100 km canvas viewing this
    second-order curvature expression is adequate for Tier-1 obstruction
    geometry and avoids conflating it with radiative transfer.
    """
    dt = max(float(target_distance_km), 1e-6)
    db = min(max(float(blocker_distance_km), 0.0), dt)
    r = float(earth_radius_km)
    target_tangent_h = float(target_height_agl_km) - (dt * dt) / (2.0 * r)
    line_tangent_h = (db / dt) * target_tangent_h
    local_ground_tangent_h = -(db * db) / (2.0 * r)
    return line_tangent_h - local_ground_tangent_h


def _direction_from_layer_id(layer_id: str):
    s = str(layer_id or "")
    if not s.startswith("dir"):
        return None
    try:
        return float(s.split("_d", 1)[0][3:])
    except Exception:
        return None


def build_viewing_path_geometry(cloud_layers: pd.DataFrame, canvases: pd.DataFrame,
                                *, earth_radius_km: float = EARTH_RADIUS_KM) -> pd.DataFrame:
    """Return target-level Cloud→Observer obstruction diagnostics.

    Three sight-lines are sampled for each target layer: cloud base, midpoint,
    and cloud top.  A nearer layer is a geometric blocker when one of those
    sight-lines crosses its vertical extent on the same direction transect.

    No COT is manufactured.  Cloud fraction is used only as an occupancy proxy
    after a geometric intersection has been established.
    """
    cols = [
        "time", "solar_altitude_deg", "canvas_id", "cloud_layer_id",
        "direction_offset_deg", "target_distance_km", "target_base_km",
        "target_top_km", "view_sample_count", "blocked_view_sample_count",
        "intervening_blocker_count", "low_cloud_blocker_count",
        "mid_cloud_blocker_count", "high_cloud_blocker_count",
        "view_obstruction_fraction_proxy", "view_geometry_state",
        "viewing_path_spectral_status", "viewing_confidence", "blocker_layer_ids",
        "note",
    ]
    if cloud_layers is None or canvases is None or cloud_layers.empty or canvases.empty:
        return pd.DataFrame(columns=cols)

    layers = cloud_layers.copy()
    cvs = canvases.copy()
    if "layer_id" not in layers or "cloud_layer_id" not in cvs:
        return pd.DataFrame(columns=cols)

    # Enrich canvas rows from authoritative cloud-layer geometry.
    lk = layers[[c for c in ["layer_id", "direction_offset_deg", "distance_km", "z_base_km", "z_top_km",
                              "cloud_fraction", "cloud_fraction_state", "geometry_confidence", "time",
                              "solar_altitude_deg"] if c in layers.columns]].copy()
    left_on = ["cloud_layer_id"]
    right_on = ["layer_id"]
    for k in ["time", "solar_altitude_deg"]:
        if k in cvs.columns and k in lk.columns:
            left_on.append(k); right_on.append(k)
    cvs = cvs.merge(lk, left_on=left_on, right_on=right_on, how="left", suffixes=("", "_layer"))

    rows = []
    group_keys = [k for k in ["time", "solar_altitude_deg"] if k in layers.columns]
    for _, target in cvs.iterrows():
        canvas_id = target.get("canvas_id")
        layer_id = target.get("cloud_layer_id")
        dt = _finite(target.get("distance_km_layer", target.get("distance_km")))
        zb = _finite(target.get("z_base_km"))
        zt = _finite(target.get("z_top_km"))
        direction = _finite(target.get("direction_offset_deg"))
        if direction is None:
            direction = _direction_from_layer_id(layer_id)
        tval = target.get("time_layer", target.get("time"))
        aval = target.get("solar_altitude_deg_layer", target.get("solar_altitude_deg"))

        base_row = {
            "time": tval, "solar_altitude_deg": aval, "canvas_id": canvas_id,
            "cloud_layer_id": layer_id, "direction_offset_deg": direction,
            "target_distance_km": dt, "target_base_km": zb, "target_top_km": zt,
        }
        if dt is None or zb is None or zt is None or direction is None or dt <= 0.0 or zt <= zb:
            rows.append({**base_row, "view_sample_count": 0, "blocked_view_sample_count": 0,
                         "intervening_blocker_count": 0, "low_cloud_blocker_count": 0,
                         "mid_cloud_blocker_count": 0, "high_cloud_blocker_count": 0,
                         "view_obstruction_fraction_proxy": np.nan,
                         "view_geometry_state": "VIEW_GEOMETRY_NOT_EVALUATED_LOCAL_TARGET",
                         "viewing_path_spectral_status": "VIEW_SPECTRAL_RT_NOT_YET_RESOLVED",
                         "viewing_confidence": "LOW", "blocker_layer_ids": "",
                         "note": "FORMATION_UNCHANGED;VIEWING_GEOMETRY_ONLY;LOCAL_OR_INCOMPLETE_TARGET"})
            continue

        cand = layers.copy()
        if "solar_altitude_deg" in cand.columns and pd.notna(aval):
            cand = cand[pd.to_numeric(cand["solar_altitude_deg"], errors="coerce").sub(float(aval)).abs() < 1e-8]
        if "time" in cand.columns and pd.notna(tval):
            # Angle is the stable key; time matching is intentionally not strict because serialized timestamps can differ in dtype.
            pass
        cand = cand[pd.to_numeric(cand.get("direction_offset_deg"), errors="coerce").sub(float(direction)).abs() < 1e-8]
        cand = cand[pd.to_numeric(cand.get("distance_km"), errors="coerce") < dt - 1e-9]
        # Same target layer must never self-block.
        cand = cand[cand.get("layer_id", pd.Series(index=cand.index, dtype=str)).astype(str) != str(layer_id)]

        sample_heights = [zb, 0.5 * (zb + zt), zt]
        sample_occ = []
        blockers = set()
        low = mid = high = 0
        blocker_class_seen = set()
        for hs in sample_heights:
            occ_terms = []
            for _, b in cand.iterrows():
                db = _finite(b.get("distance_km")); bb = _finite(b.get("z_base_km")); bt = _finite(b.get("z_top_km"))
                if db is None or bb is None or bt is None or db <= 0.0 or bt <= bb:
                    continue
                hlos = _los_height_agl_km(dt, hs, db, earth_radius_km)
                if bb - 1e-9 <= hlos <= bt + 1e-9:
                    bid = str(b.get("layer_id", ""))
                    blockers.add(bid)
                    cf = _finite(b.get("cloud_fraction"))
                    if cf is None:
                        # Geometry says cloud exists but occupancy is missing: keep obstruction unknown-ish rather than clear.
                        cf = 0.5
                    cf = min(max(cf, 0.0), 1.0)
                    occ_terms.append(cf)
                    key = (bid,)
                    if key not in blocker_class_seen:
                        blocker_class_seen.add(key)
                        midh = 0.5 * (bb + bt)
                        if midh < 2.0:
                            low += 1
                        elif midh < 6.0:
                            mid += 1
                        else:
                            high += 1
            if occ_terms:
                clear_prob = 1.0
                for cf in occ_terms:
                    clear_prob *= (1.0 - cf)
                sample_occ.append(1.0 - clear_prob)
            else:
                sample_occ.append(0.0)

        obstruction = float(np.mean(sample_occ)) if sample_occ else np.nan
        blocked_samples = int(sum(v >= 0.10 for v in sample_occ))
        if not math.isfinite(obstruction):
            state = "VIEW_GEOMETRY_UNKNOWN"
            conf = "LOW"
        elif obstruction >= 0.70:
            state = "VIEW_SEVERE_OBSTRUCTION"
            conf = "MEDIUM"
        elif obstruction >= 0.10:
            state = "VIEW_PARTIAL_OBSTRUCTION"
            conf = "MEDIUM"
        else:
            state = "VIEW_GEOMETRICALLY_CLEAR"
            conf = "MEDIUM"

        rows.append({**base_row, "view_sample_count": len(sample_heights),
                     "blocked_view_sample_count": blocked_samples,
                     "intervening_blocker_count": len(blockers),
                     "low_cloud_blocker_count": low, "mid_cloud_blocker_count": mid,
                     "high_cloud_blocker_count": high,
                     "view_obstruction_fraction_proxy": obstruction,
                     "view_geometry_state": state,
                     "viewing_path_spectral_status": "VIEW_SPECTRAL_RT_NOT_YET_RESOLVED",
                     "viewing_confidence": conf,
                     "blocker_layer_ids": ";".join(sorted(blockers)),
                     "note": "FORMATION_UNCHANGED;CLOUD_TO_OBSERVER_GEOMETRY_ONLY;CF_OCCUPANCY_PROXY_NOT_COT;UNCALIBRATED_THRESHOLDS"})

    return pd.DataFrame(rows, columns=cols)


def summarize_viewing_path(viewing: pd.DataFrame) -> pd.DataFrame:
    cols = ["time", "solar_altitude_deg", "target_count", "evaluated_target_count",
            "clear_target_count", "partial_obstruction_target_count", "severe_obstruction_target_count",
            "mean_view_obstruction_fraction_proxy", "max_view_obstruction_fraction_proxy",
            "viewing_state", "viewing_path_spectral_status", "note"]
    if viewing is None or viewing.empty:
        return pd.DataFrame(columns=cols)
    rows = []
    keys = [k for k in ["time", "solar_altitude_deg"] if k in viewing.columns]
    groups = viewing.groupby(keys, dropna=False) if keys else [((), viewing)]
    for key, g in groups:
        states = g.get("view_geometry_state", pd.Series(dtype=str)).astype(str)
        vals = pd.to_numeric(g.get("view_obstruction_fraction_proxy"), errors="coerce")
        evaluated = vals.notna()
        mean = float(vals[evaluated].mean()) if evaluated.any() else np.nan
        mx = float(vals[evaluated].max()) if evaluated.any() else np.nan
        if not evaluated.any(): state = "VIEWING_UNKNOWN"
        elif mean >= 0.70: state = "VIEWING_SEVERELY_OBSCURED"
        elif mean >= 0.10: state = "VIEWING_PARTIALLY_OBSCURED"
        else: state = "VIEWING_GEOMETRY_GOOD"
        row = {"target_count": len(g), "evaluated_target_count": int(evaluated.sum()),
               "clear_target_count": int((states == "VIEW_GEOMETRICALLY_CLEAR").sum()),
               "partial_obstruction_target_count": int((states == "VIEW_PARTIAL_OBSTRUCTION").sum()),
               "severe_obstruction_target_count": int((states == "VIEW_SEVERE_OBSTRUCTION").sum()),
               "mean_view_obstruction_fraction_proxy": mean,
               "max_view_obstruction_fraction_proxy": mx, "viewing_state": state,
               "viewing_path_spectral_status": "VIEW_SPECTRAL_RT_NOT_YET_RESOLVED",
               "note": "FORMATION_INDEPENDENT;GEOMETRY_OCCUPANCY_TIER1;NO_VIEWING_SPECTRAL_EXTINCTION_YET"}
        if keys:
            valskey = key if isinstance(key, tuple) else (key,)
            row.update(dict(zip(keys, valskey)))
        rows.append(row)
    return pd.DataFrame(rows, columns=cols)
