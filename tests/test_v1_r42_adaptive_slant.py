import pandas as pd

from firecloud.config import ModelConfig, adaptive_horizontal_distance_samples
from firecloud.contracts import (
    CloudLayer, CloudScene, CloudFractionState, GeometryConfidence, EvidenceState,
)
from firecloud.v1_runtime import build_canvas_candidates
from firecloud.optical_path import build_ray_cloud_intersections, build_r3_optical_tables


def _layer(d, z0=5.0, z1=6.0, cot=1.0):
    return CloudLayer(
        layer_id=f"L{d}", direction_offset_deg=0.0, distance_km=float(d),
        z_base_km=z0, z_top_km=z1,
        cloud_fraction_state=CloudFractionState.CLOUD_OCCUPIED, cloud_fraction=1.0,
        liquid_condensate_kgkg=1e-5, ice_condensate_kgkg=1e-6,
        phase="MIXED", effective_radius_um=12.0, cot=cot,
        geometry_confidence=GeometryConfidence.HIGH, optical_evidence=EvidenceState.FULL,
    )


def test_adaptive_sampling_contract_nodes():
    x = adaptive_horizontal_distance_samples(440)
    assert x[:9] == (0.0,5.0,10.0,15.0,20.0,25.0,30.0,35.0,40.0)
    assert tuple(v for v in x if 40 <= v <= 100) == (40.0,50.0,60.0,70.0,80.0,90.0,100.0)
    assert 120.0 in x and 140.0 in x and 440.0 in x
    assert 110.0 not in x
    cfg=ModelConfig()
    assert cfg.dynamic_distance_samples_km[:9] == x[:9]


def test_native_multicolumn_support_produces_slant_tau_without_using_sampling_as_width():
    # Canvas at 100 km plus a native-condensate cloud bank continuing through
    # several adjacent columns.  Only interior columns may receive resolved
    # midpoint support; route-edge support remains unresolved by design.
    scene=CloudScene(valid_time=None, layers=tuple(_layer(d) for d in (100,120,140,160,180)),
                     geometry_completeness=1.0, optics_completeness=1.0)
    canvases=build_canvas_candidates(scene, observer_lat=24.0, observer_lon=121.0,
                                     solar_azimuth_deg=270.0, earth_radius_km=6371.0,
                                     max_canvas_distance_km=100.0)
    c=[x for x in canvases if x.distance_km==100.0][0]
    inter=build_ray_cloud_intersections(scene,[c],solar_altitude_deg=0.0,earth_radius_km=6371.0)
    up=inter[inter.intersection_role.eq("UPSTREAM_CLOUD_INTERSECTION")]
    resolved=up[up.slant_optics_status.eq("RESOLVED_NATIVE_CONDENSATE_SLANT_RT")]
    assert not resolved.empty
    assert (resolved.slant_cloud_optical_depth > 0).all()
    assert resolved.horizontal_support_resolved.all()
    assert resolved.support_source.eq("MULTICOLUMN_NATIVE_CONDENSATE_CONTINUITY").all()
    # Explicitly audit that support is derived from neighbouring evidence, not
    # the generic statement "sampling step == cloud width".
    assert resolved.support_confidence.eq("MEDIUM").all()


def test_target_cot_is_not_counted_as_sun_to_cloudbase_path_tau():
    # With no upstream cloud, Cloud-path tau is known zero even though the target
    # itself has non-zero COT; target COT belongs to Canvas response.
    scene=CloudScene(valid_time=None, layers=(_layer(20,cot=3.0),),geometry_completeness=1.0,optics_completeness=1.0)
    canvases=build_canvas_candidates(scene,observer_lat=24,observer_lon=121,solar_azimuth_deg=270,earth_radius_km=6371)
    c=canvases[0]
    rt={"direction_offset_deg":0.0,"distance_km":20.0,"voxel_center_km":5.0}
    for wl in (550,575,600,650,700,750):
        rt[f"gas_tau_{wl}nm"]=0.1; rt[f"aerosol_tau_{wl}nm"]=0.05
    spectral=pd.DataFrame([rt])
    direct=pd.DataFrame([{"canvas_id":c.canvas_id,"direct_solar_fraction":1.0}])
    precip=pd.DataFrame([{"canvas_id":c.canvas_id,"status":"PRECIPITATION_OPTICS_RESOLVED",**{f"tau_precip_{wl}nm":0.0 for wl in (550,575,600,650,700,750)}}])
    out=build_r3_optical_tables(scene=scene,canvases=[c],direct_solar=direct,solar_rays=pd.DataFrame(),spectral_voxels=spectral,solar_altitude_deg=0.0,earth_radius_km=6371,precipitation_path_evidence=precip)
    p=out["spectral_optical_paths"]
    assert (p.tau_cloud == 0.0).all()
