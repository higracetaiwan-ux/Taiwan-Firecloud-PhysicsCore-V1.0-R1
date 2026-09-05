from pathlib import Path
import numpy as np
import pandas as pd

from firecloud.hitran_runtime import validate_runtime_lut_bytes, EXPECTED_ROWS
from firecloud.hitran_readiness import REQUIRED_TEMPERATURES_K

ROOT=Path(__file__).resolve().parents[1]

def test_hybrid_grid_uses_measured_o3_temperature_ceiling():
    assert REQUIRED_TEMPERATURES_K == (220.0,250.0,280.0,293.0)
    assert EXPECTED_ROWS == 288

def test_builder_requires_h2o_o2_hitran_and_o3_xsc():
    text=(ROOT/'build_hitran_band_coefficients.py').read_text(encoding='utf-8')
    assert 'O3_SerdyuchenkoGorshelev_213_1100nm.dat' in text
    assert 'HITRAN_HAPI_VOIGT_LOCAL' in text
    assert 'SERDYUCHENKO_GORSHELEV_XSC' in text
    assert 'outside measured Serdyuchenko range 193–293 K' in text

def test_runtime_rejects_all_hitran_o3_and_accepts_hybrid():
    rows=[]
    for gas in ('H2O','O3','O2'):
        for wl in (600,650,700,750):
            for t in (220,250,280,293):
                for p in (100,300,500,700,900,1000):
                    rows.append({'wavelength_nm':wl,'gas':gas,'sigma_cm2_molecule':1e-25,
                                 'temperature_k':t,'pressure_hpa':p,
                                 'spectroscopy_source':'HITRAN_HAPI_VOIGT_LOCAL'})
    bad=pd.DataFrame(rows).to_csv(index=False).encode()
    assert validate_runtime_lut_bytes(bad)['ok'] is False
    df=pd.DataFrame(rows)
    df.loc[df.gas.eq('O3'),'spectroscopy_source']='SERDYUCHENKO_GORSHELEV_XSC_LINEAR_T_280-293K'
    good=df.to_csv(index=False).encode()
    assert validate_runtime_lut_bytes(good)['ok'] is True

def test_streamlit_ui_has_three_hybrid_inputs():
    app=(ROOT/'app.py').read_text(encoding='utf-8')
    assert 'HITRAN line-by-line + Voigt' in app
    assert 'Serdyuchenko–Gorshelev temperature-dependent XSC' in app
    assert '上傳 O₃ Serdyuchenko–Gorshelev XSC .dat' in app
