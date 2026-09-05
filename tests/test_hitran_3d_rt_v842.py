import pandas as pd
import numpy as np
from firecloud.gas_rt import integrate_gas_sun_to_targets


def test_hitran_derived_3d_gas_integrator_produces_finite_tau(tmp_path):
    db=tmp_path/'hitran_db'; db.mkdir()
    rows=[]
    for wl in (600,650,700,750):
        for gas in ('O2','H2O','O3'):
            rows.append({'wavelength_nm':wl,'gas':gas,'sigma_cm2_molecule':1e-28,'temperature_k':280.0,'pressure_hpa':700.0})
    pd.DataFrame(rows).to_csv(db/'firecloud_600_750nm_band_coefficients.csv',index=False)
    prof=[]
    for d in tuple(range(0,1181,20)):
        for z,p in ((0,1000),(5,500),(10,250),(20,50),(30,10)):
            prof.append({'distance_km':d,'direction_offset_deg':0.0,'altitude_agl_km':z,'temperature_k':280.0,'pressure_hpa':p,
                         'o2_mole_fraction':0.20946,'h2o_mole_fraction':0.005,'o3_mole_fraction':5e-7})
    target=pd.DataFrame([{'distance_km':0.0,'direction_offset_deg':0.0,'voxel_center_km':5.0}])
    out=integrate_gas_sun_to_targets(target,pd.DataFrame(prof),0.0,db_path=str(db))
    assert np.isfinite(out.loc[0,'gas_tau_650nm'])
    assert 0 < out.loc[0,'gas_transmission_650nm'] <= 1
    assert out.loc[0,'gas_path_completeness'] > 0
    assert 'HITRAN_DERIVED_3D_GAS_RT' in out.loc[0,'gas_rt_quality']


def test_hitran_integrator_fails_closed_without_table(tmp_path):
    target=pd.DataFrame([{'distance_km':0.0,'direction_offset_deg':0.0,'voxel_center_km':5.0}])
    out=integrate_gas_sun_to_targets(target,pd.DataFrame(),0.0,db_path=str(tmp_path/'none'))
    assert np.isnan(out.loc[0,'gas_tau_650nm'])
    assert out.loc[0,'gas_rt_quality']=='HITRAN_LOCAL_BAND_TABLE_MISSING'
