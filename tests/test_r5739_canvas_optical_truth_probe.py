from datetime import datetime, timezone
from types import SimpleNamespace

import numpy as np
import pandas as pd

from firecloud.providers.gfs_canvas_optical_probe import (
    PROVIDER_NAME,
    SUPPLEMENT_PRESSURE_LEVELS_HPA,
    build_canvas_probe_evidence,
    build_nomads_request,
    summarize_canvas_probe_evidence,
)
from firecloud.case_integrity import build_analysis_integrity_audit


def _scene_canvas(z0=13.0, z1=15.5, distance=30.0, direction=0.0):
    layer = SimpleNamespace(
        layer_id="L1",
        direction_offset_deg=direction,
        distance_km=distance,
        z_base_km=z0,
        z_top_km=z1,
    )
    canvas = SimpleNamespace(canvas_id="C1", cloud_layer_id="L1")
    scene = SimpleNamespace(layers=(layer,))
    return scene, (canvas,)


def _probe_route(ql=0.0, qi=2e-7, cf=0.6, *, distance=30.0):
    row = {
        "point_id": "P1",
        "direction_offset_deg": 0.0,
        "distance_km": distance,
        "surface_elevation_m": 0.0,
        # 125 hPa inside target, 175 hPa below target.
        "geopotential_height_m_125hPa": 14000.0,
        "temperature_k_125hPa": 220.0,
        "cloud_liquid_water_kgkg_125hPa": ql,
        "cloud_ice_water_kgkg_125hPa": qi,
        "cloud_fraction_125hPa": cf,
        "geopotential_height_m_175hPa": 12000.0,
        "temperature_k_175hPa": 230.0,
        "cloud_liquid_water_kgkg_175hPa": 9e-6,
        "cloud_ice_water_kgkg_175hPa": 9e-6,
        "cloud_fraction_175hPa": 0.9,
    }
    return pd.DataFrame([row])


def test_pgrb2b_request_uses_intermediate_native_levels_and_vars():
    run = datetime(2026, 9, 10, 0, tzinfo=timezone.utc)
    _, params = build_nomads_request(run, 9, (120.0, 122.0, 23.0, 25.0))
    assert params["file"] == "gfs.t00z.pgrb2b.0p25.f009"
    assert params["var_CLWMR"] == "on"
    assert params["var_ICMR"] == "on"
    assert params["var_TCDC"] == "on"
    assert params["var_TMP"] == "on"
    assert params["var_HGT"] == "on"
    assert params["lev_125_mb"] == "on"
    assert params["lev_175_mb"] == "on"
    assert 125 in SUPPLEMENT_PRESSURE_LEVELS_HPA
    assert 150 not in SUPPLEMENT_PRESSURE_LEVELS_HPA


def test_positive_native_intermediate_condensate_is_diagnostic_only():
    scene, canvases = _scene_canvas()
    out = build_canvas_probe_evidence(
        scene, canvases, _probe_route(ql=0.0, qi=2e-7, cf=0.6),
        valid_time=datetime(2026, 9, 10, 10), solar_altitude_deg=-1.0,
    )
    assert len(out) == 1
    r = out.iloc[0]
    assert r["probe_pressure_hpa"] == 125.0
    assert bool(r["probe_positive_condensate"])
    assert r["probe_condensate_state"] == "POSITIVE"
    assert r["probe_evidence_consistency"] == "NATIVE_CONDENSATE_POSITIVE"
    assert r["probe_source"] == PROVIDER_NAME
    assert "target_cot" not in out.columns
    assert "target_optics_ready" not in out.columns
    assert "formation_state" not in out.columns


def test_zero_native_condensate_with_cloud_fraction_stays_conflict():
    scene, canvases = _scene_canvas()
    out = build_canvas_probe_evidence(scene, canvases, _probe_route(ql=0.0, qi=0.0, cf=0.7))
    assert len(out) == 1
    r = out.iloc[0]
    assert not bool(r["probe_positive_condensate"])
    assert r["probe_condensate_state"] == "ZERO"
    assert r["probe_evidence_consistency"] == "CF_CLOUD_CONDENSATE_ZERO"


def test_missing_native_condensate_stays_missing():
    scene, canvases = _scene_canvas()
    out = build_canvas_probe_evidence(scene, canvases, _probe_route(ql=np.nan, qi=np.nan, cf=0.8))
    assert len(out) == 1
    r = out.iloc[0]
    assert r["probe_condensate_state"] == "MISSING"
    assert pd.isna(r["probe_total_condensate_kgkg"])
    assert r["probe_evidence_consistency"] == "OPTICS_MISSING"


def test_probe_excludes_levels_outside_fixed_canvas_vertical_envelope():
    scene, canvases = _scene_canvas(z0=13.0, z1=15.5)
    out = build_canvas_probe_evidence(scene, canvases, _probe_route())
    assert set(out["probe_pressure_hpa"]) == {125.0}
    assert not (out["probe_pressure_hpa"] == 175.0).any()


def test_summary_counts_positive_canvas_and_rows():
    scene, canvases = _scene_canvas()
    out = build_canvas_probe_evidence(
        scene, canvases, _probe_route(),
        valid_time=datetime(2026, 9, 10, 10), solar_altitude_deg=-1.0,
    )
    summary = summarize_canvas_probe_evidence(out)
    assert len(summary) == 1
    r = summary.iloc[0]
    assert r["canvas_count_with_probe_levels"] == 1
    assert r["canvas_with_positive_supplement_condensate_count"] == 1
    assert r["positive_probe_level_count"] == 1
    assert r["probe_contract"] == "R5.7.39_DIAGNOSTIC_ONLY_NO_FORMATION_PROMOTION"


def test_integrity_accepts_valid_probe_contract():
    scene, canvases = _scene_canvas()
    out = build_canvas_probe_evidence(scene, canvases, _probe_route())
    result = {
        "canvas_optical_truth_pgrb2b_probe_required": True,
        "v1_canvas_optical_native_probe": out,
        "v1_canvas_optical_native_probe_summary": summarize_canvas_probe_evidence(out),
        "gfs_canvas_optical_probe_request_audit": pd.DataFrame([{"action":"PROBE_RESULT", "status":"READY"}]),
    }
    audit = build_analysis_integrity_audit(result)
    row = audit.loc[audit["check_id"].eq("CANVAS_OPTICAL_TRUTH_PGRB2B_PROBE_CONTRACT")].iloc[0]
    assert row["status"] == "PASS"


def test_integrity_rejects_probe_that_promotes_target_cot():
    scene, canvases = _scene_canvas()
    out = build_canvas_probe_evidence(scene, canvases, _probe_route())
    out["target_cot"] = 1.0
    audit = build_analysis_integrity_audit({
        "canvas_optical_truth_pgrb2b_probe_required": True,
        "v1_canvas_optical_native_probe": out,
    })
    row = audit.loc[audit["check_id"].eq("CANVAS_OPTICAL_TRUTH_PGRB2B_PROBE_CONTRACT")].iloc[0]
    assert row["status"] == "FAIL"


def test_empty_diagnostic_probe_is_warn_not_false_science_pass_or_fail():
    audit = build_analysis_integrity_audit({
        "canvas_optical_truth_pgrb2b_probe_required": True,
        "v1_canvas_optical_native_probe": pd.DataFrame(),
        "gfs_canvas_optical_probe_request_audit": pd.DataFrame([{"action":"PROBE_RESULT", "status":"FAILED"}]),
    })
    row = audit.loc[audit["check_id"].eq("CANVAS_OPTICAL_TRUTH_PGRB2B_PROBE_CONTRACT")].iloc[0]
    assert row["status"] == "WARN"
