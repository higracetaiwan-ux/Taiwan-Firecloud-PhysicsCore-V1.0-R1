from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_bootstrap_supports_single_gas_download_contract():
    text = (ROOT / "bootstrap_hitran_local_db.py").read_text(encoding="utf-8")
    assert '"--download-gas"' in text
    assert 'choices=tuple(TABLES.keys())' in text
    assert 'CACHE_HIT {gas}' in text
    assert 'DOWNLOADING {gas}' in text
    assert 'READY {gas}' in text


def test_streamlit_hard_timeout_kills_process_group():
    text = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'start_new_session=(os.name == "posix")' in text
    assert 'os.killpg(proc.pid, signal.SIGTERM)' in text
    assert 'HARD_TIMEOUT_TREE_KILLED' in text
    assert 'FIRECLOUD_HITRAN_GAS_TIMEOUT_SECONDS' in text
    assert 'FIRECLOUD_HITRAN_LUT_TIMEOUT_SECONDS' in text


def test_lut_manifest_version_matches_release():
    text = (ROOT / "build_hitran_band_coefficients.py").read_text(encoding="utf-8")
    assert '"version":"PhysicsCore-V1.0-R4.8.2"' in text
