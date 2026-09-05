from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_bootstrap_really_covers_535nm_and_550_band():
    s=(ROOT/'bootstrap_hitran_local_db.py').read_text()
    assert 'NUMAX = 1e7 / 535.0' in s
    assert 'DIAGNOSTIC_BANDS_NM = (550.0, 575.0, 600.0, 650.0, 700.0, 750.0)' in s

def test_streamlit_builder_uses_six_band_535_tables():
    s=(ROOT/'app.py').read_text()
    assert 'H2O_535_765' in s and 'O2_535_765' in s
    assert '"--v1-six-band"' in s
    assert '432-state Runtime LUT' in s

def test_readiness_supports_432_state_six_band_grid():
    s=(ROOT/'firecloud/hitran_readiness.py').read_text()
    assert 'SIX_BAND_WAVELENGTHS_NM = (550, 575, 600, 650, 700, 750)' in s
    assert 'six_band_550nm_ready' in s
