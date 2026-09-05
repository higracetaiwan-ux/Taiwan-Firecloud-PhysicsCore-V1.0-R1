import math
import numpy as np
import pandas as pd
from firecloud.aerosol_physics import (
    angstrom_from_pair,
    spectral_aod_loglog_interpolate,
    derive_route_spectral_aod,
    ray_segment_aerosol_tau,
    integrate_route_aerosol_to_targets,
)
from firecloud.spectral_rt import build_spectral_rt


def test_angstrom_pair_and_loglog_interpolation_are_consistent():
    alpha = 1.4
    a550 = 0.20
    a800 = a550 * (800/550) ** (-alpha)
    got = angstrom_from_pair(a550, 550, a800, 800)
    assert abs(got-alpha) < 1e-10
    a650 = spectral_aod_loglog_interpolate(650, {550:a550, 800:a800})
    expect = a550*(650/550)**(-alpha)
    assert abs(a650-expect) < 1e-10


def test_single_wavelength_does_not_invent_spectral_aod():
    df = pd.DataFrame([{"point_id":"p","distance_km":10,"direction_offset_deg":0,"aod550":0.2}])
    out = derive_route_spectral_aod(df)
    assert np.isnan(out.loc[0,"aod650"])
    assert out.loc[0,"spectral_aod_quality"] == "SPECTRAL_AOD_MISSING"


def test_ray_segment_uses_local_vertical_fraction_not_whole_column_sum():
    # Two 10-km horizontal segments at 4 km altitude should not each add the full 0.2 column AOD.
    tau = ray_segment_aerosol_tau(0.2, 4.0, 4.0, 10.0, scale_height_km=2.0)
    assert 0 < tau < 0.2
    expect = 0.2 * math.exp(-2.0) / 2.0 * 10.0
    assert abs(tau-expect) < 1e-12


def test_route_integration_uses_real_multispectral_columns():
    route = pd.DataFrame([
        {"point_id":"p0","distance_km":0.0,"direction_offset_deg":0.0,"aod550":0.20,"aod645":0.16,"aod670":0.15,"aod800":0.12},
        {"point_id":"p1","distance_km":20.0,"direction_offset_deg":0.0,"aod550":0.24,"aod645":0.19,"aod670":0.18,"aod800":0.14},
    ])
    route = derive_route_spectral_aod(route)
    vox = pd.DataFrame([{"point_id":"p1","distance_km":20.0,"direction_offset_deg":0.0,"voxel_center_km":4.0}])
    out = integrate_route_aerosol_to_targets(vox, route)
    assert out.loc[0,"route_aerosol_tau_600nm"] > out.loc[0,"route_aerosol_tau_750nm"]
    assert 0 < out.loc[0,"route_aerosol_transmission_600nm"] < 1
    assert out.loc[0,"aerosol_path_quality"] == "COLUMN_AOD_TO_EXPONENTIAL_3D_PROFILE"


def test_spectral_rt_activates_without_fixed_angstrom_when_multispectral_aod_exists():
    vox = pd.DataFrame([{
        "point_id":"p1","solar_altitude_deg":-2.0,"direction_offset_deg":0.0,"distance_km":20.0,
        "voxel_center_km":4.0,"band":"0-40 km Primary Canvas","slant_cloud_optical_depth_estimate":0.2,
        "geometric_illuminated_fraction":1.0,"cloud_fraction_used":0.8
    }])
    aero = pd.DataFrame([
        {"point_id":"p0","distance_km":0.0,"direction_offset_deg":0.0,"aod550":0.20,"aod645":0.16,"aod670":0.15,"aod800":0.12,"aerosol_provider":"TEST_MULTI"},
        {"point_id":"p1","distance_km":20.0,"direction_offset_deg":0.0,"aod550":0.24,"aod645":0.19,"aod670":0.18,"aod800":0.14,"aerosol_provider":"TEST_MULTI"},
    ])
    out = build_spectral_rt(vox,-2.0,aerosol_snapshot=aero,angstrom_exponent=None)
    assert pd.notna(out.loc[0,"aerosol_transmission_650nm"])
    assert "REAL_MULTI_WAVELENGTH_AOD" in out.loc[0,"spectral_rt_quality"]
