from pathlib import Path
import math

import pandas as pd

from firecloud.case_integrity import build_analysis_integrity_audit
from firecloud.contracts import SIX_BAND_WAVELENGTHS_NM
from firecloud.photography_decision import build_photography_decision
import firecloud.viewing_spectral as viewing_spectral


def _target(time="t0", angle=-1.0, canvas="canvas-1", layer="layer-1", distance=20.0):
    return {
        "time": time,
        "solar_altitude_deg": angle,
        "canvas_id": canvas,
        "cloud_layer_id": layer,
        "direction_offset_deg": 0.0,
        "target_distance_km": distance,
        "target_base_km": 3.0,
        "target_top_km": 4.0,
        "photographic_target_eligible": True,
    }


def _resolved_components(monkeypatch, aerosol_status="VIEW_AEROSOL_3D_RESOLVED"):
    tau = {int(w): 0.01 for w in SIX_BAND_WAVELENGTHS_NM}
    monkeypatch.setattr(
        viewing_spectral,
        "_integrate_view_aerosol",
        lambda *args, **kwargs: (
            tau.copy(),
            aerosol_status,
            20.0,
            {
                "required_segment_count": 1,
                "resolved_segment_count": 1 if aerosol_status.endswith("RESOLVED") else 0,
                "temporal_fallback_segment_count": 0,
                "temporal_missing_segment_count": 0,
            },
        ),
    )
    monkeypatch.setattr(
        viewing_spectral,
        "_integrate_view_gas",
        lambda *args, **kwargs: (tau.copy(), "VIEW_GAS_RT_RESOLVED", 20.0),
    )
    monkeypatch.setattr(
        viewing_spectral,
        "_cloud_expected_tau",
        lambda *args, **kwargs: (0.0, 0.0, "VIEW_CLOUD_PATH_CLEAR", 0, ""),
    )


def _precip(time, angle, canvas, tau):
    row = {
        "time": time,
        "solar_altitude_deg": angle,
        "canvas_id": canvas,
        "view_precipitation_status": "VIEW_PRECIPITATION_OPTICS_RESOLVED",
    }
    for wl in SIX_BAND_WAVELENGTHS_NM:
        row[f"view_tau_precip_{int(wl)}nm"] = tau
    return row


def test_exact_cot_map_is_scoped_by_time_angle_and_layer_id():
    layers = pd.DataFrame([
        {"time": "t0", "solar_altitude_deg": -1.0, "layer_id": "repeat", "cot": 2.0},
        {"time": "t1", "solar_altitude_deg": -2.0, "layer_id": "repeat", "cot": 7.0},
    ])
    cot = viewing_spectral._exact_cot_map(layers, pd.DataFrame())
    assert cot[("t0", -1.0, "repeat")][0] == 2.0
    assert cot[("t1", -2.0, "repeat")][0] == 7.0


def test_precipitation_binding_is_scoped_by_time_angle_and_canvas(monkeypatch):
    _resolved_components(monkeypatch)
    geometry = pd.DataFrame([
        _target("t0", -1.0, canvas="repeat"),
        _target("t1", -2.0, canvas="repeat"),
    ])
    precip = pd.DataFrame([
        _precip("t0", -1.0, "repeat", 0.1),
        _precip("t1", -2.0, "repeat", 0.9),
    ])
    detail = viewing_spectral.build_viewing_spectral_extinction(
        geometry, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), precip
    )
    first = detail.loc[detail["time"].eq("t0")].iloc[0]
    second = detail.loc[detail["time"].eq("t1")].iloc[0]
    assert first["view_tau_precip_650nm"] == 0.1
    assert second["view_tau_precip_650nm"] == 0.9
    assert first["view_transmission_650nm"] > second["view_transmission_650nm"]


def test_partial_component_tau_is_never_promoted_to_total_transmission(monkeypatch):
    _resolved_components(monkeypatch, aerosol_status="VIEW_AEROSOL_3D_PARTIAL")
    detail = viewing_spectral.build_viewing_spectral_extinction(
        pd.DataFrame([_target()]),
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame([_precip("t0", -1.0, "canvas-1", 0.0)]),
    )
    row = detail.iloc[0]
    assert row["viewing_spectral_status"] == "VIEW_PARTIAL_SIX_BAND_RT"
    assert pd.isna(row["view_tau_total_650nm"])
    assert pd.isna(row["view_transmission_650nm"])
    assert row["view_band_evidence_state_650nm"] == "MISSING"


def test_local_eligible_target_remains_as_explicit_unresolved_rt_row():
    detail = viewing_spectral.build_viewing_spectral_extinction(
        pd.DataFrame([_target(distance=0.0)]),
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
    )
    assert len(detail) == 1
    assert detail.iloc[0]["viewing_spectral_status"] == "VIEW_SIX_BAND_RT_UNRESOLVED"
    assert detail.iloc[0]["viewing_missing_components"] == "GEOMETRY"


def test_summary_and_photography_preserve_all_six_bands_without_overriding_formation(monkeypatch):
    _resolved_components(monkeypatch)
    detail = viewing_spectral.build_viewing_spectral_extinction(
        pd.DataFrame([_target()]),
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame([_precip("t0", -1.0, "canvas-1", 0.0)]),
    )
    summary = viewing_spectral.summarize_viewing_spectral_extinction(detail)
    formation = pd.DataFrame([{
        "time": "t0",
        "solar_altitude_deg": -1.0,
        "formation_state": "CLEAR_RED_PATH_NO_CANVAS",
    }])
    viewing = pd.DataFrame([{
        "time": "t0",
        "solar_altitude_deg": -1.0,
        "viewing_state": "VIEWING_GEOMETRY_GOOD",
    }])
    decision = build_photography_decision(formation, viewing, summary)
    row = decision.iloc[0]
    assert row["photography_opportunity"] == "NO_GO"
    assert row["viewing_spectral_state"] == "VIEW_SPECTRAL_READY"
    assert row["viewing_rt_completeness"] == 1.0
    for wl in SIX_BAND_WAVELENGTHS_NM:
        expected = math.exp(-0.02)
        assert abs(row[f"mean_view_transmission_{int(wl)}nm"] - expected) < 1e-12


def test_integrity_accepts_complete_six_band_closure_and_pipeline_handoff(monkeypatch):
    _resolved_components(monkeypatch)
    geometry = pd.DataFrame([_target()])
    precipitation = pd.DataFrame([_precip("t0", -1.0, "canvas-1", 0.0)])
    detail = viewing_spectral.build_viewing_spectral_extinction(
        geometry,
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        precipitation,
    )
    spectral_summary = viewing_spectral.summarize_viewing_spectral_extinction(detail)
    formation = pd.DataFrame([{"time": "t0", "solar_altitude_deg": -1.0, "formation_state": "FORMATION_CONFIRMED"}])
    viewing = pd.DataFrame([{"time": "t0", "solar_altitude_deg": -1.0, "viewing_state": "VIEWING_GEOMETRY_GOOD"}])
    photography = build_photography_decision(formation, viewing, spectral_summary)
    audit = build_analysis_integrity_audit({
        "v1_formation": formation,
        "v1_viewing_path_geometry": geometry,
        "v1_viewing_summary": viewing,
        "v1_viewing_precipitation_evidence": precipitation,
        "v1_viewing_spectral_extinction_550_750nm": detail,
        "v1_viewing_spectral_summary": spectral_summary,
        "v1_photography_decision": photography,
        "gfs_native_field_completeness": pd.DataFrame({
            "field": ["RWMR", "SNMR", "GRLE"],
            "status": ["READY", "READY", "READY"],
        }),
    })
    statuses = audit.set_index("check_id")["status"].to_dict()
    assert statuses["VIEWING_SIX_BAND_TARGET_COVERAGE"] == "PASS"
    assert statuses["VIEWING_SIX_BAND_SCHEMA"] == "PASS"
    assert statuses["VIEWING_SIX_BAND_NUMERIC_CLOSURE"] == "PASS"
    assert statuses["VIEWING_SIX_BAND_SUMMARY_COVERAGE"] == "PASS"
    assert statuses["VIEWING_SIX_BAND_PHOTOGRAPHY_HANDOFF"] == "PASS"
    assert statuses["VIEWING_PRECIPITATION_TARGET_COVERAGE"] == "PASS"
    assert statuses["VIEWING_NATIVE_HYDROMETEOR_HANDOFF"] == "PASS"

    model_text = (Path(__file__).resolve().parents[1] / "firecloud" / "model.py").read_text(encoding="utf-8")
    merge_at = model_text.index("snap = merge_native_into_snapshot(snap, native_df)")
    viewing_spool_at = model_text.index('_angle_frame_spool.put("viewing_route_snapshot"', merge_at)
    assert merge_at < viewing_spool_at
    viewing_drain_at = model_text.index('_view_route_snapshots = _drain_spool_matrix("viewing_route_snapshot")')
    cleanup_at = model_text.index("_angle_frame_spool.cleanup()", viewing_drain_at)
    assert viewing_spool_at < viewing_drain_at < cleanup_at
    handoff_start = model_text.index("_pre_integrity_result = {")
    handoff_end = model_text.index("analysis_integrity_audit = build_analysis_integrity_audit", handoff_start)
    handoff = model_text[handoff_start:handoff_end]
    assert '"v1_viewing_path_geometry": v1_viewing_path_geometry' in handoff
    assert '"v1_viewing_precipitation_evidence": v1_viewing_precipitation_evidence' in handoff
    assert '"v1_viewing_spectral_extinction_550_750nm": v1_viewing_spectral_extinction' in handoff
    assert '"v1_viewing_spectral_summary": v1_viewing_spectral_summary' in handoff


def test_integrity_fails_header_only_precipitation_when_native_hydrometeors_are_ready():
    geometry = pd.DataFrame([_target()])
    audit = build_analysis_integrity_audit({
        "v1_formation": pd.DataFrame([{
            "time": "t0",
            "solar_altitude_deg": -1.0,
            "formation_state": "FORMATION_CONFIRMED",
        }]),
        "v1_viewing_path_geometry": geometry,
        "v1_viewing_precipitation_evidence": pd.DataFrame(columns=[
            "time", "solar_altitude_deg", "canvas_id", "view_precipitation_status",
        ]),
        "gfs_native_field_completeness": pd.DataFrame({
            "field": ["RWMR", "SNMR", "GRLE"],
            "status": ["READY", "READY", "READY"],
        }),
    })
    statuses = audit.set_index("check_id")["status"].to_dict()
    assert statuses["VIEWING_PRECIPITATION_TARGET_COVERAGE"] == "FAIL"
    assert statuses["VIEWING_NATIVE_HYDROMETEOR_HANDOFF"] == "FAIL"
    assert statuses["ANALYSIS_INTEGRITY_OVERALL"] == "FAIL"
