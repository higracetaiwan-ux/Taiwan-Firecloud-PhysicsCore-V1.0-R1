import pandas as pd
from firecloud.illuminated_canvas_retreat import build_illuminated_canvas_retreat, build_reference_canvas_retreat_matrix


def test_actual_retreat_keeps_geometry_and_rt_separate():
    df = pd.DataFrame([
        {"solar_altitude_deg":-2.0,"distance_km":0,"cloud_base_altitude_km":5,"direct_solar_fraction":0.0,"red_base_illumination_resolved":False,"red_light_reaches_cloudbase":False},
        {"solar_altitude_deg":-2.0,"distance_km":40,"cloud_base_altitude_km":5,"direct_solar_fraction":0.8,"red_base_illumination_resolved":False,"red_light_reaches_cloudbase":False},
        {"solar_altitude_deg":-2.0,"distance_km":100,"cloud_base_altitude_km":5,"direct_solar_fraction":1.0,"red_base_illumination_resolved":False,"red_light_reaches_cloudbase":False},
    ])
    out = build_illuminated_canvas_retreat(df).iloc[0]
    assert out["geometry_nearest_any_sun_km"] == 40
    assert out["physical_red_track_state"] == "MISSING_RT"
    assert pd.isna(out["physical_red_nearest_illuminated_km"])


def test_reference_4km_retreat_moves_outward_as_sun_descends():
    out = build_reference_canvas_retreat_matrix([-1.5,-2.5], distances_km=[0,20,40,60,80,100], cloud_base_heights_km=[4.0])
    a = out[out.solar_altitude_deg.eq(-1.5)].iloc[0]
    b = out[out.solar_altitude_deg.eq(-2.5)].iloc[0]
    assert b["nearest_any_sun_km"] >= a["nearest_any_sun_km"]


def test_reference_matrix_marks_geometry_only():
    out = build_reference_canvas_retreat_matrix([-2.0], distances_km=[0,50,100], cloud_base_heights_km=[5.0])
    assert out["geometry_only"].all()
    assert (~out["spectral_rt_included"]).all()
