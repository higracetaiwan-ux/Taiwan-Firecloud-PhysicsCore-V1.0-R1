"""PhysicsCore V1.0-R5.0 secondary forecast Target-Canvas optical evidence.

This module defines the contract and arbitration layer for a *second forecast
model* that can provide native/retrieved cloud optical evidence for target
Canvas clouds.  It does not synthesize COT from cloud fraction, RH, or cloud
geometry, and it never uses satellite observations as a forecast input.

Only records explicitly labelled ``FORECAST_MODEL_NATIVE_OPTICS`` with finite
COT and FULL optical evidence are eligible for exact target-optics support.
Multi-source disagreement is preserved as disagreement and is never averaged
away.
"""
from __future__ import annotations

import math
from typing import Iterable, Optional

import pandas as pd

from .contracts import CanvasCandidate, CloudScene


def _finite(v) -> bool:
    try:
        return bool(math.isfinite(float(v)))
    except Exception:
        return False


def _overlap_fraction(z0: float, z1: float, a0: float, a1: float) -> float:
    thick=max(1e-9,float(z1)-float(z0))
    ov=max(0.0,min(float(z1),float(a1))-max(float(z0),float(a0)))
    return max(0.0,min(1.0,ov/thick))


def validate_secondary_forecast_optical_evidence(df: Optional[pd.DataFrame]) -> pd.DataFrame:
    """Normalize and fail-closed validate secondary forecast optical records."""
    cols=[
        "provider","model","source_kind","valid_time","direction_offset_deg",
        "distance_km","z_base_km","z_top_km","cot","effective_radius_um",
        "phase","optical_evidence","provenance","status",
    ]
    if df is None or df.empty:
        return pd.DataFrame(columns=cols+[
            "secondary_exact_eligible","validation_state","validation_note"
        ])
    out=df.copy()
    for c in cols:
        if c not in out.columns:
            out[c]=None
    exact=[]; state=[]; note=[]
    for _,r in out.iterrows():
        kind=str(r.get("source_kind") or "")
        oe=str(r.get("optical_evidence") or "")
        cot=r.get("cot")
        provider=str(r.get("provider") or "")
        provenance=str(r.get("provenance") or "")
        geometry_ok=all(_finite(r.get(c)) for c in ["direction_offset_deg","distance_km","z_base_km","z_top_km"])
        eligible=(
            kind=="FORECAST_MODEL_NATIVE_OPTICS"
            and oe=="FULL"
            and _finite(cot) and float(cot)>=0.0
            and bool(provider) and bool(provenance)
            and geometry_ok
        )
        exact.append(bool(eligible))
        if eligible:
            state.append("VALID_SECONDARY_FORECAST_NATIVE_OPTICS")
            note.append("FORECAST_ONLY;NO_SATELLITE_FORECAST_INPUT;NO_CF_RH_GEOMETRY_TO_COT")
        else:
            state.append("SECONDARY_FORECAST_OPTICS_NOT_EXACT_ELIGIBLE")
            note.append("MISSING_OR_NON_NATIVE_OPTICAL_EVIDENCE;FAIL_CLOSED")
    out["secondary_exact_eligible"]=exact
    out["validation_state"]=state
    out["validation_note"]=note
    return out


def match_secondary_to_canvases(
    scene: CloudScene,
    canvases: Iterable[CanvasCandidate],
    secondary: Optional[pd.DataFrame],
    *,
    solar_altitude_deg: float,
    valid_time=None,
    min_vertical_overlap_fraction: float=0.50,
    max_distance_mismatch_km: float=10.0,
) -> pd.DataFrame:
    """Match validated secondary forecast native optics to target canvases.

    Distance tolerance is matching support only; it is not cloud width.
    """
    sec=validate_secondary_forecast_optical_evidence(secondary)
    if sec.empty:
        return pd.DataFrame()
    sec=sec[sec["secondary_exact_eligible"].astype(bool)].copy()
    if sec.empty:
        return pd.DataFrame()
    layer_by_id={x.layer_id:x for x in scene.layers}
    rows=[]
    for c in canvases:
        t=layer_by_id.get(c.cloud_layer_id)
        if t is None:
            continue
        cand=sec[(sec["direction_offset_deg"].astype(float)-float(t.direction_offset_deg)).abs()<=1e-6].copy()
        if cand.empty:
            continue
        cand["distance_mismatch_km"]=(cand["distance_km"].astype(float)-float(t.distance_km)).abs()
        cand=cand[cand["distance_mismatch_km"]<=float(max_distance_mismatch_km)]
        if cand.empty:
            continue
        cand["vertical_overlap_fraction"]=[
            _overlap_fraction(float(t.z_base_km),float(t.z_top_km),float(r.z_base_km),float(r.z_top_km))
            for r in cand.itertuples(index=False)
        ]
        cand=cand[cand["vertical_overlap_fraction"]>=float(min_vertical_overlap_fraction)]
        if cand.empty:
            continue
        cand=cand.sort_values(["vertical_overlap_fraction","distance_mismatch_km"],ascending=[False,True])
        r=cand.iloc[0]
        rows.append({
            "time":valid_time,
            "solar_altitude_deg":float(solar_altitude_deg),
            "canvas_id":c.canvas_id,
            "cloud_layer_id":c.cloud_layer_id,
            "primary_direction_offset_deg":float(t.direction_offset_deg),
            "primary_distance_km":float(t.distance_km),
            "secondary_provider":r.get("provider"),
            "secondary_model":r.get("model"),
            "secondary_cot":float(r.get("cot")),
            "secondary_effective_radius_um":r.get("effective_radius_um"),
            "secondary_phase":r.get("phase"),
            "secondary_distance_km":float(r.get("distance_km")),
            "secondary_z_base_km":float(r.get("z_base_km")),
            "secondary_z_top_km":float(r.get("z_top_km")),
            "distance_mismatch_km":float(r.get("distance_mismatch_km")),
            "vertical_overlap_fraction":float(r.get("vertical_overlap_fraction")),
            "secondary_provenance":r.get("provenance"),
            "secondary_status":"MATCHED_EXACT_FORECAST_NATIVE_OPTICS",
            "sampling_distance_is_cloud_width":False,
        })
    return pd.DataFrame(rows)


def arbitrate_primary_secondary(primary: pd.DataFrame, matched_secondary: Optional[pd.DataFrame]) -> pd.DataFrame:
    """Attach secondary evidence to R4.9 primary resolver without averaging.

    Rules:
    * primary exact + secondary exact: keep primary only when not materially
      contradictory; otherwise mark disagreement and revoke exact promotion;
    * primary unresolved + secondary exact: promote only when the primary does
      not contain an explicit zero-condensate or other direct conflict;
    * explicit primary conflict + secondary positive optics: disagreement,
      never automatic replacement.
    """
    if primary is None or primary.empty:
        return pd.DataFrame()
    out=primary.copy()
    sec_by={}
    if matched_secondary is not None and not matched_secondary.empty:
        sec_by={str(r.canvas_id):r for r in matched_secondary.itertuples(index=False)}
    for c in ["secondary_provider","secondary_model","secondary_cot","secondary_effective_radius_um",
              "secondary_phase","secondary_provenance","secondary_status","multi_source_state"]:
        if c not in out.columns:
            out[c]=None
    for i,r in out.iterrows():
        s=sec_by.get(str(r.get("canvas_id")))
        if s is None:
            out.at[i,"multi_source_state"]="NO_SECONDARY_FORECAST_OPTICAL_EVIDENCE"
            continue
        scot=float(s.secondary_cot)
        out.at[i,"secondary_provider"]=s.secondary_provider
        out.at[i,"secondary_model"]=s.secondary_model
        out.at[i,"secondary_cot"]=scot
        out.at[i,"secondary_effective_radius_um"]=s.secondary_effective_radius_um
        out.at[i,"secondary_phase"]=s.secondary_phase
        out.at[i,"secondary_provenance"]=s.secondary_provenance
        out.at[i,"secondary_status"]=s.secondary_status
        state=str(r.get("resolver_state") or "")
        p_ready=bool(r.get("target_optics_ready"))
        pcot=r.get("target_cot_nominal")
        direct_conflict=state in {
            "CF_CLOUD_CONDENSATE_ZERO_UNRESOLVED",
            "CONDENSATE_CLOUD_CF_LOW_CONFLICT",
        }
        if direct_conflict:
            out.at[i,"target_optics_ready"]=False
            out.at[i,"resolver_state"]="MULTISOURCE_DIRECT_CONFLICT_UNRESOLVED"
            out.at[i,"evidence_source"]="PRIMARY_DIRECT_CONFLICT_PLUS_SECONDARY_FORECAST_NATIVE_OPTICS"
            out.at[i,"multi_source_state"]="DISAGREEMENT_NOT_AVERAGED"
            out.at[i,"note"]="SECONDARY_FORECAST_OPTICS_CANNOT_ERASE_PRIMARY_DIRECT_CONFLICT"
            continue
        if p_ready and _finite(pcot):
            p=float(pcot)
            ratio=max(p,scot)/max(1e-9,min(p,scot)) if max(p,scot)>0 else 1.0
            if ratio<=2.0:
                out.at[i,"multi_source_state"]="MULTISOURCE_AGREEMENT_PRIMARY_RETAINED"
                out.at[i,"note"]="SECONDARY_SUPPORTS_PRIMARY;NO_AVERAGING"
            else:
                out.at[i,"target_optics_ready"]=False
                out.at[i,"resolver_state"]="MULTISOURCE_COT_DISAGREEMENT_UNRESOLVED"
                out.at[i,"evidence_source"]="PRIMARY_AND_SECONDARY_FORECAST_NATIVE_OPTICS_DISAGREE"
                out.at[i,"multi_source_state"]="DISAGREEMENT_NOT_AVERAGED"
                out.at[i,"note"]="COT_RATIO_GT_2;EXACT_PROMOTION_REVOKED"
            continue
        out.at[i,"target_optics_ready"]=True
        out.at[i,"target_optics_bounded"]=False
        out.at[i,"target_cot_nominal"]=scot
        out.at[i,"target_cot_lower_bound"]=scot
        out.at[i,"target_cot_upper_bound"]=scot
        out.at[i,"target_effective_radius_um"]=s.secondary_effective_radius_um
        out.at[i,"resolver_state"]="SECONDARY_FORECAST_NATIVE_OPTICS_EXACT"
        out.at[i,"evidence_source"]="SECONDARY_FORECAST_MODEL_NATIVE_OPTICS"
        out.at[i,"bound_level"]=3
        out.at[i,"multi_source_state"]="SECONDARY_EXACT_PROMOTED_NO_PRIMARY_DIRECT_CONFLICT"
        out.at[i,"note"]="FORECAST_MODEL_NATIVE_OPTICS;NO_CF_RH_GEOMETRY_TO_COT;NO_AVERAGING"
    return out
