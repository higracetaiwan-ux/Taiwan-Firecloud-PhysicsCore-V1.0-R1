import math
import numpy as np
import pandas as pd

from firecloud.gas_rt import _sat_vapor_pressure_hpa, build_gas_profile


def _snap(temp):
    return pd.DataFrame([{
        "point_id":"p0", "distance_km":0.0, "direction_offset_deg":0.0,
        "model_surface_elevation_m":0.0,
        "geopotential_height_1000hPa":120.0,
        "temperature_1000hPa":temp,
        "relative_humidity_1000hPa":70.0,
    }])


def test_sat_vapor_pressure_no_overflow_for_legacy_celsius_near_old_singularity():
    # 29.5 °C used to be interpreted as Kelvin, pushing Tc close to -243.5 °C
    # and overflowing math.exp().
    e = _sat_vapor_pressure_hpa(29.5)
    assert math.isfinite(e)
    assert 35.0 < e < 45.0


def test_gas_profile_accepts_legacy_celsius_and_converts_to_kelvin():
    g=build_gas_profile(_snap(29.5), [1000])
    assert len(g)==1
    assert abs(g.iloc[0]["temperature_k"] - 302.65) < 1e-6
    assert np.isfinite(g.iloc[0]["h2o_mole_fraction"])
    assert g.iloc[0]["temperature_quality"] == "LEGACY_CELSIUS_CONVERTED_TO_KELVIN"


def test_gas_profile_keeps_kelvin_kelvin():
    g=build_gas_profile(_snap(290.0), [1000])
    assert abs(g.iloc[0]["temperature_k"] - 290.0) < 1e-9
    assert g.iloc[0]["temperature_quality"] == "FORECAST_PRESSURE_LEVEL_KELVIN"


def test_invalid_temperature_fails_closed_instead_of_crashing():
    g=build_gas_profile(_snap(9999.0), [1000])
    assert np.isnan(g.iloc[0]["temperature_k"])
    assert np.isnan(g.iloc[0]["h2o_mole_fraction"])
    assert g.iloc[0]["temperature_quality"] == "INVALID_TEMPERATURE_MISSING"
