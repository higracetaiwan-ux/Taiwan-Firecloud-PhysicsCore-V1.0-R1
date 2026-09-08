"""PhysicsCore V1.0-R5.7.27 Photography Decision Layer.

Formation-first outer operational interpretation.

Frozen contract:
- Formation answers whether a firecloud physically forms (Sun→CloudBase).
- Viewing answers whether an existing/possible target is visible (Cloud→Observer).
- Photography Decision may combine the two, but Viewing must never rewrite a
  Formation hard NO-GO into FAIR/GOOD/LIMITED.
- The decision timeline is driven by Formation, so the normal core analysis
  exports all 13 solar-altitude rows even when Viewing has target rows only for
  a subset of angles.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


FORMATION_CONFIRMED_STATES = {"FORMATION_CONFIRMED", "CONFIRMED"}
FORMATION_EXPLICIT_FAILED_STATES = {
    "FORMATION_FAILED",
    "FAILED",
    "NO_FORMATION",
    "NOT_FORMED_EARTH_SHADOW",
    "ILLUMINATION_BLOCKED",
    "NOT_FORMED_ILLUMINATION_BLOCKED",
}
NO_CANVAS_RESOLVED_STATES = {
    "CLEAR_RED_PATH_NO_CANVAS",
    "PARTIAL_RED_PATH_NO_CANVAS",
    "RED_PATH_ATTENUATED_NO_CANVAS",
    "NO_CANVAS_NO_DIRECT_RED_ACCESS",
    "NO_CANVAS_RED_PATH_CONFLICT",
    "NO_CANVAS_RED_PATH_UNKNOWN",
}


def formation_is_hard_no_go(state: object) -> bool:
    """True only for a resolved physical Formation NO-GO.

    ``NO_CANVAS_EVIDENCE`` is intentionally *not* included: historically it can
    mean that Canvas geometry evidence is absent/incomplete.  R5.7.26+ promotes
    resolved no-Canvas cases into one of ``NO_CANVAS_RESOLVED_STATES``.
    Missing/unknown evidence must never be converted into a physical NO-GO.
    """
    fs = str(state or "FORMATION_UNKNOWN")
    if fs in FORMATION_EXPLICIT_FAILED_STATES or fs in NO_CANVAS_RESOLVED_STATES:
        return True
    if fs.startswith("NO_CANVAS_") and fs != "NO_CANVAS_EVIDENCE":
        return True
    if fs.endswith("_NO_CANVAS"):
        return True
    return False


def _no_go_outcome(fs: str) -> tuple[str, str]:
    if fs == "NOT_FORMED_EARTH_SHADOW":
        return "NO_FIRECLOUD_EARTH_SHADOW", "FORMATION_NOT_FORMED_EARTH_SHADOW"
    if "NO_CANVAS" in fs:
        if fs == "CLEAR_RED_PATH_NO_CANVAS":
            return "NO_FIRECLOUD_NO_CANVAS_RED_PATH_OPEN", "FORMATION_NO_EFFECTIVE_CANVAS_RED_PATH_OPEN"
        return "NO_FIRECLOUD_NO_CANVAS", "FORMATION_NO_EFFECTIVE_CANVAS"
    if "ILLUMINATION_BLOCKED" in fs:
        return "NO_FIRECLOUD_ILLUMINATION_BLOCKED", "FORMATION_ILLUMINATION_BLOCKED"
    return "NO_FIRECLOUD_FORMATION_FAILED", "FORMATION_FAILED"


def build_photography_decision(
    formation: pd.DataFrame,
    viewing_summary: pd.DataFrame,
    viewing_spectral_summary: pd.DataFrame | None = None,
) -> pd.DataFrame:
    cols = [
        "time", "solar_altitude_deg", "formation_state", "formation_gate_state",
        "viewing_state", "viewing_spectral_state", "mean_view_transmission_650nm",
        "viewing_decision_role", "photography_spectral_modifier",
        "photography_outcome", "photography_opportunity", "reason", "note",
    ]

    f = formation.copy() if isinstance(formation, pd.DataFrame) else pd.DataFrame()
    v = viewing_summary.copy() if isinstance(viewing_summary, pd.DataFrame) else pd.DataFrame()

    # R5.7.27: Formation owns the decision timeline.  Viewing may legitimately
    # have rows only when a cloud target exists, but that must not collapse a
    # 13-angle Formation result into a 2-angle Photography Decision table.
    if not f.empty:
        key_cols = [c for c in ["time", "solar_altitude_deg"] if c in f.columns]
        base_keep = [*key_cols, "formation_state"] if "formation_state" in f.columns else key_cols
        merged = f[base_keep].drop_duplicates(key_cols if key_cols else None).copy()
        if "formation_state" not in merged.columns:
            merged["formation_state"] = "FORMATION_UNKNOWN"
        if not v.empty:
            keys = [k for k in ["time", "solar_altitude_deg"] if k in merged.columns and k in v.columns]
            if keys:
                vkeep = keys + [c for c in ["viewing_state"] if c in v.columns]
                merged = merged.merge(v[vkeep].drop_duplicates(keys), on=keys, how="left")
    elif not v.empty:
        merged = v.copy()
        merged["formation_state"] = "FORMATION_UNKNOWN"
    else:
        return pd.DataFrame(columns=cols)

    if "viewing_state" not in merged.columns:
        merged["viewing_state"] = np.nan

    if viewing_spectral_summary is not None and not viewing_spectral_summary.empty:
        sk = [k for k in ["time", "solar_altitude_deg"] if k in merged.columns and k in viewing_spectral_summary.columns]
        if sk:
            keep = sk + [c for c in ["viewing_spectral_state", "mean_view_transmission_650nm"] if c in viewing_spectral_summary.columns]
            merged = merged.merge(viewing_spectral_summary[keep].drop_duplicates(sk), on=sk, how="left")
    if "viewing_spectral_state" not in merged:
        merged["viewing_spectral_state"] = np.nan
    if "mean_view_transmission_650nm" not in merged:
        merged["mean_view_transmission_650nm"] = np.nan

    rows = []
    for _, r in merged.iterrows():
        fs = str(r.get("formation_state") or "FORMATION_UNKNOWN")
        hard_no_go = formation_is_hard_no_go(fs)
        confirmed = fs in FORMATION_CONFIRMED_STATES

        raw_vs = r.get("viewing_state")
        raw_ss = r.get("viewing_spectral_state")
        has_viewing = pd.notna(raw_vs) and str(raw_vs).strip() not in {"", "nan", "None"}

        # No physical target exists in resolved no-Canvas states, therefore a
        # missing Cloud→Observer target path is N/A, not an error.  For other
        # states, absence of Viewing remains unresolved rather than fabricated.
        if has_viewing:
            vs = str(raw_vs)
        elif "NO_CANVAS" in fs:
            vs = "VIEWING_NOT_APPLICABLE_NO_FORMED_TARGET"
        else:
            vs = "VIEWING_NOT_EVALUATED"

        if pd.notna(raw_ss) and str(raw_ss).strip() not in {"", "nan", "None"}:
            ss = str(raw_ss)
        elif "NO_CANVAS" in fs:
            ss = "VIEW_SPECTRAL_NOT_APPLICABLE_NO_TARGET"
        else:
            ss = "VIEW_SPECTRAL_UNRESOLVED"

        t650 = r.get("mean_view_transmission_650nm")

        # Formation hard gate is evaluated before any Viewing interpretation.
        # Viewing evidence is preserved in the row but becomes diagnostic-only.
        if hard_no_go:
            outcome, reason = _no_go_outcome(fs)
            opp = "NO_GO"
            formation_gate_state = "FORMATION_HARD_NO_GO"
            viewing_role = "DIAGNOSTIC_ONLY_FORMATION_NO_GO"
        else:
            formation_gate_state = "FORMATION_CONFIRMED" if confirmed else "FORMATION_NOT_CONFIRMED"
            viewing_role = "PHOTOGRAPHABILITY_MODIFIER"
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
                if confirmed:
                    outcome = "PHOTOGRAPHABLE_FIRECLOUD"
                    opp = "GOOD"
                    reason = "FORMATION_CONFIRMED_AND_VIEW_GEOMETRY_GOOD"
                elif fs in FORMATION_EXPLICIT_FAILED_STATES:
                    # Defensive fallback; normally caught by hard_no_go above.
                    outcome = "NO_FIRECLOUD_FORMATION_FAILED"
                    opp = "NO_GO"
                    reason = "FORMATION_FAILED"
                else:
                    outcome = "VIEW_OPEN_BUT_FORMATION_UNRESOLVED"
                    opp = "UNKNOWN"
                    reason = "FORMATION_UNRESOLVED"
            elif vs == "VIEWING_NOT_APPLICABLE_NO_FORMED_TARGET":
                outcome = "NO_PHOTOGRAPHIC_TARGET"
                opp = "NO_GO" if hard_no_go else "UNKNOWN"
                reason = "NO_FORMED_TARGET_FOR_VIEWING"
            else:
                outcome = "PHOTOGRAPHY_OUTCOME_UNKNOWN"
                opp = "UNKNOWN"
                reason = "VIEWING_UNRESOLVED"

        rows.append({
            "time": r.get("time"),
            "solar_altitude_deg": r.get("solar_altitude_deg"),
            "formation_state": fs,
            "formation_gate_state": formation_gate_state,
            "viewing_state": vs,
            "viewing_spectral_state": ss,
            "mean_view_transmission_650nm": t650,
            "viewing_decision_role": viewing_role,
            "photography_spectral_modifier": "DIAGNOSTIC_ONLY_UNCALIBRATED",
            "photography_outcome": outcome,
            "photography_opportunity": opp,
            "reason": reason,
            "note": (
                "OUTER_DECISION_LAYER_ONLY;FORMATION_FIRST_HARD_GATE;"
                "FORMATION_AND_VIEWING_REMAIN_INDEPENDENT;"
                "VIEWING_CANNOT_OVERRIDE_FORMATION_NO_GO;"
                "VIEWING_SPECTRAL_DIAGNOSTIC_DOES_NOT_REWRITE_FORMATION;"
                "NO_SINGLE_PHYSICS_SCORE"
            ),
        })
    return pd.DataFrame(rows, columns=cols)
