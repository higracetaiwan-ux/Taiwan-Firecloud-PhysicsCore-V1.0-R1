import pandas as pd

import firecloud
from firecloud.observer_environment_timeline import (
    build_observer_environment_timeline,
    summarize_observer_environment_timeline,
)
from firecloud.case_integrity import build_analysis_integrity_audit


def _event_contract():
    return pd.DataFrame([
        {"solar_altitude_deg": 0.0, "event_local_time": "2026-09-14T18:00:00+08:00"},
        {"solar_altitude_deg": -6.0, "event_local_time": "2026-09-14T18:26:48+08:00"},
    ])


def _hourly():
    rows = []
    for t, low0, low50 in [
        ("2026-09-14 15:00:00", 1.0, 10.0),
        ("2026-09-14 16:00:00", 1.5, 15.0),
        ("2026-09-14 17:00:00", 2.0, 20.0),
        ("2026-09-14 18:00:00", 4.0, 40.0),
        ("2026-09-14 19:00:00", 6.0, 60.0),
    ]:
        for point_id, dist, low in [
            ("+0.0_0000", 0.0, low0),
            ("+0.0_0050", 50.0, low50),
        ]:
            rows.append({
                "time": t,
                "point_id": point_id,
                "direction_offset_deg": 0.0,
                "distance_km": dist,
                "cloud_cover_low": low,
                "cloud_cover_mid": 1.0,
                "cloud_cover_high": 0.0,
                "visibility": 14000.0 - dist,
                "relative_humidity_2m": 88.0,
                "precipitation": 0.0,
            })
    return pd.DataFrame(rows)


def _native():
    return pd.DataFrame([
        {
            "time": "2026-09-14 18:00:00+08:00", "gfs_valid_time_utc": "2026-09-14 10:00:00+00:00", "solar_altitude_deg": 0.0,
            "direction_offset_deg": 0.0, "distance_km": 0.0,
            "native_cloud_base_km": float("nan"), "native_cloud_top_km": float("nan"),
            "native_cloud_thickness_km": float("nan"), "native_vertical_completeness": 1.0,
            "liquid_water_path_proxy_gm3_km": 0.0, "ice_water_path_proxy_gm3_km": 0.0,
        },
        {
            "time": "2026-09-14 18:00:00+08:00", "gfs_valid_time_utc": "2026-09-14 10:00:00+00:00", "solar_altitude_deg": 0.0,
            "direction_offset_deg": 0.0, "distance_km": 50.0,
            "native_cloud_base_km": float("nan"), "native_cloud_top_km": float("nan"),
            "native_cloud_thickness_km": float("nan"), "native_vertical_completeness": 1.0,
            "liquid_water_path_proxy_gm3_km": 0.0, "ice_water_path_proxy_gm3_km": 0.0,
        },
        {
            "time": "2026-09-14 18:15:00+08:00", "gfs_valid_time_utc": "2026-09-14 10:15:00+00:00", "solar_altitude_deg": -3.5,
            "direction_offset_deg": 0.0, "distance_km": 50.0,
            "native_cloud_base_km": 0.5, "native_cloud_top_km": 1.5,
            "native_cloud_thickness_km": 1.0, "native_vertical_completeness": 1.0,
            "liquid_water_path_proxy_gm3_km": 0.01, "ice_water_path_proxy_gm3_km": 0.0,
        },
    ])


def test_version_bumped_to_observer_environment_timeline_release():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.26"


def test_timeline_covers_t_minus_180_to_t_plus_60_at_five_minute_steps():
    tl = build_observer_environment_timeline(_hourly(), _event_contract(), _native())
    offsets = sorted(tl.event_offset_minutes.unique().tolist())
    assert offsets[0] == -180
    assert offsets[-1] == 60
    assert len(offsets) == 49
    assert len(tl) == 98  # 49 time steps x 2 route points


def test_coarse_timeline_uses_existing_linear_route_interpolation_contract():
    tl = build_observer_environment_timeline(_hourly(), _event_contract(), _native())
    row = tl[(tl.event_offset_minutes.eq(-30)) & (tl.distance_km.eq(50.0))].iloc[0]
    assert row.cloud_cover_low_pct == 30.0
    assert row.temporal_interpolation_method == "OPENMETEO_ROUTE_LINEAR_INTERPOLATION_EXISTING_CONTRACT"
    assert row.native_time_match_state == "NO_NATIVE_SAMPLE_WITHIN_TIME_TOLERANCE"
    assert row.coarse_native_low_cloud_relation == "COARSE_LOW_CLOUD_NATIVE_TIME_UNMATCHED"


def test_native_snapshot_is_attached_near_time_without_native_temporal_interpolation():
    tl = build_observer_environment_timeline(_hourly(), _event_contract(), _native())
    event = tl[(tl.event_offset_minutes.eq(0)) & (tl.distance_km.eq(50.0))].iloc[0]
    assert event.native_time_match_state == "NEAREST_EXISTING_NATIVE_SNAPSHOT_WITHIN_TOLERANCE"
    assert event.native_time_basis == "PROVIDER_GFS_VALID_TIME_UTC"
    assert str(event.native_provider_valid_time).startswith("2026-09-14 10:00:00")
    assert event.native_low_cloud_geometry_state == "NATIVE_NO_CLOUD_COLUMN_AT_THRESHOLD"
    assert event.coarse_native_low_cloud_relation == "COARSE_LOW_CLOUD_NATIVE_NO_COLUMN_AT_THRESHOLD"
    q15 = tl[(tl.event_offset_minutes.eq(15)) & (tl.distance_km.eq(50.0))].iloc[0]
    assert q15.native_low_cloud_geometry_state == "NATIVE_LOW_CLOUD_GEOMETRY_PRESENT"
    assert not bool(q15.native_temporal_interpolation_allowed)


def test_post_minus6_timeline_remains_diagnostic_only():
    tl = build_observer_environment_timeline(_hourly(), _event_contract(), _native())
    q = tl[tl.event_offset_minutes.eq(60)]
    assert not q.empty
    assert q.core_physics_window_state.eq("POST_MINUS6_DIAGNOSTIC_ONLY").all()
    assert not q.tau_synthesis_allowed.astype(bool).any()
    assert not q.formation_promotion_allowed.astype(bool).any()
    assert not q.viewing_target_required.astype(bool).any()


def test_summary_and_integrity_preserve_role_separation():
    tl = build_observer_environment_timeline(_hourly(), _event_contract(), _native())
    sm = summarize_observer_environment_timeline(tl)
    event_ext = sm[(sm.event_offset_minutes.eq(0)) & (sm.distance_band.eq("EXTENDED_GT40_100KM"))].iloc[0]
    assert event_ext.diagnostic_status == "COARSE_LOW_CLOUD_PRESENT_NATIVE_3D_NOT_RECONSTRUCTED"
    audit = build_analysis_integrity_audit({
        "v1_observer_environment_timeline": tl,
        "v1_observer_environment_timeline_summary": sm,
    })
    by_id = audit.set_index("check_id")["status"].to_dict()
    assert by_id["OBSERVER_ENVIRONMENT_TIMELINE_PRESENT"] == "PASS"
    assert by_id["OBSERVER_ENVIRONMENT_TIMELINE_ROLE_SEPARATION"] == "PASS"
    assert by_id["OBSERVER_ENVIRONMENT_TIMELINE_WINDOW_CONTRACT"] == "PASS"
    assert by_id["OBSERVER_ENVIRONMENT_TIMELINE_SUMMARY"] == "PASS"
