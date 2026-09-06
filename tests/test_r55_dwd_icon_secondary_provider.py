from datetime import datetime, timezone
import pandas as pd

from firecloud.providers import dwd_icon_native as icon
from firecloud.secondary_target_optics import validate_secondary_forecast_optical_evidence


def test_icon_url_contract():
    run=datetime(2026,9,6,6,tzinfo=timezone.utc)
    u=icon._url(run,4,91,"QC")
    assert u.endswith('/06/qc/icon_global_icosahedral_model-level_2026090606_004_91_QC.grib2.bz2')


def test_icon_run_lead_resolution_with_latency():
    vt=datetime(2026,9,6,10,tzinfo=timezone.utc)
    now=datetime(2026,9,6,9,tzinfo=timezone.utc)
    run,lead=icon.resolve_run_and_lead(vt,now_utc=now)
    assert run == datetime(2026,9,6,6,tzinfo=timezone.utc)
    assert lead == 4


def test_icon_positive_condensate_profiles_become_exact_secondary_optics():
    prof=pd.DataFrame([{
        'point_id':'p1','distance_km':40.0,'direction_offset_deg':0.0,'lat':24.0,'lon':121.0,
        'model_level':91,'pressure_hpa':500.0,'temperature_k':260.0,
        'altitude_msl_km':6.0,'layer_bottom_msl_km':5.8,'layer_top_msl_km':6.2,
        'qc_kgkg':2e-5,'qi_kgkg':1e-5,
    }])
    out=icon.build_secondary_optics_from_profiles(prof,datetime(2026,9,6,10,tzinfo=timezone.utc))
    assert len(out)==1
    assert out.iloc[0]['provider']=='DWD'
    assert out.iloc[0]['model']=='ICON_GLOBAL'
    assert out.iloc[0]['source_kind']=='FORECAST_MODEL_NATIVE_OPTICS'
    assert out.iloc[0]['cot'] > 0
    v=validate_secondary_forecast_optical_evidence(out)
    assert bool(v.iloc[0]['secondary_exact_eligible']) is True


def test_icon_zero_condensate_is_not_promoted():
    prof=pd.DataFrame([{
        'point_id':'p1','distance_km':40.0,'direction_offset_deg':0.0,'lat':24.0,'lon':121.0,
        'model_level':91,'pressure_hpa':500.0,'temperature_k':260.0,
        'altitude_msl_km':6.0,'layer_bottom_msl_km':5.8,'layer_top_msl_km':6.2,
        'qc_kgkg':0.0,'qi_kgkg':0.0,
    }])
    out=icon.build_secondary_optics_from_profiles(prof)
    assert out.empty


def test_default_probe_levels_cover_cloud_troposphere():
    levels=icon._model_levels()
    assert levels[0] == 55
    assert levels[-1] == 108
    assert 91 in levels and 101 in levels
