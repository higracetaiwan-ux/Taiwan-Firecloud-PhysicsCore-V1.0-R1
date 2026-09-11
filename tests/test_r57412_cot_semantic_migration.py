import math
import pandas as pd

from firecloud.canvas_cot_semantic_migration import (
    build_canvas_cot_semantic_migration_shadow,
    summarize_canvas_cot_semantic_migration_shadow,
)
from firecloud.case_integrity import build_analysis_integrity_audit


def _target():
    return pd.DataFrame([{
        "time":"2026-09-11T18:03:43+08:00", "solar_altitude_deg":0.0,
        "canvas_id":"c1", "cloud_layer_id":"l1", "direction_offset_deg":0.0,
        "distance_km":0.0, "cloud_fraction":0.409,
        "target_cot_nominal":0.0073622908948011, "direct_native_cot":0.0073622908948011,
        "target_cot_semantics":"EXACT_VALUE", "target_optical_truth_state":"EXACT_PRIMARY_NATIVE",
        "resolver_state":"DIRECT_NATIVE_CONDENSATE_COT",
    }])


def _overlap(*, conflict=False, missing=0, bracket=True, cot=0.01335034023467):
    return pd.DataFrame([{
        "time":"2026-09-11T18:03:43+08:00", "solar_altitude_deg":0.0,
        "canvas_id":"c1", "cloud_layer_id":"l1",
        "target_z_base_km":11.05813375, "target_z_top_km":12.545905,
        "target_thickness_km":1.48777125,
        "direct_target_evidence_conflict":conflict,
        "native_sample_count_inside_target":3,
        "native_condensate_known_fraction_inside_target":1.0 if not missing else 2/3,
        "native_condensate_missing_count_inside_target":missing,
        "expected_supplement_missing_count":missing,
        "vertical_bracketing_complete":bracket,
        "cot_diagnostic_state":"BLOCKED_DIRECT_EVIDENCE_CONFLICT" if conflict else "COT_ESTIMATE_ASSUMED_REFF",
        "cot_estimate_assumed_reff":float('nan') if conflict else cot,
        "cot_diagnostic_semantics":"UNRESOLVED_CONFLICT" if conflict else "DIAGNOSTIC_ASSUMED_REFF_NOT_NATIVE_COT",
        "assumed_liquid_reff_um":10.0, "assumed_ice_reff_um":30.0,
        "cloud_fraction_used_for_cot":False, "rh_used_to_infer_condensate":False,
    }])


def test_shadow_candidate_can_be_eligible_without_switching_production():
    out = build_canvas_cot_semantic_migration_shadow(_target(), _overlap())
    assert len(out) == 1
    r = out.iloc[0]
    assert bool(r["shadow_candidate_eligible"])
    assert r["migration_eligibility_state"] == "ELIGIBLE_SHADOW_CANDIDATE"
    assert r["production_target_cot_source"] == "LEGACY_CF_SCALED_GRID_CELL_MEAN"
    assert r["shadow_candidate_cot_source"] == "IN_CLOUD_EXACT_ENVELOPE_ASSUMED_REFF"
    assert r["in_cloud_cot_semantics"] == "IN_CLOUD_COT_ESTIMATE_ASSUMED_REFF"
    assert r["canvas_coverage_semantics"] == "HORIZONTAL_OCCUPANCY_SEPARATE_FROM_COT"
    assert math.isclose(r["cot_migration_delta"], 0.01335034023467 - 0.0073622908948011, abs_tol=1e-14)
    assert not bool(r["production_switch_performed"])
    assert not bool(r["production_target_cot_replaced"])
    assert not bool(r["cot_promotion_allowed"])
    assert not bool(r["formation_promotion_allowed"])


def test_direct_conflict_is_ineligible_and_fail_closed():
    out = build_canvas_cot_semantic_migration_shadow(_target(), _overlap(conflict=True))
    r = out.iloc[0]
    assert not bool(r["shadow_candidate_eligible"])
    assert "DIRECT_EVIDENCE_CONFLICT" in r["migration_ineligibility_reasons"]
    assert "VERTICAL_INTEGRATION_CONTRACT_FAILED" in r["migration_ineligibility_reasons"]
    assert math.isnan(r["in_cloud_target_cot"])


def test_missing_vertical_evidence_is_ineligible():
    out = build_canvas_cot_semantic_migration_shadow(_target(), _overlap(missing=1, bracket=False))
    r = out.iloc[0]
    assert not bool(r["shadow_candidate_eligible"])
    assert "VERTICAL_NATIVE_EVIDENCE_INSUFFICIENT" in r["migration_ineligibility_reasons"]
    assert "CONDENSATE_EVIDENCE_INCOMPLETE" in r["migration_ineligibility_reasons"]


def test_summary_preserves_shadow_only_contract():
    out = build_canvas_cot_semantic_migration_shadow(_target(), _overlap())
    s = summarize_canvas_cot_semantic_migration_shadow(out).iloc[0]
    assert s["target_count"] == 1
    assert s["shadow_candidate_eligible_count"] == 1
    assert s["production_switch_performed_count"] == 0
    assert s["cot_promotion_allowed_count"] == 0
    assert s["formation_promotion_allowed_count"] == 0


def test_analysis_integrity_accepts_valid_shadow_contract():
    target = _target()
    overlap = _overlap()
    migration = build_canvas_cot_semantic_migration_shadow(target, overlap)
    summary = summarize_canvas_cot_semantic_migration_shadow(migration)
    audit = build_analysis_integrity_audit({
        "canvas_cot_semantic_migration_required": True,
        "v1_target_canvas_optical_evidence": target,
        "v1_canvas_vertical_microphysics_overlap": overlap,
        "v1_canvas_cot_semantic_migration": migration,
        "v1_canvas_cot_semantic_migration_summary": summary,
    })
    row = audit.loc[audit["check_id"].eq("CANVAS_COT_SEMANTIC_MIGRATION_SHADOW")].iloc[0]
    assert row["status"] == "PASS"
    assert "eligible=1" in str(row["observed"])


def test_analysis_integrity_rejects_illegal_production_switch():
    target = _target()
    overlap = _overlap()
    migration = build_canvas_cot_semantic_migration_shadow(target, overlap)
    migration.loc[0, "production_switch_performed"] = True
    summary = summarize_canvas_cot_semantic_migration_shadow(migration)
    audit = build_analysis_integrity_audit({
        "canvas_cot_semantic_migration_required": True,
        "v1_target_canvas_optical_evidence": target,
        "v1_canvas_vertical_microphysics_overlap": overlap,
        "v1_canvas_cot_semantic_migration": migration,
        "v1_canvas_cot_semantic_migration_summary": summary,
    })
    row = audit.loc[audit["check_id"].eq("CANVAS_COT_SEMANTIC_MIGRATION_SHADOW")].iloc[0]
    assert row["status"] == "FAIL"


def test_target_optical_truth_direct_conflict_blocks_shadow_even_if_overlap_flag_is_stale_false():
    target = _target().copy()
    target.loc[0, "target_optical_truth_state"] = "DIRECT_EVIDENCE_CONFLICT"
    target.loc[0, "resolver_state"] = "CONDENSATE_CLOUD_CF_LOW_CONFLICT"
    out = build_canvas_cot_semantic_migration_shadow(target, _overlap(conflict=False))
    r = out.iloc[0]
    assert not bool(r["shadow_candidate_eligible"])
    assert not bool(r["direct_evidence_conflict_free"])
    assert "DIRECT_EVIDENCE_CONFLICT" in r["migration_ineligibility_reasons"]
    assert "VERTICAL_INTEGRATION_CONTRACT_FAILED" in r["migration_ineligibility_reasons"]
    assert math.isnan(r["in_cloud_target_cot"])


def test_analysis_integrity_cross_checks_target_truth_conflict_against_eligible_shadow():
    target = _target().copy()
    target.loc[0, "target_optical_truth_state"] = "DIRECT_EVIDENCE_CONFLICT"
    target.loc[0, "resolver_state"] = "CONDENSATE_CLOUD_CF_LOW_CONFLICT"
    overlap = _overlap(conflict=False)
    migration = build_canvas_cot_semantic_migration_shadow(_target(), overlap)
    # Simulate the R5.7.41.3.1 handoff bug: migration says eligible while
    # independent Target Optical Truth says direct conflict.
    summary = summarize_canvas_cot_semantic_migration_shadow(migration)
    audit = build_analysis_integrity_audit({
        "canvas_cot_semantic_migration_required": True,
        "v1_target_canvas_optical_evidence": target,
        "v1_canvas_vertical_microphysics_overlap": overlap,
        "v1_canvas_cot_semantic_migration": migration,
        "v1_canvas_cot_semantic_migration_summary": summary,
    })
    row = audit.loc[audit["check_id"].eq("CANVAS_COT_SEMANTIC_MIGRATION_SHADOW")].iloc[0]
    assert row["status"] == "FAIL"
    assert "target_conflict_handoff_ok=False" in str(row["detail"])
