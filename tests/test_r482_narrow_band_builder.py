from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_builder_has_hapi_narrow_prefilter_and_safe_fallback():
    s=(ROOT/'build_hitran_band_coefficients.py').read_text()
    assert 'DestinationTableName=tmp' in s
    assert '("BETWEEN","nu",lo,hi)' in s
    assert 'NARROW_TABLE_FALLBACK' in s
    assert 'prefilter-wing-cm1' in s

def test_builder_keeps_direct_550_and_progress_eta():
    s=(ROOT/'build_hitran_band_coefficients.py').read_text()
    assert 'compute 550 nm directly from local spectroscopy; never interpolate 550 nm' in s
    assert 'FC_PROGRESS_DONE' in s
    assert 'eta_s=' in s

def test_app_surfaces_subprocess_state_progress():
    s=(ROOT/'app.py').read_text()
    assert 'FC_PROGRESS_DONE' in s
    assert 'PhysicsCore 550 nm 光譜建表中' in s
