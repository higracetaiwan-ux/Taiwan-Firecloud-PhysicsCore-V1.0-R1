"""PhysicsCore V1.0-R5.6.1 Photography Decision Layer.

This is an outer operational interpretation layer. It never rewrites Formation
or Viewing physics. Its single purpose is to answer whether the firecloud
opportunity is photographable from the specified observer location.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def build_photography_decision(formation: pd.DataFrame, viewing_summary: pd.DataFrame) -> pd.DataFrame:
    cols = ["time", "solar_altitude_deg", "formation_state", "viewing_state",
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
        rows.append({"time": r.get("time"), "solar_altitude_deg": r.get("solar_altitude_deg"),
                     "formation_state": fs, "viewing_state": vs,
                     "photography_outcome": outcome, "photography_opportunity": opp,
                     "reason": reason,
                     "note": "OUTER_DECISION_LAYER_ONLY;FORMATION_AND_VIEWING_REMAIN_INDEPENDENT;NO_SINGLE_PHYSICS_SCORE"})
    return pd.DataFrame(rows, columns=cols)
