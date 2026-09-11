"""R5.7.40 Canvas optical vertical-conflict qualification.

Evidence-only diagnostic that combines the primary GFS pgrb2 pressure-level
cloud-fraction/hydrometeor column with the secondary-parameter pgrb2b
intermediate-level native hydrometeor column.  It never creates COT, never
changes Canvas membership, and never changes Formation.
"""
from __future__ import annotations

import math
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from .cloud_scene import ProviderCloudGeometryConfig, native_level_evidence_consistency
from .native_cloud import NATIVE_CONDENSATE_THRESHOLD_KGKG, native_levels_from_row
from .providers.gfs_native import DEFAULT_PRESSURE_LEVELS_HPA, NATIVE_PROVIDER_NAME
from .providers.gfs_canvas_optical_probe import PROVIDER_NAME as PGRB2B_PROVIDER, SUPPLEMENT_PRESSURE_LEVELS_HPA

QUALIFICATION_CONTRACT = (
    "DIRECT_NATIVE_GFS_PGRB2_PLUS_PGRB2B_VERTICAL_CONTEXT_ONLY;"
    "NO_COT_PROMOTION;NO_FORMATION_PROMOTION;NO_RH_CF_TO_CONDENSATE"
)

QUALIFICATION_STATES = {
    "PRIMARY_NATIVE_CONDENSATE_WITH_LOW_CF_CONFLICT",
    "ISOLATED_PRIMARY_CF_SPIKE_HYDROMETEOR_UNSUPPORTED",
    "INTERMEDIATE_NATIVE_CONDENSATE_SUPPORT_PRESENT",
    "ADJACENT_PRIMARY_NATIVE_CONDENSATE_SUPPORT_PRESENT",
    "PRIMARY_CF_SIGNAL_WITH_ZERO_INTERMEDIATE_HYDROMETEORS",
    "VERTICAL_CONTEXT_INCOMPLETE",
}


def _finite(v) -> bool:
    try:
        return bool(math.isfinite(float(v)))
    except Exception:
        return False


def _q_state(ql, qi) -> tuple[str, float]:
    if not (_finite(ql) and _finite(qi)):
        return "MISSING", float("nan")
    qt = max(0.0, float(ql)) + max(0.0, float(qi))
    return ("POSITIVE" if qt >= NATIVE_CONDENSATE_THRESHOLD_KGKG else "ZERO"), qt


def _cf_value(v):
    if not _finite(v):
        return float("nan")
    f = float(v)
    if f > 1.0 + 1e-9:
        f /= 100.0
    return max(0.0, min(1.0, f))


def _row_key(row: Mapping) -> tuple[float, float] | None:
    try:
        return round(float(row["direction_offset_deg"]), 6), round(float(row["distance_km"]), 6)
    except Exception:
        return None


def _supplement_level(row: Mapping | None, pressure_hpa: float, surface_elevation_m: float) -> dict:
    p = int(round(float(pressure_hpa)))
    if row is None:
        return {"pressure_hpa": float(p), "available": False, "altitude_agl_km": np.nan,
                "ql": np.nan, "qi": np.nan, "qt": np.nan, "q_state": "MISSING"}
    gh = row.get(f"geopotential_height_m_{p}hPa", np.nan)
    ql = row.get(f"cloud_liquid_water_kgkg_{p}hPa", np.nan)
    qi = row.get(f"cloud_ice_water_kgkg_{p}hPa", np.nan)
    state, qt = _q_state(ql, qi)
    z = (float(gh) - float(surface_elevation_m)) / 1000.0 if _finite(gh) and _finite(surface_elevation_m) else np.nan
    return {
        "pressure_hpa": float(p), "available": bool(_finite(z)), "altitude_agl_km": z,
        "ql": float(ql) if _finite(ql) else np.nan,
        "qi": float(qi) if _finite(qi) else np.nan,
        "qt": qt, "q_state": state,
    }


def _primary_level_context(level: Mapping | None) -> dict:
    if level is None:
        return {"pressure_hpa": np.nan, "altitude_agl_km": np.nan, "cloud_fraction": np.nan,
                "ql": np.nan, "qi": np.nan, "qt": np.nan, "q_state": "MISSING",
                "evidence_consistency": "MISSING"}
    qstate, qt = _q_state(level.get("cloud_liquid_water_kgkg"), level.get("cloud_ice_water_kgkg"))
    return {
        "pressure_hpa": float(level.get("pressure_hpa")) if _finite(level.get("pressure_hpa")) else np.nan,
        "altitude_agl_km": float(level.get("altitude_agl_km")) if _finite(level.get("altitude_agl_km")) else np.nan,
        "cloud_fraction": _cf_value(level.get("cloud_fraction")),
        "ql": float(level.get("cloud_liquid_water_kgkg")) if _finite(level.get("cloud_liquid_water_kgkg")) else np.nan,
        "qi": float(level.get("cloud_ice_water_kgkg")) if _finite(level.get("cloud_ice_water_kgkg")) else np.nan,
        "qt": qt, "q_state": qstate,
        "evidence_consistency": native_level_evidence_consistency(level, ProviderCloudGeometryConfig()),
    }


def _nearest_supplement_between(primary_p: float, neighbor_p: float | None) -> float | None:
    if neighbor_p is None or not _finite(neighbor_p):
        return None
    lo, hi = sorted((float(primary_p), float(neighbor_p)))
    candidates = [float(p) for p in SUPPLEMENT_PRESSURE_LEVELS_HPA if lo < float(p) < hi]
    if not candidates:
        return None
    return min(candidates, key=lambda p: abs(p - float(primary_p)))


def build_canvas_vertical_conflict_qualification(
    scene,
    canvases,
    primary_route: pd.DataFrame,
    pgrb2b_route: pd.DataFrame,
    *,
    valid_time=None,
    solar_altitude_deg=None,
    primary_pressure_levels_hpa: Sequence[int] = DEFAULT_PRESSURE_LEVELS_HPA,
) -> pd.DataFrame:
    """Classify native vertical context for primary CF/condensate conflicts.

    All primary pgrb2 levels whose direct evidence consistency is a
    direct cloud-fraction/native-condensate conflict are qualified. This includes
    ``CF_CLOUD_CONDENSATE_ZERO`` and ``CONDENSATE_CLOUD_CF_LOW``. The latter is
    preserved as its own conflict type and is never reinterpreted as a CF spike.
    The immediate primary levels above/below and the pgrb2b intermediate
    hydrometeor levels between them are audited. pgrb2b cloud fraction is
    intentionally not used because the pressure-level secondary-parameter
    inventory does not supply a TCDC profile.
    """
    if primary_route is None or primary_route.empty:
        return pd.DataFrame()

    primary_by_key = {}
    for _, r in primary_route.iterrows():
        k = _row_key(r)
        if k is not None:
            primary_by_key[k] = r
    supplement_by_key = {}
    if isinstance(pgrb2b_route, pd.DataFrame) and not pgrb2b_route.empty:
        for _, r in pgrb2b_route.iterrows():
            k = _row_key(r)
            if k is not None:
                supplement_by_key[k] = r

    layers = {str(x.layer_id): x for x in getattr(scene, "layers", ())}
    rows = []
    cfg = ProviderCloudGeometryConfig()

    for canvas in canvases:
        layer = layers.get(str(canvas.cloud_layer_id))
        if layer is None:
            continue
        key = (round(float(layer.direction_offset_deg), 6), round(float(layer.distance_km), 6))
        prow = primary_by_key.get(key)
        if prow is None:
            continue
        levels = native_levels_from_row(prow, primary_pressure_levels_hpa)
        if not levels:
            continue
        levels = sorted(levels, key=lambda x: float(x["altitude_agl_km"]))
        conflict_indices = []
        for idx, lev in enumerate(levels):
            z = float(lev["altitude_agl_km"])
            if z < float(layer.z_base_km) - 1e-9 or z > float(layer.z_top_km) + 1e-9:
                continue
            if native_level_evidence_consistency(lev, cfg) in {
                "CF_CLOUD_CONDENSATE_ZERO", "CONDENSATE_CLOUD_CF_LOW"
            }:
                conflict_indices.append(idx)
        if not conflict_indices:
            continue

        srow = supplement_by_key.get(key)
        elev = prow.get("model_surface_elevation_m", np.nan)
        if not _finite(elev) and srow is not None:
            elev = srow.get("surface_elevation_m", np.nan)
        if not _finite(elev):
            elev = 0.0

        for idx in conflict_indices:
            primary = _primary_level_context(levels[idx])
            below_main = _primary_level_context(levels[idx - 1] if idx > 0 else None)
            above_main = _primary_level_context(levels[idx + 1] if idx + 1 < len(levels) else None)
            # levels are sorted by altitude, so below_main has larger pressure and
            # above_main has smaller pressure under a normal atmospheric column.
            below_supp_p = _nearest_supplement_between(primary["pressure_hpa"], below_main["pressure_hpa"])
            above_supp_p = _nearest_supplement_between(primary["pressure_hpa"], above_main["pressure_hpa"])
            below_supp = _supplement_level(srow, below_supp_p, elev) if below_supp_p is not None else _supplement_level(None, primary["pressure_hpa"], elev)
            above_supp = _supplement_level(srow, above_supp_p, elev) if above_supp_p is not None else _supplement_level(None, primary["pressure_hpa"], elev)

            main_neighbors = (below_main, above_main)
            supp_neighbors = (below_supp, above_supp)
            main_complete = all(_finite(x["pressure_hpa"]) and x["q_state"] != "MISSING" and _finite(x["cloud_fraction"]) for x in main_neighbors)
            supp_complete = all(x["available"] and x["q_state"] != "MISSING" for x in supp_neighbors)
            main_positive = any(x["q_state"] == "POSITIVE" for x in main_neighbors)
            supp_positive = any(x["q_state"] == "POSITIVE" for x in supp_neighbors)
            main_clear_zero = all(
                _finite(x["cloud_fraction"]) and float(x["cloud_fraction"]) <= cfg.clear_fraction_max + 1e-12 and x["q_state"] == "ZERO"
                for x in main_neighbors
            )
            supp_zero = all(x["q_state"] == "ZERO" for x in supp_neighbors)

            primary_conflict_type = str(primary["evidence_consistency"])
            if primary_conflict_type == "CONDENSATE_CLOUD_CF_LOW":
                state = "PRIMARY_NATIVE_CONDENSATE_WITH_LOW_CF_CONFLICT"
            elif main_positive:
                state = "ADJACENT_PRIMARY_NATIVE_CONDENSATE_SUPPORT_PRESENT"
            elif supp_positive:
                state = "INTERMEDIATE_NATIVE_CONDENSATE_SUPPORT_PRESENT"
            elif not (main_complete and supp_complete):
                state = "VERTICAL_CONTEXT_INCOMPLETE"
            elif main_clear_zero and supp_zero:
                state = "ISOLATED_PRIMARY_CF_SPIKE_HYDROMETEOR_UNSUPPORTED"
            else:
                state = "PRIMARY_CF_SIGNAL_WITH_ZERO_INTERMEDIATE_HYDROMETEORS"

            rows.append({
                "time": valid_time,
                "solar_altitude_deg": float(solar_altitude_deg) if solar_altitude_deg is not None else np.nan,
                "canvas_id": canvas.canvas_id,
                "cloud_layer_id": canvas.cloud_layer_id,
                "direction_offset_deg": float(layer.direction_offset_deg),
                "distance_km": float(layer.distance_km),
                "target_z_base_km": float(layer.z_base_km),
                "target_z_top_km": float(layer.z_top_km),
                "primary_conflict_pressure_hpa": primary["pressure_hpa"],
                "primary_conflict_altitude_agl_km": primary["altitude_agl_km"],
                "primary_cloud_fraction": primary["cloud_fraction"],
                "primary_cloud_liquid_water_kgkg": primary["ql"],
                "primary_cloud_ice_water_kgkg": primary["qi"],
                "primary_total_condensate_kgkg": primary["qt"],
                "primary_evidence_consistency": primary["evidence_consistency"],
                "primary_conflict_type": primary_conflict_type,
                "below_primary_pressure_hpa": below_main["pressure_hpa"],
                "below_primary_altitude_agl_km": below_main["altitude_agl_km"],
                "below_primary_cloud_fraction": below_main["cloud_fraction"],
                "below_primary_total_condensate_kgkg": below_main["qt"],
                "below_primary_condensate_state": below_main["q_state"],
                "above_primary_pressure_hpa": above_main["pressure_hpa"],
                "above_primary_altitude_agl_km": above_main["altitude_agl_km"],
                "above_primary_cloud_fraction": above_main["cloud_fraction"],
                "above_primary_total_condensate_kgkg": above_main["qt"],
                "above_primary_condensate_state": above_main["q_state"],
                "below_supplement_pressure_hpa": below_supp["pressure_hpa"] if below_supp_p is not None else np.nan,
                "below_supplement_altitude_agl_km": below_supp["altitude_agl_km"],
                "below_supplement_total_condensate_kgkg": below_supp["qt"],
                "below_supplement_condensate_state": below_supp["q_state"],
                "below_supplement_inside_target_envelope": bool(_finite(below_supp["altitude_agl_km"]) and float(layer.z_base_km) <= float(below_supp["altitude_agl_km"]) <= float(layer.z_top_km)),
                "above_supplement_pressure_hpa": above_supp["pressure_hpa"] if above_supp_p is not None else np.nan,
                "above_supplement_altitude_agl_km": above_supp["altitude_agl_km"],
                "above_supplement_total_condensate_kgkg": above_supp["qt"],
                "above_supplement_condensate_state": above_supp["q_state"],
                "above_supplement_inside_target_envelope": bool(_finite(above_supp["altitude_agl_km"]) and float(layer.z_base_km) <= float(above_supp["altitude_agl_km"]) <= float(layer.z_top_km)),
                "primary_neighbor_context_complete": bool(main_complete),
                "supplement_hydrometeor_bracket_complete": bool(supp_complete),
                "vertical_conflict_qualification": state,
                "qualification_confidence": "FULL" if main_complete and supp_complete else "PARTIAL",
                "primary_source": NATIVE_PROVIDER_NAME,
                "supplement_source": PGRB2B_PROVIDER,
                "supplement_cloud_fraction_used": False,
                "rh_used_to_infer_condensate": False,
                "cot_promotion_allowed": False,
                "formation_promotion_allowed": False,
                "qualification_contract": QUALIFICATION_CONTRACT,
            })
    return pd.DataFrame(rows)


def summarize_vertical_conflict_qualification(table: pd.DataFrame) -> pd.DataFrame:
    if table is None or table.empty:
        return pd.DataFrame()
    rows = []
    for (tm, ang), g in table.groupby(["time", "solar_altitude_deg"], dropna=False, sort=False):
        state = g["vertical_conflict_qualification"].astype(str)
        rows.append({
            "time": tm,
            "solar_altitude_deg": ang,
            "qualified_conflict_row_count": int(len(g)),
            "qualified_canvas_count": int(g["canvas_id"].astype(str).nunique()),
            "low_cf_native_condensate_conflict_count": int(state.eq("PRIMARY_NATIVE_CONDENSATE_WITH_LOW_CF_CONFLICT").sum()),
            "isolated_primary_cf_spike_count": int(state.eq("ISOLATED_PRIMARY_CF_SPIKE_HYDROMETEOR_UNSUPPORTED").sum()),
            "intermediate_native_condensate_support_count": int(state.eq("INTERMEDIATE_NATIVE_CONDENSATE_SUPPORT_PRESENT").sum()),
            "adjacent_primary_native_condensate_support_count": int(state.eq("ADJACENT_PRIMARY_NATIVE_CONDENSATE_SUPPORT_PRESENT").sum()),
            "zero_intermediate_hydrometeor_count": int(state.eq("PRIMARY_CF_SIGNAL_WITH_ZERO_INTERMEDIATE_HYDROMETEORS").sum()),
            "vertical_context_incomplete_count": int(state.eq("VERTICAL_CONTEXT_INCOMPLETE").sum()),
            "qualification_contract": QUALIFICATION_CONTRACT,
        })
    return pd.DataFrame(rows)
