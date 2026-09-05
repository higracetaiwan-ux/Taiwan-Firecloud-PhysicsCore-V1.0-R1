import time
import numpy as np
import pandas as pd

from firecloud.aerosol_physics import (
    derive_route_spectral_aod,
    integrate_route_aerosol_to_targets,
    integrate_native_cams_aerosol_sun_to_targets,
)
from firecloud.geometry import ray_altitude_km_at_surface_distance


def _fixture():
    vox=[]
    for off in (-5.0,0.0,5.0):
        for d in range(0,441,20):
            for z in np.arange(0.25,18.0,0.5):
                vox.append({"direction_offset_deg":off,"distance_km":float(d),"voxel_center_km":float(z)})
    route=[]; levels=(1000,925,850,700,500,300,200,100)
    for off in (-5.0,0.0,5.0):
        for d in range(0,441,20):
            r={"direction_offset_deg":off,"distance_km":float(d),"aod550":0.12,"aod645":0.08,"aod670":0.075,"aod800":0.05}
            for i,p in enumerate(levels):
                r[f"cams_aerext532_m1_{p}hPa"]=1e-5*np.exp(-i/3)
                r[f"cams_geopotential_height_m_{p}hPa"]=i*2000.0
            route.append(r)
    return pd.DataFrame(vox), pd.DataFrame(route)


def test_full_lattice_aerosol_integrators_complete_quickly():
    vox, route = _fixture()
    spectral = derive_route_spectral_aod(route)
    t0=time.perf_counter()
    a=integrate_route_aerosol_to_targets(vox,spectral)
    fallback=time.perf_counter()-t0
    t0=time.perf_counter()
    b=integrate_native_cams_aerosol_sun_to_targets(vox,route,-2.0,ray_altitude_km_at_surface_distance)
    native=time.perf_counter()-t0
    assert len(a)==len(vox) and len(b)==len(vox)
    assert fallback < 3.0
    assert native < 3.0
