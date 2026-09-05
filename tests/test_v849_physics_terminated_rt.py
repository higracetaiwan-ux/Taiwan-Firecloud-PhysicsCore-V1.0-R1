import numpy as np
import pandas as pd
from firecloud.config import ModelConfig
from firecloud.gas_rt import integrate_gas_sun_to_targets
from firecloud.model import _build_physics_data_completeness


def _profile(distances=(0.0,20.0,40.0,60.0,80.0,100.0,120.0,140.0,160.0,180.0,200.0,220.0,240.0,260.0,280.0,300.0,320.0,340.0,360.0,380.0,400.0,420.0,440.0,460.0,480.0,500.0,520.0)):
    rows=[]
    for d in distances:
        for z,p,t in ((0.2,1000,290.0),(2.0,800,275.0),(5.0,500,255.0),(10.0,250,230.0),(18.0,100,215.0)):
            rows.append({'direction_offset_deg':0.0,'distance_km':d,'altitude_agl_km':z,
                         'temperature_k':t,'pressure_hpa':p,'o2_mole_fraction':0.20946,
                         'h2o_mole_fraction':0.004,'o3_mole_fraction':2e-7})
    return pd.DataFrame(rows)


def test_dynamic_domain_is_geometry_derived_not_840_constant():
    cfg=ModelConfig()
    assert cfg.dynamic_domain_max_km == 1180.0
    # Changing the deepest diagnostic angle changes the derived route domain.
    shallower=ModelConfig(solar_angles_deg=(0.0,-0.5,-1.0,-2.0,-3.0,-4.0))
    assert shallower.dynamic_domain_max_km < cfg.dynamic_domain_max_km
    assert shallower.dynamic_domain_max_km > 440.0


def test_earth_shadow_is_not_reported_as_missing_gas_path():
    targets=pd.DataFrame([{'direction_offset_deg':0.0,'distance_km':0.0,'voxel_center_km':1.0,
                           'geometric_illuminated_fraction':0.0}])
    out=integrate_gas_sun_to_targets(targets,_profile(),-6.0)
    assert out.loc[0,'gas_rt_quality']=='NOT_APPLICABLE_EARTH_SHADOW'
    assert out.loc[0,'gas_rt_failure_cause']=='EARTH_SHADOW_NO_DIRECT_SOLAR_RAY'
    assert out.loc[0,'gas_rt_domain_status']=='NOT_APPLICABLE'
    assert out.loc[0,'gas_path_completeness']==1.0


def test_target_above_real_profile_top_is_true_vertical_missing():
    targets=pd.DataFrame([{'direction_offset_deg':0.0,'distance_km':0.0,'voxel_center_km':19.0,
                           'geometric_illuminated_fraction':1.0}])
    out=integrate_gas_sun_to_targets(targets,_profile(),0.0)
    assert out.loc[0,'gas_rt_failure_cause']=='TARGET_ABOVE_GAS_PROFILE_TOP'
    assert out.loc[0,'gas_rt_domain_status']=='TRUE_VERTICAL_DATA_MISSING'
    assert np.isnan(out.loc[0,'gas_transmission_650nm'])
