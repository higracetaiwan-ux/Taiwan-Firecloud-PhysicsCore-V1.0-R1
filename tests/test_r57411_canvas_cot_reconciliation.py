import math
import pandas as pd

from firecloud.canvas_cot_reconciliation import (
    build_canvas_cot_reconciliation,
    summarize_canvas_cot_reconciliation,
)


def _frames():
    target = pd.DataFrame([{
        "time":"2026-09-11T18:03:43+08:00", "solar_altitude_deg":0.0,
        "canvas_id":"c1", "cloud_layer_id":"l1", "direction_offset_deg":0.0,
        "distance_km":0.0, "z_base_km":11.05813375, "z_top_km":12.545905,
        "direct_native_cot":0.0073622908948011,
        "target_cot_nominal":0.0073622908948011,
        "target_optics_ready":True, "target_optical_truth_state":"EXACT_PRIMARY_NATIVE",
    }])
    overlap = pd.DataFrame([{
        "time":"2026-09-11T18:03:43+08:00", "solar_altitude_deg":0.0,
        "canvas_id":"c1", "cloud_layer_id":"l1",
        "target_z_base_km":11.05813375, "target_z_top_km":12.545905,
        "cot_diagnostic_state":"COT_ESTIMATE_ASSUMED_REFF",
        "cot_estimate_assumed_reff":0.01335034023467,
        "direct_target_evidence_conflict":False,
    }])
    samples = pd.DataFrame([
        {"solar_altitude_deg":0.0,"canvas_id":"c1","inside_target_envelope":True,
         "sample_source_role":"PRIMARY_PGRB2","sample_pressure_hpa":250.0,
         "sample_altitude_agl_km":11.05813375,"sample_temperature_k":234.109902,
         "sample_cloud_fraction":0.7,"sample_cloud_liquid_water_kgkg":0.0,
         "sample_cloud_ice_water_kgkg":3.0e-7},
        {"solar_altitude_deg":0.0,"canvas_id":"c1","inside_target_envelope":True,
         "sample_source_role":"INTERMEDIATE_PGRB2B","sample_pressure_hpa":225.0,
         "sample_altitude_agl_km":11.7709375,"sample_temperature_k":228.120156,
         "sample_cloud_fraction":float('nan'),"sample_cloud_liquid_water_kgkg":0.0,
         "sample_cloud_ice_water_kgkg":6.4e-7},
        {"solar_altitude_deg":0.0,"canvas_id":"c1","inside_target_envelope":True,
         "sample_source_role":"PRIMARY_PGRB2","sample_pressure_hpa":200.0,
         "sample_altitude_agl_km":12.545905,"sample_temperature_k":221.278926,
         "sample_cloud_fraction":0.118,"sample_cloud_liquid_water_kgkg":0.0,
         "sample_cloud_ice_water_kgkg":3.4e-7},
    ])
    return target, overlap, samples


def test_reconciliation_explains_known_field_case_difference():
    target, overlap, samples = _frames()
    out = build_canvas_cot_reconciliation(target, overlap, samples)
    assert len(out) == 1
    r = out.iloc[0]
    assert r["reconciliation_state"] == "SEMANTIC_DIFFERENCE_EXPLAINED"
    assert bool(r["legacy_reconstruction_matches"])
    assert math.isclose(r["legacy_primary_exact_envelope_cf_scaled_cot"], 0.0036811454474006, rel_tol=0, abs_tol=2e-10)
    assert math.isclose(r["primary_exact_envelope_incloud_cot"], 0.0088690775096341, rel_tol=0, abs_tol=2e-10)
    assert math.isclose(r["legacy_half_cell_edge_support_delta_cot"], 0.0036811454474006, rel_tol=0, abs_tol=2e-10)
    assert math.isclose(r["cloud_fraction_semantics_delta_cot"], 0.0051879320622335, rel_tol=0, abs_tol=2e-10)
    assert math.isclose(r["pgrb2b_vertical_resolution_delta_cot"], 0.0044812627250359, rel_tol=0, abs_tol=2e-10)
    assert abs(r["reconciliation_residual_cot"]) <= 1e-10
    assert math.isclose(r["cot_ratio_overlap_to_legacy"], 1.813340284, rel_tol=2e-6)
    assert not bool(r["production_target_cot_replaced"])
    assert not bool(r["cot_promotion_allowed"])
    assert not bool(r["formation_promotion_allowed"])
    assert not bool(r["cloud_fraction_used_for_new_cot"])
    assert not bool(r["rh_used_to_infer_condensate"])


def test_no_comparable_exact_pair_returns_empty():
    target, overlap, samples = _frames()
    target.loc[0, "target_cot_nominal"] = float("nan")
    overlap.loc[0, "cot_estimate_assumed_reff"] = float("nan")
    out = build_canvas_cot_reconciliation(target, overlap, samples)
    assert out.empty


def test_reconciliation_summary_is_diagnostic_only():
    target, overlap, samples = _frames()
    out = build_canvas_cot_reconciliation(target, overlap, samples)
    summary = summarize_canvas_cot_reconciliation(out)
    assert len(summary) == 1
    r = summary.iloc[0]
    assert r["comparable_count"] == 1
    assert r["explained_count"] == 1
    assert r["legacy_reconstruction_match_count"] == 1
    assert r["closure_state"] == "EXPLAINED_DIAGNOSTIC_ONLY"
    assert r["production_target_cot_replaced_count"] == 0
    assert r["cot_promotion_allowed_count"] == 0
    assert r["formation_promotion_allowed_count"] == 0
