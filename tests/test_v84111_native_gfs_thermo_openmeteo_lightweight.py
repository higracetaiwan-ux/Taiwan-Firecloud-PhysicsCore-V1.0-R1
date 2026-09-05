from datetime import datetime
import pandas as pd
from firecloud.providers import openmeteo
from firecloud.providers.gfs_native import merge_native_into_snapshot, NATIVE_PROVIDER_NAME
from firecloud.model import _native_gfs_thermodynamic_ready

class Resp:
    status_code=200
    headers={}
    def __init__(self,data): self._data=data
    def raise_for_status(self): pass
    def json(self): return self._data

class SurfaceSession:
    calls=[]
    def get(self,*a,**k):
        params=k['params']; type(self).calls.append(params.copy())
        n=len(params['latitude'].split(','))
        data=[]
        for _ in range(n):
            h={'time':['2026-09-05T18:00']}
            for v in openmeteo.SURFACE_HOURLY_VARS: h[v]=[1]
            data.append({'hourly':h,'elevation':10})
        return Resp(data)

def test_surface_wrapper_does_not_request_pressure_profile(monkeypatch,tmp_path):
    monkeypatch.setenv('FIRECLOUD_OPENMETEO_CACHE_DIR',str(tmp_path))
    monkeypatch.setattr(openmeteo.requests,'Session',SurfaceSession)
    monkeypatch.setattr(openmeteo.time,'sleep',lambda *_:None)
    SurfaceSession.calls=[]
    pts=[{'point_id':f'0_{i:03d}','lat':24+i*.01,'lon':121+i*.01,'distance_km':i*20.,'direction_offset_deg':0.} for i in range(31)]
    out=openmeteo.fetch_route_surface_hourly(pts,datetime(2026,9,5),datetime(2026,9,5))
    assert len(SurfaceSession.calls)==2  # batch size 30
    requested=set(SurfaceSession.calls[0]['hourly'].split(','))
    assert requested==set(openmeteo.SURFACE_HOURLY_VARS)
    assert not any(v.startswith('temperature_') for v in requested)
    assert out.attrs['api_request_audit'][0]['request_profile']=='SURFACE_ONLY'
    assert out.attrs['api_request_audit'][0]['requested_variable_count']==len(openmeteo.SURFACE_HOURLY_VARS)


def test_native_gfs_backfills_canonical_pressure_contract_to_30hpa():
    snap=pd.DataFrame([{'point_id':'p','distance_km':0.,'direction_offset_deg':0.,'lat':24.,'lon':121.,'temperature_1000hPa':float('nan')}])
    row={'point_id':'p'}
    levels=(1000,925,850,700,600,500,400,300,250,200,150,100,70,50,30)
    for p in levels:
        row[f'temperature_k_{p}hPa']=280.-0.01*p
        row[f'relative_humidity_pct_{p}hPa']=40.
        row[f'geopotential_height_m_{p}hPa']=1000.+(1000-p)*20.
        row[f'cloud_fraction_{p}hPa']=0.25
    native=pd.DataFrame([row])
    out=merge_native_into_snapshot(snap,native)
    assert out.loc[0,'temperature_30hPa']==row['temperature_k_30hPa']
    assert out.loc[0,'relative_humidity_30hPa']==40.
    assert out.loc[0,'geopotential_height_30hPa']==row['geopotential_height_m_30hPa']
    assert out.loc[0,'cloud_cover_30hPa']==25.
    assert out.loc[0,'pressure_profile_primary_source']==NATIVE_PROVIDER_NAME
    assert _native_gfs_thermodynamic_ready(native) is True
