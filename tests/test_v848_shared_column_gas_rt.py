import math
import numpy as np
import pandas as pd

from firecloud.geometry import ray_altitude_km_at_surface_distance
from firecloud.gas_rt import (
    _ray_altitudes_matrix,
    _prepare_fast_lut,
    _sigma_fast,
    _sigma_fast_vector,
    integrate_gas_sun_to_targets,
)


def test_vectorized_spherical_ray_matches_scalar_geometry():
    td=120.0
    tz=np.array([2.25, 5.25, 8.25, 12.25, 17.75])
    ds=np.array([120.0, 140.0, 220.0, 440.0, 700.0])
    got=_ray_altitudes_matrix(td,tz,ds,-4.0,6371.0)
    exp=np.array([
        [ray_altitude_km_at_surface_distance(td,float(z),float(d),-4.0,6371.0) for d in ds]
        for z in tz
    ],dtype=float)
    assert np.allclose(got,exp,rtol=0,atol=1e-10,equal_nan=True)


def test_vectorized_lut_lookup_matches_scalar_packaged_runtime_lut():
    from firecloud.gas_rt import _local_band_coefficients_from_csv
    lut=_prepare_fast_lut(_local_band_coefficients_from_csv())
    tk=np.array([220.0,235.0,250.0,279.0,293.0])
    ph=np.array([100.0,250.0,500.0,850.0,1000.0])
    for gas in ('O3','O2','H2O'):
        for wl in (600,650,700,750):
            got=_sigma_fast_vector(lut,gas,wl,tk,ph)
            exp=np.array([_sigma_fast(lut,gas,wl,float(t),float(p)) for t,p in zip(tk,ph)])
            assert np.allclose(got,exp,rtol=0,atol=0,equal_nan=True)


def test_shared_column_solver_returns_one_result_per_target_with_same_column_order():
    targets=pd.DataFrame({
        'direction_offset_deg':[0.0]*4,
        'distance_km':[0.0]*4,
        'voxel_center_km':[2.0,5.0,8.0,12.0],
    })
    rows=[]
    for d in tuple(float(x) for x in range(0,1181,20)):
        for z,p,t in ((0.2,1000,290.0),(2.0,800,275.0),(5.0,500,255.0),(10.0,250,230.0),(18.0,100,210.0)):
            rows.append({
                'direction_offset_deg':0.0,'distance_km':d,'altitude_agl_km':z,
                'temperature_k':t,'pressure_hpa':p,'o2_mole_fraction':0.20946,
                'h2o_mole_fraction':0.004,'o3_mole_fraction':2e-7,
            })
    out=integrate_gas_sun_to_targets(targets,pd.DataFrame(rows),0.0)
    assert len(out)==len(targets)
    assert out['voxel_center_km'].tolist()==targets['voxel_center_km'].tolist()
    assert out['gas_transmission_650nm'].notna().any()
    assert ((out['gas_path_completeness']>=0)&(out['gas_path_completeness']<=1)).all()
