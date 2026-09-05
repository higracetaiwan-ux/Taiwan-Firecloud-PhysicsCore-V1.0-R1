import math
import numpy as np
import pandas as pd

from firecloud.cloud_optics import condensate_extinction_m1, add_native_optical_properties
from firecloud.config import ModelConfig
from firecloud.model import apply_native_microphysical_optical_blocking


def test_liquid_extinction_matches_geometric_optics_relation():
    x = condensate_extinction_m1(0.1, 0.0, cloud_fraction=1.0, liquid_reff_um=10.0)
    # beta = 3 M /(2 rho r) for Qext=2; M=1e-4 kg/m3, rho=1000, r=1e-5 m
    assert math.isclose(x["total_extinction_m1"], 0.015, rel_tol=1e-6)


def test_cloud_fraction_scales_grid_mean_extinction():
    full = condensate_extinction_m1(0.1, 0.0, cloud_fraction=1.0)
    half = condensate_extinction_m1(0.1, 0.0, cloud_fraction=0.5)
    assert math.isclose(half["total_extinction_m1"], full["total_extinction_m1"] * 0.5, rel_tol=1e-9)


def test_missing_condensate_never_becomes_clear():
    x = condensate_extinction_m1(np.nan, 0.0, cloud_fraction=1.0)
    assert np.isnan(x["total_extinction_m1"])
    assert x["optics_quality"] == "MISSING_NATIVE_CONDENSATE"


def test_vertical_voxel_cod_and_transmission():
    df = pd.DataFrame([{
        "direction_offset_deg": 0.0, "distance_km": 0.0,
        "voxel_center_km": 1.0, "voxel_bottom_km": 0.75, "voxel_top_km": 1.25,
        "cloud_fraction": 1.0, "liquid_water_content_gm3": 0.01,
        "ice_water_content_gm3": 0.0, "total_cloud_condensate_kgkg": 1e-5,
    }])
    out = add_native_optical_properties(df)
    tau = out.iloc[0]["vertical_cloud_optical_depth_estimate"]
    assert tau > 0
    assert math.isclose(out.iloc[0]["vertical_cloud_transmission_estimate"], math.exp(-tau), rel_tol=1e-9)


def test_upstream_native_cloud_reduces_transmission():
    rows=[]
    for d in (0.0,20.0,40.0):
        for z in (4.75,5.25,5.75):
            rows.append({
                "direction_offset_deg":0.0,"distance_km":d,
                "voxel_center_km":z,"voxel_bottom_km":z-0.25,"voxel_top_km":z+0.25,
                "cloud_fraction":1.0,"liquid_water_content_gm3":0.002,
                "ice_water_content_gm3":0.0,"total_cloud_condensate_kgkg":2e-6,
            })
    native=pd.DataFrame(rows)
    out=apply_native_microphysical_optical_blocking(native,-1.0,ModelConfig())
    near=out[(out.distance_km==0.0)&(out.voxel_center_km==5.25)].iloc[0]
    far=out[(out.distance_km==40.0)&(out.voxel_center_km==5.25)].iloc[0]
    assert near["slant_cloud_optical_depth_estimate"] > 0
    assert near["remaining_native_cloud_transmission_estimate"] < 1.0
    assert far["remaining_native_cloud_transmission_estimate"] == 1.0
