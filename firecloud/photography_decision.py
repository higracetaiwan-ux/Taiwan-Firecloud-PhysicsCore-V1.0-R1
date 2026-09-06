"""PhysicsCore V1.0-R5.7 Photography Decision Layer.

This is an outer operational interpretation layer. It never rewrites Formation
or Viewing physics. Its single purpose is to answer whether the firecloud
opportunity is photographable from the specified observer location.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def build_photography_decision(formation: pd.DataFrame, viewing_summary: pd.DataFrame, viewing_spectral_summary: pd.DataFrame | None = None) -> pd.DataFrame:
    cols = ["time", "solar_altitude_deg", "formation_state", "viewing_state",
            "viewing_spectral_state", "mean_view_transmission_650nm", "photography_spectral_modifier",
            "photography_outcome", "photography_opportunity", "reason", "note"]
    if viewing_summary is None or viewing_summary.empty:
        return pd.DataFrame(columns=cols)
    v = viewing_summary.copy()
    f = formation.copy() if formation is not None else pd.DataFrame()
    keys = [k for k in ["time", "solar_altitude_deg"] if k in v.columns and k in f.columns]
    if keys and not f.empty:
        merged = v.merge(f[[*keys, "formation_state"]].drop_duplicates(keys), on=keys, how="left")
    else:
        merged = v.copy(); merged["formation_state"] = np.nan
    if viewing_spectral_summary is not None and not viewing_spectral_summary.empty:
        sk=[k for k in ["time","solar_altitude_deg"] if k in merged.columns and k in viewing_spectral_summary.columns]
        if sk:
            keep=sk+[c for c in ["viewing_spectral_state","mean_view_transmission_650nm"] if c in viewing_spectral_summary.columns]
            merged=merged.merge(viewing_spectral_summary[keep].drop_duplicates(sk),on=sk,how="left")
    if "viewing_spectral_state" not in merged: merged["viewing_spectral_state"]="VIEW_SPECTRAL_UNRESOLVED"
    if "mean_view_transmission_650nm" not in merged: merged["mean_view_transmission_650nm"]=np.nan
    rows=[]
    for _, r in merged.iterrows():
        fs = str(r.get("formation_state") or "FORMATION_UNKNOWN")
        vs = str(r.get("viewing_state") or "VIEWING_UNKNOWN")
        if vs == "VIEWING_SEVERELY_OBSCURED":
            outcome = "FORMED_OR_POSSIBLY_FORMED_BUT_NOT_PHOTOGRAPHABLE_FROM_OBSERVER"
            opp = "BLOCKED"
            reason = "CLOUD_TO_OBSERVER_VIEW_SEVERELY_OBSCURED"
        elif vs == "VIEWING_PARTIALLY_OBSCURED":
            outcome = "PARTIALLY_PHOTOGRAPHABLE_IF_FORMATION_OCCURS"
            opp = "LIMITED"
            reason = "CLOUD_TO_OBSERVER_VIEW_PARTIALLY_OBSCURED"
        elif vs == "VIEWING_MINOR_OBSTRUCTION":
            outcome = "PHOTOGRAPHABLE_WITH_MINOR_FOREGROUND_OBSTRUCTION_IF_FORMATION_OCCURS"
            opp = "FAIR"
            reason = "CLOUD_TO_OBSERVER_VIEW_MINOR_OBSTRUCTION"
        elif vs == "VIEWING_PARTIAL_DATA":
            outcome = "PHOTOGRAPHABILITY_UNCERTAIN_DUE_TO_VIEWING_DATA_GAP"
            opp = "UNKNOWN"
            reason = "VIEWING_GEOMETRY_INTERSECTION_OCCUPANCY_UNRESOLVED"
        elif vs == "VIEWING_GEOMETRY_GOOD":
            if fs in {"FORMATION_CONFIRMED", "CONFIRMED"}:
                outcome = "PHOTOGRAPHABLE_FIRECLOUD"
                opp = "GOOD"
                reason = "FORMATION_CONFIRMED_AND_VIEW_GEOMETRY_GOOD"
            elif fs in {"FORMATION_FAILED", "FAILED", "NO_FORMATION"}:
                outcome = "VISIBLE_CLOUD_BUT_NO_FIRECLOUD_FORMATION"
                opp = "POOR"
                reason = "FORMATION_FAILED"
            else:
                outcome = "VIEW_OPEN_BUT_FORMATION_UNRESOLVED"
                opp = "UNKNOWN"
                reason = "FORMATION_UNRESOLVED"
        else:
            outcome = "PHOTOGRAPHY_OUTCOME_UNKNOWN"
            opp = "UNKNOWN"
            reason = "VIEWING_UNRESOLVED"
        ss=str(r.get("viewing_spectral_state") or "VIEW_SPECTRAL_UNRESOLVED")
        t650=r.get("mean_view_transmission_650nm")
        rows.append({"time": r.get("time"), "solar_altitude_deg": r.get("solar_altitude_deg"),
                     "formation_state": fs, "viewing_state": vs,
                     "viewing_spectral_state":ss,"mean_view_transmission_650nm":t650,
                     "photography_spectral_modifier":"DIAGNOSTIC_ONLY_UNCALIBRATED",
                     "photography_outcome": outcome, "photography_opportunity": opp,
                     "reason": reason,
                     "note": "OUTER_DECISION_LAYER_ONLY;FORMATION_AND_VIEWING_REMAIN_INDEPENDENT;VIEWING_SPECTRAL_DIAGNOSTIC_DOES_NOT_REWRITE_FORMATION;NO_SINGLE_PHYSICS_SCORE"})
    return pd.DataFrame(rows, columns=cols)
