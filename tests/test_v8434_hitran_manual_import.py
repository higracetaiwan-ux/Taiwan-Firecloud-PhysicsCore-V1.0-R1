from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_version_and_manual_import_bridge_present():
    init = (ROOT / "firecloud" / "__init__.py").read_text()
    assert '8.4.16.7-PhysicsCore' in init
    boot = (ROOT / "bootstrap_hitran_local_db.py").read_text()
    assert '--import-par-gas' in boot
    assert 'MANUAL_HITRAN_PAR' in boot
    assert 'wrong_molecule' in boot
    app = (ROOT / "app.py").read_text()
    assert '匯入 HITRAN line-list 氣體' in app
    assert '建立 360-state LUT' in app

def test_manual_import_keeps_original_science_grid():
    build = (ROOT / "build_hitran_band_coefficients.py").read_text()
    assert "220,250,280,293" in build
    assert "100,300,500,700,900,1000" in build
    assert 'default="600,650,700,750"' in build
    assert '"version":"V8.4.16.3"' in build
