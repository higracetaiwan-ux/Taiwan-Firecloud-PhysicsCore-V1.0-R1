import pandas as pd
from firecloud.spectroscopy_readiness import build_six_band_spectroscopy_readiness
from firecloud.precipitation import build_precipitation_path_evidence

class C:
    canvas_id='c1'

def test_spectroscopy_readiness_reports_missing_550_for_legacy_runtime(tmp_path):
    rows=[]
    for g in ('H2O','O2','O3'):
        for wl in (575,600,650,700,750):
            for t in (220,250,280,293):
                for p in (100,300,500,700,900,1000):
                    rows.append(dict(gas=g,wavelength_nm=wl,temperature_k=t,pressure_hpa=p,sigma_cm2_molecule=1e-24,spectroscopy_source='HITRAN' if g!='O3' else 'SERDYUCHENKO_GORSHELEV'))
    path=tmp_path/'lut.csv'; pd.DataFrame(rows).to_csv(path,index=False)
    out=build_six_band_spectroscopy_readiness(path)
    assert set(out[out.wavelength_nm==550].state)=={'MISSING_BAND'}
    assert out[out.wavelength_nm==575].complete_tp_grid.all()

def test_surface_rain_does_not_resolve_precip_tau():
    out=build_precipitation_path_evidence([C()],pd.DataFrame([{'precipitation':3.0}]))
    assert out.iloc[0]['status']=='PRECIPITATION_VOLUME_UNRESOLVED'
    assert 'tau_precip_550nm' not in out.columns or pd.isna(out.iloc[0].get('tau_precip_550nm'))

def test_explicit_path_hydrometeor_optics_resolves_precip():
    rec={'canvas_id':'c1','geometry_resolved_3d':True}
    for wl in (550,575,600,650,700,750): rec[f'tau_precip_{wl}nm']=0.1
    out=build_precipitation_path_evidence([C()],pd.DataFrame([{'precipitation':1.0}]),path_optics=pd.DataFrame([rec]))
    assert out.iloc[0]['status']=='PRECIPITATION_OPTICS_RESOLVED'
    assert out.iloc[0]['optical_evidence']=='FULL'
