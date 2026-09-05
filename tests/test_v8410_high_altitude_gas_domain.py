from pathlib import Path
import pandas as pd
import numpy as np

from firecloud.providers.openmeteo import PRESSURE_LEVELS_HPA as OM_LEVELS
from firecloud.providers.cams_native import DEFAULT_PRESSURE_LEVELS_HPA as CAMS_LEVELS
from firecloud.gas_rt import build_gas_profile


def test_pressure_contract_reaches_above_18km():
    for levels in (OM_LEVELS, CAMS_LEVELS):
        assert 70 in levels
        assert 50 in levels
        assert 30 in levels
        assert min(levels) <= 30


def test_gas_profile_can_bracket_18km_without_vertical_extrapolation():
    row = {"point_id":"p0", "distance_km":0.0, "direction_offset_deg":0.0, "model_surface_elevation_m":0.0}
    # Realistic approximate geopotential heights; 50 hPa is above 18 km.
    heights={100:15800.0,70:17700.0,50:19300.0,30:22000.0}
    temps={100:216.0,70:214.0,50:216.0,30:220.0}
    for p,z in heights.items():
        row[f"geopotential_height_{p}hPa"] = z
        row[f"temperature_{p}hPa"] = temps[p]
        row[f"relative_humidity_{p}hPa"] = 5.0
    snap=pd.DataFrame([row])
    o3={"point_id":"p0"}
    for p in heights:
        o3[f"cams_ozone_kgkg_{p}hPa"] = 1e-6
    gp=build_gas_profile(snap, (100,70,50,30), ozone_snapshot=pd.DataFrame([o3]))
    assert not gp.empty
    assert gp["altitude_agl_km"].max() >= 18.0
    assert set(gp["pressure_hpa"]) == {100.0,70.0,50.0,30.0}
    assert gp["o3_mole_fraction"].notna().all()


def test_model_uses_gas_pressure_contract_not_gfs_cloud_contract():
    text=(Path(__file__).resolve().parents[1]/"firecloud"/"model.py").read_text(encoding="utf-8")
    assert "PRESSURE_LEVELS_HPA as GAS_PRESSURE_LEVELS_HPA" in text
    assert "build_gas_profile(snap, GAS_PRESSURE_LEVELS_HPA" in text


def test_openmeteo_request_vars_include_high_altitude_state():
    from firecloud.providers.openmeteo import HOURLY_VARS
    for p in (70,50,30):
        assert f"temperature_{p}hPa" in HOURLY_VARS
        assert f"relative_humidity_{p}hPa" in HOURLY_VARS
        assert f"geopotential_height_{p}hPa" in HOURLY_VARS


def test_cams_request_contains_high_altitude_levels():
    from datetime import datetime, timezone
    from firecloud.providers.cams_native import build_ads_ozone_request
    req,_=build_ads_ozone_request([{"lat":24.25,"lon":120.5}], datetime(2026,9,4,12,tzinfo=timezone.utc))
    levels=set(req.get("pressure_level",[]))
    assert {"70","50","30"}.issubset(levels)
