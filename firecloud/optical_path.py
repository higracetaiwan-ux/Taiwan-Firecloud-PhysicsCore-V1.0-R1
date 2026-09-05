"""PhysicsCore V1.0 R3 Canvas-specific optical-path bridge.

R3 connects the frozen V1 geometry contracts to the existing route-resolved
spectral RT evidence without reviving the V8 global completeness gate.

Important boundary:
* cloud/ray intersections are derived from ``CloudScene`` native-layer geometry;
* interpolated legacy RT voxels may supply optical evidence only and are labelled
  ``LEGACY_RT_EVIDENCE_BRIDGE_R3``;
* a missing gas/aerosol/cloud/precipitation component remains Missing and only
  contaminates outputs that depend on it;
* precipitation-volume RT is intentionally not fabricated in R3.  Until the
  dedicated precipitation module is connected, a fully transmissive path cannot
  be claimed solely because the other components are known.
"""
from __future__ import annotations

import math
from dataclasses import asdict
from typing import Iterable, Optional

import numpy as np
import pandas as pd

from .contracts import (
    SIX_BAND_WAVELENGTHS_NM,
    BoundLevel,
    CanvasCandidate,
    CloudBaseIllumination,
    CloudScene,
    EvidenceState,
    GeometryConfidence,
    OpticalPathResult,
    PredictionUncertainty,
    SpectralOpticalPath,
)
from .geometry import ray_altitude_km_at_surface_distance


def _finite(v) -> bool:
    try:
        return bool(math.isfinite(float(v)))
    except Exception:
        return False


def _direction_match(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(float(a) - float(b)) <= float(tol)


def build_ray_cloud_intersections(
    scene: CloudScene,
    canvases: Iterable[CanvasCandidate],
    *,
    solar_altitude_deg: float,
    earth_radius_km: float,
) -> pd.DataFrame:
    """Intersect each Canvas-specific Sun→CloudBase ray with native CloudLayers.

    No fixed Corridor/REZ distance band is consulted.  A cloud can affect a
    Canvas only if it lies sunward on that Canvas direction and the actual ray
    altitude crosses the native layer vertical support.
    """
    layer_by_id = {x.layer_id: x for x in scene.layers}
    rows: list[dict] = []
    for canvas in canvases:
        target = layer_by_id.get(canvas.cloud_layer_id)
        if target is None:
            continue
        for layer in scene.layers:
            if not _direction_match(layer.direction_offset_deg, target.direction_offset_deg):
                continue
            # Sunward route starts at the Canvas.  The target itself is retained
            # explicitly as TARGET_CANVAS, not counted as an upstream blocker.
            if float(layer.distance_km) + 1e-9 < float(canvas.distance_km):
                continue
            if layer.layer_id == canvas.cloud_layer_id:
                rows.append({
                    "canvas_id": canvas.canvas_id,
                    "cloud_layer_id": layer.layer_id,
                    "intersection_role": "TARGET_CANVAS",
                    "direction_offset_deg": layer.direction_offset_deg,
                    "distance_km": layer.distance_km,
                    "ray_altitude_km": canvas.cloud_base_altitude_km,
                    "layer_base_km": layer.z_base_km,
                    "layer_top_km": layer.z_top_km,
                    "intersects": True,
                    "geometry_confidence": layer.geometry_confidence.value,
                    "optical_evidence": layer.optical_evidence.value,
                    "geometry_source": layer.geometry_source,
                })
                continue
            z = ray_altitude_km_at_surface_distance(
                canvas.distance_km,
                canvas.cloud_base_altitude_km,
                float(layer.distance_km),
                float(solar_altitude_deg),
                float(earth_radius_km),
            )
            hit = bool(
                z is not None and _finite(z)
                and float(layer.z_base_km) - 1e-9 <= float(z) <= float(layer.z_top_km) + 1e-9
            )
            if hit:
                rows.append({
                    "canvas_id": canvas.canvas_id,
                    "cloud_layer_id": layer.layer_id,
                    "intersection_role": "UPSTREAM_CLOUD_INTERSECTION",
                    "direction_offset_deg": layer.direction_offset_deg,
                    "distance_km": layer.distance_km,
                    "ray_altitude_km": float(z),
                    "layer_base_km": layer.z_base_km,
                    "layer_top_km": layer.z_top_km,
                    "intersects": True,
                    "geometry_confidence": layer.geometry_confidence.value,
                    "optical_evidence": layer.optical_evidence.value,
                    "geometry_source": layer.geometry_source,
                })
    return pd.DataFrame(rows)


def _target_rt_row(
    spectral_voxels: pd.DataFrame,
    *,
    direction_offset_deg: float,
    distance_km: float,
    target_altitude_km: float,
) -> Optional[pd.Series]:
    """Select the closest existing RT evidence row for a Canvas base.

    The selected row is *optical evidence only*.  Its interpolated voxel geometry
    is never used to create or alter CloudScene native geometry.
    """
    if spectral_voxels is None or spectral_voxels.empty:
        return None
    g = spectral_voxels.copy()
    if "direction_offset_deg" in g:
        d = pd.to_numeric(g["direction_offset_deg"], errors="coerce")
        g = g[np.isclose(d, float(direction_offset_deg), atol=1e-6, equal_nan=False)]
    if g.empty:
        return None
    if "distance_km" in g:
        dist = pd.to_numeric(g["distance_km"], errors="coerce")
        if dist.notna().any():
            mind = float((dist - float(distance_km)).abs().min())
            g = g[(dist - float(distance_km)).abs() <= mind + 1e-9]
    if g.empty:
        return None
    if {"voxel_bottom_km", "voxel_top_km"}.issubset(g.columns):
        lo = pd.to_numeric(g["voxel_bottom_km"], errors="coerce")
        hi = pd.to_numeric(g["voxel_top_km"], errors="coerce")
        contain = g[(lo <= float(target_altitude_km)) & (hi >= float(target_altitude_km))]
        if not contain.empty:
            g = contain
    center_col = "voxel_center_km" if "voxel_center_km" in g.columns else "altitude_agl_km"
    if center_col in g:
        center = pd.to_numeric(g[center_col], errors="coerce")
        if center.notna().any():
            return g.loc[(center - float(target_altitude_km)).abs().idxmin()]
    return g.iloc[0]


def _component_tau(row: Optional[pd.Series], name: str, wl: int) -> Optional[float]:
    if row is None:
        return None
    v = row.get(f"{name}_tau_{wl}nm", np.nan)
    if _finite(v):
        return max(0.0, float(v))
    return None


def _cloud_tau(row: Optional[pd.Series], wl: int) -> Optional[float]:
    if row is None:
        return None
    # Current bulk cloud extinction is effectively grey across this diagnostic
    # visible range.  We retain the explicit per-wavelength field in the V1
    # contract while preserving this R3 provenance.
    v = row.get(f"cloud_tau_{wl}nm", np.nan)
    if not _finite(v):
        v = row.get("slant_cloud_optical_depth_estimate", np.nan)
    if _finite(v):
        return max(0.0, float(v))
    t = row.get(f"cloud_transmission_{wl}nm", np.nan)
    if _finite(t) and 0.0 < float(t) <= 1.0:
        return max(0.0, -math.log(float(t)))
    if _finite(t) and float(t) == 1.0:
        return 0.0
    return None


def build_r3_optical_tables(
    *,
    scene: CloudScene,
    canvases: Iterable[CanvasCandidate],
    direct_solar: pd.DataFrame,
    solar_rays: pd.DataFrame,
    spectral_voxels: pd.DataFrame,
    solar_altitude_deg: float,
    earth_radius_km: float,
    valid_time=None,
) -> dict[str, pd.DataFrame]:
    """Build R3 ray-cloud, six-band path, illumination and uncertainty tables."""
    canvases = list(canvases)
    layer_by_id = {x.layer_id: x for x in scene.layers}
    inter = build_ray_cloud_intersections(
        scene, canvases, solar_altitude_deg=solar_altitude_deg, earth_radius_km=earth_radius_km,
    )
    if not inter.empty:
        inter.insert(0, "time", valid_time)
        inter.insert(1, "solar_altitude_deg", float(solar_altitude_deg))

    direct_map = {}
    if direct_solar is not None and not direct_solar.empty:
        for _, r in direct_solar.iterrows():
            direct_map[str(r.get("canvas_id"))] = r

    optical_rows: list[dict] = []
    illum_rows: list[dict] = []
    uncertainty_rows: list[dict] = []
    bottleneck_rows: list[dict] = []

    for canvas in canvases:
        target = layer_by_id.get(canvas.cloud_layer_id)
        if target is None:
            continue
        rtrow = _target_rt_row(
            spectral_voxels,
            direction_offset_deg=target.direction_offset_deg,
            distance_km=canvas.distance_km,
            target_altitude_km=canvas.cloud_base_altitude_km,
        )
        dsrow = direct_map.get(canvas.canvas_id)
        fsun = float(dsrow.get("direct_solar_fraction", np.nan)) if dsrow is not None and _finite(dsrow.get("direct_solar_fraction", np.nan)) else None
        canvas_inter = inter[(inter["canvas_id"] == canvas.canvas_id) & (inter["intersection_role"] == "UPSTREAM_CLOUD_INTERSECTION")] if not inter.empty else pd.DataFrame()
        unknown_cloud_intersections = False
        if not canvas_inter.empty:
            unknown_cloud_intersections = canvas_inter["optical_evidence"].astype(str).isin(["GEOMETRY_ONLY", "MISSING", "PARTIAL_OPTICS"]).any()

        known_trans: dict[int, Optional[float]] = {}
        relative_illum: dict[int, Optional[float]] = {}
        for wl in SIX_BAND_WAVELENGTHS_NM:
            tau_g = _component_tau(rtrow, "gas", wl)
            tau_a = _component_tau(rtrow, "aerosol", wl)
            tau_c = _cloud_tau(rtrow, wl)
            tau_p = None  # dedicated precipitation-volume RT is not connected in R3
            known = [x for x in (tau_g, tau_a, tau_c) if x is not None]
            partial_tau = float(sum(known)) if known else None
            partial_t = math.exp(-partial_tau) if partial_tau is not None else None

            # Full Stage-2 tau_total requires precipitation-path evidence too.
            # R3 deliberately does not assume tau_precip=0 from missing 3-D rain.
            tau_total = None
            trans = None
            missing_parts = []
            if tau_g is None: missing_parts.append("GAS")
            if tau_a is None: missing_parts.append("AEROSOL")
            if tau_c is None or unknown_cloud_intersections: missing_parts.append("CLOUD")
            missing_parts.append("PRECIP_NOT_CONNECTED_R3")

            if fsun is not None and fsun <= 0.0:
                # Earth shadow makes delivered direct illumination exactly zero
                # even when downstream extinction is unknown.
                rel = 0.0
                status = "EARTH_SHADOWED_KNOWN_ZERO"
            else:
                rel = None
                status = "UNCERTAIN_OPTICAL_PATH"
            known_trans[int(wl)] = trans
            relative_illum[int(wl)] = rel

            if not missing_parts:
                ev = EvidenceState.FULL
                bl = BoundLevel.FULL_RT
            elif partial_tau is not None:
                ev = EvidenceState.PARTIAL_OPTICS
                bl = BoundLevel.ONE_SIDED_CONSTRAINT
            else:
                ev = EvidenceState.MISSING
                bl = BoundLevel.UNBOUNDED

            optical_rows.append({
                "time": valid_time,
                "solar_altitude_deg": float(solar_altitude_deg),
                "canvas_id": canvas.canvas_id,
                "cloud_layer_id": canvas.cloud_layer_id,
                "wavelength_nm": int(wl),
                "tau_gas": tau_g,
                "tau_aerosol": tau_a,
                "tau_cloud": tau_c,
                "tau_precip": tau_p,
                "known_component_tau": partial_tau,
                "known_component_transmission": partial_t,
                "tau_total": tau_total,
                "transmission": trans,
                "direct_solar_fraction": fsun,
                "relative_base_illumination": rel,
                "evidence_state": ev.value,
                "bound_level": int(bl.value),
                "missing_components": ";".join(missing_parts),
                "critical_path_status": "UNCERTAIN_OPTICS" if ev != EvidenceState.FULL else "FULL_RT",
                "rt_evidence_source": "LEGACY_RT_EVIDENCE_BRIDGE_R3" if rtrow is not None else "NO_RT_EVIDENCE",
                "upstream_cloud_intersection_count": int(len(canvas_inter)),
                "unknown_upstream_cloud_optics": bool(unknown_cloud_intersections),
                "optical_bottleneck_segment_id": None,
            })

            if ev != EvidenceState.FULL:
                uncertainty_rows.append({
                    "time": valid_time,
                    "solar_altitude_deg": float(solar_altitude_deg),
                    "canvas_id": canvas.canvas_id,
                    "wavelength_nm": int(wl),
                    "dependency": "SPECTRAL_OPTICAL_PATH",
                    "evidence_state": ev.value,
                    "bound_level": int(bl.value),
                    "criticality": "HIGH",
                    "affected_outputs": "CloudBaseIllumination,Formation",
                    "reason": ";".join(missing_parts) or "OPTICAL_EVIDENCE_PARTIAL",
                })

        if fsun is None:
            illum_status = "DIRECT_SOLAR_UNKNOWN"
        elif fsun <= 0.0:
            illum_status = "CONFIRMED_NOT_ILLUMINATED_EARTH_SHADOW"
        else:
            illum_status = "UNCERTAIN_OPTICS"  # until full four-component path exists
        illum_rows.append({
            "time": valid_time,
            "solar_altitude_deg": float(solar_altitude_deg),
            "canvas_id": canvas.canvas_id,
            "cloud_layer_id": canvas.cloud_layer_id,
            "direct_solar_fraction": fsun,
            "illumination_status": illum_status,
            "confirmed_illuminated": False,
            "confirmed_not_illuminated": bool(fsun is not None and fsun <= 0.0),
            "uncertain_illumination": bool(fsun is None or fsun > 0.0),
            "spectral_transmission_complete": False,
            "confidence": canvas.geometry_confidence.value,
            **{f"transmission_{wl}nm": known_trans[int(wl)] for wl in SIX_BAND_WAVELENGTHS_NM},
            **{f"relative_base_illumination_{wl}nm": relative_illum[int(wl)] for wl in SIX_BAND_WAVELENGTHS_NM},
        })

        bottleneck_rows.append({
            "time": valid_time,
            "solar_altitude_deg": float(solar_altitude_deg),
            "canvas_id": canvas.canvas_id,
            "optical_bottleneck_status": "UNRESOLVED_COMPONENT_OPTICS",
            "segment_id": None,
            "reason": "R3_HAS_NO_SEGMENT_RESOLVED_FULL_FOUR_COMPONENT_TAU",
        })

    return {
        "ray_cloud_intersections": inter,
        "spectral_optical_paths": pd.DataFrame(optical_rows),
        "cloud_base_illumination": pd.DataFrame(illum_rows),
        "uncertainty": pd.DataFrame(uncertainty_rows),
        "optical_bottlenecks": pd.DataFrame(bottleneck_rows),
    }
