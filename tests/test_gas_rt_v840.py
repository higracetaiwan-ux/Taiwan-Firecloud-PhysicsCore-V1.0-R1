import pandas as pd, numpy as np
from firecloud.gas_rt import build_gas_profile, integrate_gas_sun_to_targets

def test_gas_profile_preserves_missing_ozone():
    s=pd.DataFrame([{"point_id":"p","distance_km":0,"direction_offset_deg":0,"model_surface_elevation_m":0,
                     "geopotential_height_1000hPa":100,"temperature_1000hPa":290,"relative_humidity_1000hPa":50}])
    g=build_gas_profile(s,[1000])
    assert len(g)==1 and np.isnan(g.iloc[0]["o3_mole_fraction"])
    assert g.iloc[0]["o2_mole_fraction"]>0

def test_full_gas_fails_closed_without_local_table(tmp_path):
    t=pd.DataFrame([{"distance_km":0,"direction_offset_deg":0,"voxel_center_km":5}])
    o=integrate_gas_sun_to_targets(t,pd.DataFrame(),-2,db_path=str(tmp_path))
    assert np.isnan(o.iloc[0]["gas_transmission_650nm"])
    assert "MISSING" in o.iloc[0]["gas_rt_quality"]
