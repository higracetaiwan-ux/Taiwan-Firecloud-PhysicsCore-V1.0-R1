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




def _vertical_overlap(a, b, minimum_km: float = 0.05) -> bool:
    return min(float(a.z_top_km), float(b.z_top_km)) - max(float(a.z_base_km), float(b.z_base_km)) >= float(minimum_km)

def _native_horizontal_support(scene: CloudScene) -> dict[str, dict]:
    """Infer auditable horizontal support only from adjacent native-condensate columns.

    R4.2 never equates the sampling step with cloud width.  A finite support
    interval is created only when the same vertically-overlapping cloud is backed
    by native optical evidence at the immediately adjacent sampled column on BOTH
    sides.  The support boundaries are midpoints between those evidence-bearing
    columns and are tagged as a derived multi-column continuity inference.
    """
    out = {}
    by_dir = {}
    for layer in scene.layers:
        by_dir.setdefault(float(layer.direction_offset_deg), []).append(layer)
    for _off, layers in by_dir.items():
        distances = sorted({float(x.distance_km) for x in layers})
        layers_at = {d: [x for x in layers if abs(float(x.distance_km)-d) <= 1e-9] for d in distances}
        pos = {d:i for i,d in enumerate(distances)}
        for layer in layers:
            d=float(layer.distance_km); i=pos[d]
            rec={
                "horizontal_support_resolved": False,
                "support_start_km": None, "support_end_km": None,
                "support_source": "UNRESOLVED_SINGLE_COLUMN",
                "support_confidence": "UNKNOWN",
            }
            if layer.cot is None or not _finite(layer.cot) or layer.optical_evidence not in (EvidenceState.FULL, EvidenceState.PARTIAL_OPTICS):
                rec["support_source"] = "NO_NATIVE_OPTICAL_EVIDENCE"
                out[layer.layer_id]=rec; continue
            if i == 0 or i == len(distances)-1:
                rec["support_source"] = "ROUTE_EDGE_SUPPORT_UNRESOLVED"
                out[layer.layer_id]=rec; continue
            dl, dr = distances[i-1], distances[i+1]
            def neighbour_ok(dd):
                return any(
                    n.cot is not None and _finite(n.cot)
                    and n.optical_evidence in (EvidenceState.FULL, EvidenceState.PARTIAL_OPTICS)
                    and _vertical_overlap(layer, n)
                    for n in layers_at.get(dd, ())
                )
            if neighbour_ok(dl) and neighbour_ok(dr):
                rec.update({
                    "horizontal_support_resolved": True,
                    "support_start_km": 0.5*(dl+d),
                    "support_end_km": 0.5*(d+dr),
                    "support_source": "MULTICOLUMN_NATIVE_CONDENSATE_CONTINUITY",
                    "support_confidence": "MEDIUM",
                })
            else:
                rec["support_source"] = "ADJACENT_NATIVE_CONDENSATE_CONTINUITY_NOT_CONFIRMED"
            out[layer.layer_id]=rec
    return out

def _slant_intersection_through_supported_layer(canvas, layer, support: dict, solar_altitude_deg: float, earth_radius_km: float) -> tuple[bool, Optional[float], Optional[float]]:
    """Return (hit, slant_path_km, slant_tau) for a supported cloud prism."""
    if not support.get("horizontal_support_resolved"):
        return False, None, None
    a=max(float(canvas.distance_km), float(support["support_start_km"]))
    b=float(support["support_end_km"])
    if b <= a + 1e-9:
        return False, None, None
    # Numerical line integral along the exact spherical G0 ray geometry.  0.25 km
    # is integration resolution only; it is not a forecast/cloud sampling grid.
    n=max(2, int(math.ceil((b-a)/0.25))+1)
    ds=np.linspace(a,b,n)
    zs=np.array([ray_altitude_km_at_surface_distance(
        canvas.distance_km, canvas.cloud_base_altitude_km, float(d),
        float(solar_altitude_deg), float(earth_radius_km)) for d in ds], dtype=float)
    inside=np.isfinite(zs) & (zs >= float(layer.z_base_km)-1e-9) & (zs <= float(layer.z_top_km)+1e-9)
    if not inside.any():
        return False, 0.0, 0.0
    path=0.0
    for j in range(len(ds)-1):
        if inside[j] or inside[j+1]:
            dd=float(ds[j+1]-ds[j]); dz=float(zs[j+1]-zs[j]) if np.isfinite(zs[j:j+2]).all() else 0.0
            frac=1.0 if inside[j] and inside[j+1] else 0.5
            path += frac*math.hypot(dd,dz)
    thick=max(0.0,float(layer.z_top_km)-float(layer.z_base_km))
    if path <= 0.0 or thick <= 0.0 or layer.cot is None or not _finite(layer.cot):
        return bool(path>0.0), (path if path>0.0 else 0.0), None
    tau=max(0.0,float(layer.cot))*path/thick
    return True, float(path), float(tau)

def build_ray_cloud_intersections(
    scene: CloudScene,
    canvases: Iterable[CanvasCandidate],
    *,
    solar_altitude_deg: float,
    earth_radius_km: float,
) -> pd.DataFrame:
    """Intersect Canvas-specific rays with native CloudLayers.

    R4.3 keeps the R4.2 fail-closed horizontal-support rule but indexes native
    layers by direction/distance and caches centre-point ray altitudes.  The
    physics is unchanged: sampling spacing is never interpreted as cloud width,
    and slant COT is resolved only for native-condensate-supported cloud prisms.
    """
    layer_by_id = {x.layer_id: x for x in scene.layers}
    support_map = _native_horizontal_support(scene)

    # Spatial index: avoid scanning every CloudLayer for every Canvas.  Multiple
    # vertical layers may share one sampled distance, so preserve a list per node.
    by_direction: dict[float, dict[float, list]] = {}
    for layer in scene.layers:
        by_direction.setdefault(float(layer.direction_offset_deg), {}).setdefault(float(layer.distance_km), []).append(layer)
    sorted_distances = {off: sorted(nodes) for off, nodes in by_direction.items()}

    rows: list[dict] = []
    for canvas in canvases:
        target = layer_by_id.get(canvas.cloud_layer_id)
        if target is None:
            continue
        off = float(target.direction_offset_deg)
        nodes = by_direction.get(off, {})
        distances = sorted_distances.get(off, ())
        # The Sun->CloudBase ray extends away from the observer through distances
        # >= target Canvas distance in the current route convention.
        relevant_distances = [d for d in distances if d + 1e-9 >= float(canvas.distance_km)]
        centre_ray_altitude_cache: dict[float, Optional[float]] = {}

        for d in relevant_distances:
            for layer in nodes.get(d, ()):
                support = support_map.get(layer.layer_id, {})
                base_row={
                    "canvas_id": canvas.canvas_id, "cloud_layer_id": layer.layer_id,
                    "direction_offset_deg": layer.direction_offset_deg, "distance_km": layer.distance_km,
                    "layer_base_km": layer.z_base_km, "layer_top_km": layer.z_top_km,
                    "geometry_confidence": layer.geometry_confidence.value,
                    "optical_evidence": layer.optical_evidence.value, "layer_vertical_cot": layer.cot,
                    "layer_phase": layer.phase, "effective_radius_um": layer.effective_radius_um,
                    "geometry_source": layer.geometry_source,
                    **support,
                }
                if layer.layer_id == canvas.cloud_layer_id:
                    rows.append({**base_row, "intersection_role":"TARGET_CANVAS",
                        "ray_altitude_km":canvas.cloud_base_altitude_km, "intersects":True,
                        "slant_path_km":None, "slant_cloud_optical_depth":None,
                        "slant_optics_status":"TARGET_CLOUD_RESPONSE_NOT_PATH_BLOCKER"})
                    continue
                if support.get("horizontal_support_resolved"):
                    hit,path,tau=_slant_intersection_through_supported_layer(canvas, layer, support, solar_altitude_deg, earth_radius_km)
                    if hit:
                        mid=0.5*(float(support["support_start_km"])+float(support["support_end_km"]))
                        z=ray_altitude_km_at_surface_distance(canvas.distance_km,canvas.cloud_base_altitude_km,mid,solar_altitude_deg,earth_radius_km)
                        rows.append({**base_row, "intersection_role":"UPSTREAM_CLOUD_INTERSECTION",
                            "ray_altitude_km":z, "intersects":True, "slant_path_km":path,
                            "slant_cloud_optical_depth":tau,
                            "slant_optics_status":"RESOLVED_NATIVE_CONDENSATE_SLANT_RT" if tau is not None else "SLANT_GEOMETRY_RESOLVED_OPTICS_UNKNOWN"})
                    continue
                # No horizontal optical support: retain centre-point geometry hit only
                # as an uncertainty flag; do not fabricate slant path/tau. Cache the
                # ray altitude because all vertical layers at one sampled distance
                # share the same ray geometry.
                if d not in centre_ray_altitude_cache:
                    centre_ray_altitude_cache[d]=ray_altitude_km_at_surface_distance(
                        canvas.distance_km, canvas.cloud_base_altitude_km, d, solar_altitude_deg, earth_radius_km)
                z=centre_ray_altitude_cache[d]
                hit=bool(z is not None and _finite(z) and float(layer.z_base_km)-1e-9 <= float(z) <= float(layer.z_top_km)+1e-9)
                if hit:
                    rows.append({**base_row, "intersection_role":"UPSTREAM_CLOUD_INTERSECTION",
                        "ray_altitude_km":float(z), "intersects":True, "slant_path_km":None,
                        "slant_cloud_optical_depth":None, "slant_optics_status":"POTENTIAL_BLOCKER_HORIZONTAL_SUPPORT_UNKNOWN"})
    return pd.DataFrame(rows)


def build_native_condensate_support_diagnostics(
    scene: CloudScene, intersections: pd.DataFrame
) -> pd.DataFrame:
    """Compact R4.3 audit of native-condensate support and resolved slant RT.

    This table distinguishes absence of optical evidence from absence of a cloud.
    It is diagnostic/provenance only and never acts as a Physics score.
    """
    support = _native_horizontal_support(scene)
    layers = list(scene.layers)
    optical_layers = [x for x in layers if x.cot is not None and _finite(x.cot) and x.optical_evidence in (EvidenceState.FULL, EvidenceState.PARTIAL_OPTICS)]
    resolved_layers = [x for x in layers if support.get(x.layer_id,{}).get("horizontal_support_resolved")]
    inter = intersections if intersections is not None else pd.DataFrame()
    status = inter.get("slant_optics_status", pd.Series(dtype=str)).astype(str) if not inter.empty else pd.Series(dtype=str)
    return pd.DataFrame([{
        "cloud_layer_count": len(layers),
        "native_optical_layer_count": len(optical_layers),
        "horizontal_support_resolved_layer_count": len(resolved_layers),
        "upstream_intersection_count": int(inter.get("intersection_role", pd.Series(dtype=str)).eq("UPSTREAM_CLOUD_INTERSECTION").sum()) if not inter.empty else 0,
        "resolved_native_condensate_slant_intersection_count": int(status.eq("RESOLVED_NATIVE_CONDENSATE_SLANT_RT").sum()),
        "unknown_horizontal_support_intersection_count": int(status.eq("POTENTIAL_BLOCKER_HORIZONTAL_SUPPORT_UNKNOWN").sum()),
        "support_contract": "NATIVE_MULTICOLUMN_CONDENSATE_CONTINUITY_R4_3",
        "sampling_step_is_cloud_width": False,
    }])

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


def _cloud_tau(row: Optional[pd.Series], wl: int, *, optical_evidence: EvidenceState, layer_cot: Optional[float] = None) -> Optional[float]:
    # R3.1/R4.1: geometry evidence is never optical-clear evidence.  A target or
    # blocker reconstructed from cloud fraction/base/top only must keep tau_cloud
    # Unknown even when a legacy RT voxel happens to carry transmission=1.
    if optical_evidence in (EvidenceState.GEOMETRY_ONLY, EvidenceState.MISSING):
        return None
    # R4.1 prefers CloudLayer native-level optical evidence.  It is a vertical
    # target-COT estimate, not a slant blocker integral.  Upstream slant cloud
    # opacity remains unresolved until native horizontal support is available.
    if layer_cot is not None and _finite(layer_cot):
        return max(0.0, float(layer_cot))
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
    precipitation_path_evidence: Optional[pd.DataFrame] = None,
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
        resolved_upstream_cloud_tau = 0.0
        resolved_upstream_count = 0
        if not canvas_inter.empty:
            status = canvas_inter.get("slant_optics_status", pd.Series("", index=canvas_inter.index)).astype(str)
            tauvals = pd.to_numeric(canvas_inter.get("slant_cloud_optical_depth", pd.Series(np.nan, index=canvas_inter.index)), errors="coerce")
            resolved_mask = status.eq("RESOLVED_NATIVE_CONDENSATE_SLANT_RT") & tauvals.notna()
            resolved_upstream_count = int(resolved_mask.sum())
            resolved_upstream_cloud_tau = float(tauvals[resolved_mask].sum()) if resolved_upstream_count else 0.0
            # Any geometric blocker whose horizontal/optical support is unresolved
            # keeps the total cloud-path optical depth Unknown. PARTIAL optical
            # evidence may still be usable when its slant tau was resolved.
            unknown_cloud_intersections = bool((~resolved_mask).any())

        known_trans: dict[int, Optional[float]] = {}
        relative_illum: dict[int, Optional[float]] = {}
        for wl in SIX_BAND_WAVELENGTHS_NM:
            tau_g = _component_tau(rtrow, "gas", wl)
            tau_a = _component_tau(rtrow, "aerosol", wl)
            # Target COT belongs to Canvas response, not the Sun→CloudBase path.
            # Cloud-path tau is the sum of actual upstream slant intersections.
            if canvas_inter.empty:
                tau_c = 0.0 if scene.geometry_completeness == 1.0 else None
            elif unknown_cloud_intersections:
                tau_c = None
            else:
                tau_c = max(0.0, float(resolved_upstream_cloud_tau))
            # R3.1 precipitation branch is connected fail-closed.  Only an
            # explicit path optical-depth field can produce tau_precip. Surface
            # rain rate or cloud geometry alone never fabricates optical depth.
            tau_p = None
            precip_status = "PRECIPITATION_GEOMETRY_MISSING"
            if precipitation_path_evidence is not None and not precipitation_path_evidence.empty:
                pe = precipitation_path_evidence[precipitation_path_evidence.get("canvas_id", pd.Series(dtype=str)).astype(str) == str(canvas.canvas_id)]
                if not pe.empty:
                    prow = pe.iloc[0]
                    pv = prow.get(f"tau_precip_{wl}nm", np.nan)
                    if _finite(pv):
                        tau_p = max(0.0, float(pv)); precip_status = "PRECIPITATION_OPTICS_RESOLVED"
                    else:
                        precip_status = str(prow.get("status", "PRECIPITATION_OPTICS_UNKNOWN"))
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
            if tau_p is None: missing_parts.append(precip_status)

            if not missing_parts:
                # R4.3 closes the full-path bridge: when gas, aerosol, resolved
                # upstream cloud slant opacity and precipitation-path opacity are
                # all evidenced, compute the actual total optical depth and
                # transmission.  Earlier R3/R4 checkpoints intentionally left
                # these fields unset even when evidence became complete.
                tau_total = max(0.0, float(tau_g + tau_a + tau_c + tau_p))
                trans = math.exp(-tau_total)
                rel = (float(fsun) * trans) if fsun is not None else None
                status = "FULL_OPTICAL_PATH"
            elif fsun is not None and fsun <= 0.0:
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
                "critical_path_status": (
                    "POTENTIAL_BLOCKER_OPTICS_UNKNOWN" if unknown_cloud_intersections
                    else ("UNCERTAIN_OPTICS" if ev != EvidenceState.FULL else "FULL_RT")
                ),
                "rt_evidence_source": "LEGACY_RT_EVIDENCE_BRIDGE_R3" if rtrow is not None else "NO_RT_EVIDENCE",
                "upstream_cloud_intersection_count": int(len(canvas_inter)),
                "resolved_upstream_cloud_intersection_count": int(resolved_upstream_count),
                "resolved_upstream_cloud_tau": float(resolved_upstream_cloud_tau),
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
        _full_spectral = all(known_trans.get(int(wl)) is not None for wl in SIX_BAND_WAVELENGTHS_NM)
        if fsun is not None and fsun > 0.0 and _full_spectral:
            illum_status = "CONFIRMED_ILLUMINATED_FULL_PATH"
        illum_rows.append({
            "time": valid_time,
            "solar_altitude_deg": float(solar_altitude_deg),
            "canvas_id": canvas.canvas_id,
            "cloud_layer_id": canvas.cloud_layer_id,
            "direct_solar_fraction": fsun,
            "illumination_status": illum_status,
            "confirmed_illuminated": bool(fsun is not None and fsun > 0.0 and _full_spectral),
            "confirmed_not_illuminated": bool(fsun is not None and fsun <= 0.0),
            "uncertain_illumination": bool(fsun is None or (fsun > 0.0 and not _full_spectral)),
            "spectral_transmission_complete": bool(_full_spectral),
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

    support_cols = [c for c in [
        "time","solar_altitude_deg","cloud_layer_id","direction_offset_deg","distance_km",
        "layer_base_km","layer_top_km","optical_evidence","layer_vertical_cot",
        "horizontal_support_resolved","support_start_km","support_end_km",
        "support_source","support_confidence"
    ] if c in inter.columns]
    cloud_support = (inter[support_cols].drop_duplicates(subset=[c for c in ["time","solar_altitude_deg","cloud_layer_id"] if c in support_cols])
                     if support_cols else pd.DataFrame())
    native_support_diagnostics = build_native_condensate_support_diagnostics(scene, inter)
    if not native_support_diagnostics.empty:
        native_support_diagnostics.insert(0, "time", valid_time)
        native_support_diagnostics.insert(1, "solar_altitude_deg", float(solar_altitude_deg))
    return {
        "ray_cloud_intersections": inter,
        "cloud_horizontal_support": cloud_support,
        "native_condensate_support_diagnostics": native_support_diagnostics,
        "spectral_optical_paths": pd.DataFrame(optical_rows),
        "cloud_base_illumination": pd.DataFrame(illum_rows),
        "uncertainty": pd.DataFrame(uncertainty_rows),
        "optical_bottlenecks": pd.DataFrame(bottleneck_rows),
    }
