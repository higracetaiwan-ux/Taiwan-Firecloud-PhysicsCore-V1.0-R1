from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_builder_reuses_full_spectrum_per_tp_state():
    text=(ROOT/'build_hitran_band_coefficients.py').read_text()
    assert 'full_nu_min=1e7/requested_max' in text
    assert 'full_nu_max=1e7/requested_min' in text
    assert 'total_states=2*len(temps)*len(pressures)' in text
    assert 'VOIGT_STATE {state_index}/{total_states}' in text
    # Only one HAPI Voigt call remains in the source loop, not one per band.
    assert text.count('absorptionCoefficient_Voigt(') == 1

def test_science_grid_unchanged():
    text=(ROOT/'build_hitran_band_coefficients.py').read_text()
    assert 'default="220,250,280,293"' in text
    assert 'default="100,300,500,700,900,1000"' in text
    assert 'default=0.02' in text
    assert 'band_half_width_nm":12.5' in text
    assert 'wavelengths=sorted({float(x)' in text

def test_o3_stays_serdyuchenko():
    text=(ROOT/'build_hitran_band_coefficients.py').read_text()
    assert 'Serdyuchenko' in text
    assert 'linear interpolation only within measured 193–293 K' in text

def test_timeout_has_safety_margin():
    text=(ROOT/'app.py').read_text()
    assert 'FIRECLOUD_HITRAN_LUT_TIMEOUT_SECONDS", 3600' in text

def test_builder_has_resumable_state_checkpoints():
    text=(ROOT/'build_hitran_band_coefficients.py').read_text()
    assert 'STATE_CACHE_DIRNAME' in text
    assert 'VOIGT_STATE_CACHE_HIT' in text
    assert '_write_state_checkpoint(' in text
    assert 'temporary.replace(path)' in text
