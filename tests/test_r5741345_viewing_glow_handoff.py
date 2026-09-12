import pandas as pd
import numpy as np

import firecloud.twilight_glow as glow
import firecloud.viewing_spectral as viewing


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


def _target_optics():
    return pd.DataFrame([
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


def _target():
    return pd.Series({
        "time": "t0", "solar_altitude_deg": -5.5, "direction_offset_deg": 0.0,
        "target_distance_km": 100.0, "target_base_km": 7.5, "target_top_km": 8.0,
    })


def test_same_pass_viewing_handoff_matches_legacy_glow_conflict_retrace_exactly():
    cloud = _cloud_scene()
    optics = _target_optics()
    target = _target()

    legacy = glow._observer_cloud_conflict_provenance(target, cloud, optics, 6371.0)
    sink = {}
    viewing._cloud_expected_tau(
        target, cloud, optics, 6371.0,
        cotmap=viewing._exact_cot_map(cloud, optics),
        truth_map=viewing._target_optical_truth_map(optics),
        support_cache={},
        diagnostic_sink=sink,
    )
    assert sink == legacy
    assert sink["state"] == "GLOW_OBSERVER_CLOUD_DIRECT_EVIDENCE_CONFLICT_PRESERVED"


def test_shared_viewing_runtime_context_is_reused_only_for_exact_source_objects():
    cloud = pd.DataFrame(columns=["solar_altitude_deg", "direction_offset_deg", "distance_km"])
    optics = pd.DataFrame()
    aerosol = pd.DataFrame(columns=["solar_altitude_deg", "direction_offset_deg", "distance_km"])
    gas = pd.DataFrame(columns=["solar_altitude_deg", "direction_offset_deg", "distance_km"])
    ctx = viewing.prepare_viewing_spectral_runtime_context(cloud, optics, aerosol, gas)

    geometry = pd.DataFrame([{
        "time": "t0", "solar_altitude_deg": -2.0, "canvas_id": "g0", "cloud_layer_id": "g0",
        "direction_offset_deg": 0.0, "target_distance_km": 10.0,
        "target_base_km": np.nan, "target_top_km": np.nan,
        "photographic_target_eligible": True,
    }])
    stats = {}
    viewing.build_viewing_spectral_extinction(
        geometry, cloud, optics, aerosol, gas, pd.DataFrame(),
        runtime_context=ctx, runtime_cache_stats=stats,
    )
    assert stats["runtime_context_reused"] is True

    stats2 = {}
    viewing.build_viewing_spectral_extinction(
        geometry, cloud.copy(), optics, aerosol, gas, pd.DataFrame(),
        runtime_context=ctx, runtime_cache_stats=stats2,
    )
    assert stats2["runtime_context_reused"] is False


def test_twilight_glow_consumes_viewing_cloud_handoff_without_fallback_retrace(monkeypatch):
    timeline = pd.DataFrame([{"time": "t0", "solar_altitude_deg": -4.0, "solar_azimuth_deg": 90.0}])
    red = pd.DataFrame([{
        "time": "t0", "solar_altitude_deg": -4.0, "reference_receiver_id": "r0",
        "direction_offset_deg": 0.0, "distance_km": 10.0,
        "sampled_receiver_altitude_km": 4.0, "voxel_bottom_km": 3.5, "voxel_top_km": 4.0,
        "v1_direct_solar_fraction": 0.0,
        "red_light_path_state": "NO_DIRECT_RED_ACCESS",
        "red_light_path_evidence_complete": False,
    }])
    monkeypatch.setattr(glow, "_observer_precipitation", lambda *_a, **_k: pd.DataFrame())

    def fake_view(targets, *_args, **_kwargs):
        rows = []
        for r in targets.itertuples(index=False):
            rows.append({
                "time": r.time, "solar_altitude_deg": r.solar_altitude_deg, "canvas_id": r.canvas_id,
                "viewing_spectral_status": "VIEW_PARTIAL_SIX_BAND_RT",
                "view_cloud_status": "VIEW_CLOUD_OPTICS_PARTIAL",
                "view_cloud_blocker_count": 2,
                "view_cloud_provenance_state": "GLOW_OBSERVER_CLOUD_DIRECT_EVIDENCE_CONFLICT_PRESERVED",
                "view_cloud_unresolved_blocker_count": 2,
                "view_cloud_conflict_blocker_count": 2,
                "view_cloud_unresolved_layer_ids": "L70;L80",
                "view_cloud_conflict_states": "CF_CLOUD_CONDENSATE_ZERO|DIRECT_EVIDENCE_CONFLICT",
            })
        return pd.DataFrame(rows)

    monkeypatch.setattr(glow, "build_viewing_spectral_extinction", fake_view)
    monkeypatch.setattr(
        glow, "_observer_cloud_conflict_provenance",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("fallback retrace must not run")),
    )
    stats = {}
    detail, _ = glow.build_twilight_glow_branch(
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
    assert detail.iloc[0]["glow_observer_cloud_evidence_state"] == "GLOW_OBSERVER_CLOUD_DIRECT_EVIDENCE_CONFLICT_PRESERVED"
    assert detail.iloc[0]["glow_observer_cloud_conflict_blocker_count"] == 2
    assert stats["cloud_handoff_hit_count"] == 1
    assert stats["cloud_provenance_call_count"] == 0
