import numpy as np
import pandas as pd

from firecloud.native_cloud import native_levels_from_row, build_native_cloud_volume
from firecloud.providers.gfs_native import merge_native_into_snapshot


def test_native_levels_reads_canonical_kgkg_condensate_fields():
    row=pd.Series({
        "model_surface_elevation_m":0.0,
        "geopotential_height_500hPa":5500.0,
        "cloud_liquid_water_kgkg_500hPa":1.2e-5,
        "cloud_ice_water_kgkg_500hPa":2.3e-5,
        "cloud_fraction_500hPa":0.6,
        "temperature_500hPa":255.0,
        "relative_humidity_500hPa":80.0,
    })
    pts=native_levels_from_row(row,(500,))
    assert len(pts)==1
    assert pts[0]["cloud_liquid_water_kgkg"]==1.2e-5
    assert pts[0]["cloud_ice_water_kgkg"]==2.3e-5


def test_merge_preserves_decoder_condensate_contract_and_legacy_replay_fallback():
    snap=pd.DataFrame([{"point_id":"p"}])
    native=pd.DataFrame([{
        "point_id":"p",
        "cloud_liquid_water_kgkg_500hPa":1e-5,
        "cloud_ice_water_kgkg_500hPa":2e-5,
    }])
    out=merge_native_into_snapshot(snap,native)
    assert out.loc[0,"cloud_liquid_water_kgkg_500hPa"]==1e-5
    assert out.loc[0,"cloud_ice_water_kgkg_500hPa"]==2e-5

    old=pd.DataFrame([{"point_id":"p","cloud_liquid_water_500hPa":3e-5,"cloud_ice_water_500hPa":4e-5}])
    replay=merge_native_into_snapshot(snap,old)
    assert replay.loc[0,"cloud_liquid_water_kgkg_500hPa"]==3e-5
    assert replay.loc[0,"cloud_ice_water_kgkg_500hPa"]==4e-5


def test_cloud_volume_supports_canonical_condensate_after_schema_bridge():
    rows=[]
    for p,z,ql,qi,t in [(700,3000,1e-5,0.0,270.0),(500,5500,2e-5,1e-5,255.0)]:
        pass
    row={
        "direction_offset_deg":0.0,"distance_km":20.0,"model_surface_elevation_m":0.0,
        "native_profile_source":"GFS",
        "geopotential_height_700hPa":3000.0,"geopotential_height_500hPa":5500.0,
        "cloud_liquid_water_kgkg_700hPa":1e-5,"cloud_ice_water_kgkg_700hPa":0.0,
        "cloud_liquid_water_kgkg_500hPa":2e-5,"cloud_ice_water_kgkg_500hPa":1e-5,
        "cloud_fraction_700hPa":0.5,"cloud_fraction_500hPa":0.7,
        "temperature_700hPa":270.0,"temperature_500hPa":255.0,
        "relative_humidity_700hPa":80.0,"relative_humidity_500hPa":85.0,
    }
    vox,_=build_native_cloud_volume(pd.DataFrame([row]),(700,500),[4.0],0.5)
    assert len(vox)==1
    assert bool(vox.iloc[0]["native_microphysics_supported"]) is True
    assert np.isfinite(vox.iloc[0]["cloud_liquid_water_kgkg"])
    assert np.isfinite(vox.iloc[0]["cloud_ice_water_kgkg"])
    assert vox.iloc[0]["native_quality"]=="NATIVE_CONDENSATE_INTERPOLATED"
