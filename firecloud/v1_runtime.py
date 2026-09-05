"""PhysicsCore V1.0 R2 runtime bridge.

This module turns native CloudScene evidence into Canvas-specific illumination
geometry without using the inherited V8 physics_score, fixed REZ score, or the
single global completeness gate.  R2 is deliberately geometry/illumination
foundation only; spectral optical-path and Formation are connected in later
checkpoints.
"""
from __future__ import annotations

from dataclasses import asdict
import math
from typing import Iterable
import pandas as pd

from .cloud_scene import build_cloud_scene_from_native_route
from .contracts import (
    CanvasCandidate, CanvasDomain, CloudScene, EvidenceState, GeometryConfidence,
    RefractionMode, SolarGeometryState, SolarRay, RaySegment,
)
from .geometry import destination_point, ray_altitude_km_at_surface_distance
from .illumination import direct_solar_state_g0


def canvas_domain(distance_km: float) -> CanvasDomain:
    d = float(distance_km)
    if 0.0 <= d <= 40.0:
        return CanvasDomain.PRIMARY_CANVAS_0_40
    if 40.0 < d <= 100.0:
        return CanvasDomain.EXTENDED_CANVAS_40_100
    return CanvasDomain.OTHER_DIAGNOSTIC


def build_canvas_candidates(
    scene: CloudScene,
    *,
    observer_lat: float,
    observer_lon: float,
    solar_azimuth_deg: float,
    earth_radius_km: float,
    max_canvas_distance_km: float = 100.0,
) -> list[CanvasCandidate]:
    """Create Canvas targets from native cloud layers only.

    Cloud type/coverage is not scored here.  A cloud layer inside the operational
    0-100 km Canvas domain is a geometric candidate; its physical response is a
    later Stage-3 concern.
    """
    out: list[CanvasCandidate] = []
    for layer in scene.layers:
        d = float(layer.distance_km)
        if d < 0.0 or d > float(max_canvas_distance_km):
            continue
        bearing = (float(solar_azimuth_deg) + float(layer.direction_offset_deg)) % 360.0
        lat, lon = destination_point(observer_lat, observer_lon, bearing, d, earth_radius_km)
        out.append(CanvasCandidate(
            canvas_id=f"canvas::{layer.layer_id}",
            cloud_layer_id=layer.layer_id,
            latitude=float(lat),
            longitude=float(lon),
            cloud_base_altitude_km=float(layer.z_base_km),
            distance_km=d,
            azimuth_deg=bearing,
            operational_domain=canvas_domain(d),
            geometry_confidence=layer.geometry_confidence,
            provenance=layer.provenance,
        ))
    return out


def solar_geometry_state_g0(solar_altitude_deg: float, solar_azimuth_deg: float) -> SolarGeometryState:
    a = float(solar_altitude_deg)
    return SolarGeometryState(
        solar_altitude_geometric_deg=a,
        solar_azimuth_deg=float(solar_azimuth_deg),
        solar_depression_deg=max(0.0, -a),
        refraction_mode_requested=RefractionMode.G0_GEOMETRIC,
        refraction_mode_used=RefractionMode.G0_GEOMETRIC,
        refraction_data_completeness="FULL_GEOMETRIC",
        refraction_fallback_reason=None,
        finite_solar_disk_enabled=True,
        solar_angular_diameter_deg=0.53,
    )


def build_canvas_solar_ray_g0(
    canvas: CanvasCandidate,
    *,
    solar_altitude_deg: float,
    observer_lat: float,
    observer_lon: float,
    earth_radius_km: float,
    route_end_km: float,
    step_km: float = 20.0,
) -> SolarRay:
    """Build a Canvas-specific Sun->CloudBase G0 ray.

    The ray begins at the Canvas cloud base and is sampled sunward.  Dynamic REZ
    is represented as the subset of sampled segments where the finite solar disk
    is geometrically visible (F_sun > 0).  This is a ray-derived diagnostic, not
    a score and not a fixed 350-440 km interval.
    """
    d0 = float(canvas.distance_km)
    dend = max(d0, float(route_end_km))
    step = max(1.0, float(step_km))
    distances = [d0]
    d = math.ceil((d0 + 1e-9) / step) * step
    if d <= d0 + 1e-9:
        d += step
    while d < dend - 1e-9:
        distances.append(float(d)); d += step
    if dend > d0 + 1e-9:
        distances.append(dend)

    segs: list[RaySegment] = []
    rez_ids: list[str] = []
    for i, (a, b) in enumerate(zip(distances[:-1], distances[1:])):
        mid = 0.5 * (a + b)
        z = ray_altitude_km_at_surface_distance(
            canvas.distance_km, canvas.cloud_base_altitude_km, mid,
            solar_altitude_deg, earth_radius_km,
        )
        if z is None or not math.isfinite(float(z)):
            continue
        lat, lon = destination_point(observer_lat, observer_lon, canvas.azimuth_deg, mid, earth_radius_km)
        f = direct_solar_state_g0(mid, float(z), solar_altitude_deg).direct_solar_fraction
        sid = f"{canvas.canvas_id}::seg{i:03d}"
        segs.append(RaySegment(
            segment_id=sid,
            start_distance_km=float(a),
            end_distance_km=float(b),
            midpoint_lat=float(lat), midpoint_lon=float(lon),
            midpoint_altitude_km=float(z), path_length_km=float(b-a),
            direct_solar_fraction=float(f), provenance=canvas.provenance,
        ))
        if f > 0.0:
            rez_ids.append(sid)

    return SolarRay(
        ray_id=f"ray::{canvas.canvas_id}::{float(solar_altitude_deg):+.1f}",
        canvas_id=canvas.canvas_id,
        solar_angle_deg=float(solar_altitude_deg),
        refraction_mode_used=RefractionMode.G0_GEOMETRIC,
        segments=tuple(segs),
        dynamic_rez_segment_ids=tuple(rez_ids),
    )


def build_r2_geometry_tables(
    route_at_time: pd.DataFrame,
    pressure_levels_hpa,
    *, observer_lat: float, observer_lon: float,
    solar_altitude_deg: float, solar_azimuth_deg: float,
    earth_radius_km: float, route_end_km: float, route_step_km: float,
    valid_time=None,
):
    """Return R2 CloudScene / Canvas / DirectSolar / Ray audit tables."""
    scene = build_cloud_scene_from_native_route(
        route_at_time, pressure_levels_hpa, valid_time=valid_time,
    )
    canvases = build_canvas_candidates(
        scene, observer_lat=observer_lat, observer_lon=observer_lon,
        solar_azimuth_deg=solar_azimuth_deg, earth_radius_km=earth_radius_km,
    )
    sg = solar_geometry_state_g0(solar_altitude_deg, solar_azimuth_deg)

    cloud_rows = []
    for x in scene.layers:
        r = asdict(x)
        r["solar_altitude_deg"] = float(solar_altitude_deg)
        r["time"] = valid_time
        r["cloud_fraction_state"] = x.cloud_fraction_state.value
        r["geometry_confidence"] = x.geometry_confidence.value
        r["optical_evidence"] = x.optical_evidence.value
        r["provenance"] = str(x.provenance)
        cloud_rows.append(r)

    canvas_rows=[]; direct_rows=[]; ray_rows=[]
    for c in canvases:
        ds = direct_solar_state_g0(c.distance_km, c.cloud_base_altitude_km, solar_altitude_deg)
        canvas_rows.append({
            "time": valid_time, "solar_altitude_deg": float(solar_altitude_deg),
            "canvas_id": c.canvas_id, "cloud_layer_id": c.cloud_layer_id,
            "latitude": c.latitude, "longitude": c.longitude,
            "cloud_base_altitude_km": c.cloud_base_altitude_km,
            "distance_km": c.distance_km, "azimuth_deg": c.azimuth_deg,
            "operational_domain": c.operational_domain.value,
            "geometry_confidence": c.geometry_confidence.value,
        })
        direct_rows.append({
            "time": valid_time, "solar_altitude_deg": float(solar_altitude_deg),
            "canvas_id": c.canvas_id,
            "direct_solar_fraction": ds.direct_solar_fraction,
            "solar_disk_visible_fraction": ds.solar_disk_visible_fraction,
            "shadow_diagnostic_height_km": ds.shadow_diagnostic_height_km,
            "ray_status": ds.ray_status,
            "refraction_mode_used": ds.refraction_mode_used.value,
            "confidence": ds.confidence.value,
        })
        ray = build_canvas_solar_ray_g0(
            c, solar_altitude_deg=solar_altitude_deg,
            observer_lat=observer_lat, observer_lon=observer_lon,
            earth_radius_km=earth_radius_km, route_end_km=route_end_km,
            step_km=route_step_km,
        )
        rez = set(ray.dynamic_rez_segment_ids)
        for s in ray.segments:
            ray_rows.append({
                "time": valid_time, "solar_altitude_deg": float(solar_altitude_deg),
                "ray_id": ray.ray_id, "canvas_id": ray.canvas_id,
                "segment_id": s.segment_id,
                "start_distance_km": s.start_distance_km,
                "end_distance_km": s.end_distance_km,
                "midpoint_lat": s.midpoint_lat, "midpoint_lon": s.midpoint_lon,
                "midpoint_altitude_km": s.midpoint_altitude_km,
                "path_length_km": s.path_length_km,
                "direct_solar_fraction": s.direct_solar_fraction,
                "dynamic_rez_segment": s.segment_id in rez,
                "refraction_mode_used": ray.refraction_mode_used.value,
            })

    # R2 evidence is deliberately dependency-specific. Missing aerosol/ozone is
    # not allowed to erase known CloudScene or direct-solar geometry.
    dep_rows = [
        {"time": valid_time, "solar_altitude_deg": float(solar_altitude_deg), "dependency":"CLOUD_GEOMETRY",
         "evidence_state": "FULL" if scene.geometry_completeness == 1.0 else ("PARTIAL_OPTICS" if (scene.geometry_completeness or 0)>0 else "MISSING"),
         "completeness": scene.geometry_completeness, "affected_outputs":"CanvasCandidate,RayIntersection", "criticality":"HIGH"},
        {"time": valid_time, "solar_altitude_deg": float(solar_altitude_deg), "dependency":"CLOUD_OPTICS",
         "evidence_state": "FULL" if scene.optics_completeness == 1.0 else ("PARTIAL_OPTICS" if (scene.optics_completeness or 0)>0 else "MISSING"),
         "completeness": scene.optics_completeness, "affected_outputs":"OpticalPath,Formation", "criticality":"HIGH"},
        {"time": valid_time, "solar_altitude_deg": float(solar_altitude_deg), "dependency":"DIRECT_SOLAR_GEOMETRY_G0",
         "evidence_state":"FULL", "completeness":1.0, "affected_outputs":"DirectSolarFraction,CloudBaseIllumination", "criticality":"HIGH"},
    ]
    sg_row = {
        "time": valid_time, "solar_altitude_deg": float(solar_altitude_deg),
        "solar_azimuth_deg": float(solar_azimuth_deg),
        "solar_depression_deg": sg.solar_depression_deg,
        "refraction_mode_requested": sg.refraction_mode_requested.value,
        "refraction_mode_used": sg.refraction_mode_used.value,
        "refraction_data_completeness": sg.refraction_data_completeness,
        "finite_solar_disk_enabled": sg.finite_solar_disk_enabled,
        "solar_angular_diameter_deg": sg.solar_angular_diameter_deg,
    }
    return {
        "scene": scene,
        "cloud_layers": pd.DataFrame(cloud_rows),
        "canvases": pd.DataFrame(canvas_rows),
        "direct_solar": pd.DataFrame(direct_rows),
        "solar_rays": pd.DataFrame(ray_rows),
        "dependency_status": pd.DataFrame(dep_rows),
        "solar_geometry": pd.DataFrame([sg_row]),
    }
