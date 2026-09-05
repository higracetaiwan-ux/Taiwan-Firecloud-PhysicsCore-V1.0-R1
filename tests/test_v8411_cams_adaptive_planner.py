from datetime import datetime, timezone
import pandas as pd
from firecloud.providers import cams_native


def _pts():
    pts=[]
    for d in range(0, 1001, 100):
        for off in (-5.0,0.0,5.0):
            pts.append({'point_id':f'{off}:{d}','distance_km':float(d),'direction_offset_deg':off,'lat':24.0,'lon':120.0-d/100.0})
    return pts


def test_midpoint_split_preserves_every_point_once():
    pts=_pts()
    parts=cams_native._split_points_by_distance_midpoint(pts)
    ids=[p['point_id'] for part in parts for p in part]
    assert len(parts)==2
    assert len(ids)==len(set(ids))==len(pts)


def test_adaptive_role_fetch_splits_only_failed_segment(monkeypatch):
    calls=[]
    def fake(role, points, valid_time, cache_dir, deadline_seconds, heartbeat_callback=None):
        d0=min(p['distance_km'] for p in points); d1=max(p['distance_km'] for p in points)
        calls.append((role,d0,d1,len(points)))
        # full route fails, children succeed
        if d0==0 and d1==1000:
            return {'role':role,'status':'FAILED','df':pd.DataFrame(),'meta':{'request_audit':{'status':'FAILED'}},'inventory':[],'error':'synthetic','elapsed_seconds':0.01}
        df=pd.DataFrame([{'point_id':p['point_id'],'distance_km':p['distance_km'],'direction_offset_deg':p['direction_offset_deg'],'x':1} for p in points])
        return {'role':role,'status':'OK','df':df,'meta':{'request_audit':{'status':'OK'}},'inventory':[],'error':'','elapsed_seconds':0.01}
    monkeypatch.setattr(cams_native,'_run_cams_role_isolated',fake)
    df,aud,inv,stats=cams_native._fetch_cams_role_adaptive(_pts(),datetime(2026,9,4,10,tzinfo=timezone.utc),'SPECTRAL_COLUMN_AOD',deadline_seconds=1)
    assert len(calls)==3
    assert stats['adaptive_splits']==1
    assert len(df)==len(_pts())
    assert len(aud)==3


def test_planner_best_case_uses_one_request_per_role(monkeypatch):
    calls=[]
    def fake(role, points, valid_time, cache_dir, deadline_seconds, heartbeat_callback=None):
        calls.append(role)
        df=pd.DataFrame([{'point_id':p['point_id'],'distance_km':p['distance_km'],'direction_offset_deg':p['direction_offset_deg'], role:1} for p in points])
        return {'role':role,'status':'OK','df':df,'meta':{'request_audit':{'status':'OK'}},'inventory':[],'error':'','elapsed_seconds':0.01}
    monkeypatch.setattr(cams_native,'_run_cams_role_isolated',fake)
    monkeypatch.setenv('FIRECLOUD_CAMS_INTER_ROLE_GAP_SECONDS','0')
    df,meta=cams_native.fetch_route_native_aerosol_bundle_timed(_pts(),datetime(2026,9,4,10,tzinfo=timezone.utc),deadline_seconds=1)
    assert len(calls)==3
    assert set(calls)=={'O3_PRESSURE_LEVEL','SPECTRAL_COLUMN_AOD','NATIVE_AEROSOL_532NM_PRESSURE_LEVEL'}
    assert meta['cams_request_planner']=='WHOLE_ROUTE_FIRST_ADAPTIVE_SUBTILING'
    assert meta['cams_tile_count']==3
    assert len(df)==len(_pts())
