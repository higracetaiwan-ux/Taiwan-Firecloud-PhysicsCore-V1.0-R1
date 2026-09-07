import pandas as pd
from firecloud.contracts import CanvasCandidate, CanvasDomain, CloudFractionState, CloudLayer, CloudScene, EvidenceState, GeometryConfidence, SIX_BAND_WAVELENGTHS_NM
from firecloud.tier2_scattering_readiness import build_tier2_scattering_readiness, summarize_tier2_scattering_readiness


def canvas():
    return CanvasCandidate(canvas_id='c',cloud_layer_id='l',latitude=24,longitude=120,cloud_base_altitude_km=5,distance_km=20,azimuth_deg=270,operational_domain=CanvasDomain.PRIMARY_CANVAS_0_40,geometry_confidence=GeometryConfidence.HIGH)

def scene(phase='ICE',reff=25.0):
    return CloudScene(valid_time=None,layers=(CloudLayer(layer_id='l',direction_offset_deg=0,distance_km=20,z_base_km=5,z_top_km=6,cloud_fraction_state=CloudFractionState.CLOUD_OCCUPIED,cloud_fraction=.8,phase=phase,effective_radius_um=reff,optical_evidence=EvidenceState.FULL),))

def illum():
    r={'canvas_id':'c'}
    for wl in SIX_BAND_WAVELENGTHS_NM: r[f'relative_base_illumination_{wl}nm']=0.5
    return pd.DataFrame([r])

def ev(truth='EXACT_PRIMARY_NATIVE',sem='EXACT_VALUE',lo=2,hi=2):
    return pd.DataFrame([{'canvas_id':'c','target_optical_truth_state':truth,'target_cot_semantics':sem,'target_response_eligibility':'EXACT_RESPONSE_ELIGIBLE','target_cot_lower_bound':lo,'target_cot_upper_bound':hi}])

def test_exact_inputs_ready_but_not_tier2_response_without_lut_solver():
    d=build_tier2_scattering_readiness(scene=scene(),canvases=[canvas()],target_optical_evidence=ev(),canvas_radiance=pd.DataFrame(),cloud_base_illumination=illum(),solar_altitude_deg=-2)
    r=d.iloc[0]
    assert r.tier2_input_contract_state == 'INPUTS_READY_AWAITING_LUT_SOLVER'
    assert r.tier2_response_eligibility == 'AWAITING_LUT_SOLVER'
    assert r.scattering_lut_state == 'TIER2_SCATTERING_LUT_NOT_FROZEN'
    assert r.scattering_solver_state == 'TIER2_SCATTERING_SOLVER_NOT_ENABLED'
    assert r.tier2_input_completeness_fraction == 1.0
    assert r.cf_or_rh_used_to_infer_cot == False

def test_bounded_cot_is_valid_input_but_not_exact():
    d=build_tier2_scattering_readiness(scene=scene(),canvases=[canvas()],target_optical_evidence=ev('BOUNDED_NATIVE_BRACKET','BOUNDED_INTERVAL',1,3),canvas_radiance=pd.DataFrame(),cloud_base_illumination=illum(),solar_altitude_deg=-2)
    r=d.iloc[0]
    assert r.cot_readiness_state == 'COT_BOUNDED_READY'
    assert r.tier2_input_contract_state == 'INPUTS_READY_AWAITING_LUT_SOLVER'
    assert r.cot_lower_bound == 1 and r.cot_upper_bound == 3

def test_conflict_blocks_before_phase_reff_can_rescue_it():
    d=build_tier2_scattering_readiness(scene=scene(),canvases=[canvas()],target_optical_evidence=ev('DIRECT_EVIDENCE_CONFLICT','UNRESOLVED_CONFLICT',None,None),canvas_radiance=pd.DataFrame(),cloud_base_illumination=illum(),solar_altitude_deg=-2)
    r=d.iloc[0]
    assert r.tier2_input_contract_state == 'BLOCKED_COT_CONFLICT'
    assert r.blocking_reason == 'TARGET_COT_CONFLICT_UNRESOLVED'
    assert r.tier2_response_eligibility == 'NOT_ELIGIBLE'

def test_missing_reff_is_independent_blocker():
    d=build_tier2_scattering_readiness(scene=scene(reff=None),canvases=[canvas()],target_optical_evidence=ev(),canvas_radiance=pd.DataFrame(),cloud_base_illumination=illum(),solar_altitude_deg=-2)
    assert d.iloc[0].tier2_input_contract_state == 'BLOCKED_REFF_MISSING'

def test_summary_reports_conflict_and_ready_counts():
    a=build_tier2_scattering_readiness(scene=scene(),canvases=[canvas()],target_optical_evidence=ev(),canvas_radiance=pd.DataFrame(),cloud_base_illumination=illum(),solar_altitude_deg=-2)
    b=a.copy(); b['canvas_id']='d'; b['tier2_input_contract_state']='BLOCKED_COT_CONFLICT'; b['tier2_response_eligibility']='NOT_ELIGIBLE'
    s=summarize_tier2_scattering_readiness(pd.concat([a,b],ignore_index=True)).iloc[0]
    assert s.inputs_ready_count == 1
    assert s.blocked_cot_conflict_count == 1
    assert s.closure_state == 'COT_CONFLICT_UNRESOLVED'
