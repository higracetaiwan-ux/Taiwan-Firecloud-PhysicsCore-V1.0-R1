import math
import pandas as pd
import numpy as np

from firecloud.providers.gfs_native import build_nomads_request, GFS_NATIVE_SHORTNAMES
from firecloud.precipitation import build_precipitation_path_evidence, build_viewing_precipitation_evidence
from firecloud.viewing_spectral import build_viewing_spectral_extinction

class C:
    canvas_id='canvas::dir+0.0_d5.0_L1'
    cloud_layer_id='dir+0.0_d5.0_L1'
    distance_km=5.0
    cloud_base_altitude_km=2.0


def _route_native():
    rows=[]
    for d in (0.0,5.0,10.0):
        r={'point_id':f'+0.0_{int(d):04d}','distance_km':d,'direction_offset_deg':0.0,
           'precipitation':1.0}
        for p,z,t in [(1000,100,290),(900,1000,285),(800,2000,280)]:
            r[f'geopotential_height_{p}hPa']=z
            r[f'temperature_{p}hPa']=t
            r[f'rain_water_kgkg_{p}hPa']=2e-4 if p==900 else 0.0
            r[f'snow_water_kgkg_{p}hPa']=0.0
            r[f'graupel_kgkg_{p}hPa']=0.0
        rows.append(r)
    return pd.DataFrame(rows)


def test_gfs_r57_requests_native_hydrometeors():
    assert {'RWMR','SNMR','GRLE'}.issubset(GFS_NATIVE_SHORTNAMES)
    _,params=build_nomads_request(pd.Timestamp('2026-09-06T06:00Z').to_pydatetime(),12,(120,121,24,25),pressure_levels_hpa=(900,))
    for v in ('RWMR','SNMR','GRLE'):
        assert params[f'var_{v}']=='on'


def test_precipitation_tau_requires_native_volume_not_surface_rate():
    df=_route_native()
    ev=build_precipitation_path_evidence([C()],df,solar_altitude_deg=0.0)
    r=ev.iloc[0]
    assert r['status']=='PRECIPITATION_OPTICS_RESOLVED'
    assert r['reason']=='FORECAST_NATIVE_3D_RWMR_SNMR_GRLE_PATH_INTEGRATION'
    assert math.isfinite(float(r['tau_precip_650nm']))
    no_native=df[[c for c in df.columns if not any(x in c for x in ('rain_water_kgkg','snow_water_kgkg','graupel_kgkg'))]]
    ev2=build_precipitation_path_evidence([C()],no_native,solar_altitude_deg=0.0)
    assert ev2.iloc[0]['status']=='PRECIPITATION_VOLUME_UNRESOLVED'
    assert pd.isna(ev2.iloc[0].get('tau_precip_650nm',np.nan))


def test_viewing_precipitation_is_independent_observer_path():
    viewing=pd.DataFrame([{'time':'t','solar_altitude_deg':0.0,'canvas_id':'c','photographic_target_eligible':True,
                           'target_distance_km':10.0,'target_base_km':3.0,'target_top_km':4.0,'direction_offset_deg':0.0}])
    out=build_viewing_precipitation_evidence(viewing,_route_native())
    assert out.iloc[0]['view_precipitation_status']=='VIEW_PRECIPITATION_OPTICS_RESOLVED'
    assert math.isfinite(float(out.iloc[0]['view_tau_precip_650nm']))


def test_viewing_spectral_keeps_sun_path_separate_and_fail_closed():
    viewing=pd.DataFrame([{'time':'t','solar_altitude_deg':0.0,'canvas_id':'c','cloud_layer_id':'target','photographic_target_eligible':True,
                           'target_distance_km':10.0,'target_base_km':3.0,'target_top_km':4.0,'direction_offset_deg':0.0}])
    layers=pd.DataFrame([{'time':'t','solar_altitude_deg':0.0,'layer_id':'target','direction_offset_deg':0.0,'distance_km':10.0,'z_base_km':3.0,'z_top_km':4.0,'cloud_fraction':0.5,'cot':1.0,'evidence_consistency':'CONSISTENT'}])
    out=build_viewing_spectral_extinction(viewing,layers,pd.DataFrame(),pd.DataFrame(),pd.DataFrame(),pd.DataFrame())
    r=out.iloc[0]
    assert r['viewing_spectral_status']=='VIEW_PARTIAL_SIX_BAND_RT'
    assert 'GAS' in r['viewing_missing_components'] and 'AEROSOL' in r['viewing_missing_components'] and 'PRECIPITATION' in r['viewing_missing_components']
    assert 'SUN' not in r['note'] or 'NO_SUN_PATH_REUSE' in r['note']
