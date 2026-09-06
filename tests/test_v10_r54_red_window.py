import pandas as pd
from firecloud.red_window import build_canvas_spectral_evolution, build_canvas_peak_windows


def _rad(rows):
    return pd.DataFrame(rows)


def test_geometry_does_not_create_spectral_response():
    rad=_rad([{"time":"t","solar_altitude_deg":-2.5,"canvas_id":"c","cloud_layer_id":"l","distance_km":40,"response_status":"UNCERTAIN_ILLUMINATION_PATH","brightness":None,"redness":None,"effective_illuminated_area_fraction":None}])
    pen=pd.DataFrame([{"time":"t","solar_altitude_deg":-2.5,"canvas_id":"c","cloud_layer_id":"l","direct_solar_fraction":1.0}])
    out=build_canvas_spectral_evolution(rad,pen)
    assert out.iloc[0]["spectral_response_state"]=="SPECTRAL_RT_OR_TARGET_OPTICS_UNRESOLVED"
    assert not bool(out.iloc[0]["spectral_rt_response_resolved"])


def test_distance_roles_are_frozen():
    rad=_rad([
        {"time":"t","solar_altitude_deg":-2,"canvas_id":"a","cloud_layer_id":"a","distance_km":40,"response_status":"UNCERTAIN_ILLUMINATION_PATH"},
        {"time":"t","solar_altitude_deg":-2,"canvas_id":"b","cloud_layer_id":"b","distance_km":50,"response_status":"UNCERTAIN_ILLUMINATION_PATH"},
        {"time":"t","solar_altitude_deg":-2,"canvas_id":"c","cloud_layer_id":"c","distance_km":120,"response_status":"UNCERTAIN_ILLUMINATION_PATH"},
    ])
    out=build_canvas_spectral_evolution(rad,pd.DataFrame())
    assert list(out["canvas_distance_role"])==["PRIMARY_CANVAS_0_40KM","SECONDARY_CANVAS_40_100KM","HORIZON_RESIDUAL_100PLUS_DIAGNOSTIC_ONLY"]


def test_independent_redness_and_brightness_peaks():
    rad=_rad([
        {"time":"t1","solar_altitude_deg":-2.0,"canvas_id":"c","cloud_layer_id":"l","distance_km":40,"response_status":"READY_TIER1_UNCALIBRATED","brightness":0.9,"redness":0.4,"effective_illuminated_area_fraction":0.5,"warm_red_fraction_650_750":0.4},
        {"time":"t2","solar_altitude_deg":-2.5,"canvas_id":"c","cloud_layer_id":"l","distance_km":40,"response_status":"READY_TIER1_UNCALIBRATED","brightness":0.6,"redness":0.8,"effective_illuminated_area_fraction":0.4,"warm_red_fraction_650_750":0.8},
    ])
    out=build_canvas_spectral_evolution(rad,pd.DataFrame())
    assert float(out.loc[out["brightness_peak_for_canvas"],"solar_altitude_deg"].iloc[0])==-2.0
    assert float(out.loc[out["redness_peak_for_canvas"],"solar_altitude_deg"].iloc[0])==-2.5
    win=build_canvas_peak_windows(out)
    assert set(win["dimension"])=={"brightness","redness","effective_illuminated_area_fraction","warm_red_fraction_650_750"}
