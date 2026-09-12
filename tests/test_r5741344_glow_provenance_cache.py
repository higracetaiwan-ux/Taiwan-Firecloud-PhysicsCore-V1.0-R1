import pandas as pd
import numpy as np

import firecloud.twilight_glow as glow


def _cloud_scene():
    return pd.DataFrame([
        {
            "time": "t0", "solar_altitude_deg": -5.5, "direction_offset_deg": 0.0,
            "layer_id": "L70", "distance_km": 70.0, "z_base_km": 4.7, "z_top_km": 5.5,
            "cloud_fraction": 0.20, "cot": np.nan,
            "evidence_consistency": "CF_CLOUD_CONDENSATE_ZERO",
        },
        {
            "time": "t0", "solar_altitude_deg": -5.5, "direction_offset_deg": 0.0,
            "layer_id": "L80", "distance_km": 80.0, "z_base_km": 4.7, "z_top_km": 5.5,
            "cloud_fraction": 0.25, "cot": np.nan,
            "evidence_consistency": "CF_CLOUD_CONDENSATE_ZERO",
        },
    ])


def _target(distance=100.0, z=7.75):
    return pd.Series({
        "time": "t0", "solar_altitude_deg": -5.5, "direction_offset_deg": 0.0,
        "target_distance_km": distance, "target_base_km": z - 0.25, "target_top_km": z + 0.25,
    })


def _truth_map(target_optics):
    out = {}
    for _, row in target_optics.iterrows():
        key = glow._evidence_key(row.get("time"), row.get("solar_altitude_deg"), row.get("cloud_layer_id"))
        out[key] = (
            str(row.get("target_optical_truth_state") or ""),
            str(row.get("target_cot_semantics") or ""),
            str(row.get("resolver_state") or ""),
        )
    return out


def test_cached_cloud_conflict_provenance_is_exactly_semantic_equivalent():
    cloud_layers = _cloud_scene()
    target_optics = pd.DataFrame([
        {
            "time": "t0", "solar_altitude_deg": -5.5, "cloud_layer_id": "L70",
            "target_optics_ready": False,
            "target_optical_truth_state": "DIRECT_EVIDENCE_CONFLICT",
            "target_cot_semantics": "UNRESOLVED_CONFLICT",
            "resolver_state": "DIRECT_EVIDENCE_CONFLICT",
        },
        {
            "time": "t0", "solar_altitude_deg": -5.5, "cloud_layer_id": "L80",
            "target_optics_ready": False,
            "target_optical_truth_state": "DIRECT_EVIDENCE_CONFLICT",
            "target_cot_semantics": "UNRESOLVED_CONFLICT",
            "resolver_state": "DIRECT_EVIDENCE_CONFLICT",
        },
    ])
    target = _target()
    uncached = glow._observer_cloud_conflict_provenance(target, cloud_layers, target_optics, 6371.0)

    cotmap = glow._exact_cot_map(cloud_layers, target_optics)
    cached = glow._observer_cloud_conflict_provenance(
        target, cloud_layers, target_optics, 6371.0,
        prefiltered_layers=cloud_layers,
        cotmap=cotmap,
        truth_map=_truth_map(target_optics),
        support_cache={},
    )
    assert cached == uncached
    assert cached["state"] == "GLOW_OBSERVER_CLOUD_DIRECT_EVIDENCE_CONFLICT_PRESERVED"


def test_projected_support_geometry_is_reused_across_glow_volumes(monkeypatch):
    cloud_layers = _cloud_scene()
    target_optics = pd.DataFrame()
    cotmap = glow._exact_cot_map(cloud_layers, target_optics)
    support_cache = {}
    calls = {"count": 0}
    original = glow._projected_support_interval

    def counted(*args, **kwargs):
        calls["count"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(glow, "_projected_support_interval", counted)
    kwargs = dict(
        prefiltered_layers=cloud_layers,
        cotmap=cotmap,
        truth_map={},
        support_cache=support_cache,
    )
    first = glow._observer_cloud_conflict_provenance(_target(), cloud_layers, target_optics, 6371.0, **kwargs)
    first_call_count = calls["count"]
    second = glow._observer_cloud_conflict_provenance(_target(), cloud_layers, target_optics, 6371.0, **kwargs)

    assert first == second
    assert first_call_count == len(cloud_layers)
    assert calls["count"] == first_call_count
    assert len(support_cache) == len(cloud_layers)


def test_twilight_glow_runtime_cache_stats_are_diagnostic_only(monkeypatch):
    timeline = pd.DataFrame([{
        "time": "t0", "solar_altitude_deg": -4.0, "solar_azimuth_deg": 90.0,
    }])
    red = pd.DataFrame([{
        "time": "t0", "solar_altitude_deg": -4.0, "reference_receiver_id": "r0",
        "direction_offset_deg": 0.0, "distance_km": 10.0,
        "sampled_receiver_altitude_km": 4.0, "voxel_bottom_km": 3.5, "voxel_top_km": 4.0,
        "v1_direct_solar_fraction": 0.0,
        "red_light_path_state": "NO_DIRECT_RED_ACCESS",
        "red_light_path_evidence_complete": False,
    }])
    monkeypatch.setattr(glow, "_observer_precipitation", lambda *_a, **_k: pd.DataFrame())
    monkeypatch.setattr(glow, "build_viewing_spectral_extinction", lambda targets, *_a, **_k: pd.DataFrame([
        {
            "time": r.time, "solar_altitude_deg": r.solar_altitude_deg, "canvas_id": r.canvas_id,
            "viewing_spectral_status": "VIEW_SIX_BAND_RT_UNRESOLVED",
            "view_cloud_status": "VIEW_CLOUD_EVIDENCE_MISSING",
        }
        for r in targets.itertuples(index=False)
    ]))
    stats = {}
    detail, summary = glow.build_twilight_glow_branch(
        red_light_reference=red,
        event_timeline=timeline,
        cloud_layers=pd.DataFrame(),
        target_optics=pd.DataFrame(),
        aerosol_snapshots=pd.DataFrame(),
        gas_profiles=pd.DataFrame(),
        route_snapshots=pd.DataFrame(),
        observer_lat_deg=23.0,
        observer_lon_deg=121.0,
        runtime_cache_stats=stats,
    )
    assert len(detail) == 1
    assert len(summary) == 1
    assert stats["cloud_group_count"] == 0
    assert stats["cloud_provenance_call_count"] == 0
    assert stats["support_cache_entry_count"] == 0


def test_model_exposes_non_overlapping_aggregation_telemetry_stage():
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] / "firecloud" / "model.py").read_text(encoding="utf-8")
    assert '"stage": "AGGREGATION_AND_MATRIX_BUILD"' in source
    assert '"stage": "AGGREGATION_EXCLUDING_TWILIGHT_GLOW"' in source
    assert "COMPUTED_INCLUSIVE_OF_TWILIGHT_GLOW" in source
    assert "R5741344_GLOW_CLOUD_PROVENANCE_SHARED_CACHE" in source
