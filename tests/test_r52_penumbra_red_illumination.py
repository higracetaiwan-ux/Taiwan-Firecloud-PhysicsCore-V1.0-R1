import math
import pandas as pd
from firecloud.geometry import finite_solar_disk_penumbra_heights_km, direct_solar_fraction_g0
from firecloud.penumbra_red import build_earth_shadow_penumbra_matrix, build_canvas_penumbra_red_illumination


def test_penumbra_height_ordering():
    h=finite_solar_disk_penumbra_heights_km(30.0,-2.5)
    assert h['h_any_sun_km'] < h['h_solar_center_km'] < h['h_full_solar_disk_km']
    assert 3.0 < h['h_any_sun_km'] < 4.5
    assert 4.0 < h['h_solar_center_km'] < 5.5
    assert 5.0 < h['h_full_solar_disk_km'] < 7.0


def test_fsun_tracks_penumbra_boundaries():
    h=finite_solar_disk_penumbra_heights_km(30.0,-2.5)
    assert direct_solar_fraction_g0(30.0,h['h_any_sun_km']-0.01,-2.5) == 0.0
    fmid=direct_solar_fraction_g0(30.0,h['h_solar_center_km'],-2.5)
    assert abs(fmid-0.5) < 1e-6
    assert direct_solar_fraction_g0(30.0,h['h_full_solar_disk_km']+0.01,-2.5) == 1.0


def test_core_matrix_has_36_rows():
    df=build_earth_shadow_penumbra_matrix([0,-0.5,-1,-1.5,-2,-2.5,-3,-3.5,-4])
    assert len(df)==36
    assert set(df['distance_km'])=={10.0,20.0,30.0,40.0}


def test_canvas_red_diagnostic_does_not_invent_effective_red_threshold():
    canv=pd.DataFrame([{'canvas_id':'c1','cloud_layer_id':'l1','distance_km':30.0,'cloud_base_altitude_km':5.0,'solar_altitude_deg':-2.5}])
    sp=pd.DataFrame([{'canvas_id':'c1','wavelength_nm':wl,'transmission':0.5} for wl in (650,700,750)])
    cb=pd.DataFrame([{'canvas_id':'c1','relative_base_illumination_650nm':0.2,'relative_base_illumination_700nm':0.3,'relative_base_illumination_750nm':0.4}])
    out=build_canvas_penumbra_red_illumination(canv,sp,cb)
    assert out.iloc[0]['red_light_reaches_cloudbase']
    assert out.iloc[0]['penumbra_red_illumination_state']=='RED_LIGHT_REACHES_CLOUDBASE'
    assert 'effective_red_height' not in out.columns
