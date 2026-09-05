from pathlib import Path
import numpy as np
import pandas as pd

from firecloud.config import ModelConfig
from firecloud.gas_rt import integrate_gas_sun_to_targets
from firecloud.model import _build_physics_data_completeness


def _gas_profile(bottom=0.2):
    rows=[]
    for d in (0.0,20.0,40.0,60.0,80.0,100.0,120.0,140.0,160.0,180.0,200.0,220.0,240.0,260.0,280.0,300.0,320.0,340.0,360.0,380.0,400.0,420.0,440.0,460.0,480.0,500.0,520.0,540.0,560.0,580.0,600.0,620.0,640.0,660.0,680.0,700.0,720.0,740.0,760.0,780.0,800.0,820.0,840.0,860.0,880.0,900.0,920.0,940.0,960.0,980.0,1000.0,1020.0,1040.0,1060.0,1080.0,1100.0,1120.0,1140.0,1160.0,1180.0):
        for z,p,t in ((bottom,1000,290.0),(2.0,800,275.0),(5.0,500,255.0),(10.0,250,230.0),(18.0,100,215.0),(23.0,30,220.0)):
            rows.append({'direction_offset_deg':0.0,'distance_km':d,'altitude_agl_km':z,
                         'temperature_k':t,'pressure_hpa':p,'relative_humidity_pct':5.0,
                         'o2_mole_fraction':0.20946,'h2o_mole_fraction':0.004,'o3_mole_fraction':2e-7})
    return pd.DataFrame(rows)


def test_dynamic_rt_route_terminates_at_aerosol_top_not_cloud_top():
    cfg=ModelConfig()
    assert cfg.rt_model_top_km == 18.0
    assert cfg.rt_route_termination_top_km == 30.0
    assert cfg.dynamic_domain_max_km == 1180.0


def test_true_vertical_gap_is_fail_closed_in_public_gas_transmission():
    target=pd.DataFrame([{'direction_offset_deg':0.0,'distance_km':0.0,'voxel_center_km':0.25,
                          'geometric_illuminated_fraction':1.0}])
    out=integrate_gas_sun_to_targets(target,_gas_profile(bottom=1.0),0.0)
    assert out.loc[0,'gas_rt_domain_status'].startswith('TRUE_')
    assert out.loc[0,'gas_rt_failure_cause'] in {'TARGET_BELOW_GAS_PROFILE_BOTTOM','NO_PROFILE_VERTICAL_BRACKET'}
    assert np.isnan(out.loc[0,'gas_transmission_650nm'])


def test_full_spectral_rt_requires_path_integrity_not_just_finite_numbers():
    angle=-2.0
    spectral=pd.DataFrame({
        'geometric_illuminated_fraction':[1.0,1.0],
        'distance_km':[0.0,20.0],
        'full_spectral_transmission_600nm':[0.4,0.4],
        'full_spectral_transmission_650nm':[0.4,0.4],
        'full_spectral_transmission_700nm':[0.4,0.4],
        'full_spectral_transmission_750nm':[0.4,0.4],
        'native_cams_aerosol_tau_650nm':[0.1,0.1],
        'native_cams_aerosol_path_completeness':[1.0,0.5],
        'native_cams_aerosol_domain_complete':[True,True],
        'gas_rt_domain_status':['MODEL_TOP_TERMINATED','MODEL_TOP_TERMINATED'],
        'gas_path_completeness':[1.0,1.0],
        'aerosol_path_quality':['',''],
    })
    gp=pd.DataFrame({
        'direction_offset_deg':[0.0,0.0], 'distance_km':[0.0,0.0],
        'altitude_agl_km':[0.2,23.0], 'temperature_k':[290.0,220.0],
        'pressure_hpa':[1000.0,30.0], 'relative_humidity_pct':[60.0,5.0],
        'h2o_mole_fraction':[0.01,1e-5], 'o2_mole_fraction':[0.20946,0.20946],
        'o3_mole_fraction':[2e-7,2e-6],
    })
    details={angle:{
        'cams_native_aerosol_snapshot':pd.DataFrame({'cams_aerext532_m1_1000hPa':[1e-5],'cams_aerext532_m1_30hPa':[1e-8]}),
        'cams_native_aerosol_metadata':{},
        'gas_profile':gp,
        'hitran_backend_status':{'runtime_spectroscopy_ready':True,'database_exists':True,'coefficient_table_exists':True},
        'spectral_voxels':spectral,
    }}
    base=pd.DataFrame([{'solar_altitude_deg':angle,'data_completeness':1.0}])
    out=_build_physics_data_completeness(details,[(angle,pd.Timestamp('2026-09-04 18:20'),0.0)],base)
    aero=out[out.layer=='SPECTRAL_AEROSOL_PATH'].iloc[0]
    full=out[out.layer=='FULL_SPECTRAL_RT'].iloc[0]
    assert aero.status=='PARTIAL' and abs(aero.completeness-0.5)<1e-9
    assert full.status=='PARTIAL' and abs(full.completeness-0.5)<1e-9


def test_cams_spectral_retry_is_bounded_and_role_specific():
    text=(Path(__file__).resolve().parents[1]/'firecloud'/'providers'/'cams_native.py').read_text(encoding='utf-8')
    assert 'FIRECLOUD_CAMS_SPECTRAL_RETRY_COUNT' in text
    assert 'FIRECLOUD_CAMS_SPECTRAL_RETRY_DEADLINE_SECONDS' in text
    assert 'spectral_role="SPECTRAL_COLUMN_AOD"' in text
    assert 'retry_attempted' in text
