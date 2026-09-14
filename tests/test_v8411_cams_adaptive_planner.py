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
        rows=[]
        for p in points:
            row={'point_id':p['point_id'],'distance_km':p['distance_km'],'direction_offset_deg':p['direction_offset_deg']}
            if role == 'PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE':
                for level in cams_native.DEFAULT_PRESSURE_LEVELS_HPA:
                    row[f'cams_ozone_kgkg_{int(level)}hPa']=1e-6
                    row[f'cams_aerext532_m1_{int(level)}hPa']=1e-5
                    row[f'cams_geopotential_height_m_{int(level)}hPa']=1000.0
            elif role == 'O3_NEAR_SURFACE_MODEL_LEVEL_137':
                row['cams_ozone_ml137_kgkg']=1e-7
            elif role == 'AEROSOL_SCATTERING_COLUMN_PROPERTIES':
                row.update({'aod532':0.11,'aod550':0.10,'aod645':0.08,'aod670':0.075,'aod800':0.05,
                            'ssa550':0.97,'ssa645':0.97,'ssa670':0.97,'ssa800':0.97,
                            'asymmetry550':0.72,'asymmetry645':0.72,'asymmetry670':0.72,'asymmetry800':0.72})
            else:
                row[role]=1
            rows.append(row)
        df=pd.DataFrame(rows)
        return {'role':role,'status':'OK','df':df,'meta':{'request_audit':{'request_role':role,'status':'OK'}},'inventory':[],'error':'','elapsed_seconds':0.01}
    monkeypatch.setattr(cams_native,'_run_cams_role_isolated',fake)
    monkeypatch.setenv('FIRECLOUD_CAMS_INTER_ROLE_GAP_SECONDS','0')
    df,meta=cams_native.fetch_route_native_aerosol_bundle_timed(_pts(),datetime(2026,9,4,10,tzinfo=timezone.utc),deadline_seconds=1)
    assert len(calls)==3
    assert set(calls)=={'PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE','O3_NEAR_SURFACE_MODEL_LEVEL_137','AEROSOL_SCATTERING_COLUMN_PROPERTIES'}
    assert meta['cams_request_planner']=='WHOLE_ROUTE_FIRST_ADAPTIVE_SUBTILING'
    assert meta['cams_tile_count']==3
    assert len(df)==len(_pts())


def test_http_400_invalid_combination_does_not_spatially_subdivide(monkeypatch):
    calls=[]
    def fake(role, points, valid_time, cache_dir, deadline_seconds, heartbeat_callback=None):
        calls.append((role, len(points)))
        return {
            'role': role,
            'status': 'FAILED',
            'df': pd.DataFrame(),
            'meta': {'request_audit': {'status': 'FAILED'}},
            'inventory': [],
            'error': 'RuntimeError: HTTPError: 400 Client Error: Bad Request; invalid request; Request has not produced a valid combination of values',
            'elapsed_seconds': 0.01,
        }
    monkeypatch.setattr(cams_native, '_run_cams_role_isolated', fake)
    df,aud,inv,stats = cams_native._fetch_cams_role_adaptive(
        _pts(), datetime(2026,9,4,10,tzinfo=timezone.utc),
        'O3_PRESSURE_LEVEL', deadline_seconds=1
    )
    assert len(calls) == 1
    assert stats['adaptive_splits'] == 0
    assert stats['requests'] == 1
    assert df.empty
    assert len(aud) == 1
