import inspect
from firecloud.providers import cams_native


def test_watchdog_source_uses_nonblocking_poll_and_monotonic_deadline():
    src=inspect.getsource(cams_native._run_cams_role_isolated)
    assert "proc.poll()" in src
    assert "time.monotonic()" in src
    assert "proc.wait(timeout=min(heartbeat_seconds" not in src
    assert "TIMEOUT_DEFERRED" in src
    assert "firecloud.providers.cams_worker" in src


def test_external_worker_exit_without_result_has_explicit_failure_path():
    src=inspect.getsource(cams_native._run_cams_role_isolated)
    assert "EXTERNAL_WORKER_EXITED_WITHOUT_RESULT" in src
