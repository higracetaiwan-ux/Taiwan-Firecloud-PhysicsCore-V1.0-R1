import math
import pandas as pd

from firecloud.viewing import build_viewing_path_geometry, summarize_viewing_path
from firecloud.providers import dwd_icon_native as icon


def test_near_observer_cloud_between_nodes_can_block_high_cloud_ray():
    # Low cloud is sampled at 0 and 5 km. The high-cloud ray crosses the low
    # cloud near ~1 km; R5.6 point-node logic missed this because d=0 was
    # skipped and at d=5 the ray was already above the low cloud.
    layers=pd.DataFrame([
        {"time":"t","solar_altitude_deg":-1.0,"layer_id":"dir+0.0_d0.0_L1","direction_offset_deg":0.0,"distance_km":0.0,"z_base_km":0.35,"z_top_km":0.65,"cloud_fraction":0.8},
        {"time":"t","solar_altitude_deg":-1.0,"layer_id":"dir+0.0_d5.0_L1","direction_offset_deg":0.0,"distance_km":5.0,"z_base_km":0.35,"z_top_km":0.65,"cloud_fraction":0.8},
        {"time":"t","solar_altitude_deg":-1.0,"layer_id":"dir+0.0_d40.0_L2","direction_offset_deg":0.0,"distance_km":40.0,"z_base_km":15.0,"z_top_km":17.0,"cloud_fraction":0.2},
    ])
    cvs=pd.DataFrame([{"time":"t","solar_altitude_deg":-1.0,"canvas_id":"c","cloud_layer_id":"dir+0.0_d40.0_L2","distance_km":40.0}])
    v=build_viewing_path_geometry(layers,cvs)
    r=v.iloc[0]
    assert r["projected_support_blocker_count"] >= 1
    assert r["view_geometry_state"] in {"VIEW_PARTIAL_OBSTRUCTION","VIEW_SEVERE_OBSTRUCTION"}
    assert "dir+0.0_d0.0_L1" in r["blocker_layer_ids"]
    assert "0.000-2.500" in r["blocker_support_intervals_km"]


def test_low_cloud_targets_do_not_dominate_photography_viewing_summary():
    v=pd.DataFrame([
        {"time":"t","solar_altitude_deg":-1.0,"photographic_target_eligible":False,"view_geometry_state":"VIEW_SEVERE_OBSTRUCTION","view_obstruction_fraction_proxy":0.9},
        {"time":"t","solar_altitude_deg":-1.0,"photographic_target_eligible":True,"view_geometry_state":"VIEW_GEOMETRICALLY_CLEAR","view_obstruction_fraction_proxy":0.0},
    ])
    s=summarize_viewing_path(v).iloc[0]
    assert s["target_count"] == 2
    assert s["photographic_target_count"] == 1
    assert s["viewing_state"] == "VIEWING_GEOMETRY_GOOD"


def test_missing_blocker_cloud_fraction_is_not_manufactured_as_half_cloud():
    layers=pd.DataFrame([
        {"time":"t","solar_altitude_deg":-1.0,"layer_id":"dir+0.0_d0.0_L1","direction_offset_deg":0.0,"distance_km":0.0,"z_base_km":0.35,"z_top_km":0.65,"cloud_fraction":float('nan')},
        {"time":"t","solar_altitude_deg":-1.0,"layer_id":"dir+0.0_d5.0_L1","direction_offset_deg":0.0,"distance_km":5.0,"z_base_km":0.35,"z_top_km":0.65,"cloud_fraction":float('nan')},
        {"time":"t","solar_altitude_deg":-1.0,"layer_id":"dir+0.0_d40.0_L2","direction_offset_deg":0.0,"distance_km":40.0,"z_base_km":15.0,"z_top_km":17.0,"cloud_fraction":0.2},
    ])
    cvs=pd.DataFrame([{"time":"t","solar_altitude_deg":-1.0,"canvas_id":"c","cloud_layer_id":"dir+0.0_d40.0_L2","distance_km":40.0}])
    r=build_viewing_path_geometry(layers,cvs).iloc[0]
    assert math.isnan(float(r["view_obstruction_fraction_proxy"]))
    assert r["view_geometry_state"] == "VIEW_GEOMETRY_INTERSECTION_OCCUPANCY_UNKNOWN"


def test_icon_hypsometric_vertical_geometry_is_surface_anchored():
    z=icon._hypsometric_height_from_pressure_km(1000.0, 100.0, 500.0, 260.0)
    assert 5.0 < z < 6.5
    assert math.isnan(icon._hypsometric_height_from_pressure_km(float('nan'),100.0,500.0,260.0))
