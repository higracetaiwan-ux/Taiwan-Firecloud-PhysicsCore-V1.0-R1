"""R5.7.41.1 COT diagnostic reconciliation.

Explains, without changing production science, why the legacy target
``direct_native_cot`` and the R5.7.41 target-envelope
``cot_estimate_assumed_reff`` can differ even when both are derived from the
same native GFS condensate family.

The reconciliation keeps four concepts separate:

1. legacy direct COT: primary pgrb2 only, cloud-fraction-scaled extinction,
   plus half-cell edge support outside the multi-level target centre envelope;
2. primary exact-envelope CF-scaled COT: same primary levels, but clipped to
   the declared target Cloud Base--Top;
3. primary exact-envelope in-cloud COT: no CF scaling, because cloud fraction
   is horizontal occupancy rather than in-cloud optical thickness;
4. combined exact-envelope in-cloud COT: primary pgrb2 + pgrb2b intermediate
   hydrometeor samples, no CF scaling. This is the R5.7.41 diagnostic estimate.

This module is diagnostic-only. It does not replace target COT and cannot
promote Formation.
"""
from __future__ import annotations

import math
from typing import Mapping

import numpy as np
import pandas as pd

from .cloud_optics import (
    DEFAULT_ICE_REFF_UM,
    DEFAULT_LIQUID_REFF_UM,
    condensate_extinction_m1,
)
from .native_cloud import R_D

RECONCILIATION_CONTRACT = (
    "LEGACY_GRID_CELL_MEAN_CF_SCALED_VS_TARGET_INCLOUD_EXACT_ENVELOPE;"
    "PRIMARY_PGRB2_PLUS_PGRB2B_DIAGNOSTIC;NO_CF_RH_TO_NEW_COT;"
    "NO_TARGET_COT_REPLACEMENT;NO_COT_PROMOTION;NO_FORMATION_PROMOTION"
)

RECONCILIATION_COLUMNS = [
    "time", "solar_altitude_deg", "canvas_id", "cloud_layer_id",
    "direction_offset_deg", "distance_km", "target_z_base_km", "target_z_top_km",
    "legacy_direct_native_cot", "overlap_cot_estimate_assumed_reff",
    "legacy_primary_exact_envelope_cf_scaled_cot",
    "primary_exact_envelope_incloud_cot",
    "legacy_half_cell_edge_support_delta_cot",
    "cloud_fraction_semantics_delta_cot",
    "pgrb2b_vertical_resolution_delta_cot",
    "observed_new_minus_legacy_delta_cot",
    "explained_new_minus_legacy_delta_cot",
    "reconciliation_residual_cot", "cot_ratio_overlap_to_legacy",
    "primary_inside_sample_count", "combined_inside_sample_count",
    "legacy_reconstruction_matches", "reconciliation_state",
    "legacy_cot_semantics", "overlap_cot_semantics",
    "recommended_future_target_cot_semantics",
    "production_target_cot_replaced", "cot_promotion_allowed",
    "formation_promotion_allowed", "cloud_fraction_used_for_new_cot",
    "rh_used_to_infer_condensate", "reconciliation_contract",
]

SUMMARY_COLUMNS = [
    "solar_altitude_deg", "comparable_count", "explained_count",
    "legacy_reconstruction_match_count", "mean_legacy_direct_native_cot",
    "mean_overlap_cot_estimate_assumed_reff", "mean_overlap_to_legacy_ratio",
    "mean_legacy_half_cell_edge_support_delta_cot",
    "mean_cloud_fraction_semantics_delta_cot",
    "mean_pgrb2b_vertical_resolution_delta_cot",
    "max_abs_reconciliation_residual_cot", "production_target_cot_replaced_count",
    "cot_promotion_allowed_count", "formation_promotion_allowed_count",
    "closure_state", "reconciliation_contract",
]


def _finite(v) -> bool:
    try:
        return bool(math.isfinite(float(v)))
    except Exception:
        return False


def _beta_from_sample(row: Mapping, *, use_sample_cloud_fraction: bool) -> float:
    p = row.get("sample_pressure_hpa", np.nan)
    t = row.get("sample_temperature_k", np.nan)
    ql = row.get("sample_cloud_liquid_water_kgkg", np.nan)
    qi = row.get("sample_cloud_ice_water_kgkg", np.nan)
    if not all(_finite(v) for v in (p, t, ql, qi)) or float(p) <= 0 or float(t) <= 0:
        return np.nan
    rho = (float(p) * 100.0) / (R_D * float(t))
    lwc_gm3 = max(0.0, float(ql)) * rho * 1000.0
    iwc_gm3 = max(0.0, float(qi)) * rho * 1000.0
    cf = row.get("sample_cloud_fraction", np.nan) if use_sample_cloud_fraction else 1.0
    ext = condensate_extinction_m1(
        lwc_gm3, iwc_gm3, cf,
        liquid_reff_um=DEFAULT_LIQUID_REFF_UM,
        ice_reff_um=DEFAULT_ICE_REFF_UM,
    )
    beta = ext.get("total_extinction_m1", np.nan)
    return float(beta) if _finite(beta) else np.nan


def _integrate_exact_envelope(samples: pd.DataFrame, *, use_sample_cloud_fraction: bool,
                              z_base_km: float, z_top_km: float) -> float:
    if samples is None or samples.empty:
        return np.nan
    q = samples.copy()
    q["_z"] = pd.to_numeric(q["sample_altitude_agl_km"], errors="coerce")
    q = q[q["_z"].notna()].sort_values("_z")
    if len(q) < 1:
        return np.nan
    z = q["_z"].astype(float).to_numpy()
    b = np.asarray([
        _beta_from_sample(r, use_sample_cloud_fraction=use_sample_cloud_fraction)
        for r in q.to_dict("records")
    ], dtype=float)
    if not np.isfinite(b).all():
        return np.nan
    if len(q) == 1:
        return max(0.0, float(b[0]) * max(0.0, float(z_top_km) - float(z_base_km)) * 1000.0)
    if np.any(np.diff(z) <= 0):
        return np.nan
    # The target envelope in R5.7.41 is explicitly the first/last occupied
    # native centre for multi-level CloudLayers. Do not extend beyond it here.
    cot = float(np.trapezoid(b, z * 1000.0))
    if z[0] > float(z_base_km):
        cot += b[0] * (z[0] - float(z_base_km)) * 1000.0
    if z[-1] < float(z_top_km):
        cot += b[-1] * (float(z_top_km) - z[-1]) * 1000.0
    return max(0.0, cot)


def _legacy_reconstruct(samples: pd.DataFrame, *, z_base_km: float, z_top_km: float) -> float:
    """Reconstruct R5.7.41 production direct_native_cot semantics.

    Primary pgrb2 only, sample CF scales extinction; multi-level targets add
    half a native centre spacing at each edge, matching cloud_scene.py.
    """
    if samples is None or samples.empty:
        return np.nan
    q = samples.copy()
    q = q[q.get("sample_source_role", pd.Series("", index=q.index)).astype(str).eq("PRIMARY_PGRB2")]
    q["_z"] = pd.to_numeric(q["sample_altitude_agl_km"], errors="coerce")
    q = q[q["_z"].notna()].sort_values("_z")
    if len(q) < 1:
        return np.nan
    z = q["_z"].astype(float).to_numpy()
    b = np.asarray([
        _beta_from_sample(r, use_sample_cloud_fraction=True)
        for r in q.to_dict("records")
    ], dtype=float)
    if not np.isfinite(b).all():
        return np.nan
    if len(q) == 1:
        return max(0.0, float(b[0]) * max(0.0, float(z_top_km) - float(z_base_km)) * 1000.0)
    if np.any(np.diff(z) <= 0):
        return np.nan
    cot = float(np.trapezoid(b, z * 1000.0))
    cot += b[0] * max(0.0, (z[1] - z[0]) * 500.0)
    cot += b[-1] * max(0.0, (z[-1] - z[-2]) * 500.0)
    return max(0.0, cot)


def build_canvas_cot_reconciliation(
    target_optics: pd.DataFrame,
    vertical_overlap: pd.DataFrame,
    vertical_samples: pd.DataFrame,
    *,
    residual_tolerance: float = 1.0e-10,
) -> pd.DataFrame:
    if target_optics is None or target_optics.empty or vertical_overlap is None or vertical_overlap.empty:
        return pd.DataFrame(columns=RECONCILIATION_COLUMNS)
    keys = ["time", "solar_altitude_deg", "canvas_id", "cloud_layer_id"]
    left_cols = [c for c in keys + [
        "direction_offset_deg", "distance_km", "z_base_km", "z_top_km",
        "direct_native_cot", "target_cot_nominal", "target_optics_ready",
        "target_optical_truth_state",
    ] if c in target_optics.columns]
    right_cols = [c for c in keys + [
        "target_z_base_km", "target_z_top_km", "cot_diagnostic_state",
        "cot_estimate_assumed_reff", "direct_target_evidence_conflict",
    ] if c in vertical_overlap.columns]
    m = target_optics[left_cols].merge(vertical_overlap[right_cols], on=keys, how="inner")
    rows = []
    for _, r in m.iterrows():
        legacy = r.get("target_cot_nominal", np.nan)
        newer = r.get("cot_estimate_assumed_reff", np.nan)
        if not (_finite(legacy) and _finite(newer)):
            continue
        zb = r.get("target_z_base_km", r.get("z_base_km", np.nan))
        zt = r.get("target_z_top_km", r.get("z_top_km", np.nan))
        if not (_finite(zb) and _finite(zt)) or float(zt) <= float(zb):
            continue
        sg = vertical_samples[
            (vertical_samples.get("solar_altitude_deg", pd.Series(np.nan, index=vertical_samples.index)).astype(float) == float(r["solar_altitude_deg"]))
            & (vertical_samples.get("canvas_id", pd.Series("", index=vertical_samples.index)).astype(str) == str(r["canvas_id"]))
            & (vertical_samples.get("inside_target_envelope", pd.Series(False, index=vertical_samples.index)).fillna(False).astype(bool))
        ].copy()
        primary = sg[sg.get("sample_source_role", pd.Series("", index=sg.index)).astype(str).eq("PRIMARY_PGRB2")].copy()
        legacy_recon = _legacy_reconstruct(primary, z_base_km=float(zb), z_top_km=float(zt))
        primary_cf_exact = _integrate_exact_envelope(primary, use_sample_cloud_fraction=True, z_base_km=float(zb), z_top_km=float(zt))
        primary_incloud = _integrate_exact_envelope(primary, use_sample_cloud_fraction=False, z_base_km=float(zb), z_top_km=float(zt))
        edge_delta = legacy_recon - primary_cf_exact if _finite(legacy_recon) and _finite(primary_cf_exact) else np.nan
        cf_delta = primary_incloud - primary_cf_exact if _finite(primary_incloud) and _finite(primary_cf_exact) else np.nan
        pgrb2b_delta = float(newer) - primary_incloud if _finite(primary_incloud) else np.nan
        observed_delta = float(newer) - float(legacy)
        explained_delta = (cf_delta + pgrb2b_delta - edge_delta) if all(_finite(v) for v in (cf_delta, pgrb2b_delta, edge_delta)) else np.nan
        residual = observed_delta - explained_delta if _finite(explained_delta) else np.nan
        recon_match = _finite(legacy_recon) and abs(float(legacy_recon) - float(legacy)) <= float(residual_tolerance)
        explained = recon_match and _finite(residual) and abs(float(residual)) <= float(residual_tolerance)
        rows.append({
            "time": r.get("time"), "solar_altitude_deg": float(r["solar_altitude_deg"]),
            "canvas_id": r.get("canvas_id"), "cloud_layer_id": r.get("cloud_layer_id"),
            "direction_offset_deg": r.get("direction_offset_deg"), "distance_km": r.get("distance_km"),
            "target_z_base_km": float(zb), "target_z_top_km": float(zt),
            "legacy_direct_native_cot": float(legacy),
            "overlap_cot_estimate_assumed_reff": float(newer),
            "legacy_primary_exact_envelope_cf_scaled_cot": primary_cf_exact,
            "primary_exact_envelope_incloud_cot": primary_incloud,
            "legacy_half_cell_edge_support_delta_cot": edge_delta,
            "cloud_fraction_semantics_delta_cot": cf_delta,
            "pgrb2b_vertical_resolution_delta_cot": pgrb2b_delta,
            "observed_new_minus_legacy_delta_cot": observed_delta,
            "explained_new_minus_legacy_delta_cot": explained_delta,
            "reconciliation_residual_cot": residual,
            "cot_ratio_overlap_to_legacy": (float(newer) / float(legacy) if float(legacy) > 0 else np.nan),
            "primary_inside_sample_count": int(len(primary)), "combined_inside_sample_count": int(len(sg)),
            "legacy_reconstruction_matches": bool(recon_match),
            "reconciliation_state": "SEMANTIC_DIFFERENCE_EXPLAINED" if explained else "RECONCILIATION_INCOMPLETE",
            "legacy_cot_semantics": "GRID_CELL_MEAN_CF_SCALED_PRIMARY_PGRB2_ASSUMED_REFF_WITH_HALF_CELL_EDGE_SUPPORT",
            "overlap_cot_semantics": "TARGET_INCLOUD_EXACT_ENVELOPE_PGRB2_PLUS_PGRB2B_ASSUMED_REFF_NO_CF",
            "recommended_future_target_cot_semantics": "TARGET_INCLOUD_EXACT_ENVELOPE_DIRECT_NATIVE_MICROPHYSICS",
            "production_target_cot_replaced": False,
            "cot_promotion_allowed": False,
            "formation_promotion_allowed": False,
            "cloud_fraction_used_for_new_cot": False,
            "rh_used_to_infer_condensate": False,
            "reconciliation_contract": RECONCILIATION_CONTRACT,
        })
    return pd.DataFrame(rows, columns=RECONCILIATION_COLUMNS)


def summarize_canvas_cot_reconciliation(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    rows = []
    for angle, g in df.groupby("solar_altitude_deg", dropna=False, sort=False):
        residual = pd.to_numeric(g["reconciliation_residual_cot"], errors="coerce")
        rows.append({
            "solar_altitude_deg": angle,
            "comparable_count": int(len(g)),
            "explained_count": int(g["reconciliation_state"].astype(str).eq("SEMANTIC_DIFFERENCE_EXPLAINED").sum()),
            "legacy_reconstruction_match_count": int(g["legacy_reconstruction_matches"].fillna(False).astype(bool).sum()),
            "mean_legacy_direct_native_cot": pd.to_numeric(g["legacy_direct_native_cot"], errors="coerce").mean(),
            "mean_overlap_cot_estimate_assumed_reff": pd.to_numeric(g["overlap_cot_estimate_assumed_reff"], errors="coerce").mean(),
            "mean_overlap_to_legacy_ratio": pd.to_numeric(g["cot_ratio_overlap_to_legacy"], errors="coerce").mean(),
            "mean_legacy_half_cell_edge_support_delta_cot": pd.to_numeric(g["legacy_half_cell_edge_support_delta_cot"], errors="coerce").mean(),
            "mean_cloud_fraction_semantics_delta_cot": pd.to_numeric(g["cloud_fraction_semantics_delta_cot"], errors="coerce").mean(),
            "mean_pgrb2b_vertical_resolution_delta_cot": pd.to_numeric(g["pgrb2b_vertical_resolution_delta_cot"], errors="coerce").mean(),
            "max_abs_reconciliation_residual_cot": residual.abs().max(),
            "production_target_cot_replaced_count": int(g["production_target_cot_replaced"].fillna(False).astype(bool).sum()),
            "cot_promotion_allowed_count": int(g["cot_promotion_allowed"].fillna(False).astype(bool).sum()),
            "formation_promotion_allowed_count": int(g["formation_promotion_allowed"].fillna(False).astype(bool).sum()),
            "closure_state": "EXPLAINED_DIAGNOSTIC_ONLY" if g["reconciliation_state"].astype(str).eq("SEMANTIC_DIFFERENCE_EXPLAINED").all() else "PARTIAL",
            "reconciliation_contract": RECONCILIATION_CONTRACT,
        })
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)
