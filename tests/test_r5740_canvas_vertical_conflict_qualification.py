from types import SimpleNamespace

import numpy as np
import pandas as pd

from firecloud.canvas_optical_vertical_conflict import (
    QUALIFICATION_CONTRACT,
    build_canvas_vertical_conflict_qualification,
    summarize_vertical_conflict_qualification,
)
from firecloud.case_integrity import build_analysis_integrity_audit


def _scene_canvas():
    layer = SimpleNamespace(
        layer_id="L1", direction_offset_deg=0.0, distance_km=30.0,
        z_base_km=13.4, z_top_km=15.6,
    )
    canvas = SimpleNamespace(canvas_id="C1", cloud_layer_id="L1")
    return SimpleNamespace(layers=(layer,)), (canvas,)


def _primary(*, q100=0.0, q150=0.0, q200=0.0, cf100=0.0, cf150=0.04, cf200=0.0):
    row = {
        "point_id":"P1", "direction_offset_deg":0.0, "distance_km":30.0,
        "model_surface_elevation_m":0.0,
    }
    for p,z,cf,q in [(100,16600,cf100,q100),(150,14500,cf150,q150),(200,12400,cf200,q200)]:
        row[f"geopotential_height_{p}hPa"] = z
        row[f"cloud_fraction_{p}hPa"] = cf
        row[f"cloud_liquid_water_kgkg_{p}hPa"] = 0.0
        row[f"cloud_ice_water_kgkg_{p}hPa"] = q
        row[f"temperature_{p}hPa"] = 220.0 + p/20.0
        row[f"relative_humidity_{p}hPa"] = 40.0
    return pd.DataFrame([row])


def _supp(*, q125=0.0, q175=0.0, missing175=False):
    return pd.DataFrame([{
        "point_id":"P1", "direction_offset_deg":0.0, "distance_km":30.0,
        "surface_elevation_m":0.0,
        "geopotential_height_m_125hPa":15450.0,
        "cloud_liquid_water_kgkg_125hPa":0.0,
        "cloud_ice_water_kgkg_125hPa":q125,
        "temperature_k_125hPa":220.0,
        "geopotential_height_m_175hPa":13300.0,
        "cloud_liquid_water_kgkg_175hPa":np.nan if missing175 else 0.0,
        "cloud_ice_water_kgkg_175hPa":np.nan if missing175 else q175,
        "temperature_k_175hPa":230.0,
    }])


def _build(primary=None, supp=None):
    scene, canvases = _scene_canvas()
    return build_canvas_vertical_conflict_qualification(
        scene, canvases,
        _primary() if primary is None else primary,
        _supp() if supp is None else supp,
        valid_time="2026-09-10T18:00:00+08:00", solar_altitude_deg=-1.0,
        primary_pressure_levels_hpa=(200,150,100),
    )


def test_isolated_primary_cf_spike_when_main_and_intermediate_hydrometeors_are_zero():
    out = _build()
    assert len(out) == 1
    r = out.iloc[0]
    assert r["primary_conflict_pressure_hpa"] == 150.0
    assert r["below_primary_pressure_hpa"] == 200.0
    assert r["above_primary_pressure_hpa"] == 100.0
    assert r["below_supplement_pressure_hpa"] == 175.0
    assert r["above_supplement_pressure_hpa"] == 125.0
    assert r["vertical_conflict_qualification"] == "ISOLATED_PRIMARY_CF_SPIKE_HYDROMETEOR_UNSUPPORTED"
    assert bool(r["below_supplement_inside_target_envelope"]) is False
    assert bool(r["above_supplement_inside_target_envelope"]) is True
    assert not bool(r["cot_promotion_allowed"])
    assert not bool(r["formation_promotion_allowed"])
    assert not bool(r["supplement_cloud_fraction_used"])
    assert r["qualification_contract"] == QUALIFICATION_CONTRACT


def test_positive_pgrb2b_neighbor_is_support_signal_but_not_cot_promotion():
    out = _build(supp=_supp(q125=2e-7))
    r = out.iloc[0]
    assert r["vertical_conflict_qualification"] == "INTERMEDIATE_NATIVE_CONDENSATE_SUPPORT_PRESENT"
    assert not bool(r["cot_promotion_allowed"])


def test_positive_primary_adjacent_hydrometeor_is_separate_support_state():
    out = _build(primary=_primary(q200=2e-7))
    r = out.iloc[0]
    assert r["vertical_conflict_qualification"] == "ADJACENT_PRIMARY_NATIVE_CONDENSATE_SUPPORT_PRESENT"
    assert not bool(r["formation_promotion_allowed"])


def test_missing_intermediate_hydrometeor_keeps_vertical_context_incomplete():
    out = _build(supp=_supp(missing175=True))
    r = out.iloc[0]
    assert r["vertical_conflict_qualification"] == "VERTICAL_CONTEXT_INCOMPLETE"
    assert not bool(r["supplement_hydrometeor_bracket_complete"])


def test_multiple_main_cf_signal_with_zero_hydrometeors_is_not_called_isolated_spike():
    out = _build(primary=_primary(cf200=0.03))
    # 150 hPa remains the conflict inside this Canvas; 200 hPa is below the fixed
    # layer envelope but is visible as non-clear adjacent native geometry.
    r = out.loc[out["primary_conflict_pressure_hpa"].eq(150.0)].iloc[0]
    assert r["vertical_conflict_qualification"] == "PRIMARY_CF_SIGNAL_WITH_ZERO_INTERMEDIATE_HYDROMETEORS"


def test_summary_counts_qualification_states():
    out = _build()
    summary = summarize_vertical_conflict_qualification(out)
    assert len(summary) == 1
    r = summary.iloc[0]
    assert r["qualified_canvas_count"] == 1
    assert r["isolated_primary_cf_spike_count"] == 1
    assert r["intermediate_native_condensate_support_count"] == 0


def _target_conflict():
    return pd.DataFrame([{
        "canvas_id":"C1",
        "evidence_consistency":"CF_CLOUD_CONDENSATE_ZERO",
        "target_optical_truth_state":"DIRECT_EVIDENCE_CONFLICT",
    }])


def test_integrity_accepts_complete_diagnostic_only_vertical_qualification():
    out = _build()
    audit = build_analysis_integrity_audit({
        "canvas_optical_vertical_conflict_qualification_required": True,
        "v1_target_canvas_optical_evidence": _target_conflict(),
        "v1_canvas_vertical_conflict_qualification": out,
        "v1_canvas_vertical_conflict_qualification_summary": summarize_vertical_conflict_qualification(out),
        "gfs_canvas_optical_probe_request_audit": pd.DataFrame([{"action":"PROBE_RESULT","status":"READY"}]),
    })
    row = audit.loc[audit["check_id"].eq("CANVAS_OPTICAL_VERTICAL_CONFLICT_QUALIFICATION")].iloc[0]
    assert row["status"] == "PASS"


def test_integrity_fails_if_ready_probe_has_unqualified_primary_conflict():
    audit = build_analysis_integrity_audit({
        "canvas_optical_vertical_conflict_qualification_required": True,
        "v1_target_canvas_optical_evidence": _target_conflict(),
        "v1_canvas_vertical_conflict_qualification": pd.DataFrame(),
        "gfs_canvas_optical_probe_request_audit": pd.DataFrame([{"action":"PROBE_RESULT","status":"READY"}]),
    })
    row = audit.loc[audit["check_id"].eq("CANVAS_OPTICAL_VERTICAL_CONFLICT_QUALIFICATION")].iloc[0]
    assert row["status"] == "FAIL"


def test_integrity_rejects_any_cot_promotion_attempt():
    out = _build()
    out["target_cot"] = 1.0
    audit = build_analysis_integrity_audit({
        "canvas_optical_vertical_conflict_qualification_required": True,
        "v1_target_canvas_optical_evidence": _target_conflict(),
        "v1_canvas_vertical_conflict_qualification": out,
        "gfs_canvas_optical_probe_request_audit": pd.DataFrame([{"action":"PROBE_RESULT","status":"READY"}]),
    })
    row = audit.loc[audit["check_id"].eq("CANVAS_OPTICAL_VERTICAL_CONFLICT_QUALIFICATION")].iloc[0]
    assert row["status"] == "FAIL"


def test_no_primary_conflict_allows_empty_qualification():
    audit = build_analysis_integrity_audit({
        "canvas_optical_vertical_conflict_qualification_required": True,
        "v1_target_canvas_optical_evidence": pd.DataFrame([{
            "canvas_id":"C1", "evidence_consistency":"CONSISTENT_CLOUD",
            "target_optical_truth_state":"DIRECT_NATIVE_OPTICS",
        }]),
        "v1_canvas_vertical_conflict_qualification": pd.DataFrame(),
    })
    row = audit.loc[audit["check_id"].eq("CANVAS_OPTICAL_VERTICAL_CONFLICT_QUALIFICATION")].iloc[0]
    assert row["status"] == "ALLOWED_EMPTY"
