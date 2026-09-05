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
from .cloud_optics import condensate_extinction_m1, DEFAULT_LIQUID_REFF_UM, DEFAULT_ICE_REFF_UM


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


def _normalized_cloud_fraction(level: Mapping) -> Optional[float]:
    cf = level.get("cloud_fraction", np.nan)
    if not _finite(cf):
        return None
    f = float(cf)
    if f > 1.0 + 1e-9:
        f /= 100.0
    return max(0.0, min(1.0, f))


def _native_condensate_state(level: Mapping, cfg: ProviderCloudGeometryConfig) -> str:
    ql = level.get("cloud_liquid_water_kgkg", np.nan)
    qi = level.get("cloud_ice_water_kgkg", np.nan)
    if not (_finite(ql) and _finite(qi)):
        return "MISSING"
    q = max(0.0, float(ql)) + max(0.0, float(qi))
    return "POSITIVE" if q >= cfg.condensate_threshold_kgkg else "ZERO"


def classify_native_level(level: Mapping, cfg: ProviderCloudGeometryConfig) -> CloudFractionState:
    """Classify cloud *geometry* without letting optical evidence erase it.

    PhysicsCore V1.0-R4.5.2 explicitly decouples occupancy from optics. Native
    cloud fraction is geometry evidence. Positive native condensate can add
    independent occupancy evidence, but zero condensate cannot erase a non-zero
    cloud-fraction signal. Conversely, cloud fraction never fabricates COT.
    """
    f = _normalized_cloud_fraction(level)
    qstate = _native_condensate_state(level, cfg)

    if f is not None:
        if f >= cfg.occupied_fraction_min:
            return CloudFractionState.CLOUD_OCCUPIED
        if f > cfg.clear_fraction_max:
            return CloudFractionState.PARTIAL_OCCUPANCY
        # A very low/zero cloud fraction is normally clear, but independently
        # positive native condensate is still physical occupancy evidence.
        if qstate == "POSITIVE":
            return CloudFractionState.CLOUD_OCCUPIED
        return CloudFractionState.CLEAR

    if qstate == "POSITIVE":
        return CloudFractionState.CLOUD_OCCUPIED
    if qstate == "ZERO":
        return CloudFractionState.CLEAR
    return CloudFractionState.UNKNOWN


def native_level_evidence_consistency(level: Mapping, cfg: ProviderCloudGeometryConfig) -> str:
    """Audit geometry-vs-condensate agreement without changing either evidence.

    This is diagnostic provenance, not a score. A disagreement never invents
    optical depth and never silently deletes cloud-fraction occupancy evidence.
    """
    f = _normalized_cloud_fraction(level)
    qstate = _native_condensate_state(level, cfg)
    if f is None and qstate == "MISSING":
        return "OPTICS_AND_GEOMETRY_MISSING"
    if f is None:
        return "CONDENSATE_ONLY_POSITIVE" if qstate == "POSITIVE" else "CONDENSATE_ONLY_ZERO"
    if qstate == "MISSING":
        return "OPTICS_MISSING"
    cf_cloud = f > cfg.clear_fraction_max
    if cf_cloud and qstate == "ZERO":
        return "CF_CLOUD_CONDENSATE_ZERO"
    if (not cf_cloud) and qstate == "POSITIVE":
        return "CONDENSATE_CLOUD_CF_LOW"
    if cf_cloud and qstate == "POSITIVE":
        return "CONSISTENT_CLOUD"
    return "CONSISTENT_CLEAR"


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




def _derive_native_layer_optics(levels: Sequence[Mapping], z_base_km: float, z_top_km: float, cfg: ProviderCloudGeometryConfig = ProviderCloudGeometryConfig()) -> dict:
    """Derive target-cloud visible optical evidence from *native* condensate.

    This bridge never uses RH/cloud fraction/base-top geometry to invent COT.  A
    level contributes only when native liquid+ice mixing ratio, pressure and
    temperature are all finite.  The bulk extinction uses the explicit
    condensate + assumed-r_eff geometric-optics model already used by the legacy
    native optical diagnostic, but the integration is performed on native model
    levels rather than resampled display voxels.
    """
    if not levels:
        return {"evidence": EvidenceState.MISSING, "cot": None, "effective_radius_um": None,
                "quality": "NO_NATIVE_LEVELS"}
    recs=[]
    for x in levels:
        ql=x.get("cloud_liquid_water_kgkg", np.nan); qi=x.get("cloud_ice_water_kgkg", np.nan)
        p=x.get("pressure_hpa", np.nan); t=x.get("temperature_k", np.nan)
        z=x.get("altitude_agl_km", np.nan); cf=x.get("cloud_fraction", np.nan)
        if not (_finite(ql) and _finite(qi) and _finite(p) and _finite(t) and _finite(z)):
            recs.append(None); continue
        tk=float(t); ph=float(p)
        if tk <= 0 or ph <= 0:
            recs.append(None); continue
        rho=(ph*100.0)/(287.05*tk)
        lwc=max(0.0,float(ql))*rho*1000.0
        iwc=max(0.0,float(qi))*rho*1000.0
        ext=condensate_extinction_m1(lwc, iwc, cf, DEFAULT_LIQUID_REFF_UM, DEFAULT_ICE_REFF_UM)
        beta=ext.get("total_extinction_m1", np.nan)
        recs.append(None if not _finite(beta) else (float(z), max(0.0,float(beta)), max(0.0,float(ql)), max(0.0,float(qi))))
    valid=[r for r in recs if r is not None]
    if not valid:
        ev = EvidenceState.GEOMETRY_ONLY if any(classify_native_level(x, ProviderCloudGeometryConfig()) != CloudFractionState.UNKNOWN for x in levels) else EvidenceState.MISSING
        return {"evidence": ev, "cot": None, "effective_radius_um": None,
                "quality": "MISSING_NATIVE_CONDENSATE_OR_THERMODYNAMICS"}

    # Geometry/optics decoupling: if cloud fraction says cloud is present but all
    # native condensate values are zero/near-zero, this is evidence disagreement,
    # not proof that the cloud has COT=0. Preserve the CloudLayer but fail closed
    # on optical depth.
    positive_q = [r for r in valid if (r[2] + r[3]) >= NATIVE_CONDENSATE_THRESHOLD_KGKG]
    cf_cloud_levels = [x for x in levels if (_normalized_cloud_fraction(x) or 0.0) > cfg.clear_fraction_max]
    if not positive_q and cf_cloud_levels:
        return {"evidence": EvidenceState.GEOMETRY_ONLY, "cot": None, "effective_radius_um": None,
                "quality": "CF_CLOUD_CONDENSATE_ZERO"}

    consistency = [native_level_evidence_consistency(x, cfg) for x in levels]
    # Positive condensate with very low cloud fraction is also an unresolved
    # evidence conflict. Keep the geometry, but do not turn the conflicting
    # pair into a trusted COT by multiplying condensate with a near-zero CF.
    if "CONDENSATE_CLOUD_CF_LOW" in consistency:
        return {"evidence": EvidenceState.PARTIAL_OPTICS, "cot": None, "effective_radius_um": None,
                "quality": "CONDENSATE_CLOUD_CF_LOW"}
    disagreement = "CF_CLOUD_CONDENSATE_ZERO" in consistency
    evidence = (EvidenceState.PARTIAL_OPTICS if disagreement or len(valid) != len(levels)
                else EvidenceState.FULL)
    valid=sorted(valid, key=lambda r:r[0])
    if len(valid)==1:
        thickness_m=max(0.0,float(z_top_km)-float(z_base_km))*1000.0
        cot=valid[0][1]*thickness_m
    else:
        zs=np.array([r[0] for r in valid],dtype=float)*1000.0
        bs=np.array([r[1] for r in valid],dtype=float)
        cot=float(np.trapezoid(bs,zs))
        # Native occupied-level envelopes are centre based for multi-level layers.
        # Add half-cell support at both ends using nearest native spacing so the
        # optical integral represents finite native cells without crossing a
        # CLEAR/UNKNOWN gap.
        left=max(0.0,(valid[1][0]-valid[0][0])*500.0)
        right=max(0.0,(valid[-1][0]-valid[-2][0])*500.0)
        cot += bs[0]*left + bs[-1]*right
    ql_sum=sum(r[2] for r in valid); qi_sum=sum(r[3] for r in valid)
    if ql_sum+qi_sum>0:
        reff=(ql_sum*DEFAULT_LIQUID_REFF_UM + qi_sum*DEFAULT_ICE_REFF_UM)/(ql_sum+qi_sum)
    else:
        reff=None
    return {"evidence": evidence, "cot": max(0.0,float(cot)),
            "effective_radius_um": reff,
            "quality": "NATIVE_CONDENSATE_GEOMETRIC_OPTICS_ASSUMED_REFF"}

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
        optics = _derive_native_layer_optics(gpts, z_base, z_top, provider_cfg)
        optical_prov = ForecastFieldProvenance(
            provider=provider_cfg.provider, model="NATIVE_CONDENSATE_BULK_OPTICS",
            variable="cloud_optical_depth_from_native_condensate",
            source_type=SourceType.DERIVED_PHYSICAL,
            interpolation="NATIVE_LEVEL_VERTICAL_INTEGRATION",
            fallback="ASSUMED_REFF_LIQUID_10UM_ICE_30UM",
            missing_reason=None if optics["cot"] is not None else optics["quality"],
            extra={"optical_model": optics["quality"]},
        )
        consistency_values = [native_level_evidence_consistency(p, provider_cfg) for p in gpts]
        consistency_priority = [
            "CF_CLOUD_CONDENSATE_ZERO", "CONDENSATE_CLOUD_CF_LOW", "OPTICS_MISSING",
            "OPTICS_AND_GEOMETRY_MISSING", "CONSISTENT_CLOUD", "CONSISTENT_CLEAR",
            "CONDENSATE_ONLY_POSITIVE", "CONDENSATE_ONLY_ZERO",
        ]
        layer_consistency = next((x for x in consistency_priority if x in consistency_values), "UNKNOWN")
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
            effective_radius_um=optics["effective_radius_um"],
            cot=optics["cot"],
            geometry_confidence=_geometry_confidence(states),
            optical_evidence=optics["evidence"],
            evidence_consistency=layer_consistency,
            provenance=provenance + (optical_prov,),
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
