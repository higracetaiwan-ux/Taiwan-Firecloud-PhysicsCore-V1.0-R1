"""PhysicsCore V1.0-R5.5.1 Target Canvas optical suitability.

This module classifies the *intrinsic target-cloud optical response* only.
It deliberately does NOT consume finite-solar-disk geometry, F_sun, Earth-shadow
state, Sun->CloudBase transmission, observer-path extinction, or twilight glow.
Those evidence tracks remain separate and are combined only later by Formation.

R5.5 Tier-1 regime boundaries are order-of-magnitude optical-depth regimes,
not calibrated firecloud decision thresholds.  Ground-truth calibration may
move them later without changing the evidence contract.
"""
from __future__ import annotations

import math
from typing import Iterable, Optional

import pandas as pd

from .contracts import CanvasCandidate, CloudScene

TOO_THIN = "TOO_THIN"
OPTICALLY_SUITABLE = "OPTICALLY_SUITABLE"
TOO_THICK = "TOO_THICK"
OPTICS_UNKNOWN = "OPTICS_UNKNOWN"

# Tier-1, uncalibrated optical-regime boundaries around tau~O(1).
THIN_COT_UPPER = 0.30
THICK_COT_LOWER = 3.00
MULTIPLE_SCATTERING_COT = 1.00


def _finite(v) -> bool:
    try:
        return bool(math.isfinite(float(v)))
    except Exception:
        return False


def classify_cot_regime(cot: Optional[float]) -> str:
    if not _finite(cot):
        return OPTICS_UNKNOWN
    tau = max(0.0, float(cot))
    if tau < THIN_COT_UPPER:
        return TOO_THIN
    if tau > THICK_COT_LOWER:
        return TOO_THICK
    return OPTICALLY_SUITABLE


def _interaction_fraction(tau: float) -> float:
    return max(0.0, min(1.0, 1.0 - math.exp(-max(0.0, tau))))


def _escape_weighted_response(tau: float) -> float:
    """Uncalibrated slab response capacity, not actual radiance.

    The interaction term rises with tau while the escape/self-shield term falls.
    This gives a broad O(1) maximum and prevents the old monotonic source proxy
    from treating arbitrarily thick target cloud as ever more suitable.
    """
    tau = max(0.0, float(tau))
    return _interaction_fraction(tau) * math.exp(-0.5 * tau)


def build_canvas_optical_suitability(
    scene: CloudScene,
    canvases: Iterable[CanvasCandidate],
    *,
    target_optical_evidence: Optional[pd.DataFrame] = None,
    solar_altitude_deg: Optional[float] = None,
    valid_time=None,
) -> pd.DataFrame:
    """Return per-Canvas intrinsic optical-suitability evidence.

    Exact target COT is required for a categorical suitability state.  Bounded
    adjacent-COT hypotheses remain OPTICS_UNKNOWN and are exposed only as bounds.
    Cloud fraction, RH, geometry, solar geometry and spectral path transmission
    are never converted into target COT or suitability.
    """
    canvases = list(canvases)
    layer_by_id = {x.layer_id: x for x in scene.layers}
    evmap = {}
    if target_optical_evidence is not None and not target_optical_evidence.empty:
        for _, row in target_optical_evidence.iterrows():
            evmap[str(row.get("canvas_id"))] = row

    rows = []
    for canvas in canvases:
        layer = layer_by_id.get(canvas.cloud_layer_id)
        if layer is None:
            continue
        ev = evmap.get(str(canvas.canvas_id))
        ready = False
        bounded = False
        source = "NO_RESOLVED_TARGET_COT"
        nominal = lower = upper = None
        resolver_state = "NO_TARGET_OPTICAL_EVIDENCE"
        if ev is not None:
            ready = bool(ev.get("target_optics_ready", False))
            bounded = bool(ev.get("target_optics_bounded", False))
            source = str(ev.get("evidence_source", source))
            resolver_state = str(ev.get("resolver_state", resolver_state))
            if _finite(ev.get("target_cot_nominal")):
                nominal = max(0.0, float(ev.get("target_cot_nominal")))
            if _finite(ev.get("target_cot_lower_bound")):
                lower = max(0.0, float(ev.get("target_cot_lower_bound")))
            if _finite(ev.get("target_cot_upper_bound")):
                upper = max(0.0, float(ev.get("target_cot_upper_bound")))
        elif _finite(getattr(layer, "cot", None)):
            # Standalone compatibility: finite CloudLayer COT is still native
            # optical evidence, but normal model execution uses the resolver.
            nominal = lower = upper = max(0.0, float(layer.cot))
            ready = True
            source = "CLOUD_LAYER_NATIVE_CONDENSATE"
            resolver_state = "TARGET_NATIVE_OPTICS_READY"

        exact_cot = nominal if ready and _finite(nominal) and not bounded else None
        state = classify_cot_regime(exact_cot)
        interaction = _interaction_fraction(exact_cot) if _finite(exact_cot) else None
        response = _escape_weighted_response(exact_cot) if _finite(exact_cot) else None
        lower_state = classify_cot_regime(lower) if bounded and _finite(lower) else None
        upper_state = classify_cot_regime(upper) if bounded and _finite(upper) else None
        bounded_consensus = lower_state if bounded and lower_state == upper_state else None
        thickness = None
        try:
            thickness = max(0.0, float(layer.z_top_km) - float(layer.z_base_km))
        except Exception:
            pass

        rows.append({
            "time": valid_time,
            "solar_altitude_deg": float(solar_altitude_deg) if _finite(solar_altitude_deg) else None,
            "canvas_id": canvas.canvas_id,
            "cloud_layer_id": canvas.cloud_layer_id,
            "operational_domain": canvas.operational_domain.value,
            "distance_km": float(canvas.distance_km),
            "target_cot": exact_cot,
            "target_cot_lower_bound": lower,
            "target_cot_upper_bound": upper,
            "target_optics_ready": bool(ready),
            "target_optics_bounded": bool(bounded),
            "target_optical_resolver_state": resolver_state,
            "target_optical_source": source,
            "cloud_phase": getattr(layer, "phase", None),
            "effective_radius_um": getattr(layer, "effective_radius_um", None),
            "cloud_thickness_km": thickness,
            "single_scattering_proxy": interaction,
            "multiple_scattering_flag": (bool(exact_cot >= MULTIPLE_SCATTERING_COT) if _finite(exact_cot) else None),
            "source_radiance_proxy": response,
            "source_radiance_proxy_semantics": "INTRINSIC_ESCAPE_WEIGHTED_RESPONSE_CAPACITY_NOT_ACTUAL_RADIANCE",
            "bounded_regime_lower": lower_state,
            "bounded_regime_upper": upper_state,
            "bounded_regime_consensus": bounded_consensus,
            "canvas_optical_suitability_state": state,
            "suitability_tier": "TIER1_COT_REGIME_UNCALIBRATED",
            "suitability_threshold_basis": "ORDER_OF_MAGNITUDE_TAU_REGIMES_AROUND_O1;GROUND_TRUTH_CALIBRATION_PENDING",
            "thin_cot_upper": THIN_COT_UPPER,
            "thick_cot_lower": THICK_COT_LOWER,
            "uses_penumbra_geometry": False,
            "uses_spectral_path_rt": False,
            "uses_cloud_fraction_to_infer_cot": False,
            "uses_rh_to_infer_cot": False,
        })
    return pd.DataFrame(rows)


def summarize_canvas_optical_suitability(table: pd.DataFrame) -> pd.DataFrame:
    if table is None or table.empty:
        return pd.DataFrame()
    rows = []
    for angle, g in table.groupby("solar_altitude_deg", dropna=False, sort=False):
        s = g["canvas_optical_suitability_state"].astype(str)
        rows.append({
            "solar_altitude_deg": angle,
            "canvas_count": int(len(g)),
            "too_thin_count": int(s.eq(TOO_THIN).sum()),
            "optically_suitable_count": int(s.eq(OPTICALLY_SUITABLE).sum()),
            "too_thick_count": int(s.eq(TOO_THICK).sum()),
            "optics_unknown_count": int(s.eq(OPTICS_UNKNOWN).sum()),
            "exact_optics_count": int(g["target_optics_ready"].astype(bool).sum()),
            "bounded_optics_count": int(g["target_optics_bounded"].astype(bool).sum()),
            "contract": "R5.5_TARGET_INTRINSIC_OPTICS_ONLY;NO_GEOMETRY_OR_PATH_RT_IN_SUITABILITY",
        })
    return pd.DataFrame(rows)
