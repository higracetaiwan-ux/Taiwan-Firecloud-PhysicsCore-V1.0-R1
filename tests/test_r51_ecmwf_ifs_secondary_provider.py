import pandas as pd
from firecloud.providers.ecmwf_ifs_native import build_secondary_optics_from_profiles, resolve_configured_grib_path


def test_ifs_native_condensate_becomes_secondary_optics(monkeypatch, tmp_path):
    df=pd.DataFrame([{
        'point_id':'p','distance_km':20.0,'direction_offset_deg':0.0,'model_level':100,
        'pressure_hpa':700.0,'altitude_agl_km':4.5,'layer_bottom_agl_km':4.0,'layer_top_agl_km':5.0,
        'temperature_k':275.0,'specific_humidity_kgkg':0.005,'clwc_kgkg':2e-4,'ciwc_kgkg':1e-5,
        'cloud_fraction':0.8,'crwc_kgkg':0.0,'cswc_kgkg':0.0,
    }])
    out=build_secondary_optics_from_profiles(df)
    assert len(out)==1
    r=out.iloc[0]
    assert r.source_kind=='FORECAST_MODEL_NATIVE_OPTICS'
    assert r.optical_evidence=='FULL'
    assert r.cot>0
    assert 'IFS_NATIVE_CLWC_CIWC' in r.provenance


def test_ifs_zero_condensate_not_promoted_to_cot():
    df=pd.DataFrame([{
        'point_id':'p','distance_km':20.0,'direction_offset_deg':0.0,'model_level':100,
        'pressure_hpa':700.0,'altitude_agl_km':4.5,'layer_bottom_agl_km':4.0,'layer_top_agl_km':5.0,
        'temperature_k':275.0,'specific_humidity_kgkg':0.005,'clwc_kgkg':0.0,'ciwc_kgkg':0.0,
        'cloud_fraction':0.8,
    }])
    assert build_secondary_optics_from_profiles(df).empty


def test_configured_grib_path(monkeypatch,tmp_path):
    f=tmp_path/'ifs.grib2'; f.write_bytes(b'GRIB')
    monkeypatch.setenv('FIRECLOUD_ECMWF_IFS_GRIB_PATH',str(f))
    assert resolve_configured_grib_path(None)==f
