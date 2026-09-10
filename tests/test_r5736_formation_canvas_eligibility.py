import pandas as pd

from firecloud.contracts import (
    CloudLayer, CloudScene, CloudFractionState, GeometryConfidence, EvidenceState,
    FIRECLOUD_CANVAS_MIN_BASE_KM,
)
from firecloud.v1_runtime import build_canvas_candidates, build_r2_geometry_tables
from firecloud.red_light_availability import summarize_red_light_availability
from firecloud.case_integrity import build_analysis_integrity_audit


def _layer(z0, d=20.0):
    return CloudLayer(
        layer_id=f"L{z0}", direction_offset_deg=0.0, distance_km=d,
        z_base_km=z0, z_top_km=max(z0+0.5, 2.1),
        cloud_fraction_state=CloudFractionState.CLOUD_OCCUPIED, cloud_fraction=0.8,
        geometry_confidence=GeometryConfidence.HIGH, optical_evidence=EvidenceState.GEOMETRY_ONLY,
    )


def test_low_cloud_is_retained_in_scene_but_not_promoted_to_canvas_candidate():
    scene=CloudScene(valid_time=None,layers=(_layer(0.35),),geometry_completeness=1.0,optics_completeness=0.0)
    canvases=build_canvas_candidates(scene,observer_lat=33.0,observer_lon=130.0,solar_azimuth_deg=270.0,earth_radius_km=6371.0)
    assert len(scene.layers)==1
    assert len(canvases)==0


def test_two_km_boundary_remains_eligible_without_widening_or_lowering():
    scene=CloudScene(valid_time=None,layers=(_layer(FIRECLOUD_CANVAS_MIN_BASE_KM),),geometry_completeness=1.0,optics_completeness=0.0)
    canvases=build_canvas_candidates(scene,observer_lat=24.0,observer_lon=121.0,solar_azimuth_deg=270.0,earth_radius_km=6371.0)
    assert len(canvases)==1
    assert canvases[0].cloud_base_altitude_km == FIRECLOUD_CANVAS_MIN_BASE_KM


def test_r2_exports_explicit_low_cloud_blocker_role_but_zero_canvas_rows():
    row={
        "direction_offset_deg":0.0,"distance_km":20.0,"native_profile_source":"TEST",
        "model_surface_elevation_m":0.0,
    }
    for p,z,cf in [(950,0.1,0.0),(925,0.35,0.8),(900,0.7,0.0)]:
        row[f"geopotential_height_{p}hPa"]=z*1000.0
        row[f"cloud_fraction_{p}hPa"]=cf
        row[f"cloud_liquid_water_kgkg_{p}hPa"]=0.0
        row[f"cloud_ice_water_kgkg_{p}hPa"]=0.0
        row[f"temperature_{p}hPa"]=290.0
        row[f"relative_humidity_{p}hPa"]=80.0
    out=build_r2_geometry_tables(pd.DataFrame([row]),[950,925,900],observer_lat=33.0,observer_lon=130.0,solar_altitude_deg=-1.0,solar_azimuth_deg=270.0,earth_radius_km=6371.0,route_end_km=440.0,route_step_km=20.0,valid_time="t0")
    assert len(out["cloud_layers"])==1
    assert out["cloud_layers"].iloc[0]["formation_cloud_role"] == "BLOCKER_ONLY_LOW_CLOUD"
    assert not bool(out["cloud_layers"].iloc[0]["formation_canvas_eligible"])
    assert out["canvases"].empty
    assert out["direct_solar"].empty


def test_integrity_rejects_any_below_2km_row_promoted_to_canvas():
    audit=build_analysis_integrity_audit({
        "v1_formation":pd.DataFrame([{"time":"t0","solar_altitude_deg":-1.0,"formation_state":"NO_CANVAS_EVIDENCE"}]),
        "v1_canvas_candidates":pd.DataFrame([{
            "time":"t0","solar_altitude_deg":-1.0,"canvas_id":"bad",
            "cloud_base_altitude_km":0.35,"formation_canvas_eligible":True,
            "formation_cloud_role":"FORMATION_CANVAS_TARGET",
        }]),
    })
    q=audit[audit.check_id.eq("FORMATION_CANVAS_LOW_CLOUD_ROLE_SEPARATION")].iloc[0]
    assert q.status == "FAIL"


def test_integrity_allows_no_canvas_when_formation_exists():
    audit=build_analysis_integrity_audit({
        "v1_formation":pd.DataFrame([{"time":"t0","solar_altitude_deg":-1.0,"formation_state":"NO_CANVAS_EVIDENCE"}]),
        "v1_canvas_candidates":pd.DataFrame(),
    })
    q=audit[audit.check_id.eq("FORMATION_CANVAS_LOW_CLOUD_ROLE_SEPARATION")].iloc[0]
    assert q.status == "ALLOWED_EMPTY"


def test_high_cloud_outside_100km_remains_scene_but_is_not_canvas_target():
    scene=CloudScene(valid_time=None,layers=(_layer(5.0,d=120.0),),geometry_completeness=1.0,optics_completeness=0.0)
    canvases=build_canvas_candidates(scene,observer_lat=24.0,observer_lon=121.0,solar_azimuth_deg=270.0,earth_radius_km=6371.0)
    assert len(scene.layers)==1
    assert len(canvases)==0
