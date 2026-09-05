from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_analysis_worker_is_external_and_reports_elapsed_exit_stderr():
    worker = (ROOT / "firecloud" / "analysis_worker.py").read_text(encoding="utf-8")
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "elapsed_seconds" in worker
    assert '"exit_code": 0' in worker
    assert '"exit_code": 1' in worker
    assert "worker_stderr_tail" in app
    assert "worker_last_heartbeat_at_utc" in app
    assert "_monitor_analysis_worker" in app


def test_cams_checkpoint_is_durable_and_result_status_is_recorded():
    src = (ROOT / "firecloud" / "providers" / "cams_native.py").read_text(encoding="utf-8")
    worker = (ROOT / "firecloud" / "providers" / "cams_worker.py").read_text(encoding="utf-8")
    assert '"stderr_tail"' in src
    assert '"stderr_path"' in src
    assert 'state_root / "cams_workers"' in src
    assert 'result_status not in {"TIMEOUT_DEFERRED"}' in src
    assert "exit_code=observed_returncode" in src
    assert 'return 0 if status in {"OK", "CACHE_HIT"} else 1' in worker


def test_app_reattaches_live_recovery_worker_instead_of_duplicating_it():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "_attach_existing" in app
    assert "Starting a second" in app
    assert "_old_alive" in app
