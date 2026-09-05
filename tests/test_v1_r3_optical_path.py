import pandas as pd

from firecloud.contracts import (
    SIX_BAND_WAVELENGTHS_NM, CanvasCandidate, CanvasDomain, CloudFractionState,
    CloudLayer, CloudScene, EvidenceState, GeometryConfidence,
)
from firecloud.optical_path import build_ray_cloud_intersections, build_r3_optical_tables


def _scene():
    target = CloudLayer(
        layer_id="target", direction_offset_deg=0.0, distance_km=20.0,
        z_base_km=5.0, z_top_km=6.0,
        cloud_fraction_state=CloudFractionState.CLOUD_OCCUPIED,
        cloud_fraction=0.8, geometry_confidence=GeometryConfidence.HIGH,
        optical_evidence=EvidenceState.GEOMETRY_ONLY,
    )
    # At 0 degrees the curved ray from 5 km at 20 km remains near 5 km at 40 km.
    blocker = CloudLayer(
        layer_id="blocker", direction_offset_deg=0.0, distance_km=40.0,
        z_base_km=4.5, z_top_km=5.7,
        cloud_fraction_state=CloudFractionState.CLOUD_OCCUPIED,
        cloud_fraction=0.9, geometry_confidence=GeometryConfidence.HIGH,
        optical_evidence=EvidenceState.GEOMETRY_ONLY,
    )
    return CloudScene(valid_time=None, layers=(target, blocker), geometry_completeness=1.0, optics_completeness=0.0)


def _canvas():
    return CanvasCandidate(
        canvas_id="canvas::target", cloud_layer_id="target",
        latitude=24.0, longitude=120.0, cloud_base_altitude_km=5.0,
        distance_km=20.0, azimuth_deg=270.0,
        operational_domain=CanvasDomain.PRIMARY_CANVAS_0_40,
        geometry_confidence=GeometryConfidence.HIGH,
    )


def test_r3_ray_cloud_intersection_is_ray_based_not_fixed_band():
    hits = build_ray_cloud_intersections(_scene(), [_canvas()], solar_altitude_deg=0.0, earth_radius_km=6371.0)
    assert "TARGET_CANVAS" in set(hits["intersection_role"])
    assert "UPSTREAM_CLOUD_INTERSECTION" in set(hits["intersection_role"])
    assert "blocker" in set(hits["cloud_layer_id"])


def test_r3_preserves_all_six_bands_and_missing_is_not_zero():
    direct = pd.DataFrame([{"canvas_id":"canvas::target", "direct_solar_fraction":1.0}])
    # Deliberately provide no spectral voxels: all optical components must remain
    # Missing/unknown rather than becoming zero or clear.
    out = build_r3_optical_tables(
        scene=_scene(), canvases=[_canvas()], direct_solar=direct,
        solar_rays=pd.DataFrame(), spectral_voxels=pd.DataFrame(),
        solar_altitude_deg=0.0, earth_radius_km=6371.0,
    )
    p = out["spectral_optical_paths"]
    assert tuple(sorted(p["wavelength_nm"].unique())) == tuple(SIX_BAND_WAVELENGTHS_NM)
    assert p["transmission"].isna().all()
    assert p["tau_total"].isna().all()
    assert (p["evidence_state"] == "MISSING").all()
    assert p["missing_components"].str.contains("PRECIPITATION_GEOMETRY_MISSING").all()


def test_earth_shadow_known_zero_does_not_require_optics():
    direct = pd.DataFrame([{"canvas_id":"canvas::target", "direct_solar_fraction":0.0}])
    out = build_r3_optical_tables(
        scene=_scene(), canvases=[_canvas()], direct_solar=direct,
        solar_rays=pd.DataFrame(), spectral_voxels=pd.DataFrame(),
        solar_altitude_deg=-4.0, earth_radius_km=6371.0,
    )
    p = out["spectral_optical_paths"]
    assert (p["relative_base_illumination"] == 0.0).all()
    i = out["cloud_base_illumination"].iloc[0]
    assert i["illumination_status"] == "CONFIRMED_NOT_ILLUMINATED_EARTH_SHADOW"
