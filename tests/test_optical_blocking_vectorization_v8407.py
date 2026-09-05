import math
import time
import numpy as np
import pandas as pd

from firecloud.config import ModelConfig
from firecloud.geometry import ray_altitude_km_at_surface_distance
from firecloud.model import (
    _ray_altitudes_vectorized_km,
    apply_3d_optical_blocking,
    apply_native_microphysical_optical_blocking,
)


def _synthetic_profile():
    rows=[]
    distances=np.arange(0.0, 460.0, 20.0)
    heights=np.arange(0.25, 18.0, 0.5)
    for off in (-5.0,0.0,5.0):
        for d in distances:
            for z in heights:
                occ=0.55 if 4.0 <= z <= 10.0 else 0.08
                rows.append({
                    'direction_offset_deg':off,'distance_km':d,'voxel_center_km':z,
                    'voxel_bottom_km':z-0.25,'voxel_top_km':z+0.25,
                    'cloud_occupancy':occ,'relative_humidity_pct':70.0,
                    'profile_supported':True,'profile_source':'SYNTHETIC','profile_quality':'TEST',
                })
    return pd.DataFrame(rows)


def _synthetic_native(profile):
    n=profile.copy()
    n['cloud_fraction']=n['cloud_occupancy']
    n['total_cloud_condensate_kgkg']=np.where(n['cloud_occupancy'] >= 0.5, 2e-6, 0.0)
    n['liquid_water_content_gm3']=np.where(n['cloud_occupancy'] >= 0.5, 0.12, 0.0)
    n['ice_water_content_gm3']=np.where(n['voxel_center_km'] >= 7.0, 0.06, 0.0)
    return n


def test_vectorized_ray_geometry_matches_scalar_geometry():
    cfg=ModelConfig()
    samples=np.array([40.0,80.0,120.0,220.0,340.0,440.0])
    vec=_ray_altitudes_vectorized_km(20.0,6.25,samples,-2.0,cfg.earth_radius_km)
    scalar=np.array([
        ray_altitude_km_at_surface_distance(20.0,6.25,float(d),-2.0,cfg.earth_radius_km)
        for d in samples
    ],dtype=float)
    np.testing.assert_allclose(vec,scalar,rtol=0,atol=1e-10,equal_nan=True)


def test_full_lattice_optical_blocking_is_fast_and_complete():
    cfg=ModelConfig()
    p=_synthetic_profile()
    n=_synthetic_native(p)
    t0=time.perf_counter(); po=apply_3d_optical_blocking(p,-1.0,cfg); t1=time.perf_counter()
    no=apply_native_microphysical_optical_blocking(n,-1.0,cfg); t2=time.perf_counter()
    assert len(po)==len(p)
    assert len(no)==len(n)
    assert (t1-t0) < 1.0
    assert (t2-t1) < 1.2
