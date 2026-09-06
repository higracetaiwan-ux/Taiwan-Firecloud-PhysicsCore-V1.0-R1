import math
import pandas as pd

from firecloud.viewing import build_viewing_path_geometry, summarize_viewing_path
from firecloud.photography_decision import build_photography_decision


def _layers():
    return pd.DataFrame([
        {"time":"t", "solar_altitude_deg":-1.0, "layer_id":"dir+0.0_d5.0_L1", "direction_offset_deg":0.0, "distance_km":5.0, "z_base_km":0.2, "z_top_km":2.0, "cloud_fraction":0.9, "geometry_confidence":"HIGH"},
        {"time":"t", "solar_altitude_deg":-1.0, "layer_id":"dir+0.0_d40.0_L3", "direction_offset_deg":0.0, "distance_km":40.0, "z_base_km":10.0, "z_top_km":12.0, "cloud_fraction":0.4, "geometry_confidence":"HIGH"},
    ])


def _canvases():
    return pd.DataFrame([
        {"time":"t", "solar_altitude_deg":-1.0, "canvas_id":"canvas::dir+0.0_d40.0_L3", "cloud_layer_id":"dir+0.0_d40.0_L3", "distance_km":40.0},
    ])


def test_viewing_branch_detects_intervening_cloud_without_touching_formation_inputs():
    v = build_viewing_path_geometry(_layers(), _canvases())
    assert len(v) == 1
    r = v.iloc[0]
    assert r["intervening_blocker_count"] >= 1
    assert r["view_geometry_state"] in {"VIEW_PARTIAL_OBSTRUCTION", "VIEW_SEVERE_OBSTRUCTION"}
    assert "FORMATION_UNCHANGED" in r["note"]
    assert r["viewing_path_spectral_status"] == "VIEW_SPECTRAL_RT_NOT_YET_RESOLVED"


def test_viewing_summary_remains_separate_from_formation():
    v = build_viewing_path_geometry(_layers(), _canvases())
    s = summarize_viewing_path(v)
    assert len(s) == 1
    assert s.iloc[0]["viewing_state"].startswith("VIEWING_")
    assert "FORMATION_INDEPENDENT" in s.iloc[0]["note"]


def test_photography_blocked_is_outer_decision_even_if_formation_possible():
    formation = pd.DataFrame([{"time":"t", "solar_altitude_deg":-1.0, "formation_state":"UNCERTAIN_OPTICS"}])
    viewing = pd.DataFrame([{"time":"t", "solar_altitude_deg":-1.0, "viewing_state":"VIEWING_SEVERELY_OBSCURED"}])
    d = build_photography_decision(formation, viewing)
    assert d.iloc[0]["photography_opportunity"] == "BLOCKED"
    assert d.iloc[0]["photography_outcome"] == "FORMED_OR_POSSIBLY_FORMED_BUT_NOT_PHOTOGRAPHABLE_FROM_OBSERVER"
    assert d.iloc[0]["formation_state"] == "UNCERTAIN_OPTICS"


def test_photography_good_requires_both_formation_and_view():
    formation = pd.DataFrame([{"time":"t", "solar_altitude_deg":-1.0, "formation_state":"FORMATION_CONFIRMED"}])
    viewing = pd.DataFrame([{"time":"t", "solar_altitude_deg":-1.0, "viewing_state":"VIEWING_GEOMETRY_GOOD"}])
    d = build_photography_decision(formation, viewing)
    assert d.iloc[0]["photography_opportunity"] == "GOOD"
    assert d.iloc[0]["photography_outcome"] == "PHOTOGRAPHABLE_FIRECLOUD"
