import pandas as pd
from firecloud.secondary_target_optics import validate_secondary_forecast_optical_evidence, arbitrate_primary_secondary

def _sec():
    return pd.DataFrame([dict(provider='ECMWF',model='IFS',source_kind='FORECAST_MODEL_NATIVE_OPTICS',valid_time='x',direction_offset_deg=0.0,distance_km=20.0,z_base_km=5.0,z_top_km=7.0,cot=4.0,effective_radius_um=12.0,phase='LIQUID',optical_evidence='FULL',provenance='IFS_NATIVE_CLWC_CIWC',status='OK')])

def test_secondary_validation_requires_forecast_native_optics():
    v=validate_secondary_forecast_optical_evidence(_sec())
    assert bool(v.iloc[0].secondary_exact_eligible)
    x=_sec(); x.loc[0,'source_kind']='SATELLITE_OBSERVATION'
    v=validate_secondary_forecast_optical_evidence(x)
    assert not bool(v.iloc[0].secondary_exact_eligible)

def test_primary_direct_conflict_is_not_erased_by_secondary():
    p=pd.DataFrame([dict(canvas_id='c1',resolver_state='CF_CLOUD_CONDENSATE_ZERO_UNRESOLVED',target_optics_ready=False,target_optics_bounded=False,target_cot_nominal=None,target_cot_lower_bound=None,target_cot_upper_bound=None,target_effective_radius_um=None,evidence_source='DIRECT_GEOMETRY_OPTICS_CONFLICT',bound_level=0,note='')])
    s=pd.DataFrame([dict(canvas_id='c1',secondary_provider='ECMWF',secondary_model='IFS',secondary_cot=4.0,secondary_effective_radius_um=12.0,secondary_phase='LIQUID',secondary_provenance='IFS_NATIVE_CLWC_CIWC',secondary_status='MATCHED_EXACT_FORECAST_NATIVE_OPTICS')])
    o=arbitrate_primary_secondary(p,s)
    assert not bool(o.iloc[0].target_optics_ready)
    assert o.iloc[0].resolver_state=='MULTISOURCE_DIRECT_CONFLICT_UNRESOLVED'

def test_secondary_can_promote_when_primary_missing_without_direct_conflict():
    p=pd.DataFrame([dict(canvas_id='c1',resolver_state='TARGET_OPTICS_MISSING',target_optics_ready=False,target_optics_bounded=False,target_cot_nominal=None,target_cot_lower_bound=None,target_cot_upper_bound=None,target_effective_radius_um=None,evidence_source='NONE',bound_level=0,note='')])
    s=pd.DataFrame([dict(canvas_id='c1',secondary_provider='ECMWF',secondary_model='IFS',secondary_cot=4.0,secondary_effective_radius_um=12.0,secondary_phase='LIQUID',secondary_provenance='IFS_NATIVE_CLWC_CIWC',secondary_status='MATCHED_EXACT_FORECAST_NATIVE_OPTICS')])
    o=arbitrate_primary_secondary(p,s)
    assert bool(o.iloc[0].target_optics_ready)
    assert o.iloc[0].resolver_state=='SECONDARY_FORECAST_NATIVE_OPTICS_EXACT'
    assert float(o.iloc[0].target_cot_nominal)==4.0

def test_disagreement_is_not_averaged():
    p=pd.DataFrame([dict(canvas_id='c1',resolver_state='DIRECT_NATIVE_CONDENSATE_COT',target_optics_ready=True,target_optics_bounded=False,target_cot_nominal=1.0,target_cot_lower_bound=1.0,target_cot_upper_bound=1.0,target_effective_radius_um=10.0,evidence_source='PRIMARY',bound_level=3,note='')])
    s=pd.DataFrame([dict(canvas_id='c1',secondary_provider='ECMWF',secondary_model='IFS',secondary_cot=5.0,secondary_effective_radius_um=12.0,secondary_phase='LIQUID',secondary_provenance='IFS_NATIVE_CLWC_CIWC',secondary_status='MATCHED_EXACT_FORECAST_NATIVE_OPTICS')])
    o=arbitrate_primary_secondary(p,s)
    assert not bool(o.iloc[0].target_optics_ready)
    assert o.iloc[0].resolver_state=='MULTISOURCE_COT_DISAGREEMENT_UNRESOLVED'
