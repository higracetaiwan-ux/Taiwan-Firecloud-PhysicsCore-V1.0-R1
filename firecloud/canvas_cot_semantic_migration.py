"""R5.7.41.2 Production COT semantic migration contract / shadow mode.

This module evaluates whether the R5.7.41 exact-target-envelope, in-cloud COT
estimate is *eligible to be considered* as a future Production Target COT.
It does not perform the semantic switch.

Frozen rules
------------
* Cloud fraction is horizontal occupancy / Canvas coverage and must not scale
  the candidate in-cloud COT.
* RH must not create condensate or COT.
* Missing != zero != clear.
* Direct optical evidence conflicts fail closed.
* The current candidate still uses explicit assumed effective radii and is
  therefore named ``IN_CLOUD_COT_ESTIMATE_ASSUMED_REFF``, not native/exact COT.
* Production Target COT and Formation remain unchanged in shadow mode.
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd

MIGRATION_CONTRACT = (
    "PRODUCTION_COT_SEMANTIC_MIGRATION_SHADOW_MODE;"
    "LEGACY_CF_SCALED_GRID_CELL_MEAN_REMAINS_PRODUCTION;"
    "INCLOUD_EXACT_TARGET_ENVELOPE_ASSUMED_REFF_IS_SHADOW_CANDIDATE;"
    "CLOUD_FRACTION_IS_COVERAGE_NOT_COT;NO_CF_RH_TO_CANDIDATE_COT;"
    "DIRECT_CONFLICT_FAIL_CLOSED;NO_PRODUCTION_SWITCH;"
    "NO_COT_PROMOTION;NO_FORMATION_PROMOTION"
)

PRODUCTION_SOURCE_LEGACY = "LEGACY_CF_SCALED_GRID_CELL_MEAN"
SHADOW_SOURCE_INCLOUD = "IN_CLOUD_EXACT_ENVELOPE_ASSUMED_REFF"
SHADOW_SEMANTICS = "IN_CLOUD_COT_ESTIMATE_ASSUMED_REFF"

MIGRATION_COLUMNS = [
    "time", "solar_altitude_deg", "canvas_id", "cloud_layer_id",
    "direction_offset_deg", "distance_km",
    "target_z_base_km", "target_z_top_km", "target_thickness_km",
    "cloud_fraction", "canvas_coverage_semantics",
    "legacy_grid_cell_mean_cot", "legacy_cot_semantics",
    "in_cloud_target_cot", "in_cloud_cot_semantics",
    "cot_migration_delta", "cot_migration_ratio",
    "target_envelope_valid", "vertical_native_evidence_sufficient",
    "direct_evidence_conflict_free", "condensate_evidence_complete",
    "no_cf_used_for_candidate_cot", "no_rh_used_for_condensate",
    "reff_provenance_state", "vertical_integration_contract_pass",
    "migration_eligibility_state", "migration_ineligibility_reasons",
    "shadow_candidate_eligible",
    "production_target_cot_source", "shadow_candidate_cot_source",
    "production_switch_performed", "production_target_cot_replaced",
    "cot_promotion_allowed", "formation_promotion_allowed",
    "migration_contract",
]

SUMMARY_COLUMNS = [
    "solar_altitude_deg", "target_count", "shadow_candidate_eligible_count",
    "shadow_candidate_ineligible_count", "direct_conflict_count",
    "vertical_evidence_insufficient_count", "condensate_incomplete_count",
    "assumed_reff_count", "mean_legacy_grid_cell_mean_cot",
    "mean_in_cloud_target_cot", "mean_cot_migration_delta",
    "mean_cot_migration_ratio", "production_switch_performed_count",
    "cot_promotion_allowed_count", "formation_promotion_allowed_count",
    "migration_contract",
]


def _finite(v) -> bool:
    try:
        return bool(math.isfinite(float(v)))
    except Exception:
        return False


def _as_bool(v) -> bool:
    if isinstance(v, str):
        return v.strip().lower() in {"1", "true", "yes", "y"}
    try:
        return bool(v) and not pd.isna(v)
    except Exception:
        return False


def _eligibility(row: pd.Series) -> tuple[bool, list[str], dict[str, bool | str]]:
    zb = row.get("target_z_base_km", np.nan)
    zt = row.get("target_z_top_km", np.nan)
    envelope_valid = _finite(zb) and _finite(zt) and float(zt) > float(zb)

    vertical_sufficient = (
        _as_bool(row.get("vertical_bracketing_complete", False))
        and int(row.get("native_sample_count_inside_target", 0) or 0) >= 2
        and int(row.get("expected_supplement_missing_count", 0) or 0) == 0
    )
    conflict_free = not _as_bool(row.get("direct_target_evidence_conflict", False))

    known_frac = row.get("native_condensate_known_fraction_inside_target", np.nan)
    missing_count = row.get("native_condensate_missing_count_inside_target", np.nan)
    condensate_complete = (
        _finite(known_frac) and float(known_frac) >= 1.0 - 1.0e-12
        and _finite(missing_count) and int(float(missing_count)) == 0
    )

    no_cf = not _as_bool(row.get("cloud_fraction_used_for_cot", False))
    no_rh = not _as_bool(row.get("rh_used_to_infer_condensate", False))

    lr = row.get("assumed_liquid_reff_um", np.nan)
    ir = row.get("assumed_ice_reff_um", np.nan)
    reff_explicit = _finite(lr) and float(lr) > 0 and _finite(ir) and float(ir) > 0
    reff_state = "ASSUMED_DEFAULTS_EXPLICIT" if reff_explicit else "REFF_PROVENANCE_INCOMPLETE"

    cot = row.get("cot_estimate_assumed_reff", np.nan)
    integration_pass = (
        str(row.get("cot_diagnostic_state", "")) == "COT_ESTIMATE_ASSUMED_REFF"
        and str(row.get("cot_diagnostic_semantics", "")) == "DIAGNOSTIC_ASSUMED_REFF_NOT_NATIVE_COT"
        and _finite(cot) and float(cot) >= 0.0
    )

    gates = {
        "TARGET_ENVELOPE_INVALID": envelope_valid,
        "VERTICAL_NATIVE_EVIDENCE_INSUFFICIENT": vertical_sufficient,
        "DIRECT_EVIDENCE_CONFLICT": conflict_free,
        "CONDENSATE_EVIDENCE_INCOMPLETE": condensate_complete,
        "CLOUD_FRACTION_USED_FOR_CANDIDATE_COT": no_cf,
        "RH_USED_TO_INFER_CONDENSATE": no_rh,
        "REFF_PROVENANCE_INCOMPLETE": reff_explicit,
        "VERTICAL_INTEGRATION_CONTRACT_FAILED": integration_pass,
    }
    reasons = [reason for reason, ok in gates.items() if not ok]
    eligible = not reasons
    detail = {
        "target_envelope_valid": envelope_valid,
        "vertical_native_evidence_sufficient": vertical_sufficient,
        "direct_evidence_conflict_free": conflict_free,
        "condensate_evidence_complete": condensate_complete,
        "no_cf_used_for_candidate_cot": no_cf,
        "no_rh_used_for_condensate": no_rh,
        "reff_provenance_state": reff_state,
        "vertical_integration_contract_pass": integration_pass,
    }
    return eligible, reasons, detail


def build_canvas_cot_semantic_migration_shadow(
    target_optics: pd.DataFrame,
    vertical_overlap: pd.DataFrame,
) -> pd.DataFrame:
    if target_optics is None or target_optics.empty or vertical_overlap is None or vertical_overlap.empty:
        return pd.DataFrame(columns=MIGRATION_COLUMNS)

    keys = ["time", "solar_altitude_deg", "canvas_id", "cloud_layer_id"]
    left_cols = [c for c in keys + [
        "direction_offset_deg", "distance_km", "cloud_fraction",
        "target_cot_nominal", "direct_native_cot", "target_cot_semantics",
        "target_optical_truth_state", "resolver_state",
    ] if c in target_optics.columns]
    right_cols = [c for c in keys + [
        "target_z_base_km", "target_z_top_km", "target_thickness_km",
        "direct_target_evidence_conflict", "native_sample_count_inside_target",
        "native_condensate_known_fraction_inside_target",
        "native_condensate_missing_count_inside_target",
        "expected_supplement_missing_count", "vertical_bracketing_complete",
        "cot_diagnostic_state", "cot_estimate_assumed_reff",
        "cot_diagnostic_semantics", "assumed_liquid_reff_um",
        "assumed_ice_reff_um", "cloud_fraction_used_for_cot",
        "rh_used_to_infer_condensate",
    ] if c in vertical_overlap.columns]

    merged = target_optics[left_cols].merge(vertical_overlap[right_cols], on=keys, how="inner")
    rows: list[dict] = []
    for _, r in merged.iterrows():
        eligible, reasons, detail = _eligibility(r)
        legacy = r.get("target_cot_nominal", np.nan)
        inc = r.get("cot_estimate_assumed_reff", np.nan)
        delta = float(inc) - float(legacy) if _finite(inc) and _finite(legacy) else np.nan
        ratio = float(inc) / float(legacy) if _finite(inc) and _finite(legacy) and abs(float(legacy)) > 1.0e-15 else np.nan
        rows.append({
            "time": r.get("time"),
            "solar_altitude_deg": r.get("solar_altitude_deg"),
            "canvas_id": r.get("canvas_id"),
            "cloud_layer_id": r.get("cloud_layer_id"),
            "direction_offset_deg": r.get("direction_offset_deg"),
            "distance_km": r.get("distance_km"),
            "target_z_base_km": r.get("target_z_base_km"),
            "target_z_top_km": r.get("target_z_top_km"),
            "target_thickness_km": r.get("target_thickness_km"),
            "cloud_fraction": r.get("cloud_fraction", np.nan),
            "canvas_coverage_semantics": "HORIZONTAL_OCCUPANCY_SEPARATE_FROM_COT",
            "legacy_grid_cell_mean_cot": legacy if _finite(legacy) else np.nan,
            "legacy_cot_semantics": "GRID_CELL_MEAN_CF_SCALED_LEGACY_PRODUCTION",
            "in_cloud_target_cot": inc if _finite(inc) else np.nan,
            "in_cloud_cot_semantics": SHADOW_SEMANTICS,
            "cot_migration_delta": delta,
            "cot_migration_ratio": ratio,
            **detail,
            "migration_eligibility_state": "ELIGIBLE_SHADOW_CANDIDATE" if eligible else "INELIGIBLE_SHADOW_CANDIDATE",
            "migration_ineligibility_reasons": "" if eligible else ";".join(reasons),
            "shadow_candidate_eligible": bool(eligible),
            "production_target_cot_source": PRODUCTION_SOURCE_LEGACY,
            "shadow_candidate_cot_source": SHADOW_SOURCE_INCLOUD,
            "production_switch_performed": False,
            "production_target_cot_replaced": False,
            "cot_promotion_allowed": False,
            "formation_promotion_allowed": False,
            "migration_contract": MIGRATION_CONTRACT,
        })
    return pd.DataFrame(rows, columns=MIGRATION_COLUMNS)


def summarize_canvas_cot_semantic_migration_shadow(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    rows = []
    for angle, g in df.groupby("solar_altitude_deg", dropna=False, sort=False):
        eligible = g["shadow_candidate_eligible"].fillna(False).astype(bool)
        reasons = g["migration_ineligibility_reasons"].fillna("").astype(str)
        legacy = pd.to_numeric(g["legacy_grid_cell_mean_cot"], errors="coerce")
        inc = pd.to_numeric(g["in_cloud_target_cot"], errors="coerce")
        delta = pd.to_numeric(g["cot_migration_delta"], errors="coerce")
        ratio = pd.to_numeric(g["cot_migration_ratio"], errors="coerce")
        rows.append({
            "solar_altitude_deg": float(angle),
            "target_count": int(len(g)),
            "shadow_candidate_eligible_count": int(eligible.sum()),
            "shadow_candidate_ineligible_count": int((~eligible).sum()),
            "direct_conflict_count": int(reasons.str.contains("DIRECT_EVIDENCE_CONFLICT", regex=False).sum()),
            "vertical_evidence_insufficient_count": int(reasons.str.contains("VERTICAL_NATIVE_EVIDENCE_INSUFFICIENT", regex=False).sum()),
            "condensate_incomplete_count": int(reasons.str.contains("CONDENSATE_EVIDENCE_INCOMPLETE", regex=False).sum()),
            "assumed_reff_count": int(g["reff_provenance_state"].astype(str).eq("ASSUMED_DEFAULTS_EXPLICIT").sum()),
            "mean_legacy_grid_cell_mean_cot": float(legacy.mean()) if legacy.notna().any() else np.nan,
            "mean_in_cloud_target_cot": float(inc.mean()) if inc.notna().any() else np.nan,
            "mean_cot_migration_delta": float(delta.mean()) if delta.notna().any() else np.nan,
            "mean_cot_migration_ratio": float(ratio.mean()) if ratio.notna().any() else np.nan,
            "production_switch_performed_count": int(g["production_switch_performed"].fillna(False).astype(bool).sum()),
            "cot_promotion_allowed_count": int(g["cot_promotion_allowed"].fillna(False).astype(bool).sum()),
            "formation_promotion_allowed_count": int(g["formation_promotion_allowed"].fillna(False).astype(bool).sum()),
            "migration_contract": MIGRATION_CONTRACT,
        })
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)
