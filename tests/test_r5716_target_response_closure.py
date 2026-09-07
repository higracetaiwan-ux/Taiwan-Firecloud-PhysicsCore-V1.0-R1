import pandas as pd

from firecloud.contracts import (
    CanvasCandidate, CanvasDomain, CloudFractionState, CloudLayer, CloudScene,
    EvidenceState, GeometryConfidence, SIX_BAND_WAVELENGTHS_NM,
)
from firecloud.formation import build_r4_formation_tables
from firecloud.target_canvas_optics import (
    annotate_target_optical_truth, summarize_target_canvas_optical_evidence,
    TARGET_CANVAS_OPTICAL_EVIDENCE_COLUMNS, TARGET_CANVAS_OPTICAL_SUMMARY_COLUMNS,
)


def _canvas():
    return CanvasCandidate(
        canvas_id="canvas::target", cloud_layer_id="target", latitude=24.0, longitude=120.0,
        cloud_base_altitude_km=5.0, distance_km=20.0, azimuth_deg=270.0,
        operational_domain=CanvasDomain.PRIMARY_CANVAS_0_40,
        geometry_confidence=GeometryConfidence.HIGH,
    )


def _scene():
    return CloudScene(valid_time=None, layers=(CloudLayer(
        layer_id="target", direction_offset_deg=0.0, distance_km=20.0,
        z_base_km=5.0, z_top_km=6.0,
        cloud_fraction_state=CloudFractionState.CLOUD_OCCUPIED,
        cloud_fraction=0.8, phase="ICE", effective_radius_um=25.0,
        geometry_confidence=GeometryConfidence.HIGH,
        optical_evidence=EvidenceState.GEOMETRY_ONLY,
    ),), geometry_completeness=1.0, optics_completeness=0.0)


def _illum():
    row={"canvas_id":"canvas::target","direct_solar_fraction":1.0,
         "illumination_status":"FULL_RT","spectral_transmission_complete":True}
    for wl,val in {550:.1,575:.18,600:.3,650:.6,700:.7,750:.65}.items():
        row[f"relative_base_illumination_{wl}nm"]=val
    return pd.DataFrame([row])


def test_no_canvas_keeps_fixed_provenance_schema():
    out=build_r4_formation_tables(
        scene=CloudScene(valid_time=None,layers=()), canvases=[],
        cloud_base_illumination=pd.DataFrame(), spectral_voxels=pd.DataFrame(),
        solar_altitude_deg=-2.0,
    )
    f=out["formation"].iloc[0]
    assert f["formation_state"] == "NO_CANVAS_EVIDENCE"
    for c in [
        "target_optical_truth_exact_canvas_count","target_optical_truth_bounded_canvas_count",
        "target_optical_truth_conflict_canvas_count","target_optical_truth_unknown_canvas_count",
        "target_optics_ready_canvas_count","target_optics_bounded_canvas_count",
    ]:
        assert c in out["formation"].columns
        assert int(f[c]) == 0


def test_empty_target_truth_tables_keep_schema():
    e=annotate_target_optical_truth(pd.DataFrame())
    s=summarize_target_canvas_optical_evidence(e)
    assert list(e.columns) == TARGET_CANVAS_OPTICAL_EVIDENCE_COLUMNS
    assert list(s.columns) == TARGET_CANVAS_OPTICAL_SUMMARY_COLUMNS
    assert len(e) == 0 and len(s) == 0


def test_bounded_target_produces_six_band_response_bounds_but_not_exact_response():
    ev=pd.DataFrame([{
        "canvas_id":"canvas::target","resolver_state":"ADJACENT_NATIVE_COT_BRACKET_BOUNDED",
        "target_optics_ready":False,"target_optics_bounded":True,
        "target_cot_nominal":1.5,"target_cot_lower_bound":1.0,"target_cot_upper_bound":2.0,
        "evidence_source":"TWO_SIDED_ADJACENT_NATIVE_CONDENSATE_COT",
        "target_optical_truth_state":"BOUNDED_NATIVE_BRACKET",
        "target_cot_semantics":"BOUNDED_INTERVAL",
        "target_response_eligibility":"BOUNDED_ONLY_NOT_EXACT",
    }])
    out=build_r4_formation_tables(
        scene=_scene(),canvases=[_canvas()],cloud_base_illumination=_illum(),
        spectral_voxels=pd.DataFrame(),solar_altitude_deg=-2.0,target_optical_evidence=ev,
    )
    c=out["canvas_radiance"].iloc[0]
    assert c["response_status"] == "BOUNDED_TIER1_RESPONSE_AVAILABLE"
    assert pd.isna(c["brightness"]) and pd.isna(c["redness"])
    assert pd.notna(c["brightness_lower_bound"]) and pd.notna(c["brightness_upper_bound"])
    assert c["brightness_lower_bound"] <= c["brightness_upper_bound"]
    assert c["tier2_scattering_readiness"] == "READY_FOR_TIER2_INPUTS"
    for wl in SIX_BAND_WAVELENGTHS_NM:
        assert pd.isna(c[f"cloud_radiance_proxy_{wl}nm"])
        assert pd.notna(c[f"cloud_radiance_proxy_{wl}nm_lower_bound"])
        assert pd.notna(c[f"cloud_radiance_proxy_{wl}nm_upper_bound"])
        assert c[f"cloud_radiance_proxy_{wl}nm_lower_bound"] <= c[f"cloud_radiance_proxy_{wl}nm_upper_bound"]
    assert out["formation"].iloc[0]["formation_state"] == "UNCERTAIN_OPTICS"


def test_exact_target_has_collapsed_response_interval():
    ev=pd.DataFrame([{
        "canvas_id":"canvas::target","resolver_state":"DIRECT_NATIVE_CONDENSATE_COT",
        "target_optics_ready":True,"target_optics_bounded":False,
        "target_cot_nominal":2.0,"target_cot_lower_bound":2.0,"target_cot_upper_bound":2.0,
        "evidence_source":"CLOUD_LAYER_NATIVE_CLWMR_ICMR",
        "target_optical_truth_state":"EXACT_PRIMARY_NATIVE",
        "target_cot_semantics":"EXACT_VALUE","target_response_eligibility":"EXACT_RESPONSE_ELIGIBLE",
    }])
    out=build_r4_formation_tables(
        scene=_scene(),canvases=[_canvas()],cloud_base_illumination=_illum(),
        spectral_voxels=pd.DataFrame(),solar_altitude_deg=-2.0,target_optical_evidence=ev,
    )
    c=out["canvas_radiance"].iloc[0]
    assert c["response_status"] == "READY_TIER1_UNCALIBRATED"
    for wl in SIX_BAND_WAVELENGTHS_NM:
        x=c[f"cloud_radiance_proxy_{wl}nm"]
        assert x == c[f"cloud_radiance_proxy_{wl}nm_lower_bound"] == c[f"cloud_radiance_proxy_{wl}nm_upper_bound"]
