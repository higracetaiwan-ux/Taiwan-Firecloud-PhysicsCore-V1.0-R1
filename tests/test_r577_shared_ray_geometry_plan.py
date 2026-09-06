import numpy as np
import pandas as pd

from firecloud.config import ModelConfig
from firecloud.model import (
    add_native_optical_properties,
    apply_3d_optical_blocking,
    apply_native_microphysical_optical_blocking,
    prepare_shared_ray_geometry_plan,
)


def _profile_fixture():
    rows=[]
    for off in (-5.0,0.0,5.0):
        for d in (0.0,5.0,10.0,20.0):
            for z in (0.25,0.75,1.25,1.75):
                rows.append({
                    'solar_altitude_deg':-1.5,'direction_offset_deg':off,'distance_km':d,
                    'band':'TEST','voxel_center_km':z,'voxel_bottom_km':z-0.25,'voxel_top_km':z+0.25,
                    'cloud_occupancy':0.4 if z<1.5 else 0.1,'relative_humidity_pct':80.0,
                    'profile_supported':True,'profile_source':'TEST','profile_quality':'TEST'
                })
    return pd.DataFrame(rows)


def _native_fixture(profile):
    n=profile.rename(columns={'cloud_occupancy':'cloud_fraction_used'}).copy()
    n['pressure_hpa']=900.0
    n['temperature_k']=285.0
    n['air_density_kg_m3']=1.1
    n['cloud_liquid_water_mixing_ratio_kgkg']=1e-5
    n['cloud_ice_mixing_ratio_kgkg']=0.0
    n['total_cloud_condensate_kgkg']=1e-5
    return n


def _assert_same(a,b):
    assert list(a.columns)==list(b.columns)
    assert len(a)==len(b)
    for c in a.columns:
        av=a[c]; bv=b[c]
        if pd.api.types.is_numeric_dtype(av) or pd.api.types.is_numeric_dtype(bv):
            assert np.allclose(pd.to_numeric(av,errors='coerce'), pd.to_numeric(bv,errors='coerce'), equal_nan=True, rtol=0, atol=1e-12), c
        else:
            assert av.fillna('<NA>').astype(str).equals(bv.fillna('<NA>').astype(str)), c


def test_shared_ray_geometry_plan_preserves_proxy_and_native_results():
    cfg=ModelConfig()
    angle=-1.5
    p=_profile_fixture()
    n=add_native_optical_properties(_native_fixture(p))
    plan=prepare_shared_ray_geometry_plan(p,angle,cfg)
    assert plan.get('directions')

    proxy_old=apply_3d_optical_blocking(p,angle,cfg)
    proxy_new=apply_3d_optical_blocking(p,angle,cfg,shared_ray_geometry_plan=plan)
    _assert_same(proxy_old,proxy_new)

    native_old=apply_native_microphysical_optical_blocking(n,angle,cfg,optical_properties_ready=True)
    native_new=apply_native_microphysical_optical_blocking(n,angle,cfg,optical_properties_ready=True,shared_ray_geometry_plan=plan)
    _assert_same(native_old,native_new)
