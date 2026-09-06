import pandas as pd

from firecloud.canvas_optical_suitability import (
    TOO_THIN, OPTICALLY_SUITABLE, TOO_THICK, OPTICS_UNKNOWN,
    build_canvas_optical_suitability,
)
from firecloud.contracts import (
    CanvasCandidate, CanvasDomain, CloudFractionState, CloudLayer, CloudScene,
    EvidenceState, GeometryConfidence,
)


def _scene(cot=1.0):
    layer=CloudLayer(
        layer_id="L", direction_offset_deg=0.0, distance_km=20.0,
        z_base_km=5.0, z_top_km=6.5,
        cloud_fraction_state=CloudFractionState.CLOUD_OCCUPIED,
        cloud_fraction=0.8, phase="ICE", effective_radius_um=25.0, cot=cot,
        geometry_confidence=GeometryConfidence.HIGH, optical_evidence=EvidenceState.FULL,
    )
    return CloudScene(valid_time=None,layers=(layer,),geometry_completeness=1.0,optics_completeness=1.0)


def _canvas():
    return CanvasCandidate(canvas_id="C",cloud_layer_id="L",latitude=24,longitude=121,
        cloud_base_altitude_km=5.0,distance_km=20.0,azimuth_deg=270,
        operational_domain=CanvasDomain.PRIMARY_CANVAS_0_40,geometry_confidence=GeometryConfidence.HIGH)


def _ev(cot, ready=True, bounded=False, lo=None, hi=None):
    return pd.DataFrame([{"canvas_id":"C","target_optics_ready":ready,"target_optics_bounded":bounded,
        "target_cot_nominal":cot,"target_cot_lower_bound":lo if lo is not None else cot,
        "target_cot_upper_bound":hi if hi is not None else cot,"resolver_state":"DIRECT_NATIVE_CONDENSATE_COT",
        "evidence_source":"DIRECT_NATIVE_CONDENSATE_COT"}])


def test_r55_thin_suitable_thick_are_intrinsic_cot_regimes():
    assert build_canvas_optical_suitability(_scene(.1),[_canvas()],target_optical_evidence=_ev(.1)).iloc[0].canvas_optical_suitability_state == TOO_THIN
    assert build_canvas_optical_suitability(_scene(1.0),[_canvas()],target_optical_evidence=_ev(1.0)).iloc[0].canvas_optical_suitability_state == OPTICALLY_SUITABLE
    assert build_canvas_optical_suitability(_scene(5.0),[_canvas()],target_optical_evidence=_ev(5.0)).iloc[0].canvas_optical_suitability_state == TOO_THICK


def test_r55_missing_or_bounded_cot_never_forces_thin_or_thick():
    out=build_canvas_optical_suitability(_scene(1.0),[_canvas()],target_optical_evidence=_ev(1.0,ready=False,bounded=True,lo=.2,hi=2.0)).iloc[0]
    assert out.canvas_optical_suitability_state == OPTICS_UNKNOWN
    assert pd.isna(out.target_cot)
    assert out.target_optics_bounded


def test_r55_suitability_explicitly_does_not_consume_geometry_or_path_rt():
    out=build_canvas_optical_suitability(_scene(1.0),[_canvas()],target_optical_evidence=_ev(1.0),solar_altitude_deg=-3.0).iloc[0]
    assert not out.uses_penumbra_geometry
    assert not out.uses_spectral_path_rt
    assert not out.uses_cloud_fraction_to_infer_cot
    assert out.source_radiance_proxy > 0
