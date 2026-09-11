"""R5.7.41 Canvas Optical Truth Phase 2A: target vertical microphysics overlap.

Evidence-only bridge that merges direct native GFS pressure-level hydrometeors
from the primary pgrb2 chain and the pgrb2b intermediate-level probe, then
projects those samples onto each fixed Formation Canvas Cloud Base--Top envelope.

Hard contract
-------------
* no RH/cloud-fraction -> condensate or COT;
* Missing != zero and Missing != clear;
* pgrb2b cloud fraction is never used for target geometry;
* boundary-only positive condensate is not interior target support;
* this module never promotes target COT or Formation;
* the optional COT calculation is diagnostic-only and explicitly labelled
  ASSUMED_REFF. Direct evidence conflicts block even that diagnostic estimate.
"""
from __future__ import annotations

import math
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from .cloud_optics import (
    DEFAULT_ICE_REFF_UM,
    DEFAULT_LIQUID_REFF_UM,
    condensate_extinction_m1,
)
from .cloud_scene import ProviderCloudGeometryConfig, native_level_evidence_consistency
from .native_cloud import NATIVE_CONDENSATE_THRESHOLD_KGKG, R_D, native_levels_from_row
from .providers.gfs_native import DEFAULT_PRESSURE_LEVELS_HPA, NATIVE_PROVIDER_NAME
from .providers.gfs_canvas_optical_probe import (
    PROVIDER_NAME as PGRB2B_PROVIDER,
    SUPPLEMENT_PRESSURE_LEVELS_HPA,
)

OVERLAP_CONTRACT = (
    "DIRECT_NATIVE_GFS_PGRB2_PLUS_PGRB2B_TARGET_VERTICAL_OVERLAP;"
    "BOUNDARY_NE_INTERIOR;MISSING_NE_ZERO;NO_CF_RH_TO_CONDENSATE_OR_COT;"
    "COT_DIAGNOSTIC_ASSUMED_REFF_ONLY;NO_COT_PROMOTION;NO_FORMATION_PROMOTION"
)

# Native CloudLayer multi-level boundaries are native occupied-level centres.
# Numerical tolerance only protects float serialization/round-trip; it is not
# permission to widen the physical cloud envelope.
BOUNDARY_TOLERANCE_KM = 1.0e-5  # 1 cm in km units

OVERLAP_STATES = {
    "INTERIOR_NATIVE_CONDENSATE_SUPPORT",
    "BOUNDARY_ONLY_NATIVE_CONDENSATE_SUPPORT",
    "NO_NATIVE_CONDENSATE_SUPPORT",
    "MIXED_CONFLICT_WITH_INTERIOR_SUPPORT",
    "VERTICAL_EVIDENCE_INCOMPLETE",
}


def _finite(v) -> bool:
    try:
        return bool(math.isfinite(float(v)))
    except Exception:
        return False


def _row_key(row: Mapping) -> tuple[float, float] | None:
    try:
        return round(float(row["direction_offset_deg"]), 6), round(float(row["distance_km"]), 6)
    except Exception:
        return None


def _q_state(ql, qi) -> tuple[str, float]:
    if not (_finite(ql) and _finite(qi)):
        return "MISSING", float("nan")
    qt = max(0.0, float(ql)) + max(0.0, float(qi))
    return ("POSITIVE" if qt >= NATIVE_CONDENSATE_THRESHOLD_KGKG else "ZERO"), qt


def _position(z: float, z_base: float, z_top: float, tol: float = BOUNDARY_TOLERANCE_KM) -> str:
    if not _finite(z):
        return "UNKNOWN"
    z = float(z); z_base = float(z_base); z_top = float(z_top)
    if abs(z - z_base) <= tol:
        return "BOUNDARY_LOWER"
    if abs(z - z_top) <= tol:
        return "BOUNDARY_UPPER"
    if z_base + tol < z < z_top - tol:
        return "INTERIOR"
    if z < z_base - tol:
        return "BELOW_TARGET"
    if z > z_top + tol:
        return "ABOVE_TARGET"
    # Tiny residual interval caused only by float precision near a boundary.
    return "BOUNDARY_NEAR"


def _primary_samples(row: Mapping, pressure_levels_hpa: Sequence[int]) -> list[dict]:
    out = []
    for level in native_levels_from_row(row, pressure_levels_hpa):
        state, qt = _q_state(level.get("cloud_liquid_water_kgkg"), level.get("cloud_ice_water_kgkg"))
        out.append({
            "pressure_hpa": float(level["pressure_hpa"]),
            "altitude_agl_km": float(level["altitude_agl_km"]),
            "temperature_k": float(level["temperature_k"]) if _finite(level.get("temperature_k")) else np.nan,
            "cloud_fraction": float(level["cloud_fraction"]) if _finite(level.get("cloud_fraction")) else np.nan,
            "cloud_liquid_water_kgkg": float(level["cloud_liquid_water_kgkg"]) if _finite(level.get("cloud_liquid_water_kgkg")) else np.nan,
            "cloud_ice_water_kgkg": float(level["cloud_ice_water_kgkg"]) if _finite(level.get("cloud_ice_water_kgkg")) else np.nan,
            "total_condensate_kgkg": qt,
            "condensate_state": state,
            "evidence_consistency": native_level_evidence_consistency(level, ProviderCloudGeometryConfig()),
            "sample_source": NATIVE_PROVIDER_NAME,
            "sample_source_role": "PRIMARY_PGRB2",
            "cloud_fraction_used_for_geometry": True,
            "cloud_fraction_used_for_cot": False,
        })
    return out


def _supplement_samples(row: Mapping | None, surface_elevation_m: float) -> list[dict]:
    # Preserve every requested intermediate pressure level, including unavailable
    # ones, so provider/schema gaps remain explicit Missing evidence instead of
    # disappearing and being misread as zero/clear.
    out = []
    for p in SUPPLEMENT_PRESSURE_LEVELS_HPA:
        gh = row.get(f"geopotential_height_m_{p}hPa", np.nan) if row is not None else np.nan
        ql = row.get(f"cloud_liquid_water_kgkg_{p}hPa", np.nan) if row is not None else np.nan
        qi = row.get(f"cloud_ice_water_kgkg_{p}hPa", np.nan) if row is not None else np.nan
        state, qt = _q_state(ql, qi)
        out.append({
            "pressure_hpa": float(p),
            "altitude_agl_km": ((float(gh) - float(surface_elevation_m)) / 1000.0 if _finite(gh) and _finite(surface_elevation_m) else np.nan),
            "temperature_k": float(row.get(f"temperature_k_{p}hPa")) if row is not None and _finite(row.get(f"temperature_k_{p}hPa")) else np.nan,
            "cloud_fraction": np.nan,
            "cloud_liquid_water_kgkg": float(ql) if _finite(ql) else np.nan,
            "cloud_ice_water_kgkg": float(qi) if _finite(qi) else np.nan,
            "total_condensate_kgkg": qt,
            "condensate_state": state,
            "evidence_consistency": (
                "NATIVE_CONDENSATE_POSITIVE" if state == "POSITIVE"
                else "NATIVE_CONDENSATE_ZERO" if state == "ZERO"
                else "OPTICS_MISSING"
            ),
            "sample_source": PGRB2B_PROVIDER,
            "sample_source_role": "INTERMEDIATE_PGRB2B",
            "cloud_fraction_used_for_geometry": False,
            "cloud_fraction_used_for_cot": False,
        })
    return out


def _expected_supplement_pressures(primary: list[dict], z_base: float, z_top: float) -> tuple[list[float], bool]:
    finite = sorted([s for s in primary if _finite(s.get("altitude_agl_km"))], key=lambda r: float(r["altitude_agl_km"]))
    lower = [s for s in finite if float(s["altitude_agl_km"]) <= float(z_base) + BOUNDARY_TOLERANCE_KM]
    upper = [s for s in finite if float(s["altitude_agl_km"]) >= float(z_top) - BOUNDARY_TOLERANCE_KM]
    if not lower or not upper:
        return [], False
    lo = max(lower, key=lambda s: float(s["altitude_agl_km"]))
    hi = min(upper, key=lambda s: float(s["altitude_agl_km"]))
    p0, p1 = sorted((float(lo["pressure_hpa"]), float(hi["pressure_hpa"])))
    expected = [float(p) for p in SUPPLEMENT_PRESSURE_LEVELS_HPA if p0 < float(p) < p1]
    return expected, True


def _merge_samples(primary: list[dict], supplement: list[dict]) -> list[dict]:
    # Products are designed to be complementary. If a future inventory duplicates
    # a pressure level, preserve the primary pgrb2 sample as authoritative and do
    # not average independent provider values into fabricated microphysics.
    by_p: dict[float, dict] = {}
    for rec in supplement:
        by_p[round(float(rec["pressure_hpa"]), 6)] = dict(rec)
    for rec in primary:
        by_p[round(float(rec["pressure_hpa"]), 6)] = dict(rec)
    return sorted(by_p.values(), key=lambda r: (0, float(r["altitude_agl_km"])) if _finite(r.get("altitude_agl_km")) else (1, float(r["pressure_hpa"])))


def estimate_cot_assumed_reff_from_samples(
    samples: Sequence[Mapping],
    *,
    z_base_km: float,
    z_top_km: float,
    direct_evidence_conflict: bool = False,
    liquid_reff_um: float = DEFAULT_LIQUID_REFF_UM,
    ice_reff_um: float = DEFAULT_ICE_REFF_UM,
) -> dict:
    """Diagnostic COT estimate from vertically ordered direct-native samples.

    This is deliberately stricter than the legacy layer helper. It requires
    finite ql/qi/T/P at every target-envelope sample, at least two target samples,
    and no direct evidence conflict. The result remains an assumed-r_eff estimate
    and is never target-COT promotion.
    """
    if direct_evidence_conflict:
        return {
            "cot_diagnostic_state": "BLOCKED_DIRECT_EVIDENCE_CONFLICT",
            "cot_estimate_assumed_reff": np.nan,
            "cot_semantics": "UNRESOLVED_CONFLICT",
        }
    inside = [dict(s) for s in samples if _position(s.get("altitude_agl_km"), z_base_km, z_top_km) in {"INTERIOR", "BOUNDARY_LOWER", "BOUNDARY_UPPER", "BOUNDARY_NEAR"}]
    inside = sorted(inside, key=lambda r: float(r["altitude_agl_km"]))
    if len(inside) < 2:
        return {
            "cot_diagnostic_state": "INSUFFICIENT_VERTICAL_SAMPLES",
            "cot_estimate_assumed_reff": np.nan,
            "cot_semantics": "NOT_ESTIMATED",
        }
    profile = []
    for s in inside:
        ql, qi = s.get("cloud_liquid_water_kgkg"), s.get("cloud_ice_water_kgkg")
        t, p = s.get("temperature_k"), s.get("pressure_hpa")
        if not all(_finite(v) for v in (ql, qi, t, p)) or float(t) <= 0 or float(p) <= 0:
            return {
                "cot_diagnostic_state": "MISSING_NATIVE_MICROPHYSICS_OR_THERMODYNAMICS",
                "cot_estimate_assumed_reff": np.nan,
                "cot_semantics": "NOT_ESTIMATED",
            }
        rho = (float(p) * 100.0) / (R_D * float(t))
        lwc = max(0.0, float(ql)) * rho * 1000.0
        iwc = max(0.0, float(qi)) * rho * 1000.0
        # Cloud fraction intentionally fixed to 1 here: this diagnostic asks what
        # direct condensate implies along the target native cloud volume. It does
        # not turn CF into optical depth or use pgrb2b CF.
        ext = condensate_extinction_m1(
            lwc, iwc, 1.0,
            liquid_reff_um=liquid_reff_um,
            ice_reff_um=ice_reff_um,
        )
        beta = ext.get("total_extinction_m1", np.nan)
        if not _finite(beta):
            return {
                "cot_diagnostic_state": "EXTINCTION_NOT_RESOLVED",
                "cot_estimate_assumed_reff": np.nan,
                "cot_semantics": "NOT_ESTIMATED",
            }
        profile.append((float(s["altitude_agl_km"]), max(0.0, float(beta))))
    zs = np.asarray([x[0] for x in profile], dtype=float)
    bs = np.asarray([x[1] for x in profile], dtype=float)
    if np.any(np.diff(zs) <= 0):
        return {
            "cot_diagnostic_state": "INVALID_VERTICAL_ORDER",
            "cot_estimate_assumed_reff": np.nan,
            "cot_semantics": "NOT_ESTIMATED",
        }
    # Clip integral to target boundaries using endpoint-hold only between the
    # first/last known native samples and the exact target boundaries. This is a
    # diagnostic scaffold, not a claim of native sub-layer particle structure.
    cot = float(np.trapezoid(bs, zs * 1000.0))
    if zs[0] > float(z_base_km):
        cot += bs[0] * (zs[0] - float(z_base_km)) * 1000.0
    if zs[-1] < float(z_top_km):
        cot += bs[-1] * (float(z_top_km) - zs[-1]) * 1000.0
    return {
        "cot_diagnostic_state": "COT_ESTIMATE_ASSUMED_REFF",
        "cot_estimate_assumed_reff": max(0.0, cot),
        "cot_semantics": "DIAGNOSTIC_ASSUMED_REFF_NOT_NATIVE_COT",
    }


def build_canvas_vertical_microphysics_overlap(
    scene,
    canvases,
    primary_route: pd.DataFrame,
    pgrb2b_route: pd.DataFrame,
    *,
    valid_time=None,
    solar_altitude_deg=None,
    primary_pressure_levels_hpa: Sequence[int] = DEFAULT_PRESSURE_LEVELS_HPA,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (per-canvas overlap diagnostics, per-native-sample evidence)."""
    if primary_route is None or primary_route.empty:
        return pd.DataFrame(), pd.DataFrame()

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
    canvas_rows = []
    sample_rows = []
    cfg = ProviderCloudGeometryConfig()

    for canvas in canvases:
        layer = layers.get(str(canvas.cloud_layer_id))
        if layer is None:
            continue
        key = (round(float(layer.direction_offset_deg), 6), round(float(layer.distance_km), 6))
        prow = primary_by_key.get(key)
        if prow is None:
            continue
        srow = supplement_by_key.get(key)
        elev = prow.get("model_surface_elevation_m", np.nan)
        if not _finite(elev) and srow is not None:
            elev = srow.get("surface_elevation_m", np.nan)
        if not _finite(elev):
            elev = 0.0

        primary = _primary_samples(prow, primary_pressure_levels_hpa)
        supplement = _supplement_samples(srow, float(elev))
        merged = _merge_samples(primary, supplement)
        z0, z1 = float(layer.z_base_km), float(layer.z_top_km)
        expected_supp_pressures, primary_target_bracket_available = _expected_supplement_pressures(primary, z0, z1)
        supplement_by_pressure = {round(float(s["pressure_hpa"]), 6): s for s in supplement}
        expected_supp_missing = 0
        for p_expected in expected_supp_pressures:
            s_expected = supplement_by_pressure.get(round(float(p_expected), 6))
            if s_expected is None or not _finite(s_expected.get("altitude_agl_km")) or s_expected.get("condensate_state") == "MISSING":
                expected_supp_missing += 1

        # Direct target conflict is a property of the primary geometry/evidence,
        # not of the pgrb2b probe. Keep it explicit in every sample/aggregate row.
        primary_inside = [s for s in primary if _position(s["altitude_agl_km"], z0, z1) in {"INTERIOR", "BOUNDARY_LOWER", "BOUNDARY_UPPER", "BOUNDARY_NEAR"}]
        direct_conflict = any(str(s.get("evidence_consistency")) == "CF_CLOUD_CONDENSATE_ZERO" for s in primary_inside)

        target_samples = []
        for s in merged:
            pos = _position(s.get("altitude_agl_km"), z0, z1)
            rec = {
                "time": valid_time,
                "solar_altitude_deg": float(solar_altitude_deg) if solar_altitude_deg is not None else np.nan,
                "canvas_id": canvas.canvas_id,
                "cloud_layer_id": canvas.cloud_layer_id,
                "direction_offset_deg": float(layer.direction_offset_deg),
                "distance_km": float(layer.distance_km),
                "target_z_base_km": z0,
                "target_z_top_km": z1,
                "sample_pressure_hpa": float(s["pressure_hpa"]),
                "sample_altitude_agl_km": float(s["altitude_agl_km"]),
                "sample_target_position": pos,
                "sample_temperature_k": s.get("temperature_k", np.nan),
                "sample_cloud_fraction": s.get("cloud_fraction", np.nan),
                "sample_cloud_liquid_water_kgkg": s.get("cloud_liquid_water_kgkg", np.nan),
                "sample_cloud_ice_water_kgkg": s.get("cloud_ice_water_kgkg", np.nan),
                "sample_total_condensate_kgkg": s.get("total_condensate_kgkg", np.nan),
                "sample_condensate_state": s.get("condensate_state", "MISSING"),
                "sample_evidence_consistency": s.get("evidence_consistency", "MISSING"),
                "sample_source": s.get("sample_source"),
                "sample_source_role": s.get("sample_source_role"),
                "supplement_level_expected_for_target_context": bool(
                    s.get("sample_source_role") == "INTERMEDIATE_PGRB2B"
                    and float(s.get("pressure_hpa")) in set(expected_supp_pressures)
                ),
                "cloud_fraction_used_for_geometry": bool(s.get("cloud_fraction_used_for_geometry", False)),
                "cloud_fraction_used_for_cot": False,
                "rh_used_to_infer_condensate": False,
                "inside_target_envelope": pos in {"INTERIOR", "BOUNDARY_LOWER", "BOUNDARY_UPPER", "BOUNDARY_NEAR"},
                "strict_interior": pos == "INTERIOR",
                "target_boundary_sample": pos.startswith("BOUNDARY"),
                "positive_native_condensate": s.get("condensate_state") == "POSITIVE",
                "direct_target_evidence_conflict": bool(direct_conflict),
                "overlap_contract": OVERLAP_CONTRACT,
            }
            sample_rows.append(rec)
            if rec["inside_target_envelope"]:
                target_samples.append(rec)

        known = [r for r in target_samples if r["sample_condensate_state"] != "MISSING"]
        missing = [r for r in target_samples if r["sample_condensate_state"] == "MISSING"]
        interior = [r for r in target_samples if r["strict_interior"]]
        boundary = [r for r in target_samples if r["target_boundary_sample"]]
        pos_interior = [r for r in interior if r["positive_native_condensate"]]
        pos_boundary = [r for r in boundary if r["positive_native_condensate"]]
        zero_interior = [r for r in interior if r["sample_condensate_state"] == "ZERO"]

        known_all = sorted([
            s for s in merged if s.get("condensate_state") != "MISSING" and _finite(s.get("altitude_agl_km"))
        ], key=lambda s: float(s["altitude_agl_km"]))
        lower_candidates = [s for s in known_all if float(s["altitude_agl_km"]) <= z0 + BOUNDARY_TOLERANCE_KM]
        upper_candidates = [s for s in known_all if float(s["altitude_agl_km"]) >= z1 - BOUNDARY_TOLERANCE_KM]
        lower_bracket = max(lower_candidates, key=lambda s: float(s["altitude_agl_km"])) if lower_candidates else None
        upper_bracket = min(upper_candidates, key=lambda s: float(s["altitude_agl_km"])) if upper_candidates else None
        bracket_complete = lower_bracket is not None and upper_bracket is not None

        known_target_z = sorted(float(r["sample_altitude_agl_km"]) for r in known)
        max_gap = np.nan
        if bracket_complete:
            zseq = [z0] + [z for z in known_target_z if z0 < z < z1] + [z1]
            if len(zseq) >= 2:
                max_gap = max(b - a for a, b in zip(zseq[:-1], zseq[1:]))

        target_count = len(target_samples)
        known_fraction = (len(known) / target_count) if target_count else 0.0
        interior_known_fraction = (
            sum(r["sample_condensate_state"] != "MISSING" for r in interior) / len(interior)
            if interior else 0.0
        )

        if missing or not target_samples or not bracket_complete or not primary_target_bracket_available or expected_supp_missing > 0:
            state = "VERTICAL_EVIDENCE_INCOMPLETE"
        elif pos_interior and direct_conflict:
            state = "MIXED_CONFLICT_WITH_INTERIOR_SUPPORT"
        elif pos_interior:
            state = "INTERIOR_NATIVE_CONDENSATE_SUPPORT"
        elif pos_boundary:
            state = "BOUNDARY_ONLY_NATIVE_CONDENSATE_SUPPORT"
        else:
            state = "NO_NATIVE_CONDENSATE_SUPPORT"

        # Diagnostic COT scaffold: a direct CF/native-condensate conflict blocks
        # the estimate even if some native levels are otherwise numerically usable.
        estimate_input = []
        for s in merged:
            d = dict(s)
            estimate_input.append(d)
        cot_diag = estimate_cot_assumed_reff_from_samples(
            estimate_input,
            z_base_km=z0,
            z_top_km=z1,
            direct_evidence_conflict=bool(direct_conflict),
        )

        canvas_rows.append({
            "time": valid_time,
            "solar_altitude_deg": float(solar_altitude_deg) if solar_altitude_deg is not None else np.nan,
            "canvas_id": canvas.canvas_id,
            "cloud_layer_id": canvas.cloud_layer_id,
            "direction_offset_deg": float(layer.direction_offset_deg),
            "distance_km": float(layer.distance_km),
            "target_z_base_km": z0,
            "target_z_top_km": z1,
            "target_thickness_km": max(0.0, z1 - z0),
            "direct_target_evidence_conflict": bool(direct_conflict),
            "native_sample_count_inside_target": int(target_count),
            "native_sample_count_strict_interior": int(len(interior)),
            "native_sample_count_boundary": int(len(boundary)),
            "native_condensate_known_count_inside_target": int(len(known)),
            "native_condensate_missing_count_inside_target": int(len(missing)),
            "native_condensate_positive_inside_count": int(len(pos_interior)),
            "native_condensate_positive_boundary_count": int(len(pos_boundary)),
            "native_condensate_zero_inside_count": int(len(zero_interior)),
            "native_condensate_known_fraction_inside_target": float(known_fraction),
            "native_condensate_known_fraction_strict_interior": float(interior_known_fraction),
            "primary_target_bracket_available": bool(primary_target_bracket_available),
            "expected_supplement_level_count": int(len(expected_supp_pressures)),
            "expected_supplement_missing_count": int(expected_supp_missing),
            "lower_vertical_bracket_available": bool(lower_bracket is not None),
            "upper_vertical_bracket_available": bool(upper_bracket is not None),
            "vertical_bracketing_complete": bool(bracket_complete),
            "lower_bracket_pressure_hpa": float(lower_bracket["pressure_hpa"]) if lower_bracket else np.nan,
            "lower_bracket_altitude_agl_km": float(lower_bracket["altitude_agl_km"]) if lower_bracket else np.nan,
            "upper_bracket_pressure_hpa": float(upper_bracket["pressure_hpa"]) if upper_bracket else np.nan,
            "upper_bracket_altitude_agl_km": float(upper_bracket["altitude_agl_km"]) if upper_bracket else np.nan,
            "max_known_vertical_gap_km": float(max_gap) if _finite(max_gap) else np.nan,
            "target_vertical_overlap_state": state,
            "cot_diagnostic_state": cot_diag["cot_diagnostic_state"],
            "cot_estimate_assumed_reff": cot_diag["cot_estimate_assumed_reff"],
            "cot_diagnostic_semantics": cot_diag["cot_semantics"],
            "assumed_liquid_reff_um": float(DEFAULT_LIQUID_REFF_UM),
            "assumed_ice_reff_um": float(DEFAULT_ICE_REFF_UM),
            "cloud_fraction_used_for_cot": False,
            "rh_used_to_infer_condensate": False,
            "cot_promotion_allowed": False,
            "formation_promotion_allowed": False,
            "overlap_contract": OVERLAP_CONTRACT,
        })

    return pd.DataFrame(canvas_rows), pd.DataFrame(sample_rows)


def summarize_canvas_vertical_microphysics_overlap(table: pd.DataFrame) -> pd.DataFrame:
    if table is None or table.empty:
        return pd.DataFrame()
    rows = []
    for (tm, ang), g in table.groupby(["time", "solar_altitude_deg"], dropna=False, sort=False):
        state = g["target_vertical_overlap_state"].astype(str)
        rows.append({
            "time": tm,
            "solar_altitude_deg": ang,
            "canvas_count": int(len(g)),
            "direct_conflict_canvas_count": int(g["direct_target_evidence_conflict"].astype(bool).sum()),
            "interior_native_condensate_support_count": int(state.eq("INTERIOR_NATIVE_CONDENSATE_SUPPORT").sum()),
            "boundary_only_native_condensate_support_count": int(state.eq("BOUNDARY_ONLY_NATIVE_CONDENSATE_SUPPORT").sum()),
            "mixed_conflict_with_interior_support_count": int(state.eq("MIXED_CONFLICT_WITH_INTERIOR_SUPPORT").sum()),
            "no_native_condensate_support_count": int(state.eq("NO_NATIVE_CONDENSATE_SUPPORT").sum()),
            "vertical_evidence_incomplete_count": int(state.eq("VERTICAL_EVIDENCE_INCOMPLETE").sum()),
            "cot_diagnostic_estimate_count": int(g["cot_diagnostic_state"].astype(str).eq("COT_ESTIMATE_ASSUMED_REFF").sum()),
            "cot_promotion_count": int(g["cot_promotion_allowed"].fillna(False).astype(bool).sum()),
            "formation_promotion_count": int(g["formation_promotion_allowed"].fillna(False).astype(bool).sum()),
            "overlap_contract": OVERLAP_CONTRACT,
        })
    return pd.DataFrame(rows)
