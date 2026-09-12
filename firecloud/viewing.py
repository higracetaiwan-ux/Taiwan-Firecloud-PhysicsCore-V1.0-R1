"""PhysicsCore V1.0-R5.7 Cloud→Observer viewing geometry.

R5.6.1 upgrades the R5.6 single-node line-of-sight test to a projected cloud-
volume / angular-footprint diagnostic. Forecast cloud layers are sampled at
route nodes, but clouds occupy volume between nodes. Treating each node as an
infinitesimal point can miss a foreground cloud that the observer ray crosses
between two samples (especially the 0–5 km near-observer segment).

This module remains deliberately independent of Formation:
* it never changes F_sun or Penumbra Geometry;
* it never changes Sun→CloudBase spectral RT;
* cloud fraction is only a viewing occupancy proxy, never COT;
* missing geometry/occupancy is never converted to clear sky.

R5.6.1 introduced Viewing geometry. R5.7.29 keeps that geometry frozen and
allows the independent Cloud→Observer six-band evidence branch to attach its
status without rewriting the geometric obstruction result.
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd
from .config import EARTH_RADIUS_KM
from .contracts import SIX_BAND_WAVELENGTHS_NM, FIRECLOUD_CANVAS_MIN_BASE_KM
from .shared_geometry.ray import (observer_los_height_agl_km, sample_observer_los_segment,
                                  sampled_segment_path_km)

PHOTO_TARGET_MIN_BASE_KM = FIRECLOUD_CANVAS_MIN_BASE_KM
VERTICAL_CONTINUITY_MIN_OVERLAP = 0.50

# Backward-compatible private alias; implementation lives in Shared Geometry Core.
_los_height_agl_km = observer_los_height_agl_km


def _finite(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None


def _direction_from_layer_id(layer_id: str):
    s = str(layer_id or "")
    if not s.startswith("dir"):
        return None
    try:
        return float(s.split("_d", 1)[0][3:])
    except Exception:
        return None


def _vertical_overlap_fraction(a0, a1, b0, b1) -> float:
    vals = [_finite(x) for x in (a0, a1, b0, b1)]
    if any(x is None for x in vals):
        return 0.0
    a0, a1, b0, b1 = vals
    if a1 <= a0 or b1 <= b0:
        return 0.0
    overlap = max(0.0, min(a1, b1) - max(a0, b0))
    return overlap / max(1e-9, min(a1-a0, b1-b0))


def _same_cloud_neighbor(row: pd.Series, other: pd.Series) -> bool:
    """Conservative geometric continuity test between adjacent route nodes."""
    ov = _vertical_overlap_fraction(row.get("z_base_km"), row.get("z_top_km"),
                                    other.get("z_base_km"), other.get("z_top_km"))
    return ov >= VERTICAL_CONTINUITY_MIN_OVERLAP


def _projected_support_interval(row: pd.Series, transect: pd.DataFrame) -> tuple[float, float, str, str]:
    """Infer a finite horizontal support interval around a sampled cloud node.

    Extension to a midpoint is allowed only when the nearest cloud layer at the
    adjacent route distance vertically overlaps the current layer. This prevents
    arbitrary bridging across clear gaps while fixing the R5.6 point-node miss.
    """
    d = _finite(row.get("distance_km"))
    if d is None:
        return np.nan, np.nan, "UNRESOLVED", "UNKNOWN"
    distances = sorted(set(pd.to_numeric(transect.get("distance_km"), errors="coerce").dropna().astype(float)))
    if not distances:
        return d, d, "NODE_ONLY", "LOW"
    prev_ds = [x for x in distances if x < d - 1e-9]
    next_ds = [x for x in distances if x > d + 1e-9]
    left = 0.0 if abs(d) < 1e-9 else d
    right = d
    links = []
    if prev_ds:
        pdist = max(prev_ds)
        prev = transect[pd.to_numeric(transect["distance_km"], errors="coerce").sub(pdist).abs() < 1e-8]
        if any(_same_cloud_neighbor(row, rr) for _, rr in prev.iterrows()):
            left = 0.5 * (pdist + d); links.append("LEFT")
    elif d <= 1e-9:
        left = 0.0
    if next_ds:
        ndist = min(next_ds)
        nxt = transect[pd.to_numeric(transect["distance_km"], errors="coerce").sub(ndist).abs() < 1e-8]
        if any(_same_cloud_neighbor(row, rr) for _, rr in nxt.iterrows()):
            right = 0.5 * (d + ndist); links.append("RIGHT")
    if d <= 1e-9 and next_ds and "RIGHT" in links:
        left = 0.0
    if not links:
        return d, d, "NODE_ONLY_NO_CONTINUITY", "LOW"
    return max(0.0, left), max(left, right), "ADJACENT_VERTICAL_OVERLAP_MIDPOINT_SUPPORT", "MEDIUM"


def _support_cloud_fraction_at_distance(row: pd.Series, transect: pd.DataFrame, x_km: float):
    """Interpolate CF only across vertically-continuous adjacent forecast nodes."""
    d=_finite(row.get("distance_km")); cf=_finite(row.get("cloud_fraction"))
    if d is None or cf is None: return None,"CF_MISSING"
    candidates=[]
    for _,rr in transect.iterrows():
        od=_finite(rr.get("distance_km")); ocf=_finite(rr.get("cloud_fraction"))
        if od is None or ocf is None or abs(od-d)<1e-9: continue
        if not _same_cloud_neighbor(row,rr): continue
        candidates.append((abs(od-d),od,ocf))
    if not candidates: return min(1.0,max(0.0,cf)),"NODE_CF"
    # Only nearest continuous neighbour on the side containing x is eligible.
    side=[c for c in candidates if (x_km-d)*(c[1]-d)>=-1e-12]
    if not side: return min(1.0,max(0.0,cf)),"NODE_CF"
    _,od,ocf=min(side,key=lambda q:q[0])
    if abs(od-d)<1e-9: return min(1.0,max(0.0,cf)),"NODE_CF"
    w=min(1.0,max(0.0,(x_km-d)/(od-d)))
    return min(1.0,max(0.0,(1.0-w)*cf+w*ocf)),"ADJACENT_CONTINUOUS_CF_INTERPOLATION"


def _los_intersects_projected_volume(dt: float, hs: float, support0: float, support1: float,
                                     bb: float, bt: float, earth_radius_km: float) -> bool:
    """Test LOS against a projected cloud prism over its horizontal support."""
    x0 = max(0.0, min(float(support0), dt))
    x1 = max(0.0, min(float(support1), dt))
    if x1 <= x0 + 1e-9:
        # A pure node still gets the legacy point test when it is away from the observer.
        if x0 <= 1e-9:
            return False
        h = observer_los_height_agl_km(dt, hs, x0, earth_radius_km)
        return bb - 1e-9 <= h <= bt + 1e-9
    # Curvature can make the relation slightly non-linear; dense deterministic
    # samples avoid assuming monotonicity while remaining trivial at 0–100 km.
    xs,hh = sample_observer_los_segment(dt, hs, x0, x1, sample_count=17, radius_km=earth_radius_km)
    hmin, hmax = float(np.nanmin(hh)), float(np.nanmax(hh))
    return not (hmax < bb - 1e-9 or hmin > bt + 1e-9)


def _same_cloud_values(a0, a1, b0, b1) -> bool:
    """Array-plan equivalent of _same_cloud_neighbor without pandas row access."""
    return _vertical_overlap_fraction(a0, a1, b0, b1) >= VERTICAL_CONTINUITY_MIN_OVERLAP


def _prepare_viewing_geometry_plan(transect: pd.DataFrame) -> dict:
    """Precompute immutable per-transect geometry used by all viewing targets.

    R5.7.41.3.4.8 is runtime-only.  The plan preserves the R5.6.1/R5.7.3
    semantics exactly: same nearest distinct route distances, same midpoint
    support extension rule, same vertical-overlap continuity threshold, same
    cloud-fraction neighbour eligibility and original transect row order.
    """
    n = len(transect)
    dist = pd.to_numeric(transect.get("distance_km"), errors="coerce").to_numpy(dtype=float)
    base = pd.to_numeric(transect.get("z_base_km"), errors="coerce").to_numpy(dtype=float)
    top = pd.to_numeric(transect.get("z_top_km"), errors="coerce").to_numpy(dtype=float)
    cf = pd.to_numeric(transect.get("cloud_fraction"), errors="coerce").to_numpy(dtype=float)
    ids = transect.get("layer_id", pd.Series("", index=transect.index)).astype(str).to_numpy(object)
    fd = np.isfinite(dist); fb = np.isfinite(base); ft = np.isfinite(top); fc = np.isfinite(cf)

    unique_distances = sorted(set(float(x) for x in dist[fd]))
    positions_by_distance = {
        d: np.flatnonzero(fd & (np.abs(dist - d) < 1e-8)).tolist()
        for d in unique_distances
    }
    support0 = np.full(n, np.nan, dtype=float)
    support1 = np.full(n, np.nan, dtype=float)

    # Precompute the exact legacy support interval once per layer instead of
    # rescanning/sorting a pandas transect for every target/sample encounter.
    for i in range(n):
        if not fd[i]:
            continue
        d = float(dist[i])
        prev_ds = [x for x in unique_distances if x < d - 1e-9]
        next_ds = [x for x in unique_distances if x > d + 1e-9]
        left = 0.0 if abs(d) < 1e-9 else d
        right = d
        left_link = False
        right_link = False
        ai0 = float(base[i]) if fb[i] else None
        ai1 = float(top[i]) if ft[i] else None
        if prev_ds:
            pdist = max(prev_ds)
            for j in positions_by_distance[pdist]:
                if _same_cloud_values(ai0, ai1,
                                      float(base[j]) if fb[j] else None,
                                      float(top[j]) if ft[j] else None):
                    left = 0.5 * (pdist + d)
                    left_link = True
                    break
        elif d <= 1e-9:
            left = 0.0
        if next_ds:
            ndist = min(next_ds)
            for j in positions_by_distance[ndist]:
                if _same_cloud_values(ai0, ai1,
                                      float(base[j]) if fb[j] else None,
                                      float(top[j]) if ft[j] else None):
                    right = 0.5 * (d + ndist)
                    right_link = True
                    break
        if d <= 1e-9 and right_link:
            left = 0.0
        if not (left_link or right_link):
            support0[i] = d
            support1[i] = d
        else:
            support0[i] = max(0.0, left)
            support1[i] = max(left, right)

    # Preserve the legacy neighbour list ordering and min(distance) tie rule.
    neighbours = []
    for i in range(n):
        vals = []
        if fd[i]:
            d = float(dist[i])
            ai0 = float(base[i]) if fb[i] else None
            ai1 = float(top[i]) if ft[i] else None
            for j in range(n):
                if j == i or not fd[j] or not fc[j] or abs(float(dist[j]) - d) < 1e-9:
                    continue
                if _same_cloud_values(ai0, ai1,
                                      float(base[j]) if fb[j] else None,
                                      float(top[j]) if ft[j] else None):
                    vals.append((abs(float(dist[j]) - d), float(dist[j]), float(cf[j])))
        neighbours.append(vals)

    return {
        "dist": dist, "base": base, "top": top, "cf": cf, "ids": ids,
        "fd": fd, "fb": fb, "ft": ft, "fc": fc,
        "support0": support0, "support1": support1, "neighbours": neighbours,
    }


def _planned_cf_at_distance(plan: dict, i: int, x_km: float):
    """Exact-equivalent CF interpolation using a prepared transect plan."""
    if not plan["fd"][i] or not plan["fc"][i]:
        return None, "CF_MISSING"
    d = float(plan["dist"][i]); cf = float(plan["cf"][i])
    candidates = plan["neighbours"][i]
    if not candidates:
        return min(1.0, max(0.0, cf)), "NODE_CF"
    side = [c for c in candidates if (x_km - d) * (c[1] - d) >= -1e-12]
    if not side:
        return min(1.0, max(0.0, cf)), "NODE_CF"
    _, od, ocf = min(side, key=lambda q: q[0])
    if abs(od - d) < 1e-9:
        return min(1.0, max(0.0, cf)), "NODE_CF"
    w = min(1.0, max(0.0, (x_km - d) / (od - d)))
    return min(1.0, max(0.0, (1.0 - w) * cf + w * ocf)), "ADJACENT_CONTINUOUS_CF_INTERPOLATION"


def build_viewing_path_geometry(cloud_layers: pd.DataFrame, canvases: pd.DataFrame,
                                *, earth_radius_km: float = EARTH_RADIUS_KM) -> pd.DataFrame:
    """Return target-level Cloud→Observer projected obstruction diagnostics.

    R5.7.41.3.4.8 runtime optimization:
    * immutable numeric transect plans are built once for each time/angle/direction;
    * support intervals and CF-continuity neighbours are precomputed once;
    * target blocker selection uses numeric arrays instead of repeated DataFrame scans;
    * each 17-point curved-Earth LOS sample is reused for both volume-intersection
      qualification and crossing-position CF interpolation.

    No science semantics, sample counts, thresholds or Missing behaviour change.
    """
    cols = [
        "time", "solar_altitude_deg", "canvas_id", "cloud_layer_id",
        "direction_offset_deg", "target_distance_km", "target_base_km", "target_top_km",
        "view_target_role", "photographic_target_eligible",
        "view_sample_count", "blocked_view_sample_count", "intervening_blocker_count",
        "low_cloud_blocker_count", "mid_cloud_blocker_count", "high_cloud_blocker_count",
        "projected_support_blocker_count", "view_obstruction_fraction_proxy",
        "view_geometry_state", "viewing_geometry_method", "viewing_path_spectral_status",
        "viewing_confidence", "blocker_layer_ids", "blocker_support_intervals_km", "note",
    ]
    if cloud_layers is None or canvases is None or cloud_layers.empty or canvases.empty:
        return pd.DataFrame(columns=cols)
    layers = cloud_layers.copy(); cvs = canvases.copy()
    if "layer_id" not in layers or "cloud_layer_id" not in cvs:
        return pd.DataFrame(columns=cols)

    lk = layers[[c for c in ["layer_id", "direction_offset_deg", "distance_km", "z_base_km", "z_top_km",
                              "cloud_fraction", "cloud_fraction_state", "geometry_confidence", "time",
                              "solar_altitude_deg"] if c in layers.columns]].copy()
    left_on = ["cloud_layer_id"]; right_on = ["layer_id"]
    for k in ["time", "solar_altitude_deg"]:
        if k in cvs.columns and k in lk.columns:
            left_on.append(k); right_on.append(k)
    cvs = cvs.merge(lk, left_on=left_on, right_on=right_on, how="left", suffixes=("", "_layer"))

    def _gkey(timev, angv, dirv):
        a = _finite(angv); d = _finite(dirv)
        return (str(timev), None if a is None else round(a, 8), None if d is None else round(d, 8))

    plan_cache = {}
    for key, g in layers.groupby([
        layers.get("time", pd.Series("", index=layers.index)).astype(str),
        pd.to_numeric(layers.get("solar_altitude_deg"), errors="coerce").round(8),
        pd.to_numeric(layers.get("direction_offset_deg"), errors="coerce").round(8),
    ], dropna=False, sort=False):
        pkey = (str(key[0]), None if pd.isna(key[1]) else float(key[1]),
                None if pd.isna(key[2]) else float(key[2]))
        plan_cache[pkey] = _prepare_viewing_geometry_plan(g)

    rows = []
    fractions17 = np.linspace(0.0, 1.0, 17)
    r = float(earth_radius_km)
    for _, target in cvs.iterrows():
        canvas_id = str(target.get("canvas_id", "")); layer_id = str(target.get("cloud_layer_id", ""))
        dt = _finite(target.get("distance_km")); zb = _finite(target.get("z_base_km")); zt = _finite(target.get("z_top_km")); direction = _finite(target.get("direction_offset_deg"))
        if direction is None:
            direction = _direction_from_layer_id(layer_id)
        tval = target.get("time_layer", target.get("time")); aval = target.get("solar_altitude_deg_layer", target.get("solar_altitude_deg"))
        photo_eligible = bool(zb is not None and zb >= PHOTO_TARGET_MIN_BASE_KM)
        role = "FIRECLOUD_CANVAS_TARGET" if photo_eligible else "FOREGROUND_LOW_CLOUD_OBSTRUCTION_ONLY"
        base_row = {"time": tval, "solar_altitude_deg": aval, "canvas_id": canvas_id, "cloud_layer_id": layer_id,
                    "direction_offset_deg": direction, "target_distance_km": dt, "target_base_km": zb, "target_top_km": zt,
                    "view_target_role": role, "photographic_target_eligible": photo_eligible}
        if dt is None or zb is None or zt is None or direction is None or dt <= 0.0 or zt <= zb:
            rows.append({**base_row, "view_sample_count": 0, "blocked_view_sample_count": 0, "intervening_blocker_count": 0,
                         "low_cloud_blocker_count": 0, "mid_cloud_blocker_count": 0, "high_cloud_blocker_count": 0,
                         "projected_support_blocker_count": 0, "view_obstruction_fraction_proxy": np.nan,
                         "view_geometry_state": "VIEW_GEOMETRY_NOT_EVALUATED_LOCAL_TARGET", "viewing_geometry_method": "PROJECTED_VOLUME_SUPPORT",
                         "viewing_path_spectral_status": "VIEW_SPECTRAL_PENDING", "viewing_confidence": "LOW",
                         "blocker_layer_ids": "", "blocker_support_intervals_km": "",
                         "note": "FORMATION_UNCHANGED;VIEWING_ONLY;LOCAL_OR_INCOMPLETE_TARGET"})
            continue

        key = _gkey(tval, aval, direction)
        plan = plan_cache.get(key)
        if plan is None:
            # Preserve the legacy unusual-schema fallback exactly, then prepare
            # the same immutable numeric plan for that filtered transect.
            cand_df = layers.copy()
            if "solar_altitude_deg" in cand_df.columns and pd.notna(aval):
                cand_df = cand_df[pd.to_numeric(cand_df["solar_altitude_deg"], errors="coerce").sub(float(aval)).abs() < 1e-8]
            cand_df = cand_df[pd.to_numeric(cand_df.get("direction_offset_deg"), errors="coerce").sub(float(direction)).abs() < 1e-8]
            plan = _prepare_viewing_geometry_plan(cand_df)
            plan_cache[key] = plan

        candidate_mask = plan["fd"] & (plan["dist"] < dt - 1e-9) & (plan["ids"] != layer_id)
        candidate_indices = np.flatnonzero(candidate_mask)
        sample_occ = []; blockers = set(); supports = {}; low = mid = high = 0
        class_seen = set(); support_blockers = set(); unknown_occ = False

        for hs in np.linspace(zb, zt, 7).tolist():
            occ_terms = []
            ci = candidate_indices
            if ci.size:
                db = plan["dist"][ci]; bb = plan["base"][ci]; bt = plan["top"][ci]
                s0 = plan["support0"][ci]; s1 = plan["support1"][ci]
                valid = np.isfinite(db) & np.isfinite(bb) & np.isfinite(bt) & (bt > bb) & np.isfinite(s0) & np.isfinite(s1)
                vis_ci = ci[valid]; db = db[valid]; bb = bb[valid]; bt = bt[valid]; s0 = s0[valid]; s1 = s1[valid]
                if vis_ci.size:
                    x0 = np.maximum(0.0, np.minimum(s0, dt)); x1 = np.maximum(0.0, np.minimum(s1, dt))
                    span = x1 > x0 + 1e-9
                    hit = np.zeros(vis_ci.size, dtype=bool)
                    xcross = db.copy()

                    node_positions = np.flatnonzero((~span) & (x0 > 1e-9))
                    if node_positions.size:
                        h = (np.clip(x0[node_positions], 0.0, dt) / dt) * (float(hs) - dt * dt / (2.0 * r)) \
                            + np.clip(x0[node_positions], 0.0, dt) ** 2 / (2.0 * r)
                        hit[node_positions] = (h >= bb[node_positions] - 1e-9) & (h <= bt[node_positions] + 1e-9)

                    span_positions = np.flatnonzero(span)
                    if span_positions.size:
                        # np.linspace with vector start/stop preserves the same
                        # 17 deterministic positions as the legacy sampler.
                        xs = np.linspace(x0[span_positions], x1[span_positions], 17, axis=1)
                        dclip = np.clip(xs, 0.0, dt)
                        hh = (dclip / dt) * (float(hs) - dt * dt / (2.0 * r)) + (dclip * dclip) / (2.0 * r)
                        hmin = np.nanmin(hh, axis=1); hmax = np.nanmax(hh, axis=1)
                        ihit = ~((hmax < bb[span_positions] - 1e-9) | (hmin > bt[span_positions] + 1e-9))
                        hit[span_positions] = ihit
                        if np.any(ihit):
                            hit_span_positions = span_positions[ihit]
                            hhh = hh[ihit]; xss = xs[ihit]
                            inside = np.isfinite(hhh) & (hhh >= bb[hit_span_positions, None]) & (hhh <= bt[hit_span_positions, None])
                            counts = inside.sum(axis=1)
                            crossing = np.divide((xss * inside).sum(axis=1), counts,
                                                 out=db[hit_span_positions].copy(), where=counts > 0)
                            xcross[hit_span_positions] = crossing

                    for loc in np.flatnonzero(hit):
                        i = int(vis_ci[loc]); bid = str(plan["ids"][i])
                        blockers.add(bid); support_blockers.add(bid)
                        supports[bid] = f"{plan['support0'][i]:.3f}-{plan['support1'][i]:.3f}"
                        cf, _ = _planned_cf_at_distance(plan, i, float(xcross[loc]))
                        if cf is None:
                            unknown_occ = True
                            continue
                        occ_terms.append(cf)
                        if bid not in class_seen:
                            class_seen.add(bid); midh = 0.5 * (float(plan["base"][i]) + float(plan["top"][i]))
                            if midh < 2.0: low += 1
                            elif midh < 6.0: mid += 1
                            else: high += 1
            if occ_terms:
                clear_prob = 1.0
                for cf in occ_terms:
                    clear_prob *= (1.0 - cf)
                sample_occ.append(1.0 - clear_prob)
            elif unknown_occ:
                sample_occ.append(np.nan)
            else:
                sample_occ.append(0.0)

        finite_occ = [float(v) for v in sample_occ if _finite(v) is not None]
        obstruction = float(np.mean(finite_occ)) if finite_occ else np.nan
        blocked_samples = int(sum((_finite(v) or 0.0) >= 0.10 for v in sample_occ if _finite(v) is not None))
        if unknown_occ and not finite_occ: state = "VIEW_GEOMETRY_INTERSECTION_OCCUPANCY_UNKNOWN"; conf = "LOW"
        elif not math.isfinite(obstruction): state = "VIEW_GEOMETRY_UNKNOWN"; conf = "LOW"
        elif obstruction >= 0.70: state = "VIEW_SEVERE_OBSTRUCTION"; conf = "MEDIUM"
        elif obstruction >= 0.10: state = "VIEW_PARTIAL_OBSTRUCTION"; conf = "MEDIUM"
        elif blockers and obstruction > 0.0: state = "VIEW_MINOR_OBSTRUCTION"; conf = "MEDIUM"
        else: state = "VIEW_GEOMETRICALLY_CLEAR"; conf = "MEDIUM"
        rows.append({**base_row, "view_sample_count": 7, "blocked_view_sample_count": blocked_samples,
                     "intervening_blocker_count": len(blockers), "low_cloud_blocker_count": low, "mid_cloud_blocker_count": mid,
                     "high_cloud_blocker_count": high, "projected_support_blocker_count": len(support_blockers),
                     "view_obstruction_fraction_proxy": obstruction, "view_geometry_state": state,
                     "viewing_geometry_method": "ANGULAR_FOOTPRINT_PROJECTED_VOLUME_WITH_CONTINUOUS_CF_CACHED",
                     "viewing_path_spectral_status": "VIEW_SPECTRAL_PENDING", "viewing_confidence": conf,
                     "blocker_layer_ids": ";".join(str(x) for x in sorted(blockers, key=str)),
                     "blocker_support_intervals_km": ";".join(f"{k}:{supports[k]}" for k in sorted(supports)),
                     "note": "FORMATION_UNCHANGED;CLOUD_TO_OBSERVER_PROJECTED_VOLUME;CF_OCCUPANCY_PROXY_NOT_COT;MISSING_OCCUPANCY_NOT_CLEAR;UNCALIBRATED_THRESHOLDS;R573_CACHED_TRANSECT"})
    return pd.DataFrame(rows, columns=cols)

def summarize_viewing_path(viewing: pd.DataFrame, spectral_summary: pd.DataFrame | None = None) -> pd.DataFrame:
    spectral_cols=[
        "viewing_rt_completeness","full_viewing_rt_target_count","partial_viewing_rt_target_count","unresolved_viewing_rt_target_count",
        *[f"mean_view_transmission_{int(w)}nm" for w in SIX_BAND_WAVELENGTHS_NM],
        *[f"viewing_rt_completeness_{int(w)}nm" for w in SIX_BAND_WAVELENGTHS_NM],
        "viewing_missing_components","viewing_spectral_contract",
    ]
    cols=["time","solar_altitude_deg","target_count","photographic_target_count","evaluated_target_count",
          "clear_target_count","minor_obstruction_target_count","partial_obstruction_target_count","severe_obstruction_target_count",
          "mean_view_obstruction_fraction_proxy","max_view_obstruction_fraction_proxy","viewing_state",
          "viewing_path_spectral_status",*spectral_cols,"viewing_summary_scope","note"]
    if viewing is None or viewing.empty: return pd.DataFrame(columns=cols)
    spectral_by_key={}
    if spectral_summary is not None and not spectral_summary.empty:
        for _,sr in spectral_summary.iterrows():
            av=_finite(sr.get("solar_altitude_deg"))
            spectral_by_key[(str(sr.get("time")),None if av is None else round(av,8))]=sr
    rows=[]; keys=[k for k in ["time","solar_altitude_deg"] if k in viewing.columns]
    groups=viewing.groupby(keys,dropna=False) if keys else [((),viewing)]
    for key,g0 in groups:
        eligible = g0.get("photographic_target_eligible",pd.Series(False,index=g0.index)).fillna(False).astype(bool)
        g=g0[eligible].copy()
        # Low foreground clouds remain blockers but must not themselves dominate the photography summary.
        if g.empty:
            g=g0.iloc[0:0].copy()
        states=g.get("view_geometry_state",pd.Series(dtype=str)).astype(str)
        vals=pd.to_numeric(g.get("view_obstruction_fraction_proxy"),errors="coerce") if not g.empty else pd.Series(dtype=float)
        evaluated=vals.notna(); mean=float(vals[evaluated].mean()) if evaluated.any() else np.nan; mx=float(vals[evaluated].max()) if evaluated.any() else np.nan
        unknown_intersection=states.isin(["VIEW_GEOMETRY_INTERSECTION_OCCUPANCY_UNKNOWN","VIEW_GEOMETRY_UNKNOWN"]).any()
        if not evaluated.any(): state="VIEWING_UNKNOWN"
        elif mean>=0.70: state="VIEWING_SEVERELY_OBSCURED"
        elif mean>=0.10: state="VIEWING_PARTIALLY_OBSCURED"
        elif unknown_intersection: state="VIEWING_PARTIAL_DATA"
        elif mean>0.0: state="VIEWING_MINOR_OBSTRUCTION"
        else: state="VIEWING_GEOMETRY_GOOD"
        valskey=key if isinstance(key,tuple) else (key,)
        group_values=dict(zip(keys,valskey)) if keys else {}
        av=_finite(group_values.get("solar_altitude_deg"))
        srec=spectral_by_key.get((str(group_values.get("time")),None if av is None else round(av,8)))
        row={"target_count":len(g0),"photographic_target_count":len(g),"evaluated_target_count":int(evaluated.sum()),
             "clear_target_count":int((states=="VIEW_GEOMETRICALLY_CLEAR").sum()),
             "minor_obstruction_target_count":int((states=="VIEW_MINOR_OBSTRUCTION").sum()),
             "partial_obstruction_target_count":int((states=="VIEW_PARTIAL_OBSTRUCTION").sum()),
             "severe_obstruction_target_count":int((states=="VIEW_SEVERE_OBSTRUCTION").sum()),
             "mean_view_obstruction_fraction_proxy":mean,"max_view_obstruction_fraction_proxy":mx,"viewing_state":state,
             "viewing_path_spectral_status":str(srec.get("viewing_spectral_state")) if srec is not None else "VIEW_SPECTRAL_UNRESOLVED",
             "viewing_summary_scope":"PHOTOGRAPHIC_TARGETS_BASE_GE_2KM;FOREGROUND_LOW_CLOUDS_AS_BLOCKERS_ONLY",
             "note":"FORMATION_INDEPENDENT;ANGULAR_FOOTPRINT_PROJECTED_VOLUME_TIER2;LOW_CLOUD_TARGETS_EXCLUDED_FROM_SUMMARY;R5729_SIX_BAND_VIEWING_STATUS_ATTACHED"}
        for c in spectral_cols:
            row[c]=srec.get(c,np.nan) if srec is not None else np.nan
        row.update(group_values)
        rows.append(row)
    return pd.DataFrame(rows,columns=cols)
