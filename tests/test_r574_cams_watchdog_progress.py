from pathlib import Path


def test_running_checkpoint_does_not_read_stderr_tail():
    src = Path('firecloud/providers/cams_native.py').read_text(encoding='utf-8')
    assert '"stderr_tail": "" if str(status).upper()' in src
    assert '{"RUNNING", "STARTED", "CAMS_WORKER_STARTING", "O3_WORKER_STARTING"}' in src


def test_os_level_timeout_wraps_external_cams_worker():
    src = Path('firecloud/providers/cams_native.py').read_text(encoding='utf-8')
    assert '_shutil.which("timeout")' in src
    assert '"--kill-after=2s"' in src
    assert 'observed_returncode == 124' in src
    assert '"status":"TIMEOUT_DEFERRED"' in src


def test_cams_ui_elapsed_is_scheduler_clock_driven():
    src = Path('firecloud/model.py').read_text(encoding='utf-8')
    assert '_cams_progress_started = {}' in src
    assert '_elapsed_ui = max(0.0, _now_mono - _started)' in src
    assert 'RUNNING {_elapsed_ui:.0f}s / 90s' in src
