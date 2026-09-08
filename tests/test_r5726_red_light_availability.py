import numpy as np
import pandas as pd

from firecloud.contracts import (
    CloudFractionState, CloudLayer, CloudScene, EvidenceState, GeometryConfidence,
)
from firecloud.optical_path import build_reference_receiver_cloud_path_evidence
from firecloud.red_light_availability import (
    summarize_red_light_availability, apply_red_light_context_to_formation,
    apply_red_light_context_to_headline_summary,
)
from firecloud.case_integrity import build_analysis_integrity_audit


def _scene_layer(name, d, z0, z1, *, cot=None, consistency="CONSISTENT_CLOUD"):
    return CloudLayer(
        layer_id=name, direction_offset_deg=0.0, distance_km=float(d),
        z_base_km=float(z0), z_top_km=float(z1),
        cloud_fraction_state=CloudFractionState.CLOUD_OCCUPIED, cloud_fraction=0.8,
        liquid_condensate_kgkg=(1e-5 if cot is not None else 0.0), ice_condensate_kgkg=0.0,
        phase="LIQUID" if cot is not None else "UNKNOWN",
        effective_radius_um=10.0 if cot is not None else None,
        cot=cot, geometry_confidence=GeometryConfidence.HIGH,
        optical_evidence=(EvidenceState.FULL if cot is not None else EvidenceState.GEOMETRY_ONLY),
        evidence_consistency=consistency, geometry_source="NATIVE_MODEL_LEVELS",
    )


def test_reference_receiver_no_cloud_is_full_clear_when_geometry_complete():
    scene=CloudScene(valid_time=None,layers=(),geometry_completeness=1.0,optics_completeness=1.0)
    rr=pd.DataFrame([{
        "reference_receiver_id":"r1","direction_offset_deg":0.0,"distance_km":20.0,
        "reference_cloud_base_km":5.0,"sampled_receiver_altitude_km":5.0,
    }])
    out=build_reference_receiver_cloud_path_evidence(
        scene,rr,solar_altitude_deg=-1.0,earth_radius_km=6371.0,cloud_geometry_completeness=1.0,
    )
    assert out.loc[0,"cloud_path_evidence_state"] == "FULL"
    assert out.loc[0,"upstream_cloud_intersection_count"] == 0
    assert out.loc[0,"resolved_upstream_cloud_tau"] == 0.0
    assert out.loc[0,"resolved_upstream_cloud_transmission"] == 1.0


def test_reference_receiver_cf_cloud_condensate_zero_remains_conflict():
    # Three optical rows are not needed: the unresolved CF-vs-condensate layer at
    # an upstream centre-point intersection must remain a direct evidence conflict.
    scene=CloudScene(valid_time=None,layers=(
        _scene_layer("blocker",40.0,4.5,6.5,cot=None,consistency="CF_CLOUD_CONDENSATE_ZERO"),
    ),geometry_completeness=1.0,optics_completeness=0.0)
    rr=pd.DataFrame([{
        "reference_receiver_id":"r1","direction_offset_deg":0.0,"distance_km":20.0,
        "reference_cloud_base_km":5.0,"sampled_receiver_altitude_km":5.0,
    }])
    out=build_reference_receiver_cloud_path_evidence(
        scene,rr,solar_altitude_deg=0.0,earth_radius_km=6371.0,cloud_geometry_completeness=1.0,
    )
    assert out.loc[0,"cloud_path_evidence_state"] == "DIRECT_EVIDENCE_CONFLICT"
    assert out.loc[0,"direct_evidence_conflict_count"] >= 1
    assert np.isnan(out.loc[0,"resolved_upstream_cloud_transmission"])


def _red_reference_rows(angle=0.0):
    rows=[]
    for domain in ("PRIMARY_CANVAS_0_40","EXTENDED_CANVAS_40_100"):
        for i in range(2):
            rows.append({
                "time":"2026-09-08T10:00:00Z","solar_altitude_deg":angle,
                "reference_domain":domain,"v1_direct_solar_fraction":1.0,
                "red_light_path_state":"RED_LIGHT_PATH_OPEN",
                "red_band_mean_availability":0.42 + 0.01*i,
                "cloud_geometry_completeness":1.0,
            })
    return pd.DataFrame(rows)


def test_open_red_path_plus_no_canvas_becomes_clear_red_path_no_canvas():
    s=summarize_red_light_availability(_red_reference_rows(),pd.DataFrame())
    assert len(s)==1
    r=s.iloc[0]
    assert r.red_light_path_state == "RED_LIGHT_PATH_OPEN"
    assert r.primary_canvas_state == "ABSENT"
    assert r.extended_canvas_state == "ABSENT"
    assert r.formation_context_state == "CLEAR_RED_PATH_NO_CANVAS"
    assert bool(r.unused_red_light_potential_applicable) is True
    assert 0 < r.unused_red_light_potential < 1


def test_clear_red_path_no_canvas_does_not_create_firecloud_formation():
    summary=summarize_red_light_availability(_red_reference_rows(),pd.DataFrame())
    formation=pd.DataFrame([{
        "time":"2026-09-08T10:00:00Z","solar_altitude_deg":0.0,
        "formation_state":"NO_CANVAS_EVIDENCE","formation_confidence":"UNKNOWN",
    }])
    out=apply_red_light_context_to_formation(formation,summary)
    assert out.loc[0,"formation_state_base"] == "NO_CANVAS_EVIDENCE"
    assert out.loc[0,"formation_state"] == "CLEAR_RED_PATH_NO_CANVAS"
    assert out.loc[0,"formation_confidence"] == "HIGH"
    # No brightness/redness is invented by the context state.
    assert "brightness" not in out.columns


def test_integrity_requires_no_canvas_cloud_path_to_be_not_applicable():
    red_sum=pd.DataFrame([{
        "solar_altitude_deg":0.0,"primary_canvas_count":0,"extended_canvas_count":0,
        "formation_context_state":"CLEAR_RED_PATH_NO_CANVAS",
    }])
    base={
        "route_points":pd.DataFrame([{"distance_km":0.0}]),
        "hourly_raw":pd.DataFrame([{"x":1}]),
        "v1_formation":pd.DataFrame([{"solar_altitude_deg":0.0}]),
        "performance_diagnostics":pd.DataFrame([{"x":1}]),
        "v1_canvas_candidates":pd.DataFrame(),
        "v1_spectral_optical_paths":pd.DataFrame(),
        "v1_red_light_reference":pd.DataFrame([{"solar_altitude_deg":0.0}]),
        "v1_red_light_availability_summary":red_sum,
        "summary":pd.DataFrame([{"solar_altitude_deg":0.0,"operational_decision":"CLEAR_RED_PATH_NO_CANVAS"}]),
    }
    good={**base,"physics_data_completeness":pd.DataFrame([{
        "solar_altitude_deg":0.0,"layer":"SPECTRAL_CLOUD_PATH","status":"NOT_APPLICABLE","completeness":1.0,
    }])}
    audit=build_analysis_integrity_audit(good)
    assert audit[audit.check_id.eq("NO_CANVAS_CLOUD_PATH_NOT_APPLICABLE")].iloc[0].status == "PASS"

    bad={**base,"physics_data_completeness":pd.DataFrame([{
        "solar_altitude_deg":0.0,"layer":"SPECTRAL_CLOUD_PATH","status":"MISSING","completeness":0.0,
    }])}
    audit2=build_analysis_integrity_audit(bad)
    assert audit2[audit2.check_id.eq("NO_CANVAS_CLOUD_PATH_NOT_APPLICABLE")].iloc[0].status == "FAIL"


def test_physics_data_completeness_no_canvas_cloud_path_is_not_applicable(monkeypatch):
    import firecloud.model as model
    monkeypatch.setattr(model,"native_aerosol_provider_status",lambda:{"credentials_configured":True,"provider":"CAMS"})
    monkeypatch.setattr(model,"native_ozone_provider_status",lambda:{"credentials_configured":True,"provider":"CAMS O3"})
    angle=0.0
    gp=pd.DataFrame([{
        "temperature_k":280.0,"pressure_hpa":500.0,"relative_humidity_pct":50.0,
        "h2o_mole_fraction":0.005,"o2_mole_fraction":0.21,"o3_mole_fraction":1e-7,
        "direction_offset_deg":0.0,"distance_km":0.0,"altitude_agl_km":20.0,
    }])
    cams=pd.DataFrame([{"cams_aerext532_m1_500hPa":1e-5}])
    details={angle:{
        "cams_native_aerosol_snapshot":cams,
        "cams_native_aerosol_metadata":{},
        "gas_profile":gp,
        "hitran_backend_status":{"runtime_spectroscopy_ready":True,"database_exists":True,"coefficient_table_exists":True},
        "spectral_voxels":pd.DataFrame(),
        "v1_spectral_optical_paths":pd.DataFrame(),
        "spectral_rt_requirement":{"canvas_count":0,"direct_sunlit_canvas_count":0},
    }}
    base=pd.DataFrame([{"solar_altitude_deg":angle,"data_completeness":1.0}])
    out=model._build_physics_data_completeness(details,[(angle,pd.Timestamp("2026-09-08T10:00:00Z"),270.0)],base)
    q=out[(out.solar_altitude_deg==angle)&out.layer.eq("SPECTRAL_CLOUD_PATH")].iloc[0]
    assert q.status == "NOT_APPLICABLE"
    assert q.completeness == 1.0
    assert q.missing_reason == "NO_TARGET_CLOUD_GEOMETRY"


def test_clear_red_path_no_canvas_overrides_legacy_unknown_without_using_score():
    red = summarize_red_light_availability(_red_reference_rows(), pd.DataFrame())
    legacy = pd.DataFrame([{
        "solar_altitude_deg": 0.0,
        "physics_score": 0.0089,
        "data_completeness": 1.0,
        "core_score_eligible": True,
        "operational_decision": "UNKNOWN / DATA INCOMPLETE",
    }])
    out = apply_red_light_context_to_headline_summary(legacy, red)
    assert out.loc[0, "operational_decision"] == "CLEAR_RED_PATH_NO_CANVAS"
    assert bool(out.loc[0, "legacy_physics_score_applicable"]) is False
    assert bool(out.loc[0, "core_score_eligible"]) is False
    # Legacy number remains archived, but it cannot be interpreted as a
    # Firecloud Formation score in a no-Canvas state.
    assert out.loc[0, "physics_score"] == 0.0089
    assert out.loc[0, "potential_scale_status"] == "CONTINUOUS_UNCALIBRATED_DIAGNOSTIC"


def test_no_canvas_unknown_red_path_overrides_legacy_headline_but_preserves_uncertainty():
    red = pd.DataFrame([{
        "time": pd.Timestamp("2026-09-08T10:00:00Z"),
        "solar_altitude_deg": -1.0,
        "red_light_path_state": "RED_LIGHT_PATH_UNKNOWN",
        "primary_red_light_path_state": "RED_LIGHT_PATH_UNKNOWN",
        "extended_red_light_path_state": "RED_LIGHT_PATH_UNKNOWN",
        "formation_context_state": "NO_CANVAS_RED_PATH_UNKNOWN",
        "primary_canvas_state": "ABSENT",
        "extended_canvas_state": "ABSENT",
        "unused_red_light_potential": np.nan,
        "potential_scale_status": "CONTINUOUS_UNCALIBRATED_DIAGNOSTIC",
    }])
    legacy = pd.DataFrame([{
        "solar_altitude_deg": -1.0,
        "physics_score": 0.01,
        "data_completeness": 1.0,
        "core_score_eligible": True,
        "operational_decision": "UNKNOWN / DATA INCOMPLETE",
    }])
    out = apply_red_light_context_to_headline_summary(legacy, red)
    assert out.loc[0, "operational_decision"] == "NO_CANVAS_RED_PATH_UNKNOWN"
    assert bool(out.loc[0, "core_score_eligible"]) is False
    assert bool(out.loc[0, "legacy_physics_score_applicable"]) is False
    assert out.loc[0, "red_light_path_state"] == "RED_LIGHT_PATH_UNKNOWN"


def test_no_canvas_red_path_conflict_overrides_legacy_headline_without_claiming_open():
    red = pd.DataFrame([{
        "time": pd.Timestamp("2026-09-08T10:00:00Z"),
        "solar_altitude_deg": -0.5,
        "red_light_path_state": "RED_LIGHT_PATH_CONFLICT",
        "primary_red_light_path_state": "RED_LIGHT_PATH_CONFLICT",
        "extended_red_light_path_state": "RED_LIGHT_PATH_CONFLICT",
        "formation_context_state": "NO_CANVAS_RED_PATH_CONFLICT",
        "primary_canvas_state": "ABSENT",
        "extended_canvas_state": "ABSENT",
        "unused_red_light_potential": np.nan,
        "potential_scale_status": "CONTINUOUS_UNCALIBRATED_DIAGNOSTIC",
    }])
    legacy = pd.DataFrame([{
        "solar_altitude_deg": -0.5,
        "physics_score": 0.01,
        "data_completeness": 1.0,
        "core_score_eligible": True,
        "operational_decision": "UNKNOWN / DATA INCOMPLETE",
    }])
    out = apply_red_light_context_to_headline_summary(legacy, red)
    assert out.loc[0, "operational_decision"] == "NO_CANVAS_RED_PATH_CONFLICT"
    assert out.loc[0, "red_light_path_state"] == "RED_LIGHT_PATH_CONFLICT"


def test_zero_candidates_with_incomplete_cloud_geometry_is_not_no_canvas():
    refs = _red_reference_rows()
    refs["cloud_geometry_completeness"] = 0.7
    s = summarize_red_light_availability(refs, pd.DataFrame())
    r = s.iloc[0]
    assert r.primary_canvas_state == "UNKNOWN"
    assert r.extended_canvas_state == "UNKNOWN"
    assert r.formation_context_state == "CANVAS_AVAILABILITY_UNKNOWN"
    assert bool(r.unused_red_light_potential_applicable) is False


def test_no_canvas_red_path_unknown_still_preserves_no_canvas_headline():
    red = pd.DataFrame([{
        "solar_altitude_deg": 0.0,
        "formation_context_state": "NO_CANVAS_RED_PATH_UNKNOWN",
        "primary_canvas_state": "ABSENT",
        "extended_canvas_state": "ABSENT",
        "red_light_path_state": "RED_LIGHT_PATH_UNKNOWN",
        "potential_scale_status": "CONTINUOUS_UNCALIBRATED_DIAGNOSTIC",
    }])
    legacy = pd.DataFrame([{
        "solar_altitude_deg": 0.0,
        "physics_score": 0.02,
        "data_completeness": 0.5,
        "core_score_eligible": True,
        "operational_decision": "UNKNOWN / DATA INCOMPLETE",
    }])
    out = apply_red_light_context_to_headline_summary(legacy, red)
    assert out.loc[0, "operational_decision"] == "NO_CANVAS_RED_PATH_UNKNOWN"
    assert bool(out.loc[0, "core_score_eligible"]) is False
    assert bool(out.loc[0, "legacy_physics_score_applicable"]) is False
