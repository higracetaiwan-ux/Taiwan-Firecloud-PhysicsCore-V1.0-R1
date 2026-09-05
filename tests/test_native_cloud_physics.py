import numpy as np, pandas as pd
from firecloud.native_cloud import build_native_cloud_volume

def test_native_condensate_builds_phase_and_cloud_bounds():
    r={'distance_km':100.0,'direction_offset_deg':0.0,'model_surface_elevation_m':0.0,'native_profile_source':'SYNTHETIC_NATIVE'}
    for p,z,t,ql,qi,cf in [(900,1000,280,2e-4,0,0.8),(700,3000,265,1e-4,1e-4,0.9),(500,5600,250,0,2e-4,0.7)]:
        r[f'geopotential_height_{p}hPa']=z;r[f'temperature_{p}hPa']=t;r[f'cloud_liquid_water_{p}hPa']=ql;r[f'cloud_ice_water_{p}hPa']=qi;r[f'cloud_fraction_{p}hPa']=cf;r[f'relative_humidity_{p}hPa']=95
    vox,cols=build_native_cloud_volume(pd.DataFrame([r]),(900,700,500),(1.5,2.5,4.0,5.0),0.5)
    assert vox['native_microphysics_supported'].all()
    assert set(vox['cloud_phase']).intersection({'LIQUID','MIXED','ICE'})
    assert cols.iloc[0]['native_cloud_base_km'] < cols.iloc[0]['native_cloud_top_km']

def test_missing_native_condensate_stays_missing():
    r={'distance_km':0.0,'direction_offset_deg':0.0,'model_surface_elevation_m':0.0}
    for p,z in [(900,1000),(700,3000)]:
        r[f'geopotential_height_{p}hPa']=z;r[f'temperature_{p}hPa']=270;r[f'relative_humidity_{p}hPa']=99
    vox,_=build_native_cloud_volume(pd.DataFrame([r]),(900,700),(2.0,),0.5)
    assert not vox.iloc[0]['native_microphysics_supported']
    assert np.isnan(vox.iloc[0]['total_cloud_condensate_kgkg'])
