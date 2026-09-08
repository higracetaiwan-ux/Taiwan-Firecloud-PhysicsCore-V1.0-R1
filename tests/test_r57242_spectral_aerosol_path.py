import numpy as np
import pandas as pd

from firecloud.aerosol_physics import derive_route_spectral_aod
from firecloud.model import _build_physics_data_completeness
from firecloud.spectral_rt import build_spectral_rt


def _base_summary(angle=0.0):
    return pd.DataFrame([{"solar_altitude_deg": angle, "data_completeness": 1.0}])


def _gas_profile():
    return pd.DataFrame({
        "direction_offset_deg": [0.0, 0.0],
        "distance_km": [0.0, 0.0],
        "altitude_agl_km": [0.2, 23.0],
        "temperature_k": [290.0, 220.0],
        "pressure_hpa": [1000.0, 30.0],
        "relative_humidity_pct": [60.0, 5.0],
        "h2o_mole_fraction": [0.01, 1e-5],
        "o2_mole_fraction": [0.20946, 0.20946],
        "o3_mole_fraction": [2e-7, 2e-6],
    })


def _provider_detail(angle=0.0, *, spectral=None, canvas_count=0, sunlit_count=0):
    return {
        angle: {
            "cams_native_aerosol_snapshot": pd.DataFrame({
                "cams_aerext532_m1_1000hPa": [1e-5],
                "cams_aerext532_m1_30hPa": [1e-8],
            }),
            "cams_native_aerosol_metadata": {},
            "gas_profile": _gas_profile(),
            "hitran_backend_status": {
                "runtime_spectroscopy_ready": True,
                "database_exists": True,
                "coefficient_table_exists": True,
            },
            "spectral_voxels": pd.DataFrame() if spectral is None else spectral,
            "spectral_rt_requirement": {
                "canvas_count": canvas_count,
                "direct_sunlit_canvas_count": sunlit_count,
            },
        }
    }


def test_six_band_route_aod_includes_575nm_without_fixed_angstrom_constant():
    route = pd.DataFrame([{
        "point_id": "p", "distance_km": 0.0, "direction_offset_deg": 0.0,
        "aod550": 0.20, "aod645": 0.16, "aod670": 0.15, "aod800": 0.12,
    }])
    out = derive_route_spectral_aod(route)
    for wl in (550, 575, 600, 650, 700, 750):
        assert f"aod{wl}" in out.columns
        assert pd.notna(out.loc[0, f"aod{wl}"])
    assert out.loc[0, "spectral_aod_quality"] == "REAL_MULTI_WAVELENGTH_COLUMN_AOD"


def test_no_canvas_geometry_is_not_applicable_not_missing():
    angle = 0.0
    out = _build_physics_data_completeness(
        _provider_detail(angle, canvas_count=0, sunlit_count=0),
        [(angle, pd.Timestamp("2026-09-08 18:00"), 270.0)],
        _base_summary(angle),
    )
    aero = out[out.layer == "SPECTRAL_AEROSOL_PATH"].iloc[0]
    full = out[out.layer == "FULL_SPECTRAL_RT"].iloc[0]
    assert aero.status == "NOT_APPLICABLE"
    assert aero.completeness == 1.0
    assert aero.missing_reason == "NO_TARGET_CLOUD_GEOMETRY"
    assert full.status == "NOT_APPLICABLE"
    assert full.completeness == 1.0


def test_sunlit_canvas_with_empty_spectral_table_stays_missing():
    angle = 0.0
    out = _build_physics_data_completeness(
        _provider_detail(angle, canvas_count=1, sunlit_count=1),
        [(angle, pd.Timestamp("2026-09-08 18:00"), 270.0)],
        _base_summary(angle),
    )
    aero = out[out.layer == "SPECTRAL_AEROSOL_PATH"].iloc[0]
    full = out[out.layer == "FULL_SPECTRAL_RT"].iloc[0]
    assert aero.status == "MISSING"
    assert full.status == "MISSING"


def test_partial_native_cams_path_uses_complete_sun_to_canvas_aod_fallback():
    # Real spectral column AOD extends across the fixed Formation route.
    route = pd.DataFrame([
        {
            "point_id": f"p{d}", "distance_km": float(d), "direction_offset_deg": 0.0,
            "aod550": 0.20, "aod645": 0.16, "aod670": 0.15, "aod800": 0.12,
            "aerosol_provider": "TEST_REAL_AOD",
        }
        for d in (0, 20, 100, 200, 400, 600, 800, 1000, 1180)
    ])
    route_spectral = derive_route_spectral_aod(route)

    # Native extinction exists (so native tau can be finite) but its horizontal
    # domain ends before the incoming ray reaches the 30-km aerosol atmosphere
    # top. That finite partial tau must not suppress the real-AOD fallback.
    cams = route_spectral[route_spectral.distance_km <= 200.0].copy()
    for p, z, beta in ((1000, 0.2, 1e-5), (700, 3.0, 5e-6), (300, 9.0, 1e-6), (100, 16.0, 2e-7), (30, 23.0, 5e-8)):
        cams[f"cams_aerext532_m1_{p}hPa"] = beta
        cams[f"cams_geopotential_height_m_{p}hPa"] = z * 1000.0

    vox = pd.DataFrame([{
        "point_id": "target", "solar_altitude_deg": 0.0,
        "direction_offset_deg": 0.0, "distance_km": 20.0,
        "voxel_center_km": 4.0, "band": "0-40 km Primary Canvas",
        "slant_cloud_optical_depth_estimate": 0.2,
        "geometric_illuminated_fraction": 1.0,
        "cloud_fraction_used": 0.8,
    }])
    out = build_spectral_rt(
        vox, 0.0,
        aerosol_snapshot=route,
        cams_native_aerosol_snapshot=cams,
        prepared_route_spectral_aod=route_spectral,
        angstrom_exponent=None,
    )
    assert pd.notna(out.loc[0, "native_cams_aerosol_tau_650nm"])
    assert not bool(out.loc[0, "native_cams_aerosol_domain_complete"])
    assert bool(out.loc[0, "route_aerosol_domain_complete"])
    assert out.loc[0, "route_aerosol_path_completeness"] >= 0.999
    assert bool(out.loc[0, "aerosol_rt_path_complete"])
    assert out.loc[0, "aerosol_rt_path_source"] == "REAL_MULTI_WAVELENGTH_AOD_EXPONENTIAL_SUN_TO_CANVAS"
    for wl in (550, 575, 600, 650, 700, 750):
        assert pd.notna(out.loc[0, f"aerosol_transmission_{wl}nm"])
    assert "EXPONENTIAL_SUN_TO_CANVAS_FALLBACK" in out.loc[0, "spectral_rt_quality"]
