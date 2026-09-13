import numpy as np
import pandas as pd
import firecloud
from firecloud.viewing import (
    _prepare_viewing_geometry_plan,
    _projected_support_interval,
    _planned_cf_at_distance,
    _support_cloud_fraction_at_distance,
    build_viewing_path_geometry,
)


def _transect():
    return pd.DataFrame([
        {"layer_id":"L0","time":"T","solar_altitude_deg":-2.0,"direction_offset_deg":0.0,"distance_km":0.0,"z_base_km":0.5,"z_top_km":1.5,"cloud_fraction":0.20},
        {"layer_id":"L1","time":"T","solar_altitude_deg":-2.0,"direction_offset_deg":0.0,"distance_km":10.0,"z_base_km":0.7,"z_top_km":1.7,"cloud_fraction":0.40},
        {"layer_id":"L2","time":"T","solar_altitude_deg":-2.0,"direction_offset_deg":0.0,"distance_km":20.0,"z_base_km":0.9,"z_top_km":1.9,"cloud_fraction":0.60},
        {"layer_id":"TARGET","time":"T","solar_altitude_deg":-2.0,"direction_offset_deg":0.0,"distance_km":40.0,"z_base_km":5.0,"z_top_km":6.0,"cloud_fraction":0.50},
    ])


def test_version_r5741348():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.1"


def test_prepared_plan_matches_legacy_support_and_cf_helpers():
    tr = _transect()
    plan = _prepare_viewing_geometry_plan(tr)
    for pos, (_, row) in enumerate(tr.iterrows()):
        s0, s1, _, _ = _projected_support_interval(row, tr)
        assert plan["support0"][pos] == s0
        assert plan["support1"][pos] == s1
        for x in (0.0, 5.0, 12.5, 17.5, 25.0):
            old_cf, old_method = _support_cloud_fraction_at_distance(row, tr, x)
            new_cf, new_method = _planned_cf_at_distance(plan, pos, x)
            if old_cf is None:
                assert new_cf is None
            else:
                assert new_cf == old_cf
            assert new_method == old_method


def test_geometry_phase1_preserves_sampling_contract_and_expected_obstruction():
    layers = _transect()
    canvases = pd.DataFrame([{
        "time":"T", "solar_altitude_deg":-2.0, "canvas_id":"C", "cloud_layer_id":"TARGET",
        "distance_km":40.0, "formation_canvas_eligible":True,
    }])
    out = build_viewing_path_geometry(layers, canvases)
    assert len(out) == 1
    row = out.iloc[0]
    assert int(row["view_sample_count"]) == 7
    assert row["viewing_geometry_method"] == "ANGULAR_FOOTPRINT_PROJECTED_VOLUME_WITH_CONTINUOUS_CF_CACHED"
    assert row["viewing_path_spectral_status"] == "VIEW_SPECTRAL_PENDING"
    assert "FORMATION_UNCHANGED" in row["note"]
    # Golden legacy-R5.7 geometry result for this deterministic transect.
    assert int(row["intervening_blocker_count"]) == 3
    assert row["blocker_layer_ids"] == "L0;L1;L2"
    assert row["blocker_support_intervals_km"] == "L0:0.000-5.000;L1:5.000-15.000;L2:15.000-20.000"
    assert float(row["view_obstruction_fraction_proxy"]) == 0.5884899553571429
    assert row["view_geometry_state"] == "VIEW_PARTIAL_OBSTRUCTION"
