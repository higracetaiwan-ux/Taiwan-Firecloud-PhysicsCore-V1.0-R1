import pandas as pd

import firecloud
from firecloud.observer_nearfield_cloud_environment import (
    build_observer_nearfield_cloud_environment,
    summarize_observer_nearfield_cloud_environment,
)
from firecloud.case_integrity import build_analysis_integrity_audit


def _route():
    t = pd.Timestamp("2026-09-14 18:00:00+08:00")
    return pd.DataFrame([
        {"time": t, "solar_altitude_deg": 0.0, "point_id": "+0.0_0000", "direction_offset_deg": 0.0, "distance_km": 0.0,
         "cloud_cover_low": 2.0, "cloud_cover_mid": 1.0, "cloud_cover_high": 0.0, "visibility": 14000.0, "relative_humidity_2m": 88.0, "precipitation": 0.0},
        {"time": t, "solar_altitude_deg": 0.0, "point_id": "+0.0_0050", "direction_offset_deg": 0.0, "distance_km": 50.0,
         "cloud_cover_low": 27.0, "cloud_cover_mid": 1.0, "cloud_cover_high": 0.0, "visibility": 13940.0, "relative_humidity_2m": 88.0, "precipitation": 0.0},
        {"time": t, "solar_altitude_deg": 0.0, "point_id": "+0.0_0070", "direction_offset_deg": 0.0, "distance_km": 70.0,
         "cloud_cover_low": 38.0, "cloud_cover_mid": 0.0, "cloud_cover_high": 0.0, "visibility": 13720.0, "relative_humidity_2m": 88.0, "precipitation": 0.0},
        {"time": t, "solar_altitude_deg": 0.0, "point_id": "+5.0_0070", "direction_offset_deg": 5.0, "distance_km": 70.0,
         "cloud_cover_low": 58.0, "cloud_cover_mid": 1.0, "cloud_cover_high": 0.0, "visibility": 13100.0, "relative_humidity_2m": 88.0, "precipitation": 0.0},
    ])


def _native_no_columns():
    t = pd.Timestamp("2026-09-14 18:00:00+08:00")
    rows=[]
    for off,d in [(0.0,0.0),(0.0,50.0),(0.0,70.0),(5.0,70.0)]:
        rows.append({
            "time": t, "solar_altitude_deg":0.0, "direction_offset_deg":off, "distance_km":d,
            "native_cloud_base_km":float("nan"), "native_cloud_top_km":float("nan"),
            "native_cloud_thickness_km":float("nan"), "native_vertical_completeness":1.0,
            "liquid_water_path_proxy_gm3_km":0.0, "ice_water_path_proxy_gm3_km":0.0,
        })
    return pd.DataFrame(rows)


def test_version_bumped_to_nearfield_diagnostic_release():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.30.4.1"


def test_coarse_low_cloud_is_preserved_when_native_3d_has_no_column():
    env = build_observer_nearfield_cloud_environment(_route(), _native_no_columns())
    row = env[(env.direction_offset_deg.eq(5.0)) & (env.distance_km.eq(70.0))].iloc[0]
    assert row.cloud_cover_low_pct == 58.0
    assert row.native_low_cloud_geometry_state == "NATIVE_NO_CLOUD_COLUMN_AT_THRESHOLD"
    assert row.coarse_native_low_cloud_relation == "COARSE_LOW_CLOUD_NATIVE_NO_COLUMN_AT_THRESHOLD"
    assert row.diagnostic_role == "OBSERVER_ENVIRONMENT_ONLY_NO_FORMATION_PROMOTION"
    assert not bool(row.tau_synthesis_allowed)
    assert not bool(row.formation_promotion_allowed)
    assert not bool(row.viewing_target_required)


def test_native_low_cloud_geometry_is_reported_without_promoting_formation():
    native = _native_no_columns()
    q = native[(native.direction_offset_deg.eq(0.0)) & (native.distance_km.eq(50.0))].index[0]
    native.loc[q, "native_cloud_base_km"] = 0.5
    native.loc[q, "native_cloud_top_km"] = 1.5
    native.loc[q, "native_cloud_thickness_km"] = 1.0
    native.loc[q, "liquid_water_path_proxy_gm3_km"] = 0.01
    env = build_observer_nearfield_cloud_environment(_route(), native)
    row = env[(env.direction_offset_deg.eq(0.0)) & (env.distance_km.eq(50.0))].iloc[0]
    assert row.native_low_cloud_geometry_state == "NATIVE_LOW_CLOUD_GEOMETRY_PRESENT"
    assert row.coarse_native_low_cloud_relation == "COARSE_AND_NATIVE_LOW_CLOUD"
    assert not bool(row.formation_promotion_allowed)


def test_summary_flags_coarse_native_mismatch_as_diagnostic_not_clear_sky():
    env = build_observer_nearfield_cloud_environment(_route(), _native_no_columns())
    summary = summarize_observer_nearfield_cloud_environment(env)
    row = summary[(summary.direction_offset_deg.eq(5.0)) & (summary.distance_band.eq("EXTENDED_GT40_100KM"))].iloc[0]
    assert row.coarse_low_cloud_max_pct == 58.0
    assert row.coarse_nonzero_native_no_column_point_count == 1
    assert row.diagnostic_status == "COARSE_LOW_CLOUD_PRESENT_NATIVE_3D_NOT_RECONSTRUCTED"
    assert not bool(row.tau_synthesis_allowed)
    assert not bool(row.formation_promotion_allowed)


def test_integrity_accepts_diagnostic_and_enforces_role_separation():
    env = build_observer_nearfield_cloud_environment(_route(), _native_no_columns())
    summary = summarize_observer_nearfield_cloud_environment(env)
    audit = build_analysis_integrity_audit({
        "v1_observer_nearfield_cloud_environment": env,
        "v1_observer_nearfield_cloud_environment_summary": summary,
    })
    by_id = audit.set_index("check_id")["status"].to_dict()
    assert by_id["OBSERVER_NEARFIELD_CLOUD_ENVIRONMENT_PRESENT"] == "PASS"
    assert by_id["OBSERVER_NEARFIELD_DIAGNOSTIC_ROLE_SEPARATION"] == "PASS"
    assert by_id["OBSERVER_NEARFIELD_CLOUD_ENVIRONMENT_SUMMARY"] == "PASS"


def test_integrity_fails_if_diagnostic_attempts_formation_promotion():
    env = build_observer_nearfield_cloud_environment(_route(), _native_no_columns())
    summary = summarize_observer_nearfield_cloud_environment(env)
    env.loc[:, "formation_promotion_allowed"] = True
    audit = build_analysis_integrity_audit({
        "v1_observer_nearfield_cloud_environment": env,
        "v1_observer_nearfield_cloud_environment_summary": summary,
    })
    status = audit.loc[audit.check_id.eq("OBSERVER_NEARFIELD_DIAGNOSTIC_ROLE_SEPARATION"), "status"].iloc[0]
    assert status == "FAIL"
