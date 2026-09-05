import inspect
from firecloud.providers import cams_native


def test_nonblocking_poll_watchdog_source_contract():
    src=inspect.getsource(cams_native._run_cams_role_isolated)
    assert 'rc = proc.poll()' in src
    assert 'time.monotonic()' in src
    assert 'next_heartbeat' in src
    assert 'heartbeat_callback(role,"RUNNING",elapsed)' in src
    assert 'remaining <= 0' in src
    assert 'TIMEOUT_DEFERRED' in src
    assert 'proc.wait(timeout=min(heartbeat_seconds, remaining))' not in src


def test_v8411_planner_uses_adaptive_progress_labels():
    src=inspect.getsource(cams_native.fetch_route_native_aerosol_bundle_timed)
    assert 'WHOLE_ROUTE_FIRST_ADAPTIVE_SUBTILING' in src
    assert 'label_prefix="ADAPTIVE:"' in src
