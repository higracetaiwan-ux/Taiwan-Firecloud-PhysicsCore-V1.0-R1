import numpy as np
import pandas as pd

from firecloud.contracts import (
    CanvasCandidate, CanvasDomain, CloudFractionState, CloudLayer, CloudScene,
    EvidenceState, GeometryConfidence, SIX_BAND_WAVELENGTHS_NM,
)
from firecloud.optical_path import build_ray_cloud_intersections, build_r3_optical_tables
from firecloud.spectral_rt import build_spectral_rt
from firecloud.case_integrity import build_analysis_integrity_audit


def _layer(name, d, z0, z1, *, cot=None, consistency="CONSISTENT_CLOUD", cf=0.8):
    return CloudLayer(
        layer_id=name,
        direction_offset_deg=0.0,
        distance_km=float(d),
        z_base_km=float(z0),
        z_top_km=float(z1),
        cloud_fraction_state=CloudFractionState.CLOUD_OCCUPIED,
        cloud_fraction=float(cf),
        liquid_condensate_kgkg=(1e-5 if cot is not None else 0.0),
        ice_condensate_kgkg=0.0,
        phase="LIQUID" if cot is not None else "UNKNOWN",
        effective_radius_um=10.0 if cot is not None else None,
        cot=cot,
        geometry_confidence=GeometryConfidence.HIGH,
        optical_evidence=(EvidenceState.FULL if cot is not None else EvidenceState.GEOMETRY_ONLY),
        evidence_consistency=consistency,
        geometry_source="NATIVE_MODEL_LEVELS",
    )


def _canvas():
    return CanvasCandidate(
        canvas_id="canvas::target",
        cloud_layer_id="target",
        latitude=24.0,
        longitude=121.0,
        cloud_base_altitude_km=5.0,
        distance_km=20.0,
        azimuth_deg=270.0,
        operational_domain=CanvasDomain.PRIMARY_CANVAS_0_40,
        geometry_confidence=GeometryConfidence.HIGH,
    )


def _spectral_row():
    r={"direction_offset_deg":0.0,"distance_km":20.0,"voxel_center_km":5.0}
    for wl in SIX_BAND_WAVELENGTHS_NM:
        r[f"gas_tau_{wl}nm"]=0.1
        r[f"aerosol_tau_{wl}nm"]=0.05
    return pd.DataFrame([r])


def _precip(c):
    return pd.DataFrame([{
        "canvas_id":c.canvas_id,
        "status":"PRECIPITATION_OPTICS_RESOLVED",
        **{f"tau_precip_{wl}nm":0.0 for wl in SIX_BAND_WAVELENGTHS_NM},
    }])


def test_cf_cloud_condensate_zero_is_direct_evidence_conflict_not_generic_missing():
    scene=CloudScene(
        valid_time=None,
        layers=(
            _layer("target",20,4.8,5.2,cot=0.8),
            _layer("blocker",40,5.0,6.0,cot=None,consistency="CF_CLOUD_CONDENSATE_ZERO"),
        ),
        geometry_completeness=1.0,
        optics_completeness=0.5,
    )
    c=_canvas()
    inter=build_ray_cloud_intersections(scene,[c],solar_altitude_deg=0.0,earth_radius_km=6371.0)
    up=inter[inter.intersection_role.eq("UPSTREAM_CLOUD_INTERSECTION")]
    assert len(up)==1
    assert up.iloc[0].cloud_blocker_evidence_state == "DIRECT_EVIDENCE_CONFLICT"
    assert up.iloc[0].cloud_blocker_unresolved_reason == "CF_CLOUD_CONDENSATE_ZERO"

    out=build_r3_optical_tables(
        scene=scene,canvases=[c],direct_solar=pd.DataFrame([{"canvas_id":c.canvas_id,"direct_solar_fraction":1.0}]),
        solar_rays=pd.DataFrame(),spectral_voxels=_spectral_row(),solar_altitude_deg=0.0,earth_radius_km=6371.0,
        precipitation_path_evidence=_precip(c),
    )
    p=out["spectral_optical_paths"]
    assert p.critical_path_status.eq("DIRECT_CLOUD_EVIDENCE_CONFLICT").all()
    assert p.missing_components.str.contains("CLOUD_EVIDENCE_CONFLICT", regex=False).all()
    assert p.tau_cloud.isna().all()
    assert p.tau_cloud_lower_bound.eq(0.0).all()
    assert p.cloud_conflict_intersection_count.eq(1).all()
    assert p.cloud_path_evidence_state.eq("DIRECT_EVIDENCE_CONFLICT").all()


def test_resolved_vertical_cot_without_horizontal_support_is_not_promoted_to_full_path():
    scene=CloudScene(
        valid_time=None,
        layers=(
            _layer("target",20,4.8,5.2,cot=0.8),
            _layer("blocker",40,5.0,6.0,cot=1.2,consistency="CONSISTENT_CLOUD"),
        ),
        geometry_completeness=1.0,
        optics_completeness=1.0,
    )
    c=_canvas()
    out=build_r3_optical_tables(
        scene=scene,canvases=[c],direct_solar=pd.DataFrame([{"canvas_id":c.canvas_id,"direct_solar_fraction":1.0}]),
        solar_rays=pd.DataFrame(),spectral_voxels=_spectral_row(),solar_altitude_deg=0.0,earth_radius_km=6371.0,
        precipitation_path_evidence=_precip(c),
    )
    p=out["spectral_optical_paths"]
    assert p.critical_path_status.eq("CLOUD_HORIZONTAL_SUPPORT_UNRESOLVED").all()
    assert p.missing_components.str.contains("CLOUD_HORIZONTAL_SUPPORT_UNRESOLVED", regex=False).all()
    assert p.tau_cloud.isna().all()


def test_native_cloud_slant_tau_is_public_only_when_native_path_complete():
    base={
        "point_id":"p1","solar_altitude_deg":-1.0,"direction_offset_deg":0.0,"distance_km":20.0,
        "band":"0-40 km Primary Canvas","slant_cloud_optical_depth_estimate":0.5,
        "geometric_illuminated_fraction":1.0,"cloud_fraction_used":0.8,
        "upstream_path_checked":True,"upstream_path_state":"UPSTREAM_PATH_PARTIAL_UNKNOWN",
        "native_ray_path_completeness":0.8,
    }
    out=build_spectral_rt(pd.DataFrame([base]),-1.0,aerosol_snapshot=pd.DataFrame(),angstrom_exponent=None)
    assert bool(out.loc[0,"cloud_rt_native_path_complete"]) is False
    assert np.isnan(out.loc[0,"cloud_transmission_550nm"])
    assert out.loc[0,"cloud_rt_native_known_tau_lower_bound"] == 0.5
    assert "CLOUD_NATIVE_PATH_MISSING_OR_PARTIAL" in out.loc[0,"spectral_rt_quality"]


def test_integrity_detects_full_rt_completeness_divergence_from_v1_path():
    spectral=pd.DataFrame([
        {"solar_altitude_deg":-1.0,"direct_solar_fraction":1.0,"critical_path_status":"FULL_RT"},
        {"solar_altitude_deg":-1.0,"direct_solar_fraction":1.0,"critical_path_status":"DIRECT_CLOUD_EVIDENCE_CONFLICT"},
    ])
    comp=pd.DataFrame([
        {"solar_altitude_deg":-1.0,"layer":"FULL_SPECTRAL_RT","completeness":1.0}
    ])
    # Populate the minimum structural tables so the audit runs; this test only
    # inspects the dedicated R5.7.25 consistency check.
    result={
        "route_points":pd.DataFrame([{"distance_km":0.0}]),
        "hourly_raw":pd.DataFrame([{"x":1}]),
        "v1_spectral_optical_paths":spectral,
        "physics_data_completeness":comp,
        "v1_formation":pd.DataFrame([{"x":1}]),
        "performance_diagnostics":pd.DataFrame([{"x":1}]),
        "v1_canvas_candidates":pd.DataFrame([{"canvas_id":"c"}]),
    }
    audit=build_analysis_integrity_audit(result)
    row=audit[audit.check_id.eq("FULL_RT_COMPLETENESS_V1_PATH_CONSISTENCY")].iloc[0]
    assert row.status == "FAIL"


def test_v1_canvas_direct_solar_is_bound_to_native_rt_sampling_target():
    from firecloud.model import _bind_v1_direct_solar_to_rt_targets

    target=pd.DataFrame([{
        "v1_canvas_id":"canvas::target",
        "geometric_illuminated_fraction":0.0,
        "direction_offset_deg":0.0,
        "distance_km":20.0,
        "voxel_center_km":5.0,
    }])
    direct=pd.DataFrame([{
        "canvas_id":"canvas::target",
        "direct_solar_fraction":0.125,
        "solar_disk_visible_fraction":0.125,
    }])
    out=_bind_v1_direct_solar_to_rt_targets(target,direct)
    assert out.loc[0,"v1_direct_solar_fraction"] == 0.125
    assert out.loc[0,"v1_solar_disk_visible_fraction"] == 0.125
    # The native voxel-centre diagnostic is intentionally preserved and may differ.
    assert out.loc[0,"geometric_illuminated_fraction"] == 0.0


def test_gas_rt_applicability_prefers_v1_canvas_direct_solar_over_voxel_centre_geometry():
    from firecloud.gas_rt import integrate_gas_sun_to_targets

    target=pd.DataFrame([{
        "direction_offset_deg":0.0,
        "distance_km":20.0,
        "voxel_center_km":5.0,
        "geometric_illuminated_fraction":0.0,
        "v1_direct_solar_fraction":0.125,
    }])
    # An empty gas profile intentionally leaves the science payload missing, but
    # applicability is decided before that failure and must follow the V1 Canvas.
    out=integrate_gas_sun_to_targets(target,pd.DataFrame(),-2.0)
    assert bool(out.loc[0,"rt_applicable_direct_solar"]) is True


def test_spectral_rt_applicability_prefers_v1_canvas_direct_solar_over_voxel_centre_geometry():
    base={
        "point_id":"p1","solar_altitude_deg":-2.0,"direction_offset_deg":0.0,"distance_km":20.0,
        "band":"0-40 km Primary Canvas","slant_cloud_optical_depth_estimate":0.0,
        "geometric_illuminated_fraction":0.0,"v1_direct_solar_fraction":0.125,
        "cloud_fraction_used":0.8,"upstream_path_checked":True,
        "upstream_path_state":"UPSTREAM_PATH_CHECKED","native_ray_path_completeness":1.0,
    }
    out=build_spectral_rt(pd.DataFrame([base]),-2.0,aerosol_snapshot=pd.DataFrame(),angstrom_exponent=None)
    assert bool(out.loc[0,"rt_applicable_direct_solar"]) is True
    # No aerosol/gas is fabricated; the point is that this is a required RT
    # target rather than being incorrectly treated as not applicable.
    assert out.loc[0,"spectral_rt_missing_cause"] != ""
