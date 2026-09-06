import pandas as pd

from firecloud.contracts import CanvasCandidate, CanvasDomain, CloudFractionState, CloudLayer, CloudScene, EvidenceState, GeometryConfidence
from firecloud.optical_path import build_ray_cloud_intersections, build_r3_optical_tables


def L(name,d,z0,z1,cot=None):
    return CloudLayer(
        layer_id=name,direction_offset_deg=0.0,distance_km=float(d),z_base_km=z0,z_top_km=z1,
        cloud_fraction_state=CloudFractionState.CLOUD_OCCUPIED,cloud_fraction=0.8,
        cot=cot,optical_evidence=(EvidenceState.FULL if cot is not None else EvidenceState.GEOMETRY_ONLY),
        geometry_confidence=GeometryConfidence.HIGH,
    )


def scene_and_canvas():
    scene=CloudScene(valid_time=None,layers=(
        L("target",20,4.8,5.2,0.8),
        L("b40",40,5.2,6.2),
        L("b60",60,4.8,5.6),
        L("b80",80,5.5,6.5),
    ),geometry_completeness=1.0,optics_completeness=0.25)
    canvas=CanvasCandidate(
        canvas_id="canvas::target",cloud_layer_id="target",latitude=24,longitude=121,
        cloud_base_altitude_km=5.0,distance_km=20,azimuth_deg=270,
        operational_domain=CanvasDomain.PRIMARY_CANVAS_0_40,geometry_confidence=GeometryConfidence.HIGH,
    )
    sec=pd.DataFrame([
        {"provider":"DWD","model":"ICON_GLOBAL","source_kind":"FORECAST_MODEL_NATIVE_OPTICS","optical_evidence":"FULL","secondary_exact_eligible":True,"status":"OK","direction_offset_deg":0.0,"distance_km":40.0,"z_base_km":5.2,"z_top_km":6.2,"cot":1.0},
        {"provider":"DWD","model":"ICON_GLOBAL","source_kind":"FORECAST_MODEL_NATIVE_OPTICS","optical_evidence":"FULL","secondary_exact_eligible":True,"status":"OK","direction_offset_deg":0.0,"distance_km":60.0,"z_base_km":4.8,"z_top_km":5.6,"cot":1.2},
        {"provider":"DWD","model":"ICON_GLOBAL","source_kind":"FORECAST_MODEL_NATIVE_OPTICS","optical_evidence":"FULL","secondary_exact_eligible":True,"status":"OK","direction_offset_deg":0.0,"distance_km":80.0,"z_base_km":5.5,"z_top_km":6.5,"cot":0.9},
    ])
    return scene,canvas,sec


def test_secondary_native_optics_can_resolve_upstream_slant_without_mutating_scene():
    scene,canvas,sec=scene_and_canvas()
    inter=build_ray_cloud_intersections(scene,[canvas],solar_altitude_deg=0.0,earth_radius_km=6371.0,secondary_forecast_optics=sec)
    up=inter[inter.intersection_role.eq("UPSTREAM_CLOUD_INTERSECTION")]
    resolved=up[up.slant_optics_status.eq("RESOLVED_SECONDARY_NATIVE_FORECAST_SLANT_RT")]
    assert not resolved.empty
    assert (resolved.slant_cloud_optical_depth > 0).all()
    assert resolved.path_optical_evidence_source.str.contains("DWD:ICON_GLOBAL").all()
    # Frozen CloudScene target/path geometry is not rewritten by the bridge.
    assert next(x for x in scene.layers if x.layer_id=="b60").cot is None


def test_secondary_bridge_supplies_cloud_component_only_not_geometry_or_target_response():
    scene,canvas,sec=scene_and_canvas()
    direct=pd.DataFrame([{"canvas_id":canvas.canvas_id,"direct_solar_fraction":1.0}])
    out=build_r3_optical_tables(
        scene=scene,canvases=[canvas],direct_solar=direct,solar_rays=pd.DataFrame(),spectral_voxels=pd.DataFrame(),
        solar_altitude_deg=0.0,earth_radius_km=6371.0,secondary_forecast_optics=sec,
    )
    p=out["spectral_optical_paths"]
    assert p["tau_cloud"].notna().all()
    assert (p["tau_cloud"] > 0).all()
    # Other missing components remain Missing: the bridge cannot fake full RT.
    assert p["transmission"].isna().all()
    assert p["missing_components"].str.contains("GAS").all()
    assert p["missing_components"].str.contains("PRECIPITATION").all()
