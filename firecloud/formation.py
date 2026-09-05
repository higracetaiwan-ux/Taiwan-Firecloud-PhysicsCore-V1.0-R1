"""PhysicsCore V1.0 R4 Canvas optical response and Formation bridge.

R4 is deliberately conservative:
* it consumes the R3 CloudBaseIllumination contract and native target-cloud
  optical evidence;
* it does not resurrect Legacy distance weights or a single Physics Score;
* it never fabricates cloud optical depth from Cloud Fraction / RH / geometry;
* Tier-1 radiance is an uncalibrated single-scatter source-function proxy,
  retained wavelength-by-wavelength across 550/575/600/650/700/750 nm;
* when the R3 path is uncertain, Formation remains uncertain rather than using
  known-component transmission as if it were full illumination.

The Tier-1 proxy is only an R4 response foundation.  Multiple-scattering LUTs
and refined human-visible colour reconstruction remain separate later stages.
"""
from __future__ import annotations

import math
from typing import Iterable, Optional

import numpy as np
import pandas as pd

from .spectral_color import reconstruct_six_band_colour

from .contracts import (
    SIX_BAND_WAVELENGTHS_NM,
    CanvasCandidate,
    CloudScene,
    EvidenceState,
)


def _finite(v) -> bool:
    try:
        return bool(math.isfinite(float(v)))
    except Exception:
        return False


def _target_rt_row(
    spectral_voxels: pd.DataFrame,
    *,
    canvas_id: str,
    cloud_layer_id: str,
    distance_km: float,
    target_altitude_km: float,
) -> Optional[pd.Series]:
    """Select target-cloud optical evidence without changing CloudScene geometry."""
    if spectral_voxels is None or spectral_voxels.empty:
        return None
    g = spectral_voxels
    if "v1_canvas_id" in g.columns:
        c = g[g["v1_canvas_id"].astype(str) == str(canvas_id)]
        if not c.empty:
            g = c
    if "v1_cloud_layer_id" in g.columns:
        c = g[g["v1_cloud_layer_id"].astype(str) == str(cloud_layer_id)]
        if not c.empty:
            g = c
    if g.empty:
        return None
    if "distance_km" in g.columns:
        d = pd.to_numeric(g["distance_km"], errors="coerce")
        if d.notna().any():
            md = float((d - float(distance_km)).abs().min())
            g = g[(d - float(distance_km)).abs() <= md + 1e-9]
    if g.empty:
        return None
    for lo_name, hi_name in (("voxel_bottom_km", "voxel_top_km"),):
        if lo_name in g.columns and hi_name in g.columns:
            lo = pd.to_numeric(g[lo_name], errors="coerce")
            hi = pd.to_numeric(g[hi_name], errors="coerce")
            q = g[(lo <= float(target_altitude_km)) & (hi >= float(target_altitude_km))]
            if not q.empty:
                g = q
    if "voxel_center_km" in g.columns:
        z = pd.to_numeric(g["voxel_center_km"], errors="coerce")
        if z.notna().any():
            return g.loc[(z - float(target_altitude_km)).abs().idxmin()]
    return g.iloc[0]


def _target_vertical_tau(rtrow: Optional[pd.Series], target_evidence: EvidenceState, layer_cot: Optional[float] = None) -> Optional[float]:
    """Return target-cloud *vertical* optical-depth evidence, never geometry proxy."""
    if target_evidence in (EvidenceState.GEOMETRY_ONLY, EvidenceState.MISSING):
        return None
    if layer_cot is not None and _finite(layer_cot):
        return max(0.0, float(layer_cot))
    if rtrow is None:
        return None
    for name in ("vertical_cloud_optical_depth_estimate", "target_vertical_cloud_optical_depth"):
        v = rtrow.get(name, np.nan)
        if _finite(v):
            return max(0.0, float(v))
    return None


def _source_fraction_from_tau(tau: Optional[float]) -> Optional[float]:
    """Tier-1 single-scatter source fraction.

    1-exp(-tau) is used as the fraction of incident energy interacting with the
    cloud material, not as observer-path transmission.  It is therefore not a
    Beer-Lambert substitute for final visible radiance or multiple scattering.
    """
    if tau is None or not _finite(tau):
        return None
    return max(0.0, min(1.0, 1.0 - math.exp(-max(0.0, float(tau)))))


# Approximate CIE photopic V(lambda) values at the six retained channels.
# They are physical spectral sensitivity samples, not calibrated firecloud
# decision weights.  750 nm intentionally contributes negligibly to brightness.
_PHOTOPIC_V = {550: 0.995, 575: 0.952, 600: 0.631, 650: 0.107, 700: 0.0041, 750: 0.00012}


def _brightness_proxy(radiance: dict[int, Optional[float]]) -> Optional[float]:
    vals = []
    weights = []
    for wl in SIX_BAND_WAVELENGTHS_NM:
        v = radiance.get(int(wl))
        if not _finite(v):
            return None
        vals.append(float(v)); weights.append(float(_PHOTOPIC_V[int(wl)]))
    den = sum(weights)
    return float(sum(v*w for v, w in zip(vals, weights)) / den) if den > 0 else None


def _redness_proxy(radiance: dict[int, Optional[float]]) -> Optional[float]:
    """Uncalibrated warm/red spectral-shape proxy from retained bands only.

    No blue channel is invented.  750 nm is retained only as a low-weight
    deep-red-tail diagnostic, consistent with the frozen Stage-4 boundary.
    """
    if any(not _finite(radiance.get(int(wl))) for wl in SIX_BAND_WAVELENGTHS_NM):
        return None
    r = {int(k): float(v) for k, v in radiance.items() if _finite(v)}
    num = r[650] + r[700] + 0.10*r[750]
    den = r[550] + r[575] + r[600] + r[650] + r[700] + 0.10*r[750]
    if den <= 0:
        return 0.0
    return max(0.0, min(1.0, num / den))


def build_r4_formation_tables(
    *,
    scene: CloudScene,
    canvases: Iterable[CanvasCandidate],
    cloud_base_illumination: pd.DataFrame,
    spectral_voxels: pd.DataFrame,
    solar_altitude_deg: float,
    valid_time=None,
) -> dict[str, pd.DataFrame]:
    """Build CanvasRadiance and angle-level FormationResult audit tables.

    R4 intentionally leaves Formation numerical outputs Missing when the input
    optical path or target-cloud optical evidence is unresolved.  A known Earth
    shadow zero is the one case that can produce a known zero response without
    downstream optical data.
    """
    canvases = list(canvases)
    layer_by_id = {x.layer_id: x for x in scene.layers}
    illum_map = {}
    if cloud_base_illumination is not None and not cloud_base_illumination.empty:
        for _, row in cloud_base_illumination.iterrows():
            illum_map[str(row.get("canvas_id"))] = row

    rows: list[dict] = []
    for canvas in canvases:
        layer = layer_by_id.get(canvas.cloud_layer_id)
        if layer is None:
            continue
        il = illum_map.get(canvas.canvas_id)
        fsun = None
        illum_status = "NO_ILLUMINATION_EVIDENCE"
        if il is not None:
            if _finite(il.get("direct_solar_fraction", np.nan)):
                fsun = float(il.get("direct_solar_fraction"))
            illum_status = str(il.get("illumination_status", illum_status))
        rtrow = _target_rt_row(
            spectral_voxels,
            canvas_id=canvas.canvas_id,
            cloud_layer_id=canvas.cloud_layer_id,
            distance_km=canvas.distance_km,
            target_altitude_km=canvas.cloud_base_altitude_km,
        )
        target_tau = _target_vertical_tau(rtrow, layer.optical_evidence, layer.cot)
        source_fraction = _source_fraction_from_tau(target_tau)
        cf = float(layer.cloud_fraction) if _finite(layer.cloud_fraction) else None

        radiance: dict[int, Optional[float]] = {int(wl): None for wl in SIX_BAND_WAVELENGTHS_NM}
        if fsun is not None and fsun <= 0.0:
            for wl in SIX_BAND_WAVELENGTHS_NM:
                radiance[int(wl)] = 0.0
            response_status = "CONFIRMED_ZERO_EARTH_SHADOW"
            confirmed_area = 0.0
            uncertain_area = 0.0
        else:
            complete_illum = bool(il is not None and str(il.get("spectral_transmission_complete", "False")).lower() in ("true", "1"))
            if complete_illum and source_fraction is not None:
                for wl in SIX_BAND_WAVELENGTHS_NM:
                    base = il.get(f"relative_base_illumination_{int(wl)}nm", np.nan)
                    if _finite(base):
                        radiance[int(wl)] = max(0.0, float(base)) * source_fraction
                if all(_finite(radiance[int(wl)]) for wl in SIX_BAND_WAVELENGTHS_NM):
                    response_status = "READY_TIER1_UNCALIBRATED"
                    confirmed_area = (cf if cf is not None else None)
                    uncertain_area = 0.0 if cf is not None else None
                else:
                    response_status = "UNCERTAIN_SPECTRAL_ILLUMINATION"
                    confirmed_area = 0.0
                    uncertain_area = cf
            elif source_fraction is None:
                response_status = "UNCERTAIN_TARGET_CLOUD_OPTICS"
                confirmed_area = 0.0
                uncertain_area = cf
            else:
                response_status = "UNCERTAIN_ILLUMINATION_PATH"
                confirmed_area = 0.0
                uncertain_area = cf

        brightness = _brightness_proxy(radiance)
        redness = _redness_proxy(radiance)
        colour_diag = reconstruct_six_band_colour(radiance)
        row = {
            "time": valid_time,
            "solar_altitude_deg": float(solar_altitude_deg),
            "canvas_id": canvas.canvas_id,
            "cloud_layer_id": canvas.cloud_layer_id,
            "operational_domain": canvas.operational_domain.value,
            "distance_km": float(canvas.distance_km),
            "cloud_base_altitude_km": float(canvas.cloud_base_altitude_km),
            "cloud_fraction": cf,
            "phase": layer.phase,
            "target_optical_evidence": layer.optical_evidence.value,
            "target_vertical_cloud_optical_depth": target_tau,
            "target_cloud_cot_source": ("CLOUD_LAYER_NATIVE_CONDENSATE" if layer.cot is not None else "NO_RESOLVED_TARGET_COT"),
            "target_effective_radius_um": layer.effective_radius_um,
            "tier1_source_fraction": source_fraction,
            "rt_tier": "TIER1_FAST_SOURCE_PROXY",
            "response_status": response_status,
            "brightness": brightness,
            "redness": redness,
            "effective_illuminated_area_fraction": confirmed_area,
            "uncertain_area_fraction": uncertain_area,
            "texture_structure": None,
            "colour_method": "SIX_BAND_ONLY_NO_INVENTED_BLUE;PHOTOPIC_BRIGHTNESS_PROXY;UNCALIBRATED_REDNESS_PROXY",
            "cloud_type_multiplier": "NONE",
            **colour_diag,
        }
        for wl in SIX_BAND_WAVELENGTHS_NM:
            row[f"cloud_radiance_proxy_{int(wl)}nm"] = radiance[int(wl)]
        rows.append(row)

    canvas_df = pd.DataFrame(rows)
    if canvas_df.empty:
        formation = pd.DataFrame([{
            "time": valid_time, "solar_altitude_deg": float(solar_altitude_deg),
            "formation_state": "NO_CANVAS_EVIDENCE", "brightness": None,
            "redness": None, "effective_illuminated_area": None,
            "confirmed_canvas_count": 0, "uncertain_canvas_count": 0,
            "formation_confidence": "UNKNOWN", "rt_tier": "NONE",
        }])
        return {"canvas_radiance": canvas_df, "formation": formation, "spectral_colour": pd.DataFrame()}

    ready = canvas_df[canvas_df["response_status"] == "READY_TIER1_UNCALIBRATED"].copy()
    shadow_zero = canvas_df[canvas_df["response_status"] == "CONFIRMED_ZERO_EARTH_SHADOW"].copy()
    uncertain = canvas_df[canvas_df["response_status"].str.startswith("UNCERTAIN", na=False)].copy()

    if len(shadow_zero) == len(canvas_df):
        state = "NOT_FORMED_EARTH_SHADOW"
        b = 0.0; r = 0.0; area = 0.0; conf = "HIGH"
    elif not ready.empty:
        # Aggregate only physically confirmed Canvas responses.  No distance or
        # cloud-type photography weights are applied in Formation.
        a = pd.to_numeric(ready["effective_illuminated_area_fraction"], errors="coerce")
        w = a.fillna(0.0)
        if float(w.sum()) > 0:
            b = float(np.average(pd.to_numeric(ready["brightness"], errors="coerce"), weights=w))
            r = float(np.average(pd.to_numeric(ready["redness"], errors="coerce"), weights=w))
        else:
            b = float(pd.to_numeric(ready["brightness"], errors="coerce").mean())
            r = float(pd.to_numeric(ready["redness"], errors="coerce").mean())
        area = float(a.fillna(0.0).sum())
        state = "FORMATION_EVIDENCE_AVAILABLE"
        conf = "MEDIUM" if not uncertain.empty else "LOW"
    else:
        state = "UNCERTAIN_OPTICS"
        b = None; r = None; area = None; conf = "LOW" if not uncertain.empty else "UNKNOWN"

    formation = pd.DataFrame([{
        "time": valid_time,
        "solar_altitude_deg": float(solar_altitude_deg),
        "formation_state": state,
        "brightness": b,
        "redness": r,
        "effective_illuminated_area": area,
        "confirmed_canvas_count": int(len(ready)),
        "earth_shadow_zero_canvas_count": int(len(shadow_zero)),
        "uncertain_canvas_count": int(len(uncertain)),
        "total_canvas_count": int(len(canvas_df)),
        "formation_confidence": conf,
        "rt_tier": "TIER1_FAST_SOURCE_PROXY",
        "aggregation_note": "NO_DISTANCE_WEIGHT;NO_CLOUD_TYPE_MULTIPLIER;NO_SINGLE_FORMATION_SCORE",
    }])
    colour_cols = [c for c in ["time","solar_altitude_deg","canvas_id","cloud_layer_id","response_status","brightness","redness","spectral_colour_status","cie_X_truncated","cie_Y_truncated","cie_Z_truncated","cie_x_truncated","cie_y_truncated","deep_red_tail_fraction_750","warm_red_fraction_650_750","spectral_centroid_nm","spectral_peak_wavelength_nm_diagnostic","colour_reconstruction_method"] if c in canvas_df.columns]
    spectral_colour = canvas_df[colour_cols].copy() if colour_cols else pd.DataFrame()
    return {"canvas_radiance": canvas_df, "formation": formation, "spectral_colour": spectral_colour}
