from firecloud.contracts import (
    CloudLayer, CloudScene, CanvasCandidate, CloudFractionState,
    EvidenceState, GeometryConfidence, CanvasDomain,
)
from firecloud.target_canvas_optics import build_target_canvas_optical_evidence


def L(layer_id,d,cot=None,ev=EvidenceState.GEOMETRY_ONLY,cons='OPTICS_MISSING',zb=5.0,zt=7.0):
    return CloudLayer(
        layer_id=layer_id,direction_offset_deg=0.0,distance_km=float(d),
        z_base_km=zb,z_top_km=zt,cloud_fraction_state=CloudFractionState.PARTIAL_OCCUPANCY,
        cloud_fraction=0.3,cot=cot,optical_evidence=ev,evidence_consistency=cons,
        geometry_confidence=GeometryConfidence.MEDIUM,
    )


def C(layer_id,d):
    return CanvasCandidate(
        canvas_id='canvas::'+layer_id,cloud_layer_id=layer_id,latitude=0.0,longitude=0.0,
        cloud_base_altitude_km=5.0,distance_km=float(d),azimuth_deg=270.0,
        operational_domain=CanvasDomain.PRIMARY_CANVAS_0_40,
        geometry_confidence=GeometryConfidence.MEDIUM,
    )


def test_direct_native_cot_is_exact_ready():
    t=L('t',10,cot=3.0,ev=EvidenceState.FULL,cons='CONSISTENT_CLOUD')
    df=build_target_canvas_optical_evidence(CloudScene(None,(t,)),[C('t',10)],solar_altitude_deg=-2)
    r=df.iloc[0]
    assert r.resolver_state=='DIRECT_NATIVE_CONDENSATE_COT'
    assert bool(r.target_optics_ready)
    assert not bool(r.target_optics_bounded)
    assert float(r.target_cot_nominal)==3.0


def test_missing_target_optics_can_be_bounded_only_by_immediate_two_sided_native_support():
    left=L('l',5,cot=2.0,ev=EvidenceState.FULL,cons='CONSISTENT_CLOUD')
    target=L('t',10,cot=None,ev=EvidenceState.GEOMETRY_ONLY,cons='OPTICS_MISSING')
    right=L('r',15,cot=6.0,ev=EvidenceState.FULL,cons='CONSISTENT_CLOUD')
    df=build_target_canvas_optical_evidence(CloudScene(None,(left,target,right)),[C('t',10)],solar_altitude_deg=-2)
    r=df.iloc[0]
    assert r.resolver_state=='ADJACENT_NATIVE_COT_BRACKET_BOUNDED'
    assert not bool(r.target_optics_ready)
    assert bool(r.target_optics_bounded)
    assert float(r.target_cot_lower_bound)==2.0
    assert float(r.target_cot_nominal)==4.0
    assert float(r.target_cot_upper_bound)==6.0
    assert not bool(r.sampling_step_is_cloud_width)


def test_explicit_cf_condensate_zero_conflict_is_never_overwritten_by_neighbours():
    left=L('l',5,cot=2.0,ev=EvidenceState.FULL,cons='CONSISTENT_CLOUD')
    target=L('t',10,cot=None,ev=EvidenceState.GEOMETRY_ONLY,cons='CF_CLOUD_CONDENSATE_ZERO')
    right=L('r',15,cot=6.0,ev=EvidenceState.FULL,cons='CONSISTENT_CLOUD')
    df=build_target_canvas_optical_evidence(CloudScene(None,(left,target,right)),[C('t',10)],solar_altitude_deg=-2)
    r=df.iloc[0]
    assert r.resolver_state=='CF_CLOUD_CONDENSATE_ZERO_UNRESOLVED'
    assert not bool(r.target_optics_ready)
    assert not bool(r.target_optics_bounded)
    assert r.target_cot_nominal is None or str(r.target_cot_nominal)=='nan'
