import pandas as pd

from firecloud.contracts import (
    CloudLayer, CloudScene, CloudFractionState, GeometryConfidence, EvidenceState,
)
from firecloud.v1_runtime import build_canvas_candidates
from firecloud.optical_path import (
    build_ray_cloud_intersections, build_native_condensate_support_diagnostics,
    build_r3_optical_tables,
)

WLS=(550,575,600,650,700,750)

def _layer(d, cot=1.0, z0=5.0, z1=6.0):
    return CloudLayer(
        layer_id=f"L{d}", direction_offset_deg=0.0, distance_km=float(d),
        z_base_km=z0, z_top_km=z1,
        cloud_fraction_state=CloudFractionState.CLOUD_OCCUPIED, cloud_fraction=1.0,
        liquid_condensate_kgkg=1e-5, ice_condensate_kgkg=1e-6,
        phase="MIXED", effective_radius_um=12.0, cot=float(cot),
        geometry_confidence=GeometryConfidence.HIGH, optical_evidence=EvidenceState.FULL,
        geometry_source="NATIVE_MODEL_LEVELS",
    )


def _scene():
    # 100 km is the target canvas. 120/140/160/180 km form a native-condensate
    # bank; interior columns have adjacent evidence on both sides and therefore
    # auditable midpoint horizontal support.
    return CloudScene(
        valid_time=None,
        layers=tuple(_layer(d, cot=1.5) for d in (100,120,140,160,180)),
        geometry_completeness=1.0, optics_completeness=1.0,
    )


def test_r43_native_condensate_case_resolves_slant_blocker_and_audit():
    scene=_scene()
    canvases=build_canvas_candidates(scene,observer_lat=24,observer_lon=121,
                                     solar_azimuth_deg=270,earth_radius_km=6371,
                                     max_canvas_distance_km=100)
    c=[x for x in canvases if x.distance_km==100][0]
    inter=build_ray_cloud_intersections(scene,[c],solar_altitude_deg=0,earth_radius_km=6371)
    resolved=inter[inter.slant_optics_status.eq("RESOLVED_NATIVE_CONDENSATE_SLANT_RT")]
    assert not resolved.empty
    assert resolved.slant_cloud_optical_depth.notna().all()
    assert (resolved.slant_cloud_optical_depth>0).all()
    diag=build_native_condensate_support_diagnostics(scene,inter).iloc[0]
    assert diag.native_optical_layer_count==5
    assert diag.horizontal_support_resolved_layer_count>=3
    assert diag.resolved_native_condensate_slant_intersection_count>=1
    assert diag.sampling_step_is_cloud_width == False


def test_r43_resolved_slant_tau_propagates_into_six_band_optical_path():
    scene=_scene()
    canvases=build_canvas_candidates(scene,observer_lat=24,observer_lon=121,
                                     solar_azimuth_deg=270,earth_radius_km=6371,
                                     max_canvas_distance_km=100)
    c=[x for x in canvases if x.distance_km==100][0]
    rt={"direction_offset_deg":0.0,"distance_km":100.0,"voxel_center_km":5.5}
    for wl in WLS:
        rt[f"gas_tau_{wl}nm"]=0.1
        rt[f"aerosol_tau_{wl}nm"]=0.05
    spectral=pd.DataFrame([rt])
    direct=pd.DataFrame([{"canvas_id":c.canvas_id,"direct_solar_fraction":1.0}])
    precip=pd.DataFrame([{"canvas_id":c.canvas_id,"status":"PRECIPITATION_OPTICS_RESOLVED",**{f"tau_precip_{wl}nm":0.0 for wl in WLS}}])
    out=build_r3_optical_tables(scene=scene,canvases=[c],direct_solar=direct,solar_rays=pd.DataFrame(),
                                spectral_voxels=spectral,solar_altitude_deg=0.0,earth_radius_km=6371,
                                precipitation_path_evidence=precip)
    paths=out["spectral_optical_paths"]
    assert len(paths)==6
    assert paths.tau_cloud.notna().all()
    assert (paths.tau_cloud>0).all()
    assert paths.resolved_upstream_cloud_intersection_count.gt(0).all()
    assert paths.transmission.notna().all()
    assert paths.evidence_state.eq("FULL").all()
