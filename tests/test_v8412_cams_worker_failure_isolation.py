from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_all_cams_roles_share_worker_preflight():
    src = (ROOT / "firecloud" / "providers" / "cams_native.py").read_text(encoding="utf-8")
    assert "CAMS_PREFLIGHT_CDSAPI_UNAVAILABLE" in src
    assert "CAMS_PREFLIGHT_ECCODES_UNAVAILABLE" in src
    assert "CAMS_PREFLIGHT_ADS_CREDENTIALS_MISSING" in src


def test_worker_exit_code_and_streams_are_preserved():
    src = (ROOT / "firecloud" / "providers" / "cams_native.py").read_text(encoding="utf-8")
    assert "observed_returncode" in src
    assert "stdout=" in src
    assert "stderr=" in src


def test_worker_level_failures_do_not_adaptively_split():
    src = (ROOT / "firecloud" / "providers" / "cams_native.py").read_text(encoding="utf-8")
    assert 'worker_error.startswith(("CAMS_PREFLIGHT_", "CAMS_EXTERNAL_WORKER_", "CAMS_WORKER_"))' in src


def test_o3_start_timeout_and_result_read_are_present():
    src = (ROOT / "firecloud" / "providers" / "cams_native.py").read_text(encoding="utf-8")
    assert "O3_WORKER_STARTING" in src
    assert "O3_ADS_TIMEOUT" in src
    assert "if res is None:" in src
