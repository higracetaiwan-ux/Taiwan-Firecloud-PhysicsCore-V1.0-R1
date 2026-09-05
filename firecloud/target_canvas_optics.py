"""PhysicsCore V1.0-R4.9 target Canvas optical-evidence resolver.

Purpose
-------
Resolve what is actually known about the *target cloud itself* without allowing
cloud fraction / RH / cloud-base geometry to fabricate cloud optical depth.

Evidence ladder
---------------
1. DIRECT_NATIVE_CONDENSATE_COT
   A CloudLayer already carries finite COT derived from native CLWMR/ICMR.
   This is the only exact target-COT source currently promoted to
   ``target_optics_ready=True``.
2. ADJACENT_NATIVE_COT_BRACKET
   For a geometry-only target whose native condensate is *missing* (not zero),
   immediately adjacent sampled route nodes on the same direction may bracket
   the target with vertically-overlapping native-condensate COT.  The result is
   retained only as a bounded optical hypothesis.  Sampling spacing is a
   numerical interpolation support and is explicitly NOT interpreted as cloud
   width.
3. CF_CLOUD_CONDENSATE_ZERO
   When cloud fraction indicates occupancy but native condensate is explicitly
   zero, the evidence conflicts.  No spatial interpolation is allowed to erase
   that conflict.  Target COT remains unresolved.

This module is deliberately conservative.  It creates diagnostics and bounded
hypotheses, not a new cloud-cover-to-COT parameterisation.
"""
from __future__ import annotations

import math
from typing import Iterable, Optional

import numpy as np
import pandas as pd

from .contracts import CanvasCandidate, CloudScene, EvidenceState, CloudFractionState


def _finite(v) -> bool:
    try:
        return bool(math.isfinite(float(v)))
    except Exception:
        return False


def _overlap_km(a, b) -> float:
    return max(0.0, min(float(a.z_top_km), float(b.z_top_km)) - max(float(a.z_base_km), float(b.z_base_km)))


def _overlap_fraction(target, neighbour) -> float:
    thick = max(1e-9, float(target.z_top_km) - float(target.z_base_km))
    return max(0.0, min(1.0, _overlap_km(target, neighbour) / thick))


def _resolved_native_layer(layer) -> bool:
    return bool(
        layer is not None
        and layer.optical_evidence in (EvidenceState.FULL, EvidenceState.PARTIAL_OPTICS)
        and _finite(layer.cot)
        and str(getattr(layer, "evidence_consistency", "UNKNOWN")) not in (
            "CF_CLOUD_CONDENSATE_ZERO", "CONDENSATE_CLOUD_CF_LOW"
        )
    )


def _adjacent_distance_nodes(layers, d: float) -> tuple[Optional[float], Optional[float]]:
    nodes = sorted({float(x.distance_km) for x in layers})
    left = max((x for x in nodes if x < d - 1e-9), default=None)
    right = min((x for x in nodes if x > d + 1e-9), default=None)
    return left, right


def _best_overlap_candidate(target, layers_at_distance, min_overlap_fraction: float = 0.50):
    candidates=[]
    for x in layers_at_distance:
        if not _resolved_native_layer(x):
            continue
        frac=_overlap_fraction(target, x)
        if frac + 1e-12 < float(min_overlap_fraction):
            continue
        candidates.append((frac, x))
    if not candidates:
        return None, None
    candidates.sort(key=lambda t: (t[0], float(t[1].cot)), reverse=True)
    return candidates[0][1], float(candidates[0][0])


def build_target_canvas_optical_evidence(
    scene: CloudScene,
    canvases: Iterable[CanvasCandidate],
    *,
    solar_altitude_deg: float,
    valid_time=None,
    min_vertical_overlap_fraction: float = 0.50,
) -> pd.DataFrame:
    """Build auditable per-Canvas target optical evidence.

    The resolver never converts cloud fraction, RH or cloud geometry into COT.
    A finite interpolated COT is emitted only as a *bounded hypothesis* when the
    target optics are missing and the immediately adjacent route nodes on both
    sides contain vertically-overlapping native-condensate COT.  Explicit
    condensate-zero conflicts remain unresolved and are never overwritten.
    """
    canvases=list(canvases)
    layer_by_id={x.layer_id:x for x in scene.layers}
    by_dir={}
    for x in scene.layers:
        by_dir.setdefault(float(x.direction_offset_deg), []).append(x)

    rows=[]
    for canvas in canvases:
        target=layer_by_id.get(canvas.cloud_layer_id)
        if target is None:
            continue
        consistency=str(getattr(target,"evidence_consistency","UNKNOWN") or "UNKNOWN")
        direct_cot=float(target.cot) if _finite(target.cot) else None
        direct_ready=_resolved_native_layer(target)
        geom_state=getattr(target,"cloud_fraction_state",CloudFractionState.UNKNOWN)
        geom_cloud=geom_state in (CloudFractionState.PARTIAL_OCCUPANCY, CloudFractionState.CLOUD_OCCUPIED)

        rec={
            "time":valid_time,
            "solar_altitude_deg":float(solar_altitude_deg),
            "canvas_id":canvas.canvas_id,
            "cloud_layer_id":canvas.cloud_layer_id,
            "direction_offset_deg":float(target.direction_offset_deg),
            "distance_km":float(target.distance_km),
            "z_base_km":float(target.z_base_km),
            "z_top_km":float(target.z_top_km),
            "cloud_fraction":target.cloud_fraction,
            "cloud_fraction_state":geom_state.value,
            "direct_optical_evidence":target.optical_evidence.value,
            "evidence_consistency":consistency,
            "direct_native_cot":direct_cot,
            "target_optics_ready":False,
            "target_optics_bounded":False,
            "target_cot_nominal":None,
            "target_cot_lower_bound":None,
            "target_cot_upper_bound":None,
            "target_effective_radius_um":target.effective_radius_um,
            "left_support_layer_id":None,
            "right_support_layer_id":None,
            "left_support_distance_km":None,
            "right_support_distance_km":None,
            "left_support_cot":None,
            "right_support_cot":None,
            "left_vertical_overlap_fraction":None,
            "right_vertical_overlap_fraction":None,
            "resolver_state":"TARGET_OPTICS_MISSING",
            "evidence_source":"NONE",
            "bound_level":0,
            "sampling_step_is_cloud_width":False,
            "note":"NO_CF_TO_COT;NO_RH_TO_COT;NO_GEOMETRY_TO_COT",
        }

        if direct_ready:
            rec.update({
                "target_optics_ready":True,
                "target_cot_nominal":direct_cot,
                "target_cot_lower_bound":direct_cot,
                "target_cot_upper_bound":direct_cot,
                "resolver_state":"DIRECT_NATIVE_CONDENSATE_COT",
                "evidence_source":"CLOUD_LAYER_NATIVE_CLWMR_ICMR",
                "bound_level":3,
            })
            rows.append(rec); continue

        # Explicit CF-cloud / native-condensate-zero is contradictory evidence.
        # It must remain unresolved; neighbour interpolation cannot silently
        # overwrite the model's direct zero-condensate signal.
        if consistency == "CF_CLOUD_CONDENSATE_ZERO":
            rec.update({
                "resolver_state":"CF_CLOUD_CONDENSATE_ZERO_UNRESOLVED",
                "evidence_source":"DIRECT_GEOMETRY_OPTICS_CONFLICT",
                "note":"CLOUD_FRACTION_OCCUPANCY_WITH_EXPLICIT_ZERO_NATIVE_CONDENSATE;TARGET_COT_NOT_INFERRED",
            })
            rows.append(rec); continue

        if consistency == "CONDENSATE_CLOUD_CF_LOW":
            rec.update({
                "resolver_state":"CONDENSATE_CLOUD_CF_LOW_CONFLICT",
                "evidence_source":"DIRECT_GEOMETRY_OPTICS_CONFLICT",
                "note":"POSITIVE_CONDENSATE_WITH_LOW_CF;TARGET_COT_NOT_PROMOTED",
            })
            rows.append(rec); continue

        if not geom_cloud:
            rec.update({
                "resolver_state":"NO_TARGET_CLOUD_GEOMETRY_FOR_OPTICAL_RESOLUTION",
                "evidence_source":"GEOMETRY_NOT_CLOUD",
            })
            rows.append(rec); continue

        # Strict bounded interpolation: only *immediately adjacent sampled nodes*
        # on the same direction may support the hypothesis.  We do not skip over
        # unresolved nodes, and the interval is not treated as physical cloud width.
        d=float(target.distance_km)
        same=by_dir.get(float(target.direction_offset_deg), [])
        left_d,right_d=_adjacent_distance_nodes(same,d)
        if left_d is None or right_d is None:
            rec.update({"resolver_state":"ADJACENT_OPTICAL_BRACKET_UNAVAILABLE_ROUTE_EDGE",
                        "evidence_source":"NO_TWO_SIDED_ADJACENT_SUPPORT"})
            rows.append(rec); continue
        left_layers=[x for x in same if abs(float(x.distance_km)-left_d)<=1e-9]
        right_layers=[x for x in same if abs(float(x.distance_km)-right_d)<=1e-9]
        left,lf=_best_overlap_candidate(target,left_layers,min_vertical_overlap_fraction)
        right,rf=_best_overlap_candidate(target,right_layers,min_vertical_overlap_fraction)
        if left is None or right is None:
            rec.update({
                "left_support_distance_km":left_d,
                "right_support_distance_km":right_d,
                "resolver_state":"ADJACENT_OPTICAL_BRACKET_INCOMPLETE",
                "evidence_source":"ADJACENT_NATIVE_CONDENSATE_SUPPORT_INSUFFICIENT",
            })
            rows.append(rec); continue

        # Linear interpolation is a numerical estimate between two *measured model
        # nodes*. Preserve a lower/upper bracket so this is never mistaken for a
        # direct target retrieval.
        w=(d-left_d)/(right_d-left_d) if right_d>left_d else 0.5
        lc=float(left.cot); rc=float(right.cot)
        nominal=(1.0-w)*lc+w*rc
        rec.update({
            "target_optics_bounded":True,
            "target_cot_nominal":max(0.0,float(nominal)),
            "target_cot_lower_bound":max(0.0,min(lc,rc)),
            "target_cot_upper_bound":max(0.0,max(lc,rc)),
            "left_support_layer_id":left.layer_id,
            "right_support_layer_id":right.layer_id,
            "left_support_distance_km":left_d,
            "right_support_distance_km":right_d,
            "left_support_cot":lc,
            "right_support_cot":rc,
            "left_vertical_overlap_fraction":lf,
            "right_vertical_overlap_fraction":rf,
            "resolver_state":"ADJACENT_NATIVE_COT_BRACKET_BOUNDED",
            "evidence_source":"TWO_SIDED_ADJACENT_NATIVE_CONDENSATE_COT",
            "bound_level":2,
            "note":"BOUNDED_SPATIAL_INTERPOLATION_ONLY;NOT_DIRECT_TARGET_COT;SAMPLING_SPACING_IS_NOT_CLOUD_WIDTH",
        })
        rows.append(rec)
    return pd.DataFrame(rows)


def summarize_target_canvas_optical_evidence(evidence: pd.DataFrame) -> pd.DataFrame:
    if evidence is None or evidence.empty:
        return pd.DataFrame()
    rows=[]
    for a,g in evidence.groupby("solar_altitude_deg",sort=False):
        state=g.get("resolver_state",pd.Series(dtype=str)).astype(str)
        rows.append({
            "solar_altitude_deg":float(a),
            "canvas_count":int(len(g)),
            "direct_native_target_cot_count":int(state.eq("DIRECT_NATIVE_CONDENSATE_COT").sum()),
            "bounded_adjacent_native_cot_count":int(state.eq("ADJACENT_NATIVE_COT_BRACKET_BOUNDED").sum()),
            "cf_condensate_zero_conflict_count":int(state.eq("CF_CLOUD_CONDENSATE_ZERO_UNRESOLVED").sum()),
            "other_unresolved_target_optics_count":int((~state.isin(["DIRECT_NATIVE_CONDENSATE_COT","ADJACENT_NATIVE_COT_BRACKET_BOUNDED","CF_CLOUD_CONDENSATE_ZERO_UNRESOLVED"])).sum()),
            "target_optics_exact_ready_count":int(g.get("target_optics_ready",pd.Series(False,index=g.index)).astype(bool).sum()),
            "target_optics_bounded_count":int(g.get("target_optics_bounded",pd.Series(False,index=g.index)).astype(bool).sum()),
            "resolver_contract":"R4.9_TARGET_CANVAS_OPTICAL_EVIDENCE_NO_CF_TO_COT",
            "sampling_step_is_cloud_width":False,
        })
    return pd.DataFrame(rows)
