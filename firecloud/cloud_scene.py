"""Native-model cloud-layer reconstruction for PhysicsCore V1.0 R1.

The segmentation is intentionally performed on native pressure/model levels.
A native CLEAR level breaks vertical continuity.  Interpolated 0.5-km voxels are
not used to invent a single cloud base/top spanning clear gaps.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Optional, Sequence
import math
import numpy as np
import pandas as pd

from .contracts import (
    CloudFractionState, CloudLayer, CloudScene, EvidenceState,
    ForecastFieldProvenance, GeometryConfidence, SourceType,
)
from .native_cloud import native_levels_from_row, NATIVE_CONDENSATE_THRESHOLD_KGKG


@dataclass(frozen=True)
class ProviderCloudGeometryConfig:
    provider: str = "GFS_NATIVE"
    clear_fraction_max: float = 0.01
    occupied_fraction_min: float = 0.50
    condensate_threshold_kgkg: float = NATIVE_CONDENSATE_THRESHOLD_KGKG


def _finite(v) -> bool:
    try:
        return bool(math.isfinite(float(v)))
    except Exception:
        return False


def classify_native_level(level: Mapping, cfg: ProviderCloudGeometryConfig) -> CloudFractionState:
    """Classify occupancy without converting cloud fraction into COT.

    Condensate is used as physical occupancy evidence when available.  Cloud
    fraction is geometry/occupancy evidence only; it never fabricates optics.
    """
    ql = level.get("cloud_liquid_water_kgkg", np.nan)
    qi = level.get("cloud_ice_water_kgkg", np.nan)
    cf = level.get("cloud_fraction", np.nan)
    if _finite(ql) and _finite(qi):
        q = max(0.0, float(ql)) + max(0.0, float(qi))
        if q >= cfg.condensate_threshold_kgkg:
            return CloudFractionState.CLOUD_OCCUPIED
        # Native zero/near-zero condensate is affirmative CLEAR optical/occupancy
        # evidence at that model level, not Missing.
        return CloudFractionState.CLEAR
    if _finite(cf):
        f = float(cf)
        # Providers may expose 0..1 or 0..100 fractions.
        if f > 1.0 + 1e-9:
            f /= 100.0
        f = max(0.0, min(1.0, f))
        if f <= cfg.clear_fraction_max:
            return CloudFractionState.CLEAR
        if f >= cfg.occupied_fraction_min:
            return CloudFractionState.CLOUD_OCCUPIED
        return CloudFractionState.PARTIAL_OCCUPANCY
    return CloudFractionState.UNKNOWN


def _optical_evidence(levels: Sequence[Mapping]) -> EvidenceState:
    if not levels:
        return EvidenceState.MISSING
    pairs = []
    for x in levels:
        ql, qi = x.get("cloud_liquid_water_kgkg", np.nan), x.get("cloud_ice_water_kgkg", np.nan)
        pairs.append(_finite(ql) and _finite(qi))
    if all(pairs):
        return EvidenceState.FULL
    if any(pairs):
        return EvidenceState.PARTIAL_OPTICS
    return EvidenceState.GEOMETRY_ONLY


def _geometry_confidence(states: Sequence[CloudFractionState]) -> GeometryConfidence:
    if states and all(s in (CloudFractionState.CLEAR, CloudFractionState.CLOUD_OCCUPIED) for s in states):
        return GeometryConfidence.HIGH
    if states and all(s != CloudFractionState.UNKNOWN for s in states):
        return GeometryConfidence.MEDIUM
    if any(s != CloudFractionState.UNKNOWN for s in states):
        return GeometryConfidence.LOW
    return GeometryConfidence.UNKNOWN


def segment_native_levels(
    levels: Sequence[Mapping],
    *,
    direction_offset_deg: float,
    distance_km: float,
    provider_cfg: ProviderCloudGeometryConfig = ProviderCloudGeometryConfig(),
    provenance: tuple[ForecastFieldProvenance, ...] = (),
) -> list[CloudLayer]:
    """Split one native vertical column into independent layers.

    Rules frozen for V1:
    * native CLEAR gaps split layers;
    * UNKNOWN does not bridge layers silently;
    * PARTIAL_OCCUPANCY is geometry evidence, not optical depth;
    * layer base/top are bounded by native level geometry, not display voxels.
    """
    pts = sorted((dict(x) for x in levels), key=lambda x: float(x["altitude_agl_km"]))
    if not pts:
        return []
    tagged = [(p, classify_native_level(p, provider_cfg)) for p in pts]
    groups: list[list[tuple[dict, CloudFractionState]]] = []
    cur: list[tuple[dict, CloudFractionState]] = []
    for p, state in tagged:
        if state in (CloudFractionState.CLEAR, CloudFractionState.UNKNOWN):
            if cur:
                groups.append(cur); cur = []
            continue
        cur.append((p, state))
    if cur:
        groups.append(cur)

    out: list[CloudLayer] = []
    for i, grp in enumerate(groups, 1):
        gpts = [p for p, _ in grp]
        states = [s for _, s in grp]
        z = [float(p["altitude_agl_km"]) for p in gpts]
        # R3.1 native vertical support: an occupied native pressure/model level
        # represents a finite native layer cell, not a zero-thickness plane.  We
        # derive support from neighbouring *native* level centres (half-level
        # boundaries).  This does not bridge CLEAR/UNKNOWN gaps and does not use
        # the 0.5-km visualization grid.
        if len(z) > 1:
            # Multi-level layers keep their native occupied-level envelope, which
            # preserves the R1 segmentation contract and never spans a CLEAR gap.
            z_base, z_top = min(z), max(z)
        else:
            # Only the pathological single occupied native level needs explicit
            # half-level support so slant intersections do not see zero thickness.
            all_z = [float(x[0]["altitude_agl_km"]) for x in tagged]
            j = next(j for j, x in enumerate(tagged) if float(x[0]["altitude_agl_km"]) == z[0])
            zz = z[0]
            if j > 0:
                z_base = 0.5*(all_z[j-1]+zz)
            elif len(all_z)>1:
                z_base = max(0.0, zz-0.5*(all_z[1]-zz))
            else:
                z_base = max(0.0, zz-0.125)
            if j < len(all_z)-1:
                z_top = 0.5*(zz+all_z[j+1])
            elif len(all_z)>1:
                z_top = zz+0.5*(zz-all_z[j-1])
            else:
                z_top = zz+0.125
        cfs = []
        qls = []; qis = []
        for p in gpts:
            cf = p.get("cloud_fraction", np.nan)
            if _finite(cf):
                cf = float(cf); cf = cf/100.0 if cf > 1.0 + 1e-9 else cf
                cfs.append(max(0.0, min(1.0, cf)))
            if _finite(p.get("cloud_liquid_water_kgkg", np.nan)):
                qls.append(max(0.0, float(p["cloud_liquid_water_kgkg"])))
            if _finite(p.get("cloud_ice_water_kgkg", np.nan)):
                qis.append(max(0.0, float(p["cloud_ice_water_kgkg"])))
        ql = float(np.mean(qls)) if qls else None
        qi = float(np.mean(qis)) if qis else None
        if ql is None or qi is None:
            phase = "UNKNOWN"
        elif ql >= provider_cfg.condensate_threshold_kgkg and qi >= provider_cfg.condensate_threshold_kgkg:
            phase = "MIXED"
        elif qi >= provider_cfg.condensate_threshold_kgkg:
            phase = "ICE"
        elif ql >= provider_cfg.condensate_threshold_kgkg:
            phase = "LIQUID"
        else:
            phase = "UNKNOWN"
        occupancy = (CloudFractionState.CLOUD_OCCUPIED
                     if CloudFractionState.CLOUD_OCCUPIED in states
                     else CloudFractionState.PARTIAL_OCCUPANCY)
        out.append(CloudLayer(
            layer_id=f"dir{direction_offset_deg:+.1f}_d{distance_km:.1f}_L{i}",
            direction_offset_deg=float(direction_offset_deg),
            distance_km=float(distance_km),
            z_base_km=z_base,
            z_top_km=z_top,
            cloud_fraction_state=occupancy,
            cloud_fraction=(float(np.mean(cfs)) if cfs else None),
            liquid_condensate_kgkg=ql,
            ice_condensate_kgkg=qi,
            phase=phase,
            geometry_confidence=_geometry_confidence(states),
            optical_evidence=_optical_evidence(gpts),
            provenance=provenance,
            geometry_source="NATIVE_MODEL_LEVELS",
        ))
    return out


def build_cloud_scene_from_native_route(
    route_at_time: pd.DataFrame,
    pressure_levels_hpa: Sequence[int],
    *,
    valid_time=None,
    provider_cfg: ProviderCloudGeometryConfig = ProviderCloudGeometryConfig(),
) -> CloudScene:
    layers: list[CloudLayer] = []
    geometric_columns = 0; total_columns = 0; optical_columns = 0
    for _, row in route_at_time.iterrows():
        total_columns += 1
        pts = native_levels_from_row(row, pressure_levels_hpa)
        if pts:
            geometric_columns += 1
        prov = (ForecastFieldProvenance(
            provider=provider_cfg.provider,
            model=str(row.get("native_profile_source", "GFS_NATIVE")),
            valid_time=valid_time,
            variable="native_cloud_geometry_and_condensate",
            source_type=SourceType.NATIVE_FORECAST,
            missing_reason=None if pts else "NO_NATIVE_VERTICAL_GEOMETRY",
        ),)
        seg = segment_native_levels(
            pts,
            direction_offset_deg=float(row.get("direction_offset_deg", 0.0)),
            distance_km=float(row.get("distance_km", 0.0)),
            provider_cfg=provider_cfg,
            provenance=prov,
        )
        layers.extend(seg)
        if seg and all(x.optical_evidence == EvidenceState.FULL for x in seg):
            optical_columns += 1
    denom = max(1, total_columns)
    return CloudScene(
        valid_time=valid_time,
        layers=tuple(layers),
        geometry_completeness=geometric_columns/denom,
        optics_completeness=optical_columns/denom,
    )
