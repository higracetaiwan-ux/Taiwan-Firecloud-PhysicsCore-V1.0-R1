from datetime import datetime, timezone
import pandas as pd
from firecloud.providers.gfs_native import resolve_run_and_lead, build_nomads_request, merge_native_into_snapshot


def test_resolve_cycle_and_lead_future():
    target=datetime(2026,9,3,10,tzinfo=timezone.utc)
    now=datetime(2026,9,3,8,tzinfo=timezone.utc)
    run,lead=resolve_run_and_lead(target,now)
    assert run.hour in (0,6,12,18)
    assert lead % 3 == 0 and lead >= 0


def test_nomads_request_has_native_fields_and_levels():
    run=datetime(2026,9,3,0,tzinfo=timezone.utc)
    url,p=build_nomads_request(run,12,(120,123,21,26),(1000,500,200))
    assert 'filter_gfs_0p25.pl' in url
    for v in ('CLWMR','ICMR','TCDC','TMP','RH','HGT'):
        assert p[f'var_{v}']=='on'
    assert p['lev_500_mb']=='on'


def test_merge_native_preserves_missing_policy():
    snap=pd.DataFrame([{'point_id':'a','cloud_cover_low':40.0}])
    native=pd.DataFrame([{'point_id':'a','cloud_liquid_water_500hPa':1e-5,'native_profile_source':'GFS'}])
    out=merge_native_into_snapshot(snap,native)
    assert out.loc[0,'cloud_liquid_water_500hPa']==1e-5
    assert 'cloud_ice_water_500hPa' not in out.columns
