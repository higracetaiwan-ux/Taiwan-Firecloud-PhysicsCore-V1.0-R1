import json
from datetime import datetime
from pathlib import Path

from firecloud.providers import openmeteo

class Resp:
    status_code=200
    headers={}
    def __init__(self,data): self._data=data
    def raise_for_status(self): pass
    def json(self): return self._data

class Session:
    calls=0
    def get(self,*a,**k):
        type(self).calls += 1
        params=k['params']; n=len(params['latitude'].split(','))
        data=[]
        for i in range(n):
            h={'time':['2026-09-03T18:00']}
            for v in openmeteo.HOURLY_VARS: h[v]=[1]
            data.append({'hourly':h,'elevation':0})
        return Resp(data)

def test_exact_coordinate_dedup_and_persistent_cache(monkeypatch,tmp_path):
    monkeypatch.setenv('FIRECLOUD_OPENMETEO_CACHE_DIR',str(tmp_path))
    monkeypatch.setenv('FIRECLOUD_OPENMETEO_CACHE_TTL_SECONDS','3600')
    monkeypatch.setattr(openmeteo.requests,'Session',Session)
    monkeypatch.setattr(openmeteo.time,'sleep',lambda *_:None)
    Session.calls=0
    pts=[
      {'point_id':'-5_000','lat':25.0,'lon':121.0,'distance_km':0,'direction_offset_deg':-5},
      {'point_id':'0_000','lat':25.0,'lon':121.0,'distance_km':0,'direction_offset_deg':0},
      {'point_id':'+5_000','lat':25.0,'lon':121.0,'distance_km':0,'direction_offset_deg':5},
    ]
    a=openmeteo.fetch_route_hourly(pts,datetime(2026,9,3),datetime(2026,9,3))
    assert Session.calls==1
    assert a['point_id'].nunique()==3
    assert a.attrs['unique_query_locations']==1
    assert a.attrs['api_request_audit'][0]['deduplicated_locations_saved']==2
    b=openmeteo.fetch_route_hourly(pts,datetime(2026,9,3),datetime(2026,9,3))
    assert Session.calls==1
    assert b.attrs['api_request_audit'][0]['cache_status']=='HIT'
