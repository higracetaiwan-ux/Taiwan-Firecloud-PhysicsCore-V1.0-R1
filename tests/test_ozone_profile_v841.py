import math
import pandas as pd

from firecloud.gas_rt import build_gas_profile, M_DRY_AIR, M_O3, BOLTZMANN
from firecloud.providers.cams_native import build_ads_ozone_request, native_ozone_provider_status
from datetime import datetime, timezone


def test_cams_ads_request_includes_real_pressure_level_ozone():
    pts=[{"point_id":"p0","lat":25.0,"lon":121.0}]
    req,_=build_ads_ozone_request(pts, datetime(2026,9,3,10,tzinfo=timezone.utc), pressure_levels_hpa=(1000,500,100))
    assert "ozone" in req["variable"]
    assert req["pressure_level"] == ["1000","500","100"]
    status=native_ozone_provider_status()
    assert status["native_variable"] == "ozone"
    assert "NO_FIXED_300DU" in status["profile_policy"]


def test_real_cams_o3_mass_mixing_ratio_binds_to_gas_profile():
    snap=pd.DataFrame([{
        "point_id":"p0","distance_km":20.0,"direction_offset_deg":0.0,"model_surface_elevation_m":0.0,
        "geopotential_height_500hPa":5500.0,"temperature_500hPa":255.0,"relative_humidity_500hPa":30.0,
    }])
    q=8.0e-6
    cams=pd.DataFrame([{"point_id":"p0","cams_ozone_kgkg_500hPa":q}])
    gp=build_gas_profile(snap,(500,),ozone_snapshot=cams)
    assert len(gp)==1
    expected_x=q*M_DRY_AIR/M_O3
    assert math.isclose(gp.loc[0,"o3_mole_fraction"], expected_x, rel_tol=1e-12)
    expected_n=expected_x*(50000.0/(BOLTZMANN*255.0))
    assert math.isclose(gp.loc[0,"o3_number_density_m3"], expected_n, rel_tol=1e-12)
    assert gp.loc[0,"o3_quality"] == "CAMS_PRESSURE_LEVEL_OZONE_NATIVE"


def test_o3_missing_stays_missing_no_synthetic_profile():
    snap=pd.DataFrame([{
        "point_id":"p0","distance_km":20.0,"direction_offset_deg":0.0,"model_surface_elevation_m":0.0,
        "geopotential_height_500hPa":5500.0,"temperature_500hPa":255.0,"relative_humidity_500hPa":30.0,
    }])
    gp=build_gas_profile(snap,(500,),ozone_snapshot=pd.DataFrame())
    assert pd.isna(gp.loc[0,"o3_mole_fraction"])
    assert pd.isna(gp.loc[0,"o3_number_density_m3"])
    assert gp.loc[0,"o3_quality"] == "CAMS_O3_MISSING"


def test_real_cams_o3_log_pressure_interpolation_fills_intermediate_model_level():
    snap=pd.DataFrame([{
        "point_id":"p0","distance_km":20.0,"direction_offset_deg":0.0,"model_surface_elevation_m":0.0,
        "geopotential_height_975hPa":250.0,"temperature_975hPa":286.0,"relative_humidity_975hPa":70.0,
    }])
    cams=pd.DataFrame([{"point_id":"p0","cams_ozone_kgkg_950hPa":4e-8,"cams_ozone_kgkg_1000hPa":3e-8}])
    gp=build_gas_profile(snap,(975,),ozone_snapshot=cams)
    assert pd.notna(gp.loc[0,"o3_mole_fraction"])
    assert gp.loc[0,"o3_quality"] == "CAMS_PRESSURE_LEVEL_OZONE_INTERPOLATED_LOGP"
    assert gp.loc[0,"o3_source_pressure_bracket_hpa"] == "950-1000"
