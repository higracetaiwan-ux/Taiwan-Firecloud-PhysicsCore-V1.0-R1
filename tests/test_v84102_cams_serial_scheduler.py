from datetime import datetime, timezone
import pandas as pd

from firecloud.providers import cams_native


def _ok(role, point_id='p0'):
    base = {'point_id':[point_id], 'distance_km':[0.0], 'direction_offset_deg':[0.0], 'lat':[24.25], 'lon':[120.5]}
    if role == 'O3_PRESSURE_LEVEL':
        base['cams_ozone_kgkg_100']=[1e-6]
        extra={'levels':1,'rows':1}
    elif role == 'SPECTRAL_COLUMN_AOD':
        base.update({'aod550':[0.1],'aod645':[0.08],'aod670':[0.075],'aod800':[0.05]})
        extra={'columns':['aod550','aod645','aod670','aod800'],'rows':1}
    else:
        base['cams_aerext532_m1_100']=[1e-5]
        extra={'levels':1,'rows':1}
    return {'role':role,'status':'OK','df':pd.DataFrame(base),'meta':{},'inventory':[],
            'error':'','elapsed_seconds':0.1, **extra}


def test_serial_scheduler_retries_only_failed_role(monkeypatch):
    calls=[]
    spectral_attempt={'n':0}
    def fake_run(role, points, valid_time, cache_dir=None, deadline_seconds=90.0, heartbeat_callback=None):
        calls.append(role)
        if role == 'SPECTRAL_COLUMN_AOD':
            spectral_attempt['n'] += 1
            if spectral_attempt['n'] == 1:
                return {'role':role,'status':'FAILED','df':pd.DataFrame(),'meta':{},'inventory':[],
                        'error':'RuntimeError: transient provider failure','elapsed_seconds':0.1}
        return _ok(role)
    monkeypatch.setattr(cams_native, '_run_cams_role_isolated', fake_run)
    monkeypatch.setattr(cams_native.time, 'sleep', lambda *_: None)
    monkeypatch.setenv('FIRECLOUD_CAMS_ROLE_RETRY_COUNT','1')
    pts=[{'point_id':'p0','distance_km':0.0,'direction_offset_deg':0.0,'lat':24.25,'lon':120.5}]
    df,meta=cams_native._fetch_route_native_aerosol_bundle_single_tile(
        pts, datetime(2026,9,4,10,0,tzinfo=timezone.utc), deadline_seconds=1.0)
    assert calls == ['O3_PRESSURE_LEVEL','SPECTRAL_COLUMN_AOD','SPECTRAL_COLUMN_AOD','NATIVE_AEROSOL_532NM_PRESSURE_LEVEL']
    assert meta['cams_scheduler_mode'] == 'SERIAL_EXTERNAL_SUBPROCESS_FILE_IPC_ROLES'
    assert meta['native_ozone_status'] == 'OK'
    assert meta['native_aerosol_status'] == 'OK'
    assert meta['cams_spectral_aod_status'] == 'OK'
    spectral_audit=[r for r in meta['cams_request_audit'] if r['request_role']=='SPECTRAL_COLUMN_AOD'][0]
    assert spectral_audit['retry_attempted'] is True
    assert spectral_audit['retry_count'] == 1
    assert df['point_id'].nunique() == 1


def test_timeout_is_not_immediately_duplicated(monkeypatch):
    calls=[]
    def fake_run(role, points, valid_time, cache_dir=None, deadline_seconds=90.0, heartbeat_callback=None):
        calls.append(role)
        if role == 'O3_PRESSURE_LEVEL':
            return {'role':role,'status':'TIMEOUT_DEFERRED','df':pd.DataFrame(),'meta':{},'inventory':[],
                    'error':'CAMS_ADS_WALLCLOCK_DEADLINE_EXCEEDED_90S','elapsed_seconds':90.0}
        return _ok(role)
    monkeypatch.setattr(cams_native, '_run_cams_role_isolated', fake_run)
    monkeypatch.setattr(cams_native.time, 'sleep', lambda *_: None)
    monkeypatch.setenv('FIRECLOUD_CAMS_ROLE_RETRY_COUNT','2')
    pts=[{'point_id':'p0','distance_km':0.0,'direction_offset_deg':0.0,'lat':24.25,'lon':120.5}]
    _,meta=cams_native._fetch_route_native_aerosol_bundle_single_tile(
        pts, datetime(2026,9,4,10,0,tzinfo=timezone.utc), deadline_seconds=1.0)
    assert calls.count('O3_PRESSURE_LEVEL') == 1
    assert calls == ['O3_PRESSURE_LEVEL','SPECTRAL_COLUMN_AOD','NATIVE_AEROSOL_532NM_PRESSURE_LEVEL']
    o3=[r for r in meta['cams_request_audit'] if r['request_role']=='O3_PRESSURE_LEVEL'][0]
    assert o3['timeout'] is True
    assert o3['retry_attempted'] is False
