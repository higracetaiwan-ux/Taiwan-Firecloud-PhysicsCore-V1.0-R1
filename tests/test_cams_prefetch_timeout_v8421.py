from datetime import datetime, timezone
import pandas as pd
from firecloud.providers import cams_native as cams


def test_cams_bundle_propagates_isolated_timeout(monkeypatch):
    def fake_run(role, points, valid_time, cache_dir=None, deadline_seconds=90.0, heartbeat_callback=None):
        if heartbeat_callback:
            heartbeat_callback(role, 'RUNNING', 0.0)
            heartbeat_callback(role, 'RUNNING', min(5.0, deadline_seconds))
        return {
            'role': role,
            'status': 'TIMEOUT_DEFERRED',
            'df': pd.DataFrame(),
            'meta': {},
            'inventory': [],
            'error': f'CAMS_ADS_WALLCLOCK_DEADLINE_EXCEEDED_{deadline_seconds:.0f}S',
            'elapsed_seconds': float(deadline_seconds),
        }
    monkeypatch.setattr(cams, '_run_cams_role_isolated', fake_run)
    monkeypatch.setenv('FIRECLOUD_CAMS_GENERIC_RETRY_COUNT','0')
    monkeypatch.setenv('FIRECLOUD_CAMS_SPECTRAL_RETRY_COUNT','0')
    df, meta = cams.fetch_route_native_aerosol_bundle_timed(
        [{'point_id':'p0','lat':25.0,'lon':121.0}],
        datetime(2026,9,3,tzinfo=timezone.utc),
        deadline_seconds=0.25,
    )
    assert df.empty
    audits=meta.get('cams_request_audit', [])
    assert audits
    assert all(a.get('final_status') == 'TIMEOUT_DEFERRED' for a in audits)
