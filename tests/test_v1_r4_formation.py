import pandas as pd

from firecloud.contracts import (
    CanvasCandidate, CanvasDomain, CloudFractionState, CloudLayer, CloudScene,
    EvidenceState, GeometryConfidence, SIX_BAND_WAVELENGTHS_NM,
)
from firecloud.formation import build_r4_formation_tables


def _canvas():
    return CanvasCandidate(
        canvas_id="canvas::target", cloud_layer_id="target", latitude=24.0, longitude=120.0,
        cloud_base_altitude_km=5.0, distance_km=20.0, azimuth_deg=270.0,
        operational_domain=CanvasDomain.PRIMARY_CANVAS_0_40,
        geometry_confidence=GeometryConfidence.HIGH,
    )


def _scene(evidence=EvidenceState.FULL):
    layer = CloudLayer(
        layer_id="target", direction_offset_deg=0.0, distance_km=20.0,
        z_base_km=5.0, z_top_km=6.0,
        cloud_fraction_state=CloudFractionState.CLOUD_OCCUPIED,
        cloud_fraction=0.8, phase="ICE", geometry_confidence=GeometryConfidence.HIGH,
        optical_evidence=evidence,
    )
    return CloudScene(valid_time=None, layers=(layer,), geometry_completeness=1.0,
                      optics_completeness=1.0 if evidence == EvidenceState.FULL else 0.0)


def _illum(fsun=1.0, complete=True):
    row = {
        "canvas_id":"canvas::target", "direct_solar_fraction":fsun,
        "illumination_status":"FULL_RT" if complete else "UNCERTAIN_OPTICS",
        "spectral_transmission_complete":complete,
    }
    vals={550:0.10,575:0.18,600:0.30,650:0.60,700:0.70,750:0.65}
    for wl in SIX_BAND_WAVELENGTHS_NM:
        row[f"relative_base_illumination_{wl}nm"] = vals[wl] if complete else None
    return pd.DataFrame([row])


def _spectral_tau(tau=2.0):
    return pd.DataFrame([{
        "v1_canvas_id":"canvas::target", "v1_cloud_layer_id":"target",
        "distance_km":20.0, "voxel_bottom_km":4.75, "voxel_top_km":5.25,
        "voxel_center_km":5.0, "vertical_cloud_optical_depth_estimate":tau,
    }])


def test_r4_ready_response_keeps_three_dimensions_separate():
    out=build_r4_formation_tables(
        scene=_scene(), canvases=[_canvas()], cloud_base_illumination=_illum(),
        spectral_voxels=_spectral_tau(), solar_altitude_deg=-2.0,
    )
    c=out["canvas_radiance"].iloc[0]
    assert c["response_status"] == "READY_TIER1_UNCALIBRATED"
    assert pd.notna(c["brightness"])
    assert pd.notna(c["redness"])
    assert c["effective_illuminated_area_fraction"] == 0.8
    assert c["cloud_type_multiplier"] == "NONE"
    for wl in SIX_BAND_WAVELENGTHS_NM:
        assert pd.notna(c[f"cloud_radiance_proxy_{wl}nm"])
    f=out["formation"].iloc[0]
    assert f["formation_state"] == "FORMATION_EVIDENCE_AVAILABLE"
    assert "NO_SINGLE_FORMATION_SCORE" in f["aggregation_note"]


def test_r4_geometry_only_never_fabricates_cloud_response():
    out=build_r4_formation_tables(
        scene=_scene(EvidenceState.GEOMETRY_ONLY), canvases=[_canvas()],
        cloud_base_illumination=_illum(), spectral_voxels=_spectral_tau(),
        solar_altitude_deg=-2.0,
    )
    c=out["canvas_radiance"].iloc[0]
    assert c["response_status"] == "UNCERTAIN_TARGET_CLOUD_OPTICS"
    assert pd.isna(c["target_vertical_cloud_optical_depth"])
    assert pd.isna(c["brightness"])
    assert pd.isna(c["redness"])
    assert out["formation"].iloc[0]["formation_state"] == "UNCERTAIN_OPTICS"


def test_r4_known_earth_shadow_zero_is_known_zero_without_cloud_optics():
    out=build_r4_formation_tables(
        scene=_scene(EvidenceState.GEOMETRY_ONLY), canvases=[_canvas()],
        cloud_base_illumination=_illum(fsun=0.0, complete=False),
        spectral_voxels=pd.DataFrame(), solar_altitude_deg=-4.0,
    )
    c=out["canvas_radiance"].iloc[0]
    assert c["response_status"] == "CONFIRMED_ZERO_EARTH_SHADOW"
    assert c["brightness"] == 0.0
    assert c["redness"] == 0.0
    assert out["formation"].iloc[0]["formation_state"] == "NOT_FORMED_EARTH_SHADOW"
