import pandas as pd
from firecloud.gas_rt import active_gas_wavelengths, SIX_BAND_GAS_WAVELENGTHS_NM, EXTENDED_GAS_WAVELENGTHS_NM
from firecloud.hitran_runtime import validate_runtime_lut_bytes

T=(220.0,250.0,280.0,293.0); P=(100.0,300.0,500.0,700.0,900.0,1000.0)
def make(wls):
    rows=[]
    for g in ('H2O','O2','O3'):
        for wl in wls:
            for t in T:
                for p in P:
                    rows.append(dict(gas=g,wavelength_nm=wl,temperature_k=t,pressure_hpa=p,sigma_cm2_molecule=1e-24,spectroscopy_source='SERDYUCHENKO_GORSHELEV' if g=='O3' else 'HITRAN'))
    return pd.DataFrame(rows)

def test_active_gas_wavelengths_six_band_only_when_complete():
    assert active_gas_wavelengths(make((550,575,600,650,700,750))) == SIX_BAND_GAS_WAVELENGTHS_NM
    assert active_gas_wavelengths(make((575,600,650,700,750))) == EXTENDED_GAS_WAVELENGTHS_NM

def test_runtime_validator_accepts_complete_six_band_grid():
    raw=make((550,575,600,650,700,750)).to_csv(index=False).encode()
    a=validate_runtime_lut_bytes(raw)
    assert a['ok'], a['errors']
    assert a['active_wavelengths_nm']==[550.0,575.0,600.0,650.0,700.0,750.0]
