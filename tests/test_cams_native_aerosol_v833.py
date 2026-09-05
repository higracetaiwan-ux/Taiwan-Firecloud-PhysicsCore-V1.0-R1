from datetime import datetime, timezone
import numpy as np
import pandas as pd

from firecloud.aerosol_physics import integrate_native_cams_aerosol_sun_to_targets
from firecloud.providers.cams_native import build_ads_request, build_ads_ozone_request, build_ads_spectral_aod_request, resolve_cams_run_and_lead


def test_cams_run_resolver_uses_00_or_12_cycle():
    target=datetime(2026,9,3,10,tzinfo=timezone.utc)
    run,lead=resolve_cams_run_and_lead(target, now_utc=datetime(2026,9,3,20,tzinfo=timezone.utc))
    assert run.hour in (0,12)
    assert lead % 3 == 0


def test_ads_requests_include_native_extinction_and_real_spectral_aod():
    pts=[{"lat":25.0,"lon":121.0}]
    t=datetime(2026,9,3,6,tzinfo=timezone.utc)
    req,_=build_ads_request(pts,t,pressure_levels_hpa=(1000,850,500))
    assert "aerosol_extinction_coefficient_532nm" in req["variable"]
    assert req["pressure_level"] == ["1000","850","500"]
    sreq,_=build_ads_spectral_aod_request(pts,t)
    assert "total_aerosol_optical_depth_550nm" in sreq["variable"]
    assert "total_aerosol_optical_depth_800nm" in sreq["variable"]


def test_native_cams_integration_traces_upstream_sun_path_and_uses_native_vertical_profile():
    vox=pd.DataFrame([{
        "point_id":"0_100", "direction_offset_deg":0.0, "distance_km":100.0,
        "voxel_center_km":5.0,
    }])
    rows=[]
    for d in (100.0,120.0,140.0):
        r={"point_id":f"0_{int(d)}","direction_offset_deg":0.0,"distance_km":d,
           "aod550":0.20,"aod645":0.16,"aod670":0.15,"aod800":0.12}
        # Native 532-nm extinction profile with real height support.
        for p,z,b in [(1000,0.1,1.0e-4),(850,1.5,8.0e-5),(700,3.0,5.0e-5),(500,5.5,2.0e-5),(300,9.0,2.0e-6)]:
            r[f"cams_geopotential_height_m_{p}hPa"]=z*1000.0
            r[f"cams_aerext532_m1_{p}hPa"]=b
        rows.append(r)
    cams=pd.DataFrame(rows)

    def ray_alt(d_t,z_t,d_s,solar_alt,radius):
        # A simple monotonic incoming ray for this unit test.
        return z_t + 0.02*(d_s-d_t)

    out=integrate_native_cams_aerosol_sun_to_targets(vox,cams,-2.0,ray_alt)
    assert np.isfinite(out.loc[0,"native_cams_aerosol_tau_650nm"])
    assert 0 < out.loc[0,"native_cams_aerosol_transmission_650nm"] <= 1
    assert "SUN_TO_CANVAS" in out.loc[0,"native_cams_aerosol_quality"]
