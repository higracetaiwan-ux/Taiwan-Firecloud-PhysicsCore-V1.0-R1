from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from datetime import date, datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, wait
import math
import os
import re
import threading
from time import perf_counter
import numpy as np
import pandas as pd

from .config import (
    CLOUD_LAYERS_KM, BANDS, ILLUMINATION_HEIGHTS_KM, ModelConfig,
    VOXEL_ALTITUDE_CENTERS_KM, VOXEL_VERTICAL_STEP_KM,
    PROFILE_CLOUD_OCCUPANCY_THRESHOLD, PROFILE_RH_SUPPORT_THRESHOLD_PCT,
    CLOUD_EXTINCTION_PROXY_PER_KM, RAY_HORIZONTAL_STEP_KM,
    horizontal_sampling_segment, adaptive_horizontal_distance_samples,
)
from .geometry import (
    destination_point,
    earth_shadow_min_altitude_km,
    cloud_layer_illuminated_fraction,
    ray_altitude_km_at_surface_distance,
    dynamic_rez_entry_distance_km,
    geometric_illumination_state,
)
from .solar import find_time_for_solar_altitude, solar_azimuth_deg
from .providers.openmeteo import (
    fetch_route_hourly, fetch_route_surface_hourly, fetch_route_pressure_hourly,
    interpolate_route_at_time, PRESSURE_LEVELS_HPA as GAS_PRESSURE_LEVELS_HPA,
)
from .providers.aerosol import fetch_route_aerosol, interpolate_route_aerosol_at_time
from .providers.cams_native import (
    fetch_route_native_aerosol_bundle, fetch_route_native_aerosol_bundle_timed, native_aerosol_provider_status, native_ozone_provider_status, resolve_cams_run_and_lead,
)
from .aerosol_physics import derive_route_spectral_aod
from .native_cloud import build_native_cloud_volume
from .cloud_optics import add_native_optical_properties
from .spectral_rt import build_spectral_rt, summarize_spectral_rt
from .gas_rt import build_gas_profile, hitran_backend_status, prepare_gas_rt_context
from .providers.gfs_native import fetch_route_native, merge_native_into_snapshot, resolve_run_and_lead, DEFAULT_PRESSURE_LEVELS_HPA, native_provider_status
from .v1_runtime import build_r2_geometry_tables
from .optical_path import build_r3_optical_tables
from .formation import build_r4_formation_tables
from .target_canvas_optics import build_target_canvas_optical_evidence, summarize_target_canvas_optical_evidence
from .formation_prerequisites import build_formation_prerequisite_table
from .optical_validation import build_cloud_optical_validation_table
from .precipitation import build_precipitation_path_evidence
from .spectroscopy_readiness import build_six_band_spectroscopy_readiness


def _clamp01(x):
    return max(0.0, min(1.0, float(x)))


def _band_name(d: float) -> str:
    for lo, hi, name in BANDS:
        if lo <= d <= hi:
            return name
    return "Outside"




def build_geometry_diagnostics(cfg: ModelConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build the full 0..-6° Earth-shadow / Dynamic-REZ illumination diagnostics.

    Returns:
      matrix: one row per solar angle × distance × cloud-height checkpoint.
      rez: one row per solar angle × cloud height with the geometric first-sunlit
           surface distance toward the Sun.
    These are pure spherical-Earth diagnostics and do not depend on forecast cloud.
    """
    matrix_rows = []
    rez_rows = []
    _rez_angles = tuple(dict.fromkeys((*cfg.firecloud_core_angles_deg, *cfg.late_glow_angles_deg)))
    for angle in _rez_angles:
        for z in ILLUMINATION_HEIGHTS_KM:
            entry = dynamic_rez_entry_distance_km(angle, z, cfg.earth_radius_km)
            rez_rows.append({
                "solar_altitude_deg": float(angle),
                "cloud_altitude_km": float(z),
                "dynamic_rez_entry_distance_km": float(entry),
                "legacy_within_440km_domain": bool(entry <= 440.0),
                "dynamic_domain_max_km": float(cfg.dynamic_domain_max_km),
                "within_dynamic_domain": bool(entry <= cfg.dynamic_domain_max_km),
            })
    # The coarse illumination matrix follows the active runtime grid so it stays
    # shape-compatible with the per-angle execution. Late-angle REZ entries are
    # retained separately as legacy/diagnostic geometry.
    for angle in cfg.solar_angles_deg:
        for d in cfg.dynamic_distance_samples_km:
            band = _band_name(float(d))
            for z in ILLUMINATION_HEIGHTS_KM:
                sunlit, shadow_h, clearance = geometric_illumination_state(
                    d, z, angle, cfg.earth_radius_km
                )
                matrix_rows.append({
                    "solar_altitude_deg": float(angle),
                    "distance_km": float(d),
                    "band": band,
                    "cloud_altitude_km": float(z),
                    "earth_shadow_top_km": float(shadow_h),
                    "clearance_above_shadow_km": float(clearance),
                    "geometric_state": "ILLUMINATED" if sunlit else "EARTH_SHADOWED",
                    "illuminated": bool(sunlit),
                })
    return pd.DataFrame(matrix_rows), pd.DataFrame(rez_rows)

def build_route_points(lat: float, lon: float, sun_azimuth_deg: float, cfg: ModelConfig) -> list[dict]:
    points = []
    for off in cfg.direction_offsets_deg:
        bearing = (sun_azimuth_deg + off) % 360
        for d in cfg.dynamic_distance_samples_km:
            plat, plon = destination_point(lat, lon, bearing, d, cfg.earth_radius_km)
            _seg_name, _nom_step = horizontal_sampling_segment(float(d))
            points.append({
                "point_id": f"{off:+.1f}_{int(round(float(d))):04d}",
                "distance_km": float(d),
                "sampling_segment": _seg_name,
                "nominal_sampling_step_km": float(_nom_step),
                "sampling_is_cloud_width": False,
                "direction_offset_deg": float(off),
                "bearing_deg": bearing,
                "lat": plat,
                "lon": plon,
            })
    return points


def layer_cloud_cover(row: pd.Series, layer: str) -> float:
    key = {"low": "cloud_cover_low", "mid": "cloud_cover_mid", "high": "cloud_cover_high"}[layer]
    v = row.get(key, np.nan)
    if pd.isna(v):
        return np.nan
    return _clamp01(float(v) / 100.0)


def forecast_layer_for_altitude(altitude_km: float) -> str | None:
    """Map a diagnostic altitude checkpoint to the provider's coarse cloud layer.

    The current provider exposes only low/mid/high cloud-cover fields, not true
    cloud-base/top profiles.  A checkpoint is therefore supported only when it
    lies inside one of the configured coarse vertical envelopes.  Unsupported
    heights stay Missing rather than being extrapolated as clear sky.
    """
    z = float(altitude_km)
    names = list(CLOUD_LAYERS_KM)
    for i, name in enumerate(names):
        z0, z1 = CLOUD_LAYERS_KM[name]
        # Internal boundaries belong to the upper layer (e.g. 2 km -> mid).
        if (z0 <= z < z1) or (i == len(names) - 1 and math.isclose(z, z1)):
            return name
    return None




def _build_coarse_route_index(route_at_time: pd.DataFrame) -> dict[float, dict[str, np.ndarray]]:
    """Pre-index coarse low/mid/high cloud cover once per direction.

    V8.4.0.6 performance-only helper.  Values preserve the exact legacy
    low/mid/high cover semantics; Missing remains NaN.
    """
    out = {}
    if route_at_time.empty:
        return out
    for off, g0 in route_at_time.groupby("direction_offset_deg", sort=False):
        g = g0.sort_values("distance_km")
        def cv(col):
            return pd.to_numeric(g.get(col, pd.Series(np.nan, index=g.index)), errors="coerce").to_numpy(dtype=float) / 100.0
        out[float(off)] = {
            "distance_km": pd.to_numeric(g["distance_km"], errors="coerce").to_numpy(dtype=float),
            "low": np.clip(cv("cloud_cover_low"), 0.0, 1.0),
            "mid": np.clip(cv("cloud_cover_mid"), 0.0, 1.0),
            "high": np.clip(cv("cloud_cover_high"), 0.0, 1.0),
        }
    return out


def _upstream_path_transmission_indexed(index: dict, direction_offset_deg: float,
        target_distance_km: float, target_altitude_km: float,
        solar_altitude_deg: float, cfg: ModelConfig) -> tuple[float, float]:
    """Array-indexed equivalent of upstream_path_transmission_proxy()."""
    rec = index.get(float(direction_offset_deg))
    if rec is None:
        return 1.0, 1.0
    distances = rec["distance_km"]
    start = int(np.searchsorted(distances, float(target_distance_km) + 1e-9, side="right"))
    if start >= len(distances):
        return 1.0, 1.0
    trans = 1.0; known = 0; total = 0
    for j in range(start, len(distances)):
        d = float(distances[j])
        ray_h = ray_altitude_km_at_surface_distance(
            target_distance_km, target_altitude_km, d, solar_altitude_deg, cfg.earth_radius_km
        )
        if ray_h is None or ray_h < 0:
            continue
        total += 1
        layer = forecast_layer_for_altitude(ray_h)
        if layer is None:
            continue
        cover = rec[layer][j]
        if np.isnan(cover):
            continue
        known += 1
        obstruction = min(0.97, float(cover) * cfg.obstruction_scale[layer])
        trans *= (1.0 - obstruction)
    completeness = known / total if total else 1.0
    return (trans if known or total == 0 else np.nan), completeness


def upstream_path_transmission_proxy(
    route_at_time: pd.DataFrame,
    direction_offset_deg: float,
    target_distance_km: float,
    target_altitude_km: float,
    solar_altitude_deg: float,
    cfg: ModelConfig,
) -> tuple[float, float]:
    """Cloud-obstruction proxy *upstream* of a target voxel.

    This differs deliberately from the legacy operational path proxy: the target
    grid cell itself is excluded so forecast cloud presence is not multiplied by
    its own cloud-cover obstruction a second time.  This new diagnostic does not
    alter the existing core score path calculation.
    """
    g = route_at_time[route_at_time["direction_offset_deg"] == direction_offset_deg].copy()
    g = g[g["distance_km"] > float(target_distance_km) + 1e-9].sort_values("distance_km")
    if g.empty:
        # At the far edge of the sampled domain there is no sampled upstream cell.
        return 1.0, 1.0

    trans = 1.0
    known = 0
    total = 0
    for _, row in g.iterrows():
        d = float(row["distance_km"])
        ray_h = ray_altitude_km_at_surface_distance(
            target_distance_km, target_altitude_km, d, solar_altitude_deg, cfg.earth_radius_km
        )
        if ray_h is None or ray_h < 0:
            continue
        total += 1
        active_layer = forecast_layer_for_altitude(ray_h)
        if active_layer is None:
            # Above provider-supported cloud layers: do not invent obstruction.
            # It is outside the vertical forecast support, so completeness drops.
            continue
        cover = layer_cloud_cover(row, active_layer)
        if pd.isna(cover):
            continue
        known += 1
        obstruction = min(0.97, cover * cfg.obstruction_scale[active_layer])
        trans *= (1.0 - obstruction)

    completeness = known / total if total else 1.0
    return (trans if known or total == 0 else np.nan), completeness


def build_forecast_voxel_illumination(
    route_at_time: pd.DataFrame, solar_altitude_deg: float, cfg: ModelConfig
) -> pd.DataFrame:
    """Overlay forecast cloud occupancy onto the geometric illumination lattice.

    Each row is angle × direction × surface distance × diagnostic altitude.
    Because the current forecast source supplies only low/mid/high cloud cover,
    `cloud_cover_fraction` is a coarse occupancy proxy, not a true 3-D cloud
    volume fraction.  The effective illuminated-cloud proxy is:

        cloud_cover_fraction × geometric_sunlit × upstream_transmission_proxy

    Missing vertical support or missing cloud data remains Missing.
    """
    rows = []
    if route_at_time.empty:
        return pd.DataFrame(rows)
    coarse_index = _build_coarse_route_index(route_at_time)

    for _, r in route_at_time.iterrows():
        d = float(r["distance_km"])
        off = float(r["direction_offset_deg"])
        band = _band_name(d)
        for z in ILLUMINATION_HEIGHTS_KM:
            layer = forecast_layer_for_altitude(z)
            sunlit, shadow_h, clearance = geometric_illumination_state(
                d, z, solar_altitude_deg, cfg.earth_radius_km
            )
            base = {
                "solar_altitude_deg": float(solar_altitude_deg),
                "direction_offset_deg": off,
                "distance_km": d,
                "band": band,
                "cloud_altitude_km": float(z),
                "forecast_layer": layer if layer is not None else "UNSUPPORTED",
                "earth_shadow_top_km": float(shadow_h),
                "clearance_above_shadow_km": float(clearance),
                "geometric_illuminated": bool(sunlit),
            }

            if layer is None:
                rows.append({
                    **base,
                    "cloud_cover_fraction": np.nan,
                    "upstream_transmission_proxy": np.nan,
                    "path_completeness": 0.0,
                    "illuminated_fraction_of_present_cloud_proxy": np.nan,
                    "effective_illuminated_cloud_proxy": np.nan,
                    "voxel_state": "NO_VERTICAL_FORECAST_SUPPORT",
                })
                continue

            cover = layer_cloud_cover(r, layer)
            if pd.isna(cover):
                rows.append({
                    **base,
                    "cloud_cover_fraction": np.nan,
                    "upstream_transmission_proxy": np.nan,
                    "path_completeness": 0.0,
                    "illuminated_fraction_of_present_cloud_proxy": np.nan,
                    "effective_illuminated_cloud_proxy": np.nan,
                    "voxel_state": "MISSING_CLOUD_FORECAST",
                })
                continue

            if cover <= 0.0:
                rows.append({
                    **base,
                    "cloud_cover_fraction": 0.0,
                    "upstream_transmission_proxy": np.nan,
                    "path_completeness": 1.0,
                    "illuminated_fraction_of_present_cloud_proxy": 0.0,
                    "effective_illuminated_cloud_proxy": 0.0,
                    "voxel_state": "NO_FORECAST_CLOUD",
                })
                continue

            if not sunlit:
                rows.append({
                    **base,
                    "cloud_cover_fraction": cover,
                    "upstream_transmission_proxy": 0.0,
                    "path_completeness": 1.0,
                    "illuminated_fraction_of_present_cloud_proxy": 0.0,
                    "effective_illuminated_cloud_proxy": 0.0,
                    "voxel_state": "CLOUD_EARTH_SHADOWED",
                })
                continue

            trans, comp = _upstream_path_transmission_indexed(
                coarse_index, off, d, float(z), solar_altitude_deg, cfg
            )
            if pd.isna(trans):
                illum_frac = np.nan
                effective = np.nan
                state = "SUNLIT_PATH_UNKNOWN"
            else:
                illum_frac = _clamp01(trans)
                effective = _clamp01(cover * illum_frac)
                state = "SUNLIT_FORECAST_CLOUD"
            rows.append({
                **base,
                "cloud_cover_fraction": cover,
                "upstream_transmission_proxy": trans,
                "path_completeness": comp,
                "illuminated_fraction_of_present_cloud_proxy": illum_frac,
                "effective_illuminated_cloud_proxy": effective,
                "voxel_state": state,
            })

    return pd.DataFrame(rows)


def path_transmission_proxy(
    route_at_time: pd.DataFrame,
    direction_offset_deg: float,
    target_distance_km: float,
    target_altitude_km: float,
    solar_altitude_deg: float,
    cfg: ModelConfig,
) -> tuple[float, float, list[dict]]:
    """Empirical cloud-obstruction transmission along the solar ray.

    This is not radiative-transfer COT. It maps forecast cloud-cover bins onto the
    ray height and compounds obstruction probabilistically. Missing data lowers the
    completeness and is not treated as clear sky.
    """
    g = route_at_time[route_at_time["direction_offset_deg"] == direction_offset_deg].copy()
    g = g[g["distance_km"] >= target_distance_km].sort_values("distance_km")
    if g.empty:
        return np.nan, 0.0, []

    trans = 1.0
    known = 0
    total = 0
    diagnostic = []
    for _, row in g.iterrows():
        d = float(row["distance_km"])
        ray_h = ray_altitude_km_at_surface_distance(
            target_distance_km, target_altitude_km, d, solar_altitude_deg, cfg.earth_radius_km
        )
        if ray_h is None or ray_h < 0:
            continue
        total += 1
        active_layer = None
        for layer, (z0, z1) in CLOUD_LAYERS_KM.items():
            if z0 <= ray_h < z1:
                active_layer = layer
                break
        if active_layer is None:
            diagnostic.append({"distance_km": d, "ray_altitude_km": ray_h, "layer": "above_high", "cover": 0.0})
            known += 1
            continue
        cover = layer_cloud_cover(row, active_layer)
        if pd.isna(cover):
            diagnostic.append({"distance_km": d, "ray_altitude_km": ray_h, "layer": active_layer, "cover": np.nan})
            continue
        known += 1
        scale = cfg.obstruction_scale[active_layer]
        # Segment obstruction proxy. cap avoids one forecast grid cell forcing exact zero.
        obstruction = min(0.97, cover * scale)
        trans *= (1.0 - obstruction)
        diagnostic.append({"distance_km": d, "ray_altitude_km": ray_h, "layer": active_layer, "cover": cover})

    completeness = known / total if total else 0.0
    return trans if known else np.nan, completeness, diagnostic


def evaluate_canvas_voxel(
    row: pd.Series,
    layer: str,
    solar_altitude_deg: float,
    cfg: ModelConfig,
) -> dict:
    d = float(row["distance_km"])
    z0, z1 = CLOUD_LAYERS_KM[layer]
    shadow_h = earth_shadow_min_altitude_km(d, solar_altitude_deg, cfg.earth_radius_km)
    geom_frac = cloud_layer_illuminated_fraction(z0, z1, shadow_h)
    cover = layer_cloud_cover(row, layer)
    return {
        "distance_km": d,
        "layer": layer,
        "layer_bottom_km": z0,
        "layer_top_km": z1,
        "shadow_altitude_km": shadow_h,
        "geometric_illuminated_fraction": geom_frac,
        "cloud_cover_fraction": cover,
    }


def _coverage_mean(values):
    vals = [v for v in values if not pd.isna(v)]
    return float(np.mean(vals)) if vals else np.nan


def evaluate_candidate(route_at_time: pd.DataFrame, solar_altitude_deg: float, cfg: ModelConfig) -> dict:
    directions = []
    voxel_rows = []
    for off in cfg.direction_offsets_deg:
        g = route_at_time[route_at_time["direction_offset_deg"] == off].copy()
        canvas = g[g["distance_km"] <= 100]
        illuminated_contributions = []
        transmission_values = []
        transmission_completeness = []

        for _, row in canvas.iterrows():
            d = float(row["distance_km"])
            for layer in ("mid", "high"):
                v = evaluate_canvas_voxel(row, layer, solar_altitude_deg, cfg)
                cover = v["cloud_cover_fraction"]
                if pd.isna(cover) or cover <= 0:
                    v["path_transmission_proxy"] = np.nan
                    v["effective_illuminated_cloud"] = np.nan if pd.isna(cover) else 0.0
                    voxel_rows.append({**v, "direction_offset_deg": off})
                    continue
                target_alt = (v["layer_bottom_km"] + v["layer_top_km"]) / 2.0
                trans, comp, _ = path_transmission_proxy(
                    route_at_time, off, d, target_alt, solar_altitude_deg, cfg
                )
                v["path_transmission_proxy"] = trans
                v["path_completeness"] = comp
                eff = cover * v["geometric_illuminated_fraction"] * (trans if not pd.isna(trans) else np.nan)
                v["effective_illuminated_cloud"] = eff
                voxel_rows.append({**v, "direction_offset_deg": off})
                if not pd.isna(eff):
                    illuminated_contributions.append(eff)
                if not pd.isna(trans):
                    transmission_values.append(trans)
                    transmission_completeness.append(comp)

        canvas_score = _coverage_mean(illuminated_contributions)
        path_t = _coverage_mean(transmission_values)
        path_c = _coverage_mean(transmission_completeness)

        # REZ diagnostic: low/mid cloud at 350-440 km, where low cloud is most damaging.
        rez = g[(g["distance_km"] >= 350) & (g["distance_km"] <= 440)]
        rez_obs = []
        known = 0
        total = 0
        for _, row in rez.iterrows():
            for layer in ("low", "mid", "high"):
                total += 1
                cc = layer_cloud_cover(row, layer)
                if pd.isna(cc):
                    continue
                known += 1
                rez_obs.append(cc * cfg.obstruction_scale[layer])
        rez_open_proxy = 1.0 - float(np.mean(rez_obs)) if rez_obs else np.nan
        rez_completeness = known / total if total else 0.0

        # Strong blocking diagnostic at 300-350 km.
        sb = g[(g["distance_km"] >= 300) & (g["distance_km"] <= 350)]
        sb_obs = []
        for _, row in sb.iterrows():
            for layer in ("low", "mid"):
                cc = layer_cloud_cover(row, layer)
                if not pd.isna(cc):
                    sb_obs.append(cc * cfg.obstruction_scale[layer])
        strong_block = float(np.mean(sb_obs)) if sb_obs else np.nan

        direction_physics = np.nan
        if not pd.isna(canvas_score) and not pd.isna(path_t) and not pd.isna(rez_open_proxy):
            direction_physics = _clamp01(canvas_score * (0.45 + 0.55 * rez_open_proxy) * (0.50 + 0.50 * path_t))
            if not pd.isna(strong_block):
                direction_physics *= (1.0 - 0.55 * _clamp01(strong_block))

        directions.append({
            "direction_offset_deg": off,
            "canvas_effective": canvas_score,
            "path_transmission": path_t,
            "path_completeness": path_c,
            "rez_open_proxy": rez_open_proxy,
            "rez_completeness": rez_completeness,
            "strong_block_proxy": strong_block,
            "physics_score": direction_physics,
        })

    ddf = pd.DataFrame(directions)
    valid = ddf.dropna(subset=["physics_score"])
    if valid.empty:
        physics = np.nan
    else:
        num = den = 0.0
        for _, row in valid.iterrows():
            w = cfg.direction_weights.get(float(row["direction_offset_deg"]), 0.0)
            num += w * float(row["physics_score"])
            den += w
        physics = num / den if den else np.nan

    # Data completeness kept separate from physics.
    comp_parts = []
    for _, r in ddf.iterrows():
        for k in ("path_completeness", "rez_completeness"):
            if not pd.isna(r[k]):
                comp_parts.append(float(r[k]))
    completeness = float(np.mean(comp_parts)) if comp_parts else 0.0

    # Visual magnitude proxy includes sky coverage of cloud plus physics, still separate.
    visual = np.nan
    if not pd.isna(physics):
        visual = _clamp01(physics * (0.8 + 0.2 * completeness))

    if completeness < cfg.min_data_completeness:
        operational = "UNKNOWN / DATA INCOMPLETE"
    elif pd.isna(physics):
        operational = "UNKNOWN"
    elif physics >= cfg.go_physics_threshold:
        operational = "GO"
    elif physics >= cfg.conditional_physics_threshold:
        operational = "CONDITIONAL GO"
    else:
        operational = "NO-GO"

    return {
        "physics_score": physics,
        "visual_magnitude": visual,
        "data_completeness": completeness,
        "operational_decision": operational,
        "directions": ddf,
        "voxels": pd.DataFrame(voxel_rows),
    }



def _pressure_profile_points(row: pd.Series) -> list[dict]:
    """Extract pressure-level vertical cloud points as AGL samples.

    Open-Meteo pressure-level cloud cover is a resolved pressure-level field, but
    depending on the selected NWP model it can be native parameterised cloud
    cover or an RH-derived estimate. We therefore retain provenance and do not
    label it as cloud liquid/ice water content.
    """
    from .providers.openmeteo import PRESSURE_LEVELS_HPA
    elev_m = row.get("model_surface_elevation_m", np.nan)
    elev_m = float(elev_m) if not pd.isna(elev_m) else 0.0
    out = []
    for p_hpa in PRESSURE_LEVELS_HPA:
        cc = row.get(f"cloud_cover_{p_hpa}hPa", np.nan)
        rh = row.get(f"relative_humidity_{p_hpa}hPa", np.nan)
        gh = row.get(f"geopotential_height_{p_hpa}hPa", np.nan)
        if pd.isna(gh):
            continue
        z_agl = (float(gh) - elev_m) / 1000.0
        if z_agl < -0.25 or z_agl > 20.0:
            continue
        occ = np.nan if pd.isna(cc) else _clamp01(float(cc) / 100.0)
        out.append({
            "pressure_hpa": float(p_hpa),
            "altitude_agl_km": max(0.0, z_agl),
            "cloud_cover_fraction": occ,
            "relative_humidity_pct": np.nan if pd.isna(rh) else float(rh),
            "profile_source": str(row.get("pressure_profile_primary_source", row.get("vertical_profile_source", "OPEN_METEO_PRESSURE_LEVEL"))),
        })
    return sorted(out, key=lambda x: x["altitude_agl_km"])


def build_pressure_profile_cloud_volume(
    route_at_time: pd.DataFrame, solar_altitude_deg: float, cfg: ModelConfig
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build the V8.1.0 pressure-level 3-D forecast cloud volume.

    The vertical lattice is interpolated in *geopotential-height AGL*, not by
    assuming fixed heights for pressure levels. Cloud occupancy comes from the
    pressure-level cloud-cover field; RH is carried as supporting evidence.
    Missing pressure-level cloud cover remains Missing.
    """
    rows = []
    if route_at_time.empty:
        return pd.DataFrame(), pd.DataFrame()

    for _, r in route_at_time.iterrows():
        pts = _pressure_profile_points(r)
        d = float(r["distance_km"]); off = float(r["direction_offset_deg"])
        profile_source = (pts[0].get("profile_source") if pts else str(r.get("pressure_profile_primary_source", r.get("vertical_profile_source", "OPEN_METEO_PRESSURE_LEVEL"))))
        if len(pts) < 2:
            for z in VOXEL_ALTITUDE_CENTERS_KM:
                rows.append({
                    "solar_altitude_deg": float(solar_altitude_deg), "direction_offset_deg": off,
                    "distance_km": d, "band": _band_name(d), "voxel_center_km": float(z),
                    "voxel_bottom_km": float(z-VOXEL_VERTICAL_STEP_KM/2),
                    "voxel_top_km": float(z+VOXEL_VERTICAL_STEP_KM/2),
                    "cloud_occupancy": np.nan, "relative_humidity_pct": np.nan,
                    "profile_supported": False, "profile_source": profile_source,
                    "profile_quality": "INSUFFICIENT_VERTICAL_LEVELS",
                })
            continue

        alts = np.array([x["altitude_agl_km"] for x in pts], dtype=float)
        cc = np.array([x["cloud_cover_fraction"] for x in pts], dtype=float)
        rh = np.array([x["relative_humidity_pct"] for x in pts], dtype=float)
        # Only interpolate cloud cover when both bracketing data are known.
        for z in VOXEL_ALTITUDE_CENTERS_KM:
            z=float(z); supported = bool(alts.min() <= z <= alts.max())
            occ = rh_i = np.nan
            quality = "OUTSIDE_PRESSURE_PROFILE_SUPPORT"
            if supported:
                j = int(np.searchsorted(alts, z))
                if j == 0: lo=hi=0
                elif j >= len(alts): lo=hi=len(alts)-1
                else: lo,hi=j-1,j
                if lo == hi:
                    w=0.0
                else:
                    w=(z-alts[lo])/(alts[hi]-alts[lo])
                if not pd.isna(cc[lo]) and not pd.isna(cc[hi]):
                    occ=float(cc[lo]*(1-w)+cc[hi]*w)
                    quality="PRESSURE_LEVEL_INTERPOLATED"
                else:
                    quality="MISSING_CLOUD_COVER_BRACKET"
                if not pd.isna(rh[lo]) and not pd.isna(rh[hi]):
                    rh_i=float(rh[lo]*(1-w)+rh[hi]*w)
            rows.append({
                "solar_altitude_deg": float(solar_altitude_deg), "direction_offset_deg": off,
                "distance_km": d, "band": _band_name(d), "voxel_center_km": z,
                "voxel_bottom_km": float(z-VOXEL_VERTICAL_STEP_KM/2),
                "voxel_top_km": float(z+VOXEL_VERTICAL_STEP_KM/2),
                "cloud_occupancy": occ, "relative_humidity_pct": rh_i,
                "rh_cloud_support": (bool(rh_i >= PROFILE_RH_SUPPORT_THRESHOLD_PCT) if not pd.isna(rh_i) else np.nan),
                "profile_supported": supported, "profile_source": profile_source,
                "profile_quality": quality,
            })

    vox = pd.DataFrame(rows)
    columns=[]
    for (off,d),g in vox.groupby(["direction_offset_deg","distance_km"],sort=False):
        known=g[g["cloud_occupancy"].notna()].copy()
        cloudy=known[known["cloud_occupancy"] >= PROFILE_CLOUD_OCCUPANCY_THRESHOLD]
        if cloudy.empty:
            base=top=thick=np.nan
        else:
            base=float(cloudy["voxel_bottom_km"].min()); top=float(cloudy["voxel_top_km"].max()); thick=top-base
        cv=float((known["cloud_occupancy"]*VOXEL_VERTICAL_STEP_KM).sum()) if not known.empty else np.nan
        columns.append({
            "solar_altitude_deg": float(solar_altitude_deg), "direction_offset_deg": float(off),
            "distance_km": float(d), "band": _band_name(float(d)),
            "profile_cloud_base_km": base, "profile_cloud_top_km": top,
            "profile_cloud_envelope_thickness_km": thick,
            "profile_cloud_volume_proxy_km": cv,
            "vertical_profile_completeness": float(g["cloud_occupancy"].notna().mean()),
            "boundary_quality": "PRESSURE_LEVEL_CLOUD_COVER_PROFILE",
        })
    return vox, pd.DataFrame(columns)


def _ray_altitudes_vectorized_km(target_distance_km: float, target_altitude_km: float, sample_distances_km: np.ndarray, solar_altitude_deg: float, radius_km: float) -> np.ndarray:
    """Vectorized equivalent of ray_altitude_km_at_surface_distance for one target.

    Returns NaN where the forward solar ray does not cross the requested radial
    line. V8.4.0.7 performance helper; geometry is algebraically identical to
    firecloud.geometry.ray_altitude_km_at_surface_distance.
    """
    ds = np.asarray(sample_distances_km, dtype=float)
    if ds.size == 0:
        return np.empty(0, dtype=float)
    alpha = math.radians(float(solar_altitude_deg))
    dt = float(target_distance_km) / float(radius_km)
    delta_s = ds / float(radius_km)
    rho_t = float(radius_km) + float(target_altitude_km)
    px = rho_t * math.cos(dt)
    py = rho_t * math.sin(dt)
    sx = math.sin(alpha); sy = math.cos(alpha)
    rx = np.cos(delta_s); ry = np.sin(delta_s)
    det = sx * (-ry) - sy * (-rx)
    good = np.abs(det) >= 1.0e-12
    t = np.full(ds.shape, np.nan, dtype=float)
    rho = np.full(ds.shape, np.nan, dtype=float)
    b1, b2 = -px, -py
    t[good] = (b1 * (-ry[good]) - b2 * (-rx[good])) / det[good]
    rho[good] = (sx * b2 - sy * b1) / det[good]
    good &= (t >= -1.0e-8) & (rho > 0.0)
    out = np.full(ds.shape, np.nan, dtype=float)
    out[good] = rho[good] - float(radius_km)
    return out


def apply_3d_optical_blocking(profile_voxels: pd.DataFrame, solar_altitude_deg: float, cfg: ModelConfig) -> pd.DataFrame:
    """Vectorized 3-D ray tracing through upstream vertical cloud columns.

    V8.4.0.7 keeps the V8.1.3 optical definition unchanged but vectorizes each
    target ray over all upstream distance segments. This removes Python-level
    per-segment geometry/nearest-height loops while preserving the same nearest
    0.5-km voxel lookup and Beer-Lambert engineering proxy.
    """
    if profile_voxels.empty:
        return pd.DataFrame()

    out = []
    cos_sun = max(0.05, math.cos(math.radians(abs(float(solar_altitude_deg)))))
    radius = float(cfg.earth_radius_km)

    for off, gdir0 in profile_voxels.groupby("direction_offset_deg", sort=False):
        gdir = gdir0.sort_values(["distance_km", "voxel_center_km"]).copy()
        distances = np.array(sorted(gdir["distance_km"].unique()), dtype=float)
        heights = np.array(sorted(gdir["voxel_center_km"].unique()), dtype=float)
        di = {float(v): i for i, v in enumerate(distances)}
        zi = {float(v): i for i, v in enumerate(heights)}

        occ = np.full((len(distances), len(heights)), np.nan, dtype=float)
        for r in gdir.itertuples(index=False):
            occ[di[float(r.distance_km)], zi[float(r.voxel_center_km)]] = r.cloud_occupancy

        # heights are monotonic and approximately uniform; searchsorted gives the
        # same nearest-cell result as argmin(abs(...)), with tie resolved low.
        for target in gdir.itertuples(index=False):
            rec = target._asdict()
            d_t = float(target.distance_km); z_t = float(target.voxel_center_km)
            i0 = di[d_t]
            occ_t = target.cloud_occupancy
            shadow_h = earth_shadow_min_altitude_km(d_t, solar_altitude_deg, radius)
            geom_frac = cloud_layer_illuminated_fraction(float(target.voxel_bottom_km), float(target.voxel_top_km), shadow_h)

            ds = distances[i0 + 1:]
            upstream_unknown_len = 0.0
            if ds.size:
                prev = np.concatenate(([d_t], ds[:-1]))
                dx = ds - prev
                valid_dx = dx > 0.0
                mids = ds - dx / 2.0
                ray_h = _ray_altitudes_vectorized_km(d_t, z_t, mids, solar_altitude_deg, radius)
                valid = valid_dx & np.isfinite(ray_h) & (ray_h >= 0.0)
                slant = np.where(valid, dx / cos_sun, 0.0)
                total_len = float(np.sum(slant))

                idx_hi = np.searchsorted(heights, ray_h, side="left")
                idx_hi = np.clip(idx_hi, 0, len(heights)-1)
                idx_lo = np.clip(idx_hi-1, 0, len(heights)-1)
                choose_hi = np.abs(heights[idx_hi]-ray_h) < np.abs(ray_h-heights[idx_lo])
                k = np.where(choose_hi, idx_hi, idx_lo)
                rows = np.arange(i0+1, len(distances))
                o = occ[rows, k]
                known = valid & np.isfinite(o)
                known_len = float(np.sum(np.where(known, dx / cos_sun, 0.0)))
                upstream_unknown_len = float(np.sum(np.where(valid & ~np.isfinite(o), dx / cos_sun, 0.0)))
                blocker_hits = int(np.sum(known & (o >= PROFILE_CLOUD_OCCUPANCY_THRESHOLD)))
                tau = float(CLOUD_EXTINCTION_PROXY_PER_KM * np.sum(np.where(known, o * (dx / cos_sun), 0.0)))
            else:
                tau = known_len = total_len = 0.0; blocker_hits = 0

            upstream_path_checked = bool(ds.size)
            # The farthest sampled voxel has no downstream sample in this
            # finite route.  It is a domain endpoint, not a clear ray.  Do
            # not turn the empty path into a fabricated 100% transmission.
            upstream_path_state = "UPSTREAM_PATH_CHECKED" if upstream_path_checked else "ROUTE_ENDPOINT_NO_UPSTREAM_CHECK"
            if upstream_path_checked and total_len <= 0.0:
                upstream_path_state = "UPSTREAM_PATH_GEOMETRY_UNAVAILABLE"
            elif upstream_path_checked and upstream_unknown_len > 0.0:
                upstream_path_state = "UPSTREAM_PATH_PARTIAL_UNKNOWN" if known_len > 0.0 else "UPSTREAM_PATH_UNKNOWN"
            comp = known_len / total_len if total_len > 0 else (np.nan if not upstream_path_checked else 0.0)
            transmission = math.exp(-tau) if (upstream_path_checked and known_len > 0) else (np.nan if not upstream_path_checked or total_len > 0 else np.nan)
            if not upstream_path_checked:
                state = "ROUTE_ENDPOINT_NO_UPSTREAM_CHECK"; eff = np.nan
            elif pd.isna(occ_t):
                state = "MISSING_TARGET_CLOUD_PROFILE"; eff = np.nan
            elif float(occ_t) < PROFILE_CLOUD_OCCUPANCY_THRESHOLD:
                state = "NO_FORECAST_CLOUD"; eff = 0.0
            elif geom_frac <= 0:
                state = "SHADOWED_CLOUD_BLOCKER_CAPABLE"; eff = 0.0
            elif pd.isna(transmission):
                state = "SUNLIT_TARGET_PATH_UNKNOWN"; eff = np.nan
            else:
                eff = _clamp01(float(occ_t) * float(geom_frac) * float(transmission))
                state = "PARTIALLY_ILLUMINATED_TARGET" if geom_frac < 0.999 else "ILLUMINATED_TARGET"

            rec.update({
                "earth_shadow_top_km": float(shadow_h),
                "geometric_illuminated_fraction": float(geom_frac),
                "slant_cloud_optical_depth_proxy": float(tau),
                "remaining_transmission_proxy": transmission,
                "ray_path_completeness": float(comp),
                "upstream_path_checked": upstream_path_checked,
                "upstream_path_state": upstream_path_state,
                "upstream_unknown_path_fraction": (float(upstream_unknown_len / total_len) if total_len > 0 else np.nan),
                "upstream_blocker_hit_count": int(blocker_hits),
                "effective_illuminated_cloud_volume_proxy": eff,
                "optical_state": state,
                "optical_model": "BEER_LAMBERT_ENGINEERING_PROXY",
            })
            out.append(rec)
    return pd.DataFrame(out)



def apply_native_microphysical_optical_blocking(native_voxels: pd.DataFrame, solar_altitude_deg: float, cfg: ModelConfig, *, optical_properties_ready: bool = False) -> pd.DataFrame:
    """Trace Sun→target rays through native condensate-derived extinction.

    V8.4.0.7 vectorizes upstream segment geometry and supports a pre-enriched
    native optical base so angle-independent CLWMR/ICMR→extinction conversion can
    be cached per GFS run/lead. Physical definitions and thresholds are unchanged.
    """
    if native_voxels.empty:
        return pd.DataFrame()

    enriched = native_voxels.copy() if optical_properties_ready else add_native_optical_properties(native_voxels)
    out = []
    cos_sun = max(0.05, math.cos(math.radians(abs(float(solar_altitude_deg)))))
    radius = float(cfg.earth_radius_km)

    for off, gdir0 in enriched.groupby("direction_offset_deg", sort=False):
        gdir = gdir0.sort_values(["distance_km", "voxel_center_km"]).copy()
        distances = np.array(sorted(gdir["distance_km"].unique()), dtype=float)
        heights = np.array(sorted(gdir["voxel_center_km"].unique()), dtype=float)
        di = {float(v): i for i, v in enumerate(distances)}
        zi = {float(v): i for i, v in enumerate(heights)}
        beta = np.full((len(distances), len(heights)), np.nan, dtype=float)
        for r in gdir.itertuples(index=False):
            beta[di[float(r.distance_km)], zi[float(r.voxel_center_km)]] = getattr(r, "total_extinction_m1")

        for target in gdir.itertuples(index=False):
            rec = target._asdict()
            d_t = float(target.distance_km); z_t = float(target.voxel_center_km)
            i0 = di[d_t]
            target_q = getattr(target, "total_cloud_condensate_kgkg", np.nan)
            shadow_h = earth_shadow_min_altitude_km(d_t, solar_altitude_deg, radius)
            geom_frac = cloud_layer_illuminated_fraction(float(target.voxel_bottom_km), float(target.voxel_top_km), shadow_h)

            ds = distances[i0 + 1:]
            upstream_unknown_len = 0.0
            if ds.size:
                prev = np.concatenate(([d_t], ds[:-1]))
                dx = ds - prev
                valid_dx = dx > 0.0
                mids = ds - dx / 2.0
                ray_h = _ray_altitudes_vectorized_km(d_t, z_t, mids, solar_altitude_deg, radius)
                valid = valid_dx & np.isfinite(ray_h) & (ray_h >= 0.0)
                slant_km = np.where(valid, dx / cos_sun, 0.0)
                total_len = float(np.sum(slant_km))

                idx_hi = np.searchsorted(heights, ray_h, side="left")
                idx_hi = np.clip(idx_hi, 0, len(heights)-1)
                idx_lo = np.clip(idx_hi-1, 0, len(heights)-1)
                choose_hi = np.abs(heights[idx_hi]-ray_h) < np.abs(ray_h-heights[idx_lo])
                k = np.where(choose_hi, idx_hi, idx_lo)
                rows = np.arange(i0+1, len(distances))
                b = beta[rows, k]
                known = valid & np.isfinite(b)
                known_len = float(np.sum(np.where(known, dx / cos_sun, 0.0)))
                upstream_unknown_len = float(np.sum(np.where(valid & ~np.isfinite(b), dx / cos_sun, 0.0)))
                segment_tau = np.where(known, np.maximum(0.0, b) * (dx / cos_sun) * 1000.0, 0.0)
                tau = float(np.sum(segment_tau))
                blocker_hits = int(np.sum(segment_tau >= 0.05))
            else:
                tau = known_len = total_len = 0.0; blocker_hits = 0

            upstream_path_checked = bool(ds.size)
            upstream_path_state = "UPSTREAM_PATH_CHECKED" if upstream_path_checked else "ROUTE_ENDPOINT_NO_UPSTREAM_CHECK"
            if upstream_path_checked and total_len <= 0.0:
                upstream_path_state = "UPSTREAM_PATH_GEOMETRY_UNAVAILABLE"
            elif upstream_path_checked and upstream_unknown_len > 0.0:
                upstream_path_state = "UPSTREAM_PATH_PARTIAL_UNKNOWN" if known_len > 0.0 else "UPSTREAM_PATH_UNKNOWN"
            comp = known_len / total_len if total_len > 0 else (np.nan if not upstream_path_checked else 0.0)
            transmission = math.exp(-tau) if (upstream_path_checked and known_len > 0) else (np.nan if not upstream_path_checked or total_len > 0 else np.nan)
            target_missing = pd.isna(target_q)
            target_cloudy = bool(not target_missing and float(target_q) >= 1.0e-7)
            target_on_sunlit_path = bool(target_cloudy and geom_frac > 0.0)
            if target_missing:
                target_role = "TARGET_CONDENSATE_MISSING"
            elif not target_cloudy:
                target_role = "CLEAR_OR_NO_NATIVE_CLOUD"
            elif geom_frac <= 0.0:
                target_role = "SHADOWED_NATIVE_CLOUD_BLOCKER_CAPABLE"
            elif not upstream_path_checked:
                target_role = "SUNLIT_NATIVE_TARGET_PATH_NOT_CHECKED"
            elif upstream_path_state in {"UPSTREAM_PATH_PARTIAL_UNKNOWN", "UPSTREAM_PATH_UNKNOWN", "UPSTREAM_PATH_GEOMETRY_UNAVAILABLE"}:
                target_role = "SUNLIT_NATIVE_TARGET_PATH_UNKNOWN"
            else:
                target_role = "ILLUMINATED_NATIVE_CANVAS_CANDIDATE"
            native_canvas_eligible = bool(target_role == "ILLUMINATED_NATIVE_CANVAS_CANDIDATE" and pd.notna(transmission))
            if not upstream_path_checked:
                state = "ROUTE_ENDPOINT_NO_UPSTREAM_CHECK"; eff = np.nan
            elif pd.isna(target_q):
                state = "MISSING_NATIVE_TARGET_CONDENSATE"; eff = np.nan
            elif float(target_q) < 1.0e-7:
                state = "NO_NATIVE_FORECAST_CLOUD"; eff = 0.0
            elif geom_frac <= 0:
                state = "SHADOWED_NATIVE_CLOUD_BLOCKER_CAPABLE"; eff = 0.0
            elif pd.isna(transmission):
                state = "SUNLIT_NATIVE_TARGET_PATH_UNKNOWN"; eff = np.nan
            else:
                cf = getattr(target, "cloud_fraction_used", getattr(target, "cloud_fraction", 1.0))
                cf = 1.0 if pd.isna(cf) else _clamp01(cf)
                eff = _clamp01(cf * float(geom_frac) * float(transmission))
                state = "PARTIALLY_ILLUMINATED_NATIVE_TARGET" if geom_frac < 0.999 else "ILLUMINATED_NATIVE_TARGET"

            rec.update({
                "solar_altitude_deg": float(solar_altitude_deg),
                "earth_shadow_top_km": float(shadow_h),
                "geometric_illuminated_fraction": float(geom_frac),
                "slant_cloud_optical_depth_estimate": float(tau),
                "remaining_native_cloud_transmission_estimate": transmission,
                "native_ray_path_completeness": float(comp),
                "upstream_path_checked": upstream_path_checked,
                "upstream_path_state": upstream_path_state,
                "native_upstream_unknown_path_fraction": (float(upstream_unknown_len / total_len) if total_len > 0 else np.nan),
                "native_target_role": target_role,
                "native_target_cloud_on_sunlit_path": target_on_sunlit_path,
                "native_target_can_be_effective_canvas": native_canvas_eligible,
                "native_upstream_blocker_hit_count": int(blocker_hits),
                "effective_illuminated_native_cloud_fraction_estimate": eff,
                "native_optical_state": state,
                "native_optical_model": "CLWMR_ICMR_GEOMETRIC_OPTICS_ASSUMED_REFF_BEER_LAMBERT",
            })
            out.append(rec)
    return pd.DataFrame(out)



def summarize_native_optical_blocking(native_optical_voxels: pd.DataFrame) -> pd.DataFrame:
    if native_optical_voxels.empty:
        return pd.DataFrame()
    rows = []
    for (off, d), g in native_optical_voxels.groupby(["direction_offset_deg", "distance_km"], sort=False):
        q = g["total_cloud_condensate_kgkg"]
        cloudy = g[q.fillna(-1) >= 1.0e-7]
        total_cod = g["vertical_cloud_optical_depth_estimate"].sum(min_count=1)
        rows.append({
            "solar_altitude_deg": float(g["solar_altitude_deg"].iloc[0]),
            "direction_offset_deg": float(off), "distance_km": float(d), "band": _band_name(float(d)),
            "native_cloudy_vertical_cells": int(len(cloudy)),
            "column_vertical_cod_estimate": float(total_cod) if not pd.isna(total_cod) else np.nan,
            "max_upstream_slant_cod_estimate": float(g["slant_cloud_optical_depth_estimate"].max(skipna=True)) if g["slant_cloud_optical_depth_estimate"].notna().any() else np.nan,
            "mean_remaining_native_cloud_transmission_estimate": float(g["remaining_native_cloud_transmission_estimate"].mean(skipna=True)) if g["remaining_native_cloud_transmission_estimate"].notna().any() else np.nan,
            "native_optical_path_completeness": float(g["native_ray_path_completeness"].mean()),
            "native_upstream_path_state": (g["upstream_path_state"].value_counts().index[0] if "upstream_path_state" in g and not g["upstream_path_state"].dropna().empty else ""),
            "native_endpoint_count": int((g.get("upstream_path_state", pd.Series(index=g.index, dtype=str)) == "ROUTE_ENDPOINT_NO_UPSTREAM_CHECK").sum()),
            "native_target_cloud_on_sunlit_path_count": int(g.get("native_target_cloud_on_sunlit_path", pd.Series(False, index=g.index)).fillna(False).astype(bool).sum()),
            "native_effective_canvas_candidate_count": int(g.get("native_target_can_be_effective_canvas", pd.Series(False, index=g.index)).fillna(False).astype(bool).sum()),
            "native_optical_model": "CLWMR_ICMR_GEOMETRIC_OPTICS_ASSUMED_REFF_BEER_LAMBERT",
        })
    return pd.DataFrame(rows)

def summarize_vertical_blocking(optical_voxels: pd.DataFrame) -> pd.DataFrame:
    if optical_voxels.empty:
        return pd.DataFrame()
    rows=[]
    for (off,d),g in optical_voxels.groupby(["direction_offset_deg","distance_km"],sort=False):
        cloudy=g[g["cloud_occupancy"].fillna(-1)>=PROFILE_CLOUD_OCCUPANCY_THRESHOLD]
        illum=(g["effective_illuminated_cloud_volume_proxy"]*VOXEL_VERTICAL_STEP_KM).sum(min_count=1)
        total=(g["cloud_occupancy"]*VOXEL_VERTICAL_STEP_KM).sum(min_count=1)
        rows.append({
            "solar_altitude_deg": float(g["solar_altitude_deg"].iloc[0]),
            "direction_offset_deg": float(off), "distance_km": float(d), "band": _band_name(float(d)),
            "cloudy_vertical_cells": int(len(cloudy)),
            "max_upstream_tau_proxy": float(g["slant_cloud_optical_depth_proxy"].max(skipna=True)) if g["slant_cloud_optical_depth_proxy"].notna().any() else np.nan,
            "mean_remaining_transmission_proxy": float(g["remaining_transmission_proxy"].mean(skipna=True)) if g["remaining_transmission_proxy"].notna().any() else np.nan,
            "cloud_volume_proxy_km": float(total) if not pd.isna(total) else np.nan,
            "illuminated_cloud_volume_proxy_km": float(illum) if not pd.isna(illum) else np.nan,
            "illuminated_fraction_of_cloud_volume_proxy": (float(illum/total) if total and not pd.isna(illum) else (0.0 if total==0 else np.nan)),
            "path_completeness": float(g["ray_path_completeness"].mean()),
            "upstream_path_state": (g["upstream_path_state"].value_counts().index[0] if "upstream_path_state" in g and not g["upstream_path_state"].dropna().empty else ""),
            "endpoint_count": int((g.get("upstream_path_state", pd.Series(index=g.index, dtype=str)) == "ROUTE_ENDPOINT_NO_UPSTREAM_CHECK").sum()),
        })
    return pd.DataFrame(rows)

def _merge_route_hourly_frames(base: pd.DataFrame, extra: pd.DataFrame) -> pd.DataFrame:
    """Fill Missing hourly provider columns by point/time without duplicating rows."""
    if base is None or base.empty:
        return extra.copy() if extra is not None else pd.DataFrame()
    if extra is None or extra.empty:
        return base.copy()
    keys=[c for c in ("time","point_id","distance_km","direction_offset_deg","lat","lon") if c in base.columns and c in extra.columns]
    if "time" not in keys or "point_id" not in keys:
        return base.copy()
    b=base.copy(); e=extra.copy()
    b["time"]=pd.to_datetime(b["time"],errors="coerce")
    e["time"]=pd.to_datetime(e["time"],errors="coerce")
    # Avoid many-to-many merges if a provider duplicated a logical point/time.
    b=b.drop_duplicates(subset=["time","point_id"],keep="last")
    e=e.drop_duplicates(subset=["time","point_id"],keep="last")
    merge_keys=["time","point_id"]
    payload=[c for c in e.columns if c not in merge_keys and c not in {"distance_km","direction_offset_deg","lat","lon"}]
    tmp=e[merge_keys+payload].copy()
    overlap=[c for c in payload if c in b.columns]
    renamed={c:f"__fallback__{c}" for c in overlap}
    tmp=tmp.rename(columns=renamed)
    out=b.merge(tmp,on=merge_keys,how="left")
    for c in overlap:
        fb=f"__fallback__{c}"
        out[c]=out[c].where(out[c].notna(),out[fb])
        out=out.drop(columns=[fb])
    attrs=dict(getattr(base,"attrs",{}) or {})
    audits=list(attrs.get("api_request_audit",[]) or []) + list(getattr(extra,"attrs",{}).get("api_request_audit",[]) or [])
    attrs["api_request_audit"]=audits
    attrs["pressure_fallback_merged"]=True
    out.attrs=attrs
    return out


def _native_gfs_thermodynamic_ready(native_df: pd.DataFrame) -> bool:
    """Require a real GFS thermodynamic profile reaching the 30-hPa model top."""
    if native_df is None or native_df.empty:
        return False
    good=[]
    for p in GAS_PRESSURE_LEVELS_HPA:
        cols=(f"temperature_k_{p}hPa",f"relative_humidity_pct_{p}hPa",f"geopotential_height_m_{p}hPa")
        if all(c in native_df.columns and pd.to_numeric(native_df[c],errors="coerce").notna().any() for c in cols):
            good.append(int(p))
    return 30 in good and len(good) >= 12


def _select_v1_canvas_rt_targets(native_optical_voxels: pd.DataFrame, canvases, scene) -> pd.DataFrame:
    """Return the minimal RT target set required by PhysicsCore V1 Canvas bases.

    R3.3 candidate filtering removes the legacy all-voxel spectral solve from the
    default PhysicsCore path. The full native cloud volume is still retained for
    geometry and blocker intersection; only expensive target radiative transfer
    is reduced to one nearest native optical voxel per Canvas base. Set
    FIRECLOUD_V1_RT_TARGET_MODE=ALL_VOXELS to restore the legacy diagnostic solve.
    """
    if native_optical_voxels is None or native_optical_voxels.empty:
        return pd.DataFrame()
    mode=str(os.getenv("FIRECLOUD_V1_RT_TARGET_MODE","CANVAS_CANDIDATES") or "CANVAS_CANDIDATES").upper().strip()
    if mode in {"ALL","ALL_VOXELS","LEGACY_ALL_VOXELS"}:
        out=native_optical_voxels.copy()
        out["v1_rt_target_mode"]="ALL_VOXELS"
        return out
    if not canvases or scene is None:
        return native_optical_voxels.iloc[0:0].copy()
    layer_by_id={layer.layer_id:layer for layer in getattr(scene,"layers",())}
    selected=[]
    for canvas in canvases:
        layer=layer_by_id.get(canvas.cloud_layer_id)
        if layer is None:
            continue
        g=native_optical_voxels
        if "direction_offset_deg" in g.columns:
            dd=pd.to_numeric(g["direction_offset_deg"],errors="coerce")
            g=g[np.isclose(dd,float(layer.direction_offset_deg),atol=1e-6,equal_nan=False)]
        if g.empty:
            continue
        if "distance_km" in g.columns:
            dist=pd.to_numeric(g["distance_km"],errors="coerce")
            if dist.notna().any():
                mind=(dist-float(canvas.distance_km)).abs().min()
                g=g[(dist-float(canvas.distance_km)).abs() <= float(mind)+1e-9]
        if g.empty:
            continue
        target=float(canvas.cloud_base_altitude_km)
        if {"voxel_bottom_km","voxel_top_km"}.issubset(g.columns):
            lo=pd.to_numeric(g["voxel_bottom_km"],errors="coerce")
            hi=pd.to_numeric(g["voxel_top_km"],errors="coerce")
            contain=g[(lo<=target)&(hi>=target)]
            if not contain.empty:
                g=contain
        center_col="voxel_center_km" if "voxel_center_km" in g.columns else "altitude_agl_km"
        if center_col in g.columns:
            center=pd.to_numeric(g[center_col],errors="coerce")
            chosen=(center-target).abs().idxmin() if center.notna().any() else g.index[0]
        else:
            chosen=g.index[0]
        row=native_optical_voxels.loc[[chosen]].copy()
        row["v1_canvas_id"]=str(canvas.canvas_id)
        row["v1_cloud_layer_id"]=str(canvas.cloud_layer_id)
        row["v1_canvas_base_altitude_km"]=target
        row["v1_rt_target_mode"]="CANVAS_CANDIDATES"
        selected.append(row)
    if not selected:
        return native_optical_voxels.iloc[0:0].copy()
    out=pd.concat(selected,ignore_index=True)
    subset=[c for c in ("direction_offset_deg","distance_km","voxel_center_km") if c in out.columns]
    return out.drop_duplicates(subset=subset,keep="first").reset_index(drop=True) if subset else out.reset_index(drop=True)


def analyze_event(lat: float, lon: float, day: date, event: str, tz_name: str = "Asia/Taipei",
                  cfg: ModelConfig | None = None, progress_callback=None) -> dict:
    cfg = cfg or ModelConfig()
    _analysis_t0 = perf_counter()
    performance_rows = []
    def _progress(fraction: float, message: str):
        if progress_callback is not None:
            try:
                progress_callback(float(fraction), str(message))
            except Exception:
                pass
    _progress(0.02, "計算 0°～−6° 曙暮光幾何…")
    _stage_t0 = perf_counter()
    candidates = []
    # Build all candidate times first.
    for angle in cfg.solar_angles_deg:
        t = find_time_for_solar_altitude(lat, lon, day, event, angle, tz_name)
        az = solar_azimuth_deg(lat, lon, t)
        candidates.append((angle, t, az))

    # Use the middle candidate azimuth to build one route lattice; directional motion across
    # the ~30 minute interval is small, and each offset remains explicit.
    performance_rows.append({"stage": "SOLAR_GEOMETRY_AND_TIMELINE", "elapsed_seconds": perf_counter()-_stage_t0, "cache_status": "COMPUTED"})
    ref_az = candidates[len(candidates)//2][2]
    route_points = build_route_points(lat, lon, ref_az, cfg)
    _sampling_nodes = list(cfg.dynamic_distance_samples_km)
    horizontal_sampling_profile = pd.DataFrame([
        {
            "node_distance_km": float(d),
            "sampling_segment": horizontal_sampling_segment(float(d))[0],
            "nominal_step_km": float(horizontal_sampling_segment(float(d))[1]),
            "sampling_is_cloud_width": False,
            "contract": "ADAPTIVE_HORIZONTAL_SAMPLING_V1_R4_3",
        }
        for d in _sampling_nodes
    ])
    start = min(t for _, t, _ in candidates) - timedelta(hours=2)
    end = max(t for _, t, _ in candidates) + timedelta(hours=2)
    _progress(0.10, "下載 Open-Meteo 輕量路徑營運欄位…")
    _stage_t0 = perf_counter()
    def _openmeteo_progress(batch_idx, total_batches, message):
        total_batches = max(1, int(total_batches))
        frac = 0.10 + 0.18 * min(1.0, max(0.0, float(batch_idx) / total_batches))
        _progress(frac, f"Open-Meteo｜{message}")
    # V8.4.11.1: do not ask the free Open-Meteo endpoint for 19 pressure
    # levels × 4 fields × 180 route points on the normal path. Native GFS GRIB
    # already carries the real pressure-level thermodynamic state.
    hourly = fetch_route_surface_hourly(route_points, start, end, tz_name, progress_callback=_openmeteo_progress)
    openmeteo_request_audit = pd.DataFrame(hourly.attrs.get("api_request_audit", []))
    _om_provider_status = str(hourly.attrs.get("openmeteo_status", "UNKNOWN"))
    if _om_provider_status == "PARTIAL_RATE_LIMIT":
        _progress(0.275, "Open-Meteo 輕量營運欄位仍遇 HTTP 429：已開啟 circuit；缺失保持 Missing，氣壓層改由原生 GFS 提供。")
    elif _om_provider_status == "PARTIAL_MISSING":
        _progress(0.275, "Open-Meteo 部分營運欄位缺失：Missing 不視為無雲；氣壓層由原生 GFS 提供。")
    _om_status = (
        "CACHE_HIT" if (not openmeteo_request_audit.empty and (openmeteo_request_audit["cache_status"] == "HIT").all())
        else _om_provider_status
    )
    performance_rows.append({"stage": "OPENMETEO_SURFACE_FETCH", "elapsed_seconds": perf_counter()-_stage_t0, "cache_status": _om_status})
    # V8.4.7.3: do not request Open-Meteo Air Quality AOD550 up front. Native
    # CAMS spectral AOD is the primary source and is prefetched below. The
    # Open-Meteo/CAMS AOD endpoint is now called only if at least one required
    # CAMS time state lacks usable aerosol data, preventing semantically
    # overlapping API requests on healthy CAMS runs.
    aerosol_hourly = pd.DataFrame()
    aerosol_error = None
    _progress(0.28, "Open-Meteo 路徑階段完成，準備原生資料鏈…")

    result_rows = []
    details = {}
    # PhysicsCore V1.0-R2 geometry/illumination audit frames. These are the new
    # runtime contracts and are deliberately independent from the inherited V8
    # physics_score / global completeness gate retained below only for legacy UI.
    v1_cloud_layer_frames = []
    v1_canvas_frames = []
    v1_direct_solar_frames = []
    v1_solar_ray_frames = []
    v1_dependency_frames = []
    v1_solar_geometry_frames = []
    v1_ray_cloud_intersection_frames = []
    v1_cloud_horizontal_support_frames = []
    v1_native_condensate_support_diagnostic_frames = []
    v1_spectral_optical_path_frames = []
    v1_cloud_base_illumination_frames = []
    v1_uncertainty_frames = []
    v1_optical_bottleneck_frames = []
    v1_canvas_radiance_frames = []
    v1_formation_frames = []
    v1_spectral_colour_frames = []
    v1_precipitation_path_frames = []
    v1_target_canvas_optical_evidence_frames = []
    v1_target_canvas_optical_summary_frames = []
    native_cache = {}
    cams_native_cache = {}
    native_volume_cache = {}
    native_optical_base_cache = {}
    gas_profile_cache = {}
    gas_rt_context_cache = {}
    aerosol_spectral_cache = {}
    core_set = {float(x) for x in cfg.firecloud_core_angles_deg}
    late_set = {float(x) for x in cfg.late_glow_angles_deg}

    # V8.4.0.2: provider I/O is prefetched before the per-angle loop. Previously the
    # first 0.0° checkpoint silently paid the entire first GFS NOMADS + CAMS ADS
    # download/decode cost, making the UI look frozen at “0.0° (1/8)”. The work is
    # unchanged scientifically; only its scheduling/progress reporting is corrected.
    gfs_requests = {}
    cams_requests = {}
    for _angle, _t, _az in candidates:
        try:
            _run, _lead = resolve_run_and_lead(_t)
            gfs_requests.setdefault((_run.isoformat(), int(_lead)), _t)
        except Exception:
            pass
        try:
            _crun, _clead = resolve_cams_run_and_lead(_t)
            cams_requests.setdefault((_crun.isoformat(), int(_clead)), _t)
        except Exception:
            pass

    _progress(0.30, f"預先取得 GFS 原生雲微物理（{len(gfs_requests)} 個時次）…")
    _prefetch_t0 = perf_counter()
    for _i, (_key, _t) in enumerate(gfs_requests.items()):
        _request_t0 = perf_counter()
        _meta = {"native_status": "UNAVAILABLE", **native_provider_status()}
        try:
            native_cache[_key] = fetch_route_native(route_points, _t)
        except Exception as exc:
            native_cache[_key] = (pd.DataFrame(), {**_meta, "native_status": "FAILED", "native_error": f"{type(exc).__name__}: {exc}"})
        performance_rows.append({"stage": "GFS_NOMADS_DOWNLOAD_DECODE", "elapsed_seconds": perf_counter()-_request_t0, "cache_status": "PREFETCH", "cache_key": str(_key)})
        _progress(0.30 + 0.035 * (_i + 1) / max(1, len(gfs_requests)), f"GFS 原生雲微物理：{_i+1}/{len(gfs_requests)}")
    performance_rows.append({"stage": "GFS_PREFETCH_TOTAL", "elapsed_seconds": perf_counter()-_prefetch_t0, "cache_status": "PREFETCH"})

    # Native GFS is now the primary pressure-level thermodynamic provider. Only
    # if one required GFS state cannot reach the 30-hPa domain do we submit the
    # old heavy Open-Meteo pressure request as a deferred fallback.
    _gfs_thermo_ready = bool(gfs_requests) and all(
        _native_gfs_thermodynamic_ready(native_cache.get(k, (pd.DataFrame(), {}))[0]) for k in gfs_requests
    )
    if _gfs_thermo_ready:
        performance_rows.append({"stage":"OPENMETEO_PRESSURE_PROFILE_FALLBACK","elapsed_seconds":0.0,"cache_status":"SKIPPED_GFS_NATIVE_THERMODYNAMIC_READY"})
        _progress(0.337, "GFS 原生 1000–30 hPa 熱力剖面 READY；略過 Open-Meteo 重型氣壓層請求。")
    else:
        _progress(0.337, "GFS 原生氣壓層不完整，啟用 Open-Meteo 氣壓層備援…")
        _pf_t0=perf_counter()
        def _pressure_fallback_progress(batch_idx,total_batches,message):
            _progress(0.337, f"Open-Meteo 氣壓層備援｜{message}")
        pressure_hourly=fetch_route_pressure_hourly(route_points,start,end,tz_name,progress_callback=_pressure_fallback_progress)
        hourly=_merge_route_hourly_frames(hourly,pressure_hourly)
        openmeteo_request_audit=pd.DataFrame(hourly.attrs.get("api_request_audit", []))
        performance_rows.append({"stage":"OPENMETEO_PRESSURE_PROFILE_FALLBACK","elapsed_seconds":perf_counter()-_pf_t0,"cache_status":pressure_hourly.attrs.get("openmeteo_status","UNKNOWN")})

    _progress(0.34, f"預先取得 CAMS O₃／3D 氣膠／光譜 AOD 三條獨立資料鏈（{len(cams_requests)} 個唯一時次；持久快取優先，未命中時每時次 90 秒 grace window）…")
    _prefetch_t0 = perf_counter()
    _cams_items = list(cams_requests.items())
    # The request planner already deduplicates identical (run, lead) keys.  The
    # remaining expensive work is normally two different forecast times.  Run
    # at most two *time bundles* concurrently; each bundle continues to fetch
    # O3, spectral AOD, and native aerosol serially.  This preserves the ADS
    # queue protection added in V8.4.11 while avoiding a full 2-time serial wait.
    try:
        _cams_parallel_workers = max(1, int(os.getenv("FIRECLOUD_CAMS_PREFETCH_WORKERS", "2")))
    except Exception:
        _cams_parallel_workers = 2
    _cams_parallel_workers = min(_cams_parallel_workers, 2, max(1, len(_cams_items)))
    _cams_progress_lock = threading.Lock()
    _cams_progress_states = {}

    def _fetch_cams_time_bundle(_item):
        _key, _t = _item
        _request_t0 = perf_counter()
        _meta = {"native_aerosol_status": "UNAVAILABLE", "native_ozone_status": "UNAVAILABLE", **native_aerosol_provider_status()}
        _role_state = {}

        def _cams_role_progress(_role, _status, _elapsed):
            _short = {
                "NATIVE_AEROSOL_532NM_PRESSURE_LEVEL": "3D氣膠",
                "NATIVE_AEROSOL_532NM_PRESSURE_LEVEL_RETRY": "3D氣膠重試",
                "O3_PRESSURE_LEVEL": "O₃",
                "O3_PRESSURE_LEVEL_RETRY": "O₃重試",
                "SPECTRAL_COLUMN_AOD": "光譜AOD",
                "SPECTRAL_COLUMN_AOD_RETRY": "光譜AOD重試",
            }.get(_role, _role)
            if str(_status).upper() == "RUNNING":
                _role_state[_short] = f"RUNNING {float(_elapsed):.0f}s / 90s"
            else:
                _role_state[_short] = f"{_status} {float(_elapsed):.1f}s"
            with _cams_progress_lock:
                _cams_progress_states[_key] = dict(_role_state)

        try:
            _payload = fetch_route_native_aerosol_bundle_timed(route_points, _t, progress_callback=_cams_role_progress)
            if isinstance(_payload, tuple) and len(_payload) == 2:
                _df, _bundle_meta = _payload
                _bundle_meta = dict(_bundle_meta or {})
                _bundle_meta["cams_prefetch_parallel_workers"] = _cams_parallel_workers
                _bundle_meta["cams_prefetch_parallel_key"] = str(_key)
                _payload = (_df, _bundle_meta)
        except Exception as exc:
            _payload = (pd.DataFrame(), {**_meta, "native_aerosol_status": "UNAVAILABLE", "native_ozone_status": "UNAVAILABLE", "cams_bundle_error": f"{type(exc).__name__}: {exc}"})
        return _key, _t, _payload, perf_counter() - _request_t0

    def _render_cams_prefetch_progress(_completed):
        with _cams_progress_lock:
            _states = {k: dict(v) for k, v in _cams_progress_states.items()}
        _parts = []
        for _idx, (_key, _t) in enumerate(_cams_items, start=1):
            _summary = "｜".join(f"{k}:{v}" for k, v in _states.get(_key, {}).items())
            _parts.append(f"時次 {_idx}/{len(_cams_items)}" + (f"｜{_summary}" if _summary else "｜等待"))
        _progress(0.34 + 0.04 * float(_completed) / max(1, len(_cams_items)), "CAMS 並行預取（唯一時次；每時次內三鏈串行）｜" + "；".join(_parts))

    _future_to_item = {}
    with ThreadPoolExecutor(max_workers=_cams_parallel_workers, thread_name_prefix="cams-time-prefetch") as _pool:
        for _item in _cams_items:
            _future_to_item[_pool.submit(_fetch_cams_time_bundle, _item)] = _item
        _pending = set(_future_to_item)
        while _pending:
            _done, _pending = wait(_pending, timeout=0.5)
            _render_cams_prefetch_progress(len(_future_to_item) - len(_pending))
            for _future in _done:
                try:
                    _key, _t, _payload, _elapsed = _future.result()
                except Exception as exc:
                    _key, _t = _future_to_item[_future]
                    _payload = (pd.DataFrame(), {
                        "native_aerosol_status": "UNAVAILABLE",
                        "native_ozone_status": "UNAVAILABLE",
                        "cams_bundle_error": f"{type(exc).__name__}: {exc}",
                    })
                    _elapsed = perf_counter() - _prefetch_t0
                cams_native_cache[_key] = _payload
                _bundle_meta = _payload[1] if isinstance(_payload, tuple) and len(_payload) == 2 else {}
                for _audit in (_bundle_meta or {}).get("cams_request_audit", []):
                    performance_rows.append({
                        "stage": f"CAMS_{_audit.get('request_role','UNKNOWN')}",
                        "elapsed_seconds": float(_audit.get("elapsed_seconds", 0.0) or 0.0),
                        "cache_status": _audit.get("final_status", _audit.get("status", "")),
                        "cache_key": str(_key),
                    })
                performance_rows.append({"stage": "CAMS_NATIVE_FETCH", "elapsed_seconds": _elapsed, "cache_status": "PREFETCH_PARALLEL" if _cams_parallel_workers > 1 else "PREFETCH", "cache_key": str(_key)})
                _render_cams_prefetch_progress(len(_future_to_item) - len(_pending))
    performance_rows.append({"stage": "CAMS_PREFETCH_SCHEDULER", "elapsed_seconds": perf_counter()-_prefetch_t0, "cache_status": "BOUNDED_UNIQUE_TIME_PARALLEL", "detail": f"workers={_cams_parallel_workers}; unique_times={len(_cams_items)}"})
    performance_rows.append({"stage": "CAMS_PREFETCH_TOTAL", "elapsed_seconds": perf_counter()-_prefetch_t0, "cache_status": "PREFETCH_PARALLEL" if _cams_parallel_workers > 1 else "PREFETCH"})

    # Fetch Open-Meteo Air Quality AOD only when CAMS native/spectral aerosol is
    # unavailable for at least one requested time. This is a fallback, not a
    # second mandatory aerosol request chain.
    _cams_aerosol_complete = True
    for _k in cams_requests:
        _df, _meta = cams_native_cache.get(_k, (pd.DataFrame(), {}))
        if _df is None or _df.empty:
            _cams_aerosol_complete = False; break
    _stage_t0 = perf_counter()
    if _cams_aerosol_complete and len(cams_requests) > 0:
        performance_rows.append({"stage":"AEROSOL_ROUTE_FETCH","elapsed_seconds":0.0,"cache_status":"SKIPPED_CAMS_PRIMARY_READY","detail":"Open-Meteo AOD550 fallback not requested"})
    else:
        _progress(0.385, "CAMS 氣膠不完整，取得 Open-Meteo AOD550 備援…")
        try:
            aerosol_hourly = fetch_route_aerosol(route_points, start, end, tz_name)
            aerosol_error = None
        except Exception as exc:
            aerosol_hourly = pd.DataFrame(); aerosol_error = f"{type(exc).__name__}: {exc}"
        performance_rows.append({"stage":"AEROSOL_ROUTE_FETCH","elapsed_seconds":perf_counter()-_stage_t0,"cache_status":"FETCHED_FALLBACK" if aerosol_error is None else "FAILED","detail":aerosol_error or ""})

    def _angle_progress(idx: int, sub: float, message: str):
        # Reserve 0.40..0.91 for 8 checkpoints and expose sub-stage progress so a
        # CPU-heavy RT step can never masquerade as an infinite wait.
        frac = 0.40 + 0.51 * (idx + max(0.0, min(1.0, sub))) / max(1, len(candidates))
        _progress(frac, message)

    # V8.4.6: precompute all Open-Meteo route snapshots before the expensive
    # per-angle 3-D stages.  This isolates interpolation cost, avoids repeated
    # pandas group/filter work, and makes any provider-frame problem visible
    # before a later angle can look frozen at the first sub-stage label.
    _progress(0.395, f"預先內插 {len(candidates)} 個太陽高度角路徑預報…")
    _snapshot_t0 = perf_counter()
    route_snapshot_cache = {}
    for _si, (_sa, _st, _saz) in enumerate(candidates):
        _key = pd.Timestamp(_st.replace(tzinfo=None))
        _one_t0 = perf_counter()
        route_snapshot_cache[_key] = interpolate_route_at_time(hourly, _st)
        performance_rows.append({"time": _st, "solar_altitude_deg": float(_sa), "stage": "OPENMETEO_ROUTE_INTERPOLATION", "elapsed_seconds": perf_counter()-_one_t0, "cache_status": "PRECOMPUTED"})
        _progress(0.395 + 0.005 * (_si + 1) / max(1, len(candidates)), f"路徑預報內插：{_si+1}/{len(candidates)}")
    performance_rows.append({"stage": "OPENMETEO_ROUTE_INTERPOLATION_TOTAL", "elapsed_seconds": perf_counter()-_snapshot_t0, "cache_status": "PRECOMPUTED"})

    _angles_t0 = perf_counter()
    for candidate_index, (angle, t, az) in enumerate(candidates):
        _angle_t0 = perf_counter()
        label = f"太陽高度角 {float(angle):.1f}°（{candidate_index+1}/{len(candidates)}）"
        _angle_progress(candidate_index, 0.00, f"{label}：載入已內插路徑預報…")
        snap = route_snapshot_cache.get(pd.Timestamp(t.replace(tzinfo=None)), pd.DataFrame()).copy()
        _angle_progress(candidate_index, 0.04, f"{label}：合併 GFS 原生雲微物理…")
        native_meta = {"native_status": "UNAVAILABLE", **native_provider_status()}
        cache_key = None
        try:
            run, lead = resolve_run_and_lead(t)
            cache_key = (run.isoformat(), int(lead))
            native_df, native_meta = native_cache.get(cache_key, (pd.DataFrame(), native_meta))
            if native_df is not None and not native_df.empty:
                snap = merge_native_into_snapshot(snap, native_df)
        except Exception as exc:
            native_meta = {**native_meta, "native_status": "FAILED", "native_error": f"{type(exc).__name__}: {exc}"}
        _angle_progress(candidate_index, 0.10, f"{label}：建立 V1.0 CloudScene／Canvas-specific 光路…")
        _v1 = build_r2_geometry_tables(
            snap, DEFAULT_PRESSURE_LEVELS_HPA,
            observer_lat=lat, observer_lon=lon,
            solar_altitude_deg=float(angle), solar_azimuth_deg=float(az),
            earth_radius_km=cfg.earth_radius_km,
            route_end_km=cfg.dynamic_domain_max_km,
            route_step_km=cfg.dynamic_route_step_km,
            route_sampling_nodes_km=cfg.dynamic_distance_samples_km,
            valid_time=t,
        )
        for _key, _dest in [
            ("cloud_layers", v1_cloud_layer_frames),
            ("canvases", v1_canvas_frames),
            ("direct_solar", v1_direct_solar_frames),
            ("solar_rays", v1_solar_ray_frames),
            ("dependency_status", v1_dependency_frames),
            ("solar_geometry", v1_solar_geometry_frames),
        ]:
            _df = _v1.get(_key, pd.DataFrame())
            if _df is not None and not _df.empty:
                _dest.append(_df)
        # Legacy candidate evaluation remains temporarily available as a
        # diagnostic compatibility branch only. It is not a PhysicsCore V1
        # contract and must not gate the R2 geometry/illumination outputs.
        ev = evaluate_candidate(snap, angle, cfg)
        # V8.4.0.5: split the former generic "建立 3D 雲體" stage into four
        # explicit checkpoints.  This makes a slow cloud-volume builder visible
        # instead of making the UI appear frozen for several minutes.
        _angle_progress(candidate_index, 0.20, f"{label}：建立粗層雲體照明格點…")
        _ts = perf_counter()
        forecast_voxels = build_forecast_voxel_illumination(snap, angle, cfg)
        performance_rows.append({"time": t, "solar_altitude_deg": float(angle), "stage": "FORECAST_VOXEL_ILLUMINATION", "elapsed_seconds": perf_counter()-_ts, "cache_status": "COMPUTED"})

        _angle_progress(candidate_index, 0.245, f"{label}：重建 0.5 km 垂直雲柱…")
        _ts = perf_counter()
        reconstructed_voxels, reconstructed_columns = reconstruct_cloud_columns_3d(snap, angle, cfg)
        performance_rows.append({"time": t, "solar_altitude_deg": float(angle), "stage": "RECONSTRUCTED_0P5KM_CLOUD_COLUMN", "elapsed_seconds": perf_counter()-_ts, "cache_status": "COMPUTED"})

        _angle_progress(candidate_index, 0.295, f"{label}：建立氣壓層 3D 雲體…")
        _ts = perf_counter()
        profile_voxels, profile_columns = build_pressure_profile_cloud_volume(snap, angle, cfg)
        performance_rows.append({"time": t, "solar_altitude_deg": float(angle), "stage": "PRESSURE_PROFILE_CLOUD_VOLUME", "elapsed_seconds": perf_counter()-_ts, "cache_status": "COMPUTED"})

        _angle_progress(candidate_index, 0.34, f"{label}：建立 GFS 原生雲微物理體積…")
        # V8.4.0.6: native GFS condensate volume depends on the resolved GFS run/lead,
        # not on solar altitude. Reuse it for every angle sharing the same forecast
        # state. This changes scheduling only; no cloud physics is altered.
        _ts = perf_counter()
        _nv_key = cache_key
        if _nv_key is not None and _nv_key in native_volume_cache:
            _nv, _nc = native_volume_cache[_nv_key]
            native_voxels, native_columns = _nv.copy(), _nc.copy()
            _nv_status = "HIT"
        else:
            native_voxels, native_columns = build_native_cloud_volume(
                snap, DEFAULT_PRESSURE_LEVELS_HPA, VOXEL_ALTITUDE_CENTERS_KM, VOXEL_VERTICAL_STEP_KM
            )
            if _nv_key is not None:
                native_volume_cache[_nv_key] = (native_voxels.copy(), native_columns.copy())
            _nv_status = "MISS"
        performance_rows.append({"time": t, "solar_altitude_deg": float(angle), "stage": "GFS_NATIVE_CLOUD_VOLUME", "elapsed_seconds": perf_counter()-_ts, "cache_status": _nv_status, "cache_key": str(_nv_key)})
        _angle_progress(candidate_index, 0.38, f"{label}：計算雲層 3D 光學阻擋…")
        _ts = perf_counter()
        _opt_proxy_t0 = perf_counter()
        optical_voxels = apply_3d_optical_blocking(profile_voxels, angle, cfg)
        optical_columns = summarize_vertical_blocking(optical_voxels)
        performance_rows.append({"time": t, "solar_altitude_deg": float(angle), "stage": "CLOUD_PROXY_RAY_BLOCKING", "elapsed_seconds": perf_counter()-_opt_proxy_t0, "cache_status": "COMPUTED"})

        _native_base_t0 = perf_counter()
        if _nv_key is not None and _nv_key in native_optical_base_cache:
            _native_optical_base = native_optical_base_cache[_nv_key]
            _native_base_status = "HIT"
        else:
            _native_optical_base = add_native_optical_properties(native_voxels) if not native_voxels.empty else native_voxels.copy()
            if _nv_key is not None:
                native_optical_base_cache[_nv_key] = _native_optical_base.copy()
            _native_base_status = "MISS"
        performance_rows.append({"time": t, "solar_altitude_deg": float(angle), "stage": "NATIVE_CLOUD_OPTICAL_BASE", "elapsed_seconds": perf_counter()-_native_base_t0, "cache_status": _native_base_status, "cache_key": str(_nv_key)})
        _native_ray_t0 = perf_counter()
        native_optical_voxels = apply_native_microphysical_optical_blocking(_native_optical_base, angle, cfg, optical_properties_ready=True)
        native_optical_columns = summarize_native_optical_blocking(native_optical_voxels)
        performance_rows.append({"time": t, "solar_altitude_deg": float(angle), "stage": "NATIVE_CLOUD_RAY_BLOCKING", "elapsed_seconds": perf_counter()-_native_ray_t0, "cache_status": "COMPUTED"})
        performance_rows.append({"time": t, "solar_altitude_deg": float(angle), "stage": "CLOUD_3D_OPTICAL_BLOCKING", "elapsed_seconds": perf_counter()-_ts, "cache_status": "COMPUTED"})
        aerosol_snap = interpolate_route_aerosol_at_time(aerosol_hourly, t) if not aerosol_hourly.empty else pd.DataFrame()
        # V8.3.3: optional credential-gated native CAMS 3-D aerosol extinction.
        # A CAMS bundle contains pressure-level extinction at 532 nm plus real
        # multi-wavelength column AOD when ADS returns those fields. Failure never
        # becomes clear sky; the V8.3.2 Open-Meteo AOD diagnostic remains separate.
        cams_aerosol_meta = {"native_aerosol_status": "UNAVAILABLE", "native_ozone_status": "UNAVAILABLE", **native_aerosol_provider_status()}
        cams_aerosol_snap = pd.DataFrame()
        try:
            cams_run, cams_lead = resolve_cams_run_and_lead(t)
            cams_key = (cams_run.isoformat(), int(cams_lead))
            cams_aerosol_snap, cams_aerosol_meta = cams_native_cache.get(cams_key, (pd.DataFrame(), cams_aerosol_meta))
        except Exception as exc:
            cams_aerosol_meta = {**cams_aerosol_meta, "native_aerosol_status": "FAILED", "native_ozone_status": "FAILED", "native_aerosol_error": f"{type(exc).__name__}: {exc}", "native_ozone_error": f"{type(exc).__name__}: {exc}"}
        spectral_source_snap = cams_aerosol_snap if not cams_aerosol_snap.empty else aerosol_snap
        _spec_key = cams_key if 'cams_key' in locals() else cache_key
        if _spec_key is not None and _spec_key in aerosol_spectral_cache:
            aerosol_spectral_snap = aerosol_spectral_cache[_spec_key].copy()
            _aero_spec_status = "HIT"
        else:
            aerosol_spectral_snap = derive_route_spectral_aod(spectral_source_snap) if not spectral_source_snap.empty else pd.DataFrame()
            if _spec_key is not None:
                aerosol_spectral_cache[_spec_key] = aerosol_spectral_snap.copy()
            _aero_spec_status = "MISS"
        performance_rows.append({"time": t, "solar_altitude_deg": float(angle), "stage": "AEROSOL_SPECTRAL_DERIVATION", "elapsed_seconds": 0.0, "cache_status": _aero_spec_status, "cache_key": str(_spec_key)})
        _angle_progress(candidate_index, 0.58, f"{label}：建立氣體狀態…")
        _ts = perf_counter()
        _o3_bind_t0 = perf_counter()
        _gas_key = (cache_key, cams_key if 'cams_key' in locals() else None)
        if _gas_key in gas_profile_cache:
            gas_profile = gas_profile_cache[_gas_key].copy()
            _gas_cache_status = "HIT"
        else:
            gas_profile = build_gas_profile(snap, GAS_PRESSURE_LEVELS_HPA, ozone_snapshot=cams_aerosol_snap)
            gas_profile_cache[_gas_key] = gas_profile.copy()
            _gas_cache_status = "MISS"
        performance_rows.append({"time": t, "solar_altitude_deg": float(angle), "stage": "GAS_PROFILE_CACHE", "elapsed_seconds": 0.0, "cache_status": _gas_cache_status, "cache_key": str(_gas_key)})
        performance_rows.append({"time": t, "solar_altitude_deg": float(angle), "stage": "CAMS_O3_PROFILE_BINDING", "elapsed_seconds": perf_counter()-_o3_bind_t0, "cache_status": "BOUND" if gas_profile.get("o3_mole_fraction", pd.Series(dtype=float)).notna().any() else "MISSING"})
        _gas_ctx_t0 = perf_counter()
        if _gas_key in gas_rt_context_cache:
            gas_rt_context = gas_rt_context_cache[_gas_key]
            _gas_ctx_status = "HIT"
        else:
            gas_rt_context = prepare_gas_rt_context(gas_profile)
            gas_rt_context_cache[_gas_key] = gas_rt_context
            _gas_ctx_status = "MISS"
        performance_rows.append({"time": t, "solar_altitude_deg": float(angle), "stage": "GAS_RT_PREPARED_CONTEXT", "elapsed_seconds": perf_counter()-_gas_ctx_t0, "cache_status": _gas_ctx_status, "cache_key": str(_gas_key), "detail": f"bands={','.join(map(str,gas_rt_context.wavelengths))}; valid={gas_rt_context.valid}; cause={gas_rt_context.failure_cause}"})
        _angle_progress(candidate_index, 0.61, f"{label}：開始 550–750 nm 六波段光譜 RT…")
        def _spectral_progress(_frac, _msg):
            _angle_progress(candidate_index, 0.61 + 0.25*max(0.0,min(1.0,float(_frac))), f"{label}：光譜 RT｜{_msg}")
        _rt_filter_t0 = perf_counter()
        rt_target_voxels = _select_v1_canvas_rt_targets(native_optical_voxels, _v1.get("canvas_objects", ()), _v1.get("scene"))
        _mode = rt_target_voxels.get("v1_rt_target_mode", pd.Series(["NONE"])).iloc[0] if not rt_target_voxels.empty else "NONE"
        performance_rows.append({"time": t, "solar_altitude_deg": float(angle), "stage": "V1_RT_CANDIDATE_FILTER", "elapsed_seconds": perf_counter()-_rt_filter_t0, "cache_status": "FILTERED", "detail": f"targets={len(rt_target_voxels)}; source_voxels={len(native_optical_voxels)}; mode={_mode}"})
        spectral_voxels = build_spectral_rt(
            rt_target_voxels, angle, aerosol_snapshot=spectral_source_snap,
            cams_native_aerosol_snapshot=cams_aerosol_snap, angstrom_exponent=None,
            earth_radius_km=cfg.earth_radius_km, gas_profile=gas_profile,
            progress_callback=_spectral_progress,
            prepared_route_spectral_aod=aerosol_spectral_snap,
            gas_prepared_context=gas_rt_context,
        )
        performance_rows.append({"time": t, "solar_altitude_deg": float(angle), "stage": "GAS_AND_SPECTRAL_RT", "elapsed_seconds": perf_counter()-_ts, "cache_status": "COMPUTED"})
        _angle_progress(candidate_index, 0.88, f"{label}：彙整光譜與垂直欄位…")
        spectral_columns = summarize_spectral_rt(spectral_voxels)

        # PhysicsCore V1.0-R3: connect Canvas-specific native geometry to the
        # route-resolved spectral evidence. Missing components remain local to
        # the dependent optical/illumination outputs; they do not erase the
        # already-known CloudScene or DirectSolarFraction.
        _angle_progress(candidate_index, 0.955, f"{label}：建立 V1.0 六波段 OpticalPathResult…")
        _precip_path_evidence = build_precipitation_path_evidence(_v1.get("canvas_objects", ()), snap, valid_time=t)
        _v1["precipitation_path_evidence"] = _precip_path_evidence
        if _precip_path_evidence is not None and not _precip_path_evidence.empty:
            _pp=_precip_path_evidence.copy(); _pp.insert(1,"solar_altitude_deg",float(angle)); v1_precipitation_path_frames.append(_pp)
        _r3 = build_r3_optical_tables(
            scene=_v1["scene"],
            canvases=_v1.get("canvas_objects", ()),
            direct_solar=_v1.get("direct_solar", pd.DataFrame()),
            solar_rays=_v1.get("solar_rays", pd.DataFrame()),
            spectral_voxels=spectral_voxels,
            solar_altitude_deg=float(angle),
            earth_radius_km=cfg.earth_radius_km,
            valid_time=t,
            precipitation_path_evidence=_precip_path_evidence,
        )
        for _key, _dest in [
            ("ray_cloud_intersections", v1_ray_cloud_intersection_frames),
            ("cloud_horizontal_support", v1_cloud_horizontal_support_frames),
            ("native_condensate_support_diagnostics", v1_native_condensate_support_diagnostic_frames),
            ("spectral_optical_paths", v1_spectral_optical_path_frames),
            ("cloud_base_illumination", v1_cloud_base_illumination_frames),
            ("uncertainty", v1_uncertainty_frames),
            ("optical_bottlenecks", v1_optical_bottleneck_frames),
        ]:
            _df = _r3.get(_key, pd.DataFrame())
            if _df is not None and not _df.empty:
                _dest.append(_df)

        # PhysicsCore V1.0-R4.9: resolve target-Canvas optical evidence before
        # Formation.  Exact direct-native COT and bounded adjacent-native
        # hypotheses remain distinct; CF/RH/geometry never fabricate COT.
        _angle_progress(candidate_index, 0.968, f"{label}：解析 Target Canvas Optical Evidence…")
        _target_canvas_optics = build_target_canvas_optical_evidence(
            _v1["scene"], _v1.get("canvas_objects", ()),
            solar_altitude_deg=float(angle), valid_time=t,
        )
        if _target_canvas_optics is not None and not _target_canvas_optics.empty:
            v1_target_canvas_optical_evidence_frames.append(_target_canvas_optics)
            _target_summary = summarize_target_canvas_optical_evidence(_target_canvas_optics)
            if _target_summary is not None and not _target_summary.empty:
                _target_summary.insert(0, "time", t)
                v1_target_canvas_optical_summary_frames.append(_target_summary)

        # PhysicsCore V1.0-R4.9 Formation consumes the resolver output. Missing
        # or conflicting target optics stays Unknown; bounded hypotheses are
        # exported but not silently promoted to exact radiance.
        _angle_progress(candidate_index, 0.972, f"{label}：建立 R4.9 Canvas Optical Response／Formation…")
        _r4 = build_r4_formation_tables(
            scene=_v1["scene"],
            canvases=_v1.get("canvas_objects", ()),
            cloud_base_illumination=_r3.get("cloud_base_illumination", pd.DataFrame()),
            spectral_voxels=spectral_voxels,
            solar_altitude_deg=float(angle),
            valid_time=t,
            target_optical_evidence=_target_canvas_optics,
        )
        if not _r4.get("canvas_radiance", pd.DataFrame()).empty:
            v1_canvas_radiance_frames.append(_r4["canvas_radiance"])
        if not _r4.get("formation", pd.DataFrame()).empty:
            v1_formation_frames.append(_r4["formation"])
        if not _r4.get("spectral_colour", pd.DataFrame()).empty:
            v1_spectral_colour_frames.append(_r4["spectral_colour"])
        _angle_progress(candidate_index, 0.98, f"{label}：完成")
        performance_rows.append({"time": t, "solar_altitude_deg": float(angle), "stage": "PER_ANGLE_PHYSICS_TOTAL", "elapsed_seconds": perf_counter()-_angle_t0, "cache_status": "COMPUTED"})
        angle_f = float(angle)
        is_core = angle_f in core_set
        is_late = angle_f in late_set

        if angle_f == 0.0:
            phase = "HORIZON BASELINE"
        elif is_core and is_late:
            phase = "CORE / LATE-GLOW TRANSITION"
        elif is_core:
            phase = "FIRECLOUD CORE"
        elif is_late:
            phase = "LATE GLOW / THIRD BURN"
        else:
            phase = "TWILIGHT DIAGNOSTIC"

        # Keep the physical/visual values visible for diagnostics at every civil-
        # twilight checkpoint, but only core angles may drive GO/NO-GO selection.
        displayed_operational = ev["operational_decision"] if is_core else "DIAGNOSTIC ONLY"

        result_rows.append({
            "solar_altitude_deg": angle,
            "time": t,
            "solar_azimuth_deg": az,
            "twilight_phase": phase,
            "core_score_eligible": is_core,
            "late_glow_diagnostic": is_late,
            "physics_score": ev["physics_score"],
            "visual_magnitude": ev["visual_magnitude"],
            "data_completeness": ev["data_completeness"],
            "operational_decision": displayed_operational,
        })
        details[angle] = {
            "snapshot": snap,
            "twilight_phase": phase,
            "core_score_eligible": is_core,
            "late_glow_diagnostic": is_late,
            "forecast_voxels": forecast_voxels,
            "reconstructed_voxels": reconstructed_voxels,
            "reconstructed_columns": reconstructed_columns,
            "profile_voxels": profile_voxels,
            "profile_columns": profile_columns,
            "native_voxels": native_voxels,
            "native_columns": native_columns,
            "native_provider_metadata": native_meta,
            "optical_voxels": optical_voxels,
            "optical_columns": optical_columns,
            "native_optical_voxels": native_optical_voxels,
            "native_optical_columns": native_optical_columns,
            "spectral_voxels": spectral_voxels,
            "spectral_columns": spectral_columns,
            "gas_profile": gas_profile,
            "hitran_backend_status": hitran_backend_status(),
            "aerosol_spectral_snapshot": aerosol_spectral_snap,
            "cams_native_aerosol_snapshot": cams_aerosol_snap,
            "cams_native_aerosol_metadata": cams_aerosol_meta,
            **ev,
        }

    performance_rows.append({"stage": "ALL_ANGLES_PHYSICS_TOTAL", "elapsed_seconds": perf_counter()-_angles_t0, "cache_status": "COMPUTED"})
    _progress(0.93, "彙整民用曙暮光時間軸與矩陣…")
    _aggregate_t0 = perf_counter()
    summary = pd.DataFrame(result_rows).sort_values("time")
    # IMPORTANT: expanding the timeline to 0...-6° must not change the existing
    # firecloud core selection domain. Only -0.5...-4° candidates can win.
    valid = summary[summary["core_score_eligible"]].dropna(subset=["physics_score"])
    selected_angle = None
    if not valid.empty:
        # Prefer highest physical candidate; ties favor higher visual magnitude then completeness.
        ranked = valid.sort_values(["physics_score", "visual_magnitude", "data_completeness"], ascending=False)
        selected_angle = float(ranked.iloc[0]["solar_altitude_deg"])

    illumination_matrix, dynamic_rez = build_geometry_diagnostics(cfg)
    voxel_frames = []
    for angle, t, _az in candidates:
        vf = details[angle]["forecast_voxels"].copy()
        if not vf.empty:
            vf["time"] = t
            voxel_frames.append(vf)
    forecast_voxel_matrix = pd.concat(voxel_frames, ignore_index=True) if voxel_frames else pd.DataFrame()
    recon_v_frames, recon_c_frames = [], []
    for angle, t, _az in candidates:
        rv = details[angle]["reconstructed_voxels"].copy()
        rc = details[angle]["reconstructed_columns"].copy()
        if not rv.empty:
            rv["time"] = t; recon_v_frames.append(rv)
        if not rc.empty:
            rc["time"] = t; recon_c_frames.append(rc)
    reconstructed_voxel_matrix = pd.concat(recon_v_frames, ignore_index=True) if recon_v_frames else pd.DataFrame()
    reconstructed_cloud_columns = pd.concat(recon_c_frames, ignore_index=True) if recon_c_frames else pd.DataFrame()
    profile_v_frames, profile_c_frames, native_v_frames, native_c_frames, optical_v_frames, optical_c_frames, native_opt_v_frames, native_opt_c_frames, spectral_v_frames, spectral_c_frames, aerosol_spec_frames, cams_aerosol_frames, gas_profile_frames = [], [], [], [], [], [], [], [], [], [], [], [], []
    for angle, t, _az in candidates:
        for key, dest in [("profile_voxels", profile_v_frames), ("profile_columns", profile_c_frames),
                          ("native_voxels", native_v_frames), ("native_columns", native_c_frames),
                          ("optical_voxels", optical_v_frames), ("optical_columns", optical_c_frames),
                          ("native_optical_voxels", native_opt_v_frames), ("native_optical_columns", native_opt_c_frames),
                          ("spectral_voxels", spectral_v_frames), ("spectral_columns", spectral_c_frames)]:
            df = details[angle][key].copy()
            if not df.empty:
                df["time"] = t
                if "solar_altitude_deg" not in df.columns:
                    df["solar_altitude_deg"] = float(angle)
                dest.append(df)
        adf = details[angle].get("aerosol_spectral_snapshot", pd.DataFrame()).copy()
        if not adf.empty:
            adf["time"] = t
            adf["solar_altitude_deg"] = float(angle)
            aerosol_spec_frames.append(adf)
        gpf = details[angle].get("gas_profile", pd.DataFrame()).copy()
        if not gpf.empty:
            gpf["time"] = t; gpf["solar_altitude_deg"] = float(angle); gas_profile_frames.append(gpf)
        cdf = details[angle].get("cams_native_aerosol_snapshot", pd.DataFrame()).copy()
        if not cdf.empty:
            cdf["time"] = t
            cdf["solar_altitude_deg"] = float(angle)
            cams_aerosol_frames.append(cdf)
    pressure_profile_voxel_matrix = pd.concat(profile_v_frames, ignore_index=True) if profile_v_frames else pd.DataFrame()
    pressure_profile_cloud_columns = pd.concat(profile_c_frames, ignore_index=True) if profile_c_frames else pd.DataFrame()
    native_cloud_voxel_matrix = pd.concat(native_v_frames, ignore_index=True) if native_v_frames else pd.DataFrame()
    native_cloud_columns = pd.concat(native_c_frames, ignore_index=True) if native_c_frames else pd.DataFrame()
    optical_blocking_voxel_matrix = pd.concat(optical_v_frames, ignore_index=True) if optical_v_frames else pd.DataFrame()
    vertical_blocking_columns = pd.concat(optical_c_frames, ignore_index=True) if optical_c_frames else pd.DataFrame()
    native_optical_blocking_voxel_matrix = pd.concat(native_opt_v_frames, ignore_index=True) if native_opt_v_frames else pd.DataFrame()
    native_optical_blocking_columns = pd.concat(native_opt_c_frames, ignore_index=True) if native_opt_c_frames else pd.DataFrame()
    spectral_rt_voxel_matrix = pd.concat(spectral_v_frames, ignore_index=True) if spectral_v_frames else pd.DataFrame()
    spectral_rt_columns = pd.concat(spectral_c_frames, ignore_index=True) if spectral_c_frames else pd.DataFrame()
    aerosol_spectral_route_snapshots = pd.concat(aerosol_spec_frames, ignore_index=True) if aerosol_spec_frames else pd.DataFrame()
    cams_native_aerosol_route_snapshots = pd.concat(cams_aerosol_frames, ignore_index=True) if cams_aerosol_frames else pd.DataFrame()
    gas_profile_route_snapshots = pd.concat(gas_profile_frames, ignore_index=True) if gas_profile_frames else pd.DataFrame()

    v1_cloud_layers = pd.concat(v1_cloud_layer_frames, ignore_index=True) if v1_cloud_layer_frames else pd.DataFrame()
    v1_canvas_candidates = pd.concat(v1_canvas_frames, ignore_index=True) if v1_canvas_frames else pd.DataFrame()
    v1_direct_solar = pd.concat(v1_direct_solar_frames, ignore_index=True) if v1_direct_solar_frames else pd.DataFrame()
    v1_solar_rays = pd.concat(v1_solar_ray_frames, ignore_index=True) if v1_solar_ray_frames else pd.DataFrame()
    v1_dependency_status = pd.concat(v1_dependency_frames, ignore_index=True) if v1_dependency_frames else pd.DataFrame()
    v1_solar_geometry = pd.concat(v1_solar_geometry_frames, ignore_index=True) if v1_solar_geometry_frames else pd.DataFrame()
    v1_ray_cloud_intersections = pd.concat(v1_ray_cloud_intersection_frames, ignore_index=True) if v1_ray_cloud_intersection_frames else pd.DataFrame()
    v1_cloud_horizontal_support = pd.concat(v1_cloud_horizontal_support_frames, ignore_index=True) if v1_cloud_horizontal_support_frames else pd.DataFrame()
    v1_native_condensate_support_diagnostics = pd.concat(v1_native_condensate_support_diagnostic_frames, ignore_index=True) if v1_native_condensate_support_diagnostic_frames else pd.DataFrame()
    v1_spectral_optical_paths = pd.concat(v1_spectral_optical_path_frames, ignore_index=True) if v1_spectral_optical_path_frames else pd.DataFrame()
    v1_cloud_base_illumination = pd.concat(v1_cloud_base_illumination_frames, ignore_index=True) if v1_cloud_base_illumination_frames else pd.DataFrame()
    v1_uncertainty = pd.concat(v1_uncertainty_frames, ignore_index=True) if v1_uncertainty_frames else pd.DataFrame()
    v1_optical_bottlenecks = pd.concat(v1_optical_bottleneck_frames, ignore_index=True) if v1_optical_bottleneck_frames else pd.DataFrame()
    v1_canvas_radiance = pd.concat(v1_canvas_radiance_frames, ignore_index=True) if v1_canvas_radiance_frames else pd.DataFrame()
    v1_formation = pd.concat(v1_formation_frames, ignore_index=True) if v1_formation_frames else pd.DataFrame()
    v1_spectral_colour = pd.concat(v1_spectral_colour_frames, ignore_index=True) if v1_spectral_colour_frames else pd.DataFrame()
    v1_precipitation_path_evidence = pd.concat(v1_precipitation_path_frames, ignore_index=True) if v1_precipitation_path_frames else pd.DataFrame()
    v1_target_canvas_optical_evidence = pd.concat(v1_target_canvas_optical_evidence_frames, ignore_index=True) if v1_target_canvas_optical_evidence_frames else pd.DataFrame()
    v1_target_canvas_optical_summary = pd.concat(v1_target_canvas_optical_summary_frames, ignore_index=True) if v1_target_canvas_optical_summary_frames else pd.DataFrame()
    _lut_path = Path(__file__).resolve().parent.parent / "hitran_runtime" / "firecloud_600_750nm_band_coefficients.csv"
    v1_six_band_spectroscopy_readiness = build_six_band_spectroscopy_readiness(_lut_path)
    v1_cloud_optical_validation = build_cloud_optical_validation_table(
        cloud_layers=v1_cloud_layers, canvases=v1_canvas_candidates,
        horizontal_support=v1_cloud_horizontal_support, intersections=v1_ray_cloud_intersections,
    )
    v1_formation_prerequisites = build_formation_prerequisite_table(
        spectral_paths=v1_spectral_optical_paths, canvas_radiance=v1_canvas_radiance, formation=v1_formation,
    )

    # V1 Core runtime summary is intentionally dimension/evidence based. There
    # is no Physics Score, GO/NO-GO, or single global completeness percentage.
    _v1_summary_rows = []
    for _angle, _time, _az in candidates:
        _a = float(_angle)
        _cl = v1_cloud_layers[pd.to_numeric(v1_cloud_layers.get("solar_altitude_deg"), errors="coerce").eq(_a)] if not v1_cloud_layers.empty else pd.DataFrame()
        _ca = v1_canvas_candidates[pd.to_numeric(v1_canvas_candidates.get("solar_altitude_deg"), errors="coerce").eq(_a)] if not v1_canvas_candidates.empty else pd.DataFrame()
        _ds = v1_direct_solar[pd.to_numeric(v1_direct_solar.get("solar_altitude_deg"), errors="coerce").eq(_a)] if not v1_direct_solar.empty else pd.DataFrame()
        _dep0 = v1_dependency_status[(pd.to_numeric(v1_dependency_status.get("solar_altitude_deg"), errors="coerce").eq(_a)) & (v1_dependency_status.get("dependency", pd.Series(dtype=str)).eq("CLOUD_GEOMETRY"))] if not v1_dependency_status.empty else pd.DataFrame()
        _geom = float(pd.to_numeric(_dep0.get("completeness"), errors="coerce").iloc[0]) if not _dep0.empty and pd.notna(pd.to_numeric(_dep0.get("completeness"), errors="coerce").iloc[0]) else float("nan")
        _states = _ds.get("ray_status", pd.Series(dtype=str)).astype(str) if not _ds.empty else pd.Series(dtype=str)
        _fr = v1_formation[pd.to_numeric(v1_formation.get("solar_altitude_deg"), errors="coerce").eq(_a)].copy() if not v1_formation.empty else pd.DataFrame()
        _v1_summary_rows.append({
            "time": _time, "solar_altitude_deg": _a, "solar_azimuth_deg": float(_az),
            "cloud_layer_count": int(len(_cl)), "canvas_candidate_count": int(len(_ca)),
            "full_solar_canvas_count": int((_states == "FULL_SOLAR_DISK").sum()),
            "partial_solar_canvas_count": int((_states == "PARTIAL_SOLAR_DISK").sum()),
            "earth_shadowed_canvas_count": int((_states == "FULL_EARTH_SHADOW").sum()),
            "cloud_geometry_completeness": _geom,
            "v1_geometry_status": "READY" if (len(_ca) > 0 and (_states.isin(["FULL_SOLAR_DISK","PARTIAL_SOLAR_DISK"]).any())) else ("NO_ILLUMINATED_CANVAS" if len(_ca)>0 else "NO_CANVAS_EVIDENCE"),
            "formation_status": (
                str(_fr.iloc[0]["formation_state"]) if not _fr.empty else "NO_R4_FORMATION_EVIDENCE"
            ),
            "formation_brightness": (float(_fr.iloc[0]["brightness"]) if not _fr.empty and pd.notna(_fr.iloc[0]["brightness"]) else float("nan")),
            "formation_redness": (float(_fr.iloc[0]["redness"]) if not _fr.empty and pd.notna(_fr.iloc[0]["redness"]) else float("nan")),
            "formation_effective_illuminated_area": (float(_fr.iloc[0]["effective_illuminated_area"]) if not _fr.empty and pd.notna(_fr.iloc[0]["effective_illuminated_area"]) else float("nan")),
            "optical_path_status": (
                "R3_UNCERTAIN_OPTICS" if not v1_cloud_base_illumination.empty else "NO_R3_ILLUMINATION_EVIDENCE"
            ),
            "viewing_status": "NOT_YET_CONNECTED_R4",
        })
    v1_core_summary = pd.DataFrame(_v1_summary_rows)

    physics_data_completeness = _build_physics_data_completeness(details, candidates, summary)

    # V8.4.9.1: the headline summary completeness must reflect the actual
    # mandatory PhysicsCore data chain, not only the legacy path/REZ forecast
    # coverage. Missing CAMS aerosol/O3/gas/full spectral RT can therefore no
    # longer coexist with summary data_completeness == 1.0.
    mandatory_layers = ["FORECAST_CLOUD", "NATIVE_AEROSOL", "O3_PROFILE",
                        "GAS_PROFILE", "HITRAN_SPECTROSCOPY", "GAS_VERTICAL_DOMAIN",
                        "SPECTRAL_AEROSOL_PATH", "FULL_SPECTRAL_RT"]
    operational_rows=[]
    if not physics_data_completeness.empty:
        for angle,g in physics_data_completeness.groupby("solar_altitude_deg", dropna=False):
            mg=g[g["layer"].isin(mandatory_layers)]
            vals=pd.to_numeric(mg["completeness"],errors="coerce").dropna()
            overall=float(vals.min()) if len(vals) else 0.0
            failed=mg[mg["status"].astype(str).isin(["FAILED","MISSING","NOT_CONFIGURED"])]
            partial=mg[mg["status"].astype(str).eq("PARTIAL")]
            if not failed.empty: status="MISSING"; reason=";".join(failed["layer"].astype(str).tolist())+"_UNAVAILABLE"
            elif not partial.empty or overall < 0.999: status="PARTIAL"; reason="MANDATORY_PHYSICS_INPUTS_PARTIAL"
            else: status="READY"; reason=""
            tval=g["time"].iloc[0] if "time" in g and len(g) else pd.NaT
            operational_rows.append({"time":tval,"solar_altitude_deg":float(angle),"layer":"OVERALL_OPERATIONAL_INPUTS",
                                     "status":status,"completeness":overall,"provider":"PhysicsCore mandatory layer gate",
                                     "missing_reason":reason})
            mask=np.isclose(pd.to_numeric(summary["solar_altitude_deg"],errors="coerce"),float(angle))
            summary.loc[mask,"data_completeness"]=overall
            if overall < cfg.min_data_completeness:
                coremask=mask & summary["core_score_eligible"].astype(bool)
                summary.loc[coremask,"operational_decision"]="UNKNOWN / DATA INCOMPLETE"
        if operational_rows:
            physics_data_completeness=pd.concat([physics_data_completeness,pd.DataFrame(operational_rows)],ignore_index=True)

    # R2 dependency-aware evidence bridge: expose every legacy provider/RT
    # dependency independently without collapsing them to a single minimum.
    # This makes CAMS/O3/aerosol Missing affect only dependent downstream
    # quantities in the V1 contract. The inherited OVERALL_OPERATIONAL_INPUTS
    # row remains legacy diagnostic data only.
    if not physics_data_completeness.empty:
        _dep = physics_data_completeness[physics_data_completeness["layer"].ne("OVERALL_OPERATIONAL_INPUTS")].copy()
        if not _dep.empty:
            _dep["dependency"] = _dep["layer"].astype(str)
            _status_map = {"READY":"FULL", "PARTIAL":"PARTIAL_OPTICS", "MISSING":"MISSING", "FAILED":"MISSING", "NOT_CONFIGURED":"MISSING"}
            _dep["evidence_state"] = _dep["status"].astype(str).map(_status_map).fillna("MISSING")
            _dep["criticality"] = _dep["dependency"].map({
                "FORECAST_CLOUD":"HIGH", "NATIVE_AEROSOL":"MEDIUM", "O3_PROFILE":"MEDIUM",
                "GAS_PROFILE":"HIGH", "HITRAN_SPECTROSCOPY":"HIGH", "GAS_VERTICAL_DOMAIN":"HIGH",
                "SPECTRAL_AEROSOL_PATH":"MEDIUM", "FULL_SPECTRAL_RT":"HIGH",
            }).fillna("MEDIUM")
            _dep["affected_outputs"] = _dep["dependency"].map({
                "FORECAST_CLOUD":"CloudScene,CanvasCandidate,OpticalPath",
                "NATIVE_AEROSOL":"SpectralOpticalPath,Formation",
                "O3_PROFILE":"SpectralOpticalPath,Formation",
                "GAS_PROFILE":"SpectralOpticalPath,Formation",
                "HITRAN_SPECTROSCOPY":"SpectralOpticalPath,Formation",
                "GAS_VERTICAL_DOMAIN":"SpectralOpticalPath,Formation",
                "SPECTRAL_AEROSOL_PATH":"SpectralOpticalPath,Formation",
                "FULL_SPECTRAL_RT":"Formation",
            }).fillna("DIAGNOSTIC")
            _dep = _dep[[c for c in ["time","solar_altitude_deg","dependency","status","evidence_state","completeness","criticality","affected_outputs","provider","missing_reason"] if c in _dep.columns]]
            v1_dependency_status = pd.concat([v1_dependency_status, _dep], ignore_index=True, sort=False)

    # Re-rank only after the real mandatory-layer completeness gate has been
    # propagated into summary. Physically scored but data-incomplete candidates
    # remain visible, yet they cannot silently win an operational selection.
    valid = summary[summary["core_score_eligible"] & (pd.to_numeric(summary["data_completeness"],errors="coerce") >= cfg.min_data_completeness)].dropna(subset=["physics_score"])
    selected_angle = None
    if not valid.empty:
        ranked = valid.sort_values(["physics_score", "visual_magnitude", "data_completeness"], ascending=False)
        selected_angle = float(ranked.iloc[0]["solar_altitude_deg"])

    spectral_coverage_diagnostics = _build_spectral_coverage_diagnostics(spectral_rt_voxel_matrix)
    performance_rows.append({"stage": "AGGREGATION_AND_MATRIX_BUILD", "elapsed_seconds": perf_counter()-_aggregate_t0, "cache_status": "COMPUTED"})
    _progress(1.0, "分析完成。")
    _analysis_elapsed = perf_counter() - _analysis_t0
    performance_rows.append({"stage": "TOTAL_ANALYSIS_CORE", "elapsed_seconds": _analysis_elapsed, "cache_status": "COMPUTED"})

    # R4.5 GFS native-condensate provider validation/audit tables.
    _gfs_meta_unique = []
    _seen_gfs_meta = set()
    for _d in details.values():
        _m = (_d.get("native_provider_metadata", {}) or {})
        _k = (_m.get("gfs_run_utc"), _m.get("gfs_forecast_hour"), _m.get("gfs_file"))
        if _k in _seen_gfs_meta:
            continue
        _seen_gfs_meta.add(_k); _gfs_meta_unique.append(_m)
    gfs_native_request_audit = pd.DataFrame([
        {**r, "gfs_run_utc":m.get("gfs_run_utc"), "gfs_forecast_hour":m.get("gfs_forecast_hour"),
         "gfs_file":m.get("gfs_file"), "native_status":m.get("native_status")}
        for m in _gfs_meta_unique for r in (m.get("gfs_native_request_audit", []) or [])
    ])
    gfs_grib_message_inventory = pd.DataFrame([
        {**r, "gfs_run_utc":m.get("gfs_run_utc"), "gfs_forecast_hour":m.get("gfs_forecast_hour"),
         "gfs_file":m.get("gfs_file")}
        for m in _gfs_meta_unique for r in (m.get("gfs_grib_message_inventory", []) or [])
    ])
    gfs_native_field_completeness = pd.DataFrame([
        {**r, "gfs_run_utc":m.get("gfs_run_utc"), "gfs_forecast_hour":m.get("gfs_forecast_hour"),
         "gfs_file":m.get("gfs_file"), "native_status":m.get("native_status"),
         "clwmr_nonnull_route_values":m.get("native_clwmr_nonnull_values"),
         "icmr_nonnull_route_values":m.get("native_icmr_nonnull_values")}
        for m in _gfs_meta_unique for r in (m.get("gfs_native_field_completeness", []) or [])
    ])
    return {
        "summary": summary,
        "details": details,
        "illumination_matrix": illumination_matrix,
        "dynamic_rez": dynamic_rez,
        "forecast_voxel_matrix": forecast_voxel_matrix,
        "reconstructed_voxel_matrix": reconstructed_voxel_matrix,
        "reconstructed_cloud_columns": reconstructed_cloud_columns,
        "pressure_profile_voxel_matrix": pressure_profile_voxel_matrix,
        "pressure_profile_cloud_columns": pressure_profile_cloud_columns,
        "native_cloud_voxel_matrix": native_cloud_voxel_matrix,
        "native_cloud_columns": native_cloud_columns,
        "optical_blocking_voxel_matrix": optical_blocking_voxel_matrix,
        "vertical_blocking_columns": vertical_blocking_columns,
        "native_optical_blocking_voxel_matrix": native_optical_blocking_voxel_matrix,
        "native_optical_blocking_columns": native_optical_blocking_columns,
        "spectral_rt_voxel_matrix": spectral_rt_voxel_matrix,
        "spectral_rt_columns": spectral_rt_columns,
        "selected_angle": selected_angle,
        "route_points": pd.DataFrame(route_points),
        "horizontal_sampling_profile": horizontal_sampling_profile,
        "hourly_raw": hourly,
        "aerosol_hourly_raw": aerosol_hourly,
        "aerosol_spectral_route_snapshots": aerosol_spectral_route_snapshots,
        "cams_native_aerosol_route_snapshots": cams_native_aerosol_route_snapshots,
        "cams_native_aerosol_provider_status": native_aerosol_provider_status(),
        "cams_native_ozone_provider_status": native_ozone_provider_status(),
        "cams_grib_message_inventory": pd.DataFrame([r for _d in details.values() for r in ((_d.get("cams_native_aerosol_metadata", {}) or {}).get("grib_message_inventory", []) or [])]).drop_duplicates().reset_index(drop=True) if details else pd.DataFrame(),
        "gfs_native_request_audit": gfs_native_request_audit,
        "gfs_grib_message_inventory": gfs_grib_message_inventory,
        "gfs_native_field_completeness": gfs_native_field_completeness,
        "cams_request_audit": _audit_dataframe_dedup([r for _d in details.values() for r in ((_d.get("cams_native_aerosol_metadata", {}) or {}).get("cams_request_audit", []) or [])]) if details else pd.DataFrame(),
        "cams_tile_audit": _audit_dataframe_dedup([r for _d in details.values() for r in ((_d.get("cams_native_aerosol_metadata", {}) or {}).get("cams_tile_audit", []) or [])]) if details else pd.DataFrame(),
        "gas_profile_route_snapshots": gas_profile_route_snapshots,
        "ozone_profile_route_snapshots": gas_profile_route_snapshots[[c for c in ["time","solar_altitude_deg","point_id","distance_km","direction_offset_deg","pressure_hpa","altitude_agl_km","temperature_k","o3_mass_mixing_ratio_kgkg","o3_mole_fraction","o3_number_density_m3","o3_quality"] if c in gas_profile_route_snapshots.columns]].copy() if not gas_profile_route_snapshots.empty else pd.DataFrame(),
        "hitran_backend_status": hitran_backend_status(),
        "physics_data_completeness": physics_data_completeness,  # LEGACY diagnostic only in R2
        "v1_cloud_layers": v1_cloud_layers,
        "v1_canvas_candidates": v1_canvas_candidates,
        "v1_direct_solar_fraction": v1_direct_solar,
        "v1_solar_rays": v1_solar_rays,
        "v1_dependency_status": v1_dependency_status,
        "v1_solar_geometry": v1_solar_geometry,
        "v1_ray_cloud_intersections": v1_ray_cloud_intersections,
        "v1_cloud_horizontal_support": v1_cloud_horizontal_support,
        "v1_native_condensate_support_diagnostics": v1_native_condensate_support_diagnostics,
        "v1_spectral_optical_paths": v1_spectral_optical_paths,
        "v1_cloud_base_illumination": v1_cloud_base_illumination,
        "v1_uncertainty": v1_uncertainty,
        "v1_optical_bottlenecks": v1_optical_bottlenecks,
        "v1_canvas_radiance": v1_canvas_radiance,
        "v1_formation": v1_formation,
        "v1_spectral_colour": v1_spectral_colour,
        "v1_cloud_optical_validation": v1_cloud_optical_validation,
        "v1_formation_prerequisites": v1_formation_prerequisites,
        "v1_precipitation_path_evidence": v1_precipitation_path_evidence,
        "v1_target_canvas_optical_evidence": v1_target_canvas_optical_evidence,
        "v1_target_canvas_optical_summary": v1_target_canvas_optical_summary,
        "v1_six_band_spectroscopy_readiness": v1_six_band_spectroscopy_readiness,
        "v1_core_summary": v1_core_summary,
        "spectral_coverage_diagnostics": spectral_coverage_diagnostics,
        "performance_diagnostics": pd.DataFrame(performance_rows),
        "aerosol_provider_error": aerosol_error,
        "openmeteo_request_audit": openmeteo_request_audit,
        "openmeteo_aerosol_request_audit": pd.DataFrame(aerosol_hourly.attrs.get("api_request_audit", [])) if not aerosol_hourly.empty else pd.DataFrame(),
        "reference_azimuth_deg": ref_az,
        "config": cfg,
    }




def _audit_dataframe_dedup(rows):
    if not rows:
        return pd.DataFrame()
    import json
    def _canon(v):
        if isinstance(v, (list, tuple, dict, set)):
            try:
                if isinstance(v, set):
                    v = sorted(v)
                return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
            except Exception:
                return str(v)
        return v
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    for c in df.columns:
        if df[c].map(lambda x: isinstance(x, (list, tuple, dict, set))).any():
            df[c] = df[c].map(_canon)
    return df.drop_duplicates().reset_index(drop=True)

def _build_spectral_coverage_diagnostics(spectral: pd.DataFrame) -> pd.DataFrame:
    """V8.4.6.3 auditable gas/full-spectral coverage by angle/direction/distance."""
    if spectral is None or spectral.empty:
        return pd.DataFrame()
    rows=[]
    full_col="full_spectral_transmission_650nm"
    for key,g in spectral.groupby(["solar_altitude_deg","direction_offset_deg","distance_km"], dropna=False):
        valid=pd.to_numeric(g.get(full_col,pd.Series(np.nan,index=g.index)),errors="coerce").notna()
        illum=pd.to_numeric(g.get("geometric_illuminated_fraction",pd.Series(0.0,index=g.index)),errors="coerce").fillna(0)>0
        gas_domain=g.get("gas_rt_domain_status",pd.Series("MISSING",index=g.index)).fillna("MISSING").astype(str)
        expected_geometry=gas_domain.isin({"NOT_APPLICABLE","MODEL_TOP_TERMINATED","MODEL_BOTTOM_TERMINATED"})
        not_applicable=gas_domain.eq("NOT_APPLICABLE")
        true_missing=(~valid) & ~not_applicable
        causes=g.loc[true_missing,"gas_rt_failure_cause"].fillna("").astype(str) if "gas_rt_failure_cause" in g else pd.Series(dtype=str)
        expected_causes=g.loc[expected_geometry,"gas_rt_expected_termination"].fillna("").astype(str) if "gas_rt_expected_termination" in g else pd.Series(dtype=str)
        spectral_causes=g.loc[~valid,"spectral_rt_missing_cause"].fillna("").astype(str) if "spectral_rt_missing_cause" in g else pd.Series(dtype=str)
        distance=float(key[2]) if pd.notna(key[2]) else np.nan
        decision_required=illum & (distance <= 100.0 + 1e-9)
        decision_causes=g.loc[decision_required & ~valid,"gas_rt_failure_cause"].fillna("").astype(str) if "gas_rt_failure_cause" in g else pd.Series(dtype=str)
        applicable=~not_applicable
        rows.append({"solar_altitude_deg":key[0],"direction_offset_deg":key[1],"distance_km":key[2],
                     "voxel_count":len(g),"full_rt_valid_count":int(valid.sum()),"full_rt_missing_count":int((~valid).sum()),
                     "full_rt_completeness":float(valid.mean()),"illuminated_voxel_count":int(illum.sum()),
                     "illuminated_full_rt_completeness":float(valid[illum].mean()) if illum.any() else np.nan,
                     "applicable_voxel_count":int(applicable.sum()),
                     "applicable_full_rt_valid_count":int((valid & applicable).sum()),
                     "applicable_full_rt_completeness":float(valid[applicable].mean()) if applicable.any() else np.nan,
                     "expected_geometry_termination_count":int(expected_geometry.sum()),
                     "true_missing_count":int(true_missing.sum()),
                     "decision_rt_required_voxel_count":int(decision_required.sum()),
                     "decision_full_rt_valid_count":int((valid & decision_required).sum()),
                     "decision_full_rt_completeness":float(valid[decision_required].mean()) if decision_required.any() else np.nan,
                     "dominant_missing_cause":causes.value_counts().index[0] if len(causes) and not causes.value_counts().empty else "",
                     "dominant_expected_geometry_termination":expected_causes.value_counts().index[0] if len(expected_causes) and not expected_causes.value_counts().empty else "",
                     "dominant_decision_missing_cause":decision_causes.value_counts().index[0] if len(decision_causes) and not decision_causes.value_counts().empty else "",
                     "dominant_spectral_missing_cause":spectral_causes.value_counts().index[0] if len(spectral_causes) and not spectral_causes.value_counts().empty else ""})
    return pd.DataFrame(rows)

def _build_physics_data_completeness(details: dict, candidates, base_summary: pd.DataFrame) -> pd.DataFrame:
    """V8.4.0.4 layered readiness audit. Missing is never converted to zero/clear."""
    rows=[]
    base_by_angle={float(r["solar_altitude_deg"]):r for _,r in base_summary.iterrows()}
    for angle,t,_az in candidates:
        d=details[angle]; base=base_by_angle.get(float(angle), {})
        forecast_c=float(base.get("data_completeness", np.nan)) if hasattr(base,"get") else np.nan
        forecast_status="READY" if pd.notna(forecast_c) and forecast_c>=0.999 else ("PARTIAL" if pd.notna(forecast_c) and forecast_c>0 else "MISSING")

        cams=d.get("cams_native_aerosol_snapshot", pd.DataFrame()); cm=d.get("cams_native_aerosol_metadata", {}) or {}
        provider=native_aerosol_provider_status()
        if not provider.get("credentials_configured",False):
            aerosol_status="NOT_CONFIGURED"; aerosol_c=0.0; aerosol_reason="CAMS_ADS_CREDENTIALS_NOT_CONFIGURED"
        elif cams is None or cams.empty:
            raw=str(cm.get("native_aerosol_error", ""))
            aerosol_status="FAILED" if raw else "MISSING"; aerosol_c=0.0; aerosol_reason=raw or "CAMS_NATIVE_3D_AEROSOL_MISSING"
        else:
            ext_cols=[c for c in cams.columns if str(c).startswith("cams_aerext532_m1_")]
            if ext_cols:
                extmat=cams[ext_cols].apply(pd.to_numeric, errors="coerce")
                aerosol_c=float(extmat.notna().to_numpy().mean()) if extmat.size else 0.0
            else:
                aerosol_c=0.0
            raw=str(cm.get("native_aerosol_error", ""))
            if aerosol_c>=0.999:
                aerosol_status="READY"; aerosol_reason=""
            elif aerosol_c>0:
                aerosol_status="PARTIAL"; aerosol_reason="NATIVE_EXTINCTION_PROFILE_PARTIAL"
            else:
                aerosol_status="FAILED" if raw else "MISSING"; aerosol_reason=raw or "CAMS_NATIVE_3D_AEROSOL_MISSING"

        gp=d.get("gas_profile", pd.DataFrame())
        o3provider=native_ozone_provider_status()
        o3vals=pd.to_numeric(gp.get("o3_mole_fraction", pd.Series(dtype=float)), errors="coerce") if gp is not None and not gp.empty else pd.Series(dtype=float)
        if not o3provider.get("credentials_configured",False):
            o3_status="NOT_CONFIGURED"; o3_c=0.0; o3_reason="CAMS_ADS_CREDENTIALS_NOT_CONFIGURED"
        elif gp is None or gp.empty:
            o3_status="MISSING"; o3_c=0.0; o3_reason="O3_GAS_PROFILE_MISSING"
        else:
            o3_c=float(o3vals.notna().mean()) if len(o3vals) else 0.0
            if o3_c>=0.999: o3_status="READY"; o3_reason=""
            elif o3_c>0: o3_status="PARTIAL"; o3_reason="CAMS_PRESSURE_LEVEL_O3_PARTIAL"
            else:
                raw=str((d.get("cams_native_aerosol_metadata",{}) or {}).get("native_ozone_error", ""))
                o3_status="FAILED" if raw else "MISSING"; o3_reason=raw or "CAMS_PRESSURE_LEVEL_O3_MISSING"

        req=["temperature_k","pressure_hpa","relative_humidity_pct","h2o_mole_fraction","o2_mole_fraction","o3_mole_fraction"]
        if gp is None or gp.empty:
            gas_c=0.0; gas_status="MISSING"; gas_reason="GAS_PROFILE_MISSING"
        else:
            fracs=[float(pd.to_numeric(gp.get(c,pd.Series(np.nan,index=gp.index)),errors="coerce").notna().mean()) for c in req]
            gas_c=float(np.mean(fracs)) if fracs else 0.0
            if all(x>=0.999 for x in fracs): gas_status="READY"; gas_reason=""
            elif any(x>0 for x in fracs): gas_status="PARTIAL"; gas_reason="O3_PROFILE_MISSING" if fracs[-1]==0 else "ATMOSPHERIC_STATE_PARTIAL"
            else: gas_status="MISSING"; gas_reason="ATMOSPHERIC_STATE_MISSING"

        hs=d.get("hitran_backend_status", {}) or {}
        spectral=d.get("spectral_voxels", pd.DataFrame())
        qualities=set(spectral.get("gas_rt_quality",pd.Series(dtype=str)).dropna().astype(str).unique()) if spectral is not None and not spectral.empty else set()
        if hs.get("runtime_spectroscopy_ready",False):
            hit_status="READY"; hit_c=1.0; hit_reason=""
        elif not hs.get("database_exists",False):
            hit_status="NOT_CONFIGURED"; hit_c=0.0; hit_reason="LOCAL_HITRAN_DB_MISSING"
        elif not hs.get("coefficient_table_exists",False):
            hit_status="NOT_CONFIGURED"; hit_c=0.0; hit_reason="HITRAN_LOCAL_BAND_TABLE_MISSING"
        else:
            hit_status="PARTIAL"; hit_c=0.5; hit_reason=str(hs.get("coefficient_table_missing_reason") or "HITRAN_LOCAL_BAND_TABLE_INCOMPLETE")

        wavelength_values=[]
        if spectral is not None and not spectral.empty:
            for col in spectral.columns:
                m=re.fullmatch(r"full_spectral_transmission_(\d+)nm",str(col))
                if m: wavelength_values.append(int(m.group(1)))
        wavelengths=tuple(sorted(set(wavelength_values))) or (600,650,700,750)
        full_cols=[f"full_spectral_transmission_{wl}nm" for wl in wavelengths]
        diagnostic_full_c=0.0
        spectral_aerosol_c=0.0; spectral_aerosol_status="MISSING"; spectral_aerosol_reason="SPECTRAL_AEROSOL_RT_INPUT_MISSING"
        if spectral is None or spectral.empty:
            full_c=0.0; full_status="MISSING"; full_reason="SPECTRAL_RT_INPUT_MISSING"
            diagnostic_full_c=0.0; diagnostic_status="MISSING"; diagnostic_reason="SPECTRAL_RT_INPUT_MISSING"
        else:
            # Operational FULL_SPECTRAL_RT is scoped to the physically relevant
            # direct-sunlit Canvas (0–100 km). Finite transmission numbers alone
            # are NOT sufficient: gas and aerosol path-domain integrity must also
            # be complete, otherwise a partial tau could masquerade as full RT.
            if "geometric_illuminated_fraction" in spectral.columns and "distance_km" in spectral.columns:
                geom=pd.to_numeric(spectral["geometric_illuminated_fraction"],errors="coerce").fillna(0.0)
                dist=pd.to_numeric(spectral["distance_km"],errors="coerce")
                req=(geom>0.0)&(dist<=100.0+1e-9)
            else:
                req=pd.Series(True,index=spectral.index,dtype=bool)

            # Earth-shadow rows are geometrically N/A, not failed RT inputs.
            # Keep MODEL_TOP/BOTTOM_TERMINATED rows in the denominator because
            # they are valid finite-atmosphere paths; only NOT_APPLICABLE rows
            # are removed from the all-route diagnostic completeness rate.
            diagnostic_domain=spectral.get("gas_rt_domain_status",pd.Series("MISSING",index=spectral.index)).astype(str)
            diagnostic_req=~diagnostic_domain.eq("NOT_APPLICABLE")
            all_vals=[float(pd.to_numeric(spectral.get(c,pd.Series(np.nan,index=spectral.index)),errors="coerce").loc[diagnostic_req].notna().mean()) for c in full_cols] if diagnostic_req.any() else []
            diagnostic_full_c=float(np.mean(all_vals)) if all_vals else 1.0
            diagnostic_status="READY" if (not all_vals or all(x>=0.999 for x in all_vals)) else ("PARTIAL" if any(x>0 for x in all_vals) else "MISSING")
            diagnostic_reason="" if diagnostic_status=="READY" else "ALL_ROUTE_DIAGNOSTIC_RT_PARTIAL"

            # Native CAMS 3-D aerosol is only complete when every required path
            # segment has real spectral scaling and the ray reaches the configured
            # 30-km aerosol atmosphere top. The old code accepted any finite tau,
            # even when path completeness was 20–70%.
            native_tau=pd.to_numeric(spectral.get("native_cams_aerosol_tau_650nm",pd.Series(np.nan,index=spectral.index)),errors="coerce")
            native_comp=pd.to_numeric(spectral.get("native_cams_aerosol_path_completeness",pd.Series(np.nan,index=spectral.index)),errors="coerce")
            native_dom=spectral.get("native_cams_aerosol_domain_complete",pd.Series(False,index=spectral.index)).fillna(False).astype(bool)
            native_valid=native_tau.notna() & (native_comp>=0.999) & native_dom

            fallback_cols=[f"route_aerosol_transmission_{wl}nm" for wl in wavelengths]
            fallback_finite=pd.Series(True,index=spectral.index,dtype=bool)
            for c in fallback_cols:
                fallback_finite &= pd.to_numeric(spectral.get(c,pd.Series(np.nan,index=spectral.index)),errors="coerce").notna()
            fallback_q=spectral.get("aerosol_path_quality",pd.Series("",index=spectral.index)).astype(str)
            fallback_valid=(~native_tau.notna()) & fallback_finite & fallback_q.eq("COLUMN_AOD_TO_EXPONENTIAL_3D_PROFILE")
            aerosol_valid=native_valid | fallback_valid

            if not req.any():
                spectral_aerosol_c=1.0; spectral_aerosol_status="READY"; spectral_aerosol_reason="NO_DIRECT_SUNLIT_CANVAS_AEROSOL_RT_REQUIRED"
                full_c=1.0; full_status="READY"; full_reason="NO_DIRECT_SUNLIT_CANVAS_RT_REQUIRED"
            else:
                spectral_aerosol_c=float(aerosol_valid.loc[req].mean())
                if spectral_aerosol_c>=0.999:
                    spectral_aerosol_status="READY"; spectral_aerosol_reason=""
                elif spectral_aerosol_c>0:
                    spectral_aerosol_status="PARTIAL"; spectral_aerosol_reason="NATIVE_AEROSOL_SPECTRAL_PATH_OR_DOMAIN_PARTIAL"
                else:
                    spectral_aerosol_status="MISSING"; spectral_aerosol_reason="NATIVE_AEROSOL_SPECTRAL_PATH_MISSING"

                full_finite=pd.Series(True,index=spectral.index,dtype=bool)
                for c in full_cols:
                    full_finite &= pd.to_numeric(spectral.get(c,pd.Series(np.nan,index=spectral.index)),errors="coerce").notna()
                gas_domain=spectral.get("gas_rt_domain_status",pd.Series("MISSING",index=spectral.index)).astype(str)
                gas_comp=pd.to_numeric(spectral.get("gas_path_completeness",pd.Series(0.0,index=spectral.index)),errors="coerce").fillna(0.0)
                gas_valid=(~gas_domain.str.startswith("TRUE_")) & (gas_comp>=0.999)
                row_valid=full_finite & gas_valid & aerosol_valid
                full_c=float(row_valid.loc[req].mean())
                if full_c>=0.999:
                    full_status="READY"; full_reason="MODEL_DOMAIN_COMPLETE;STRATOSPHERE_ABOVE_PROFILE_TOP_NOT_INTEGRATED"
                elif full_c>0:
                    full_status="PARTIAL"; full_reason="FULL_SPECTRAL_RT_COMPONENT_PATH_INCOMPLETE"
                else:
                    full_status="MISSING"; full_reason="FULL_RT_REQUIRES_COMPLETE_CLOUD_AEROSOL_GAS_AND_HITRAN_PATHS"

        # Explicit vertical-domain audit: current Open-Meteo/CAMS gas profile tops
        # are real pressure-level data and are not extrapolated upward.
        if gp is None or gp.empty:
            gas_vertical_status="MISSING"; gas_vertical_c=0.0; gas_vertical_reason="GAS_PROFILE_MISSING"
        else:
            if {"direction_offset_deg","distance_km","altitude_agl_km"}.issubset(gp.columns):
                tops=gp.groupby(["direction_offset_deg","distance_km"],dropna=False)["altitude_agl_km"].max()
            elif "altitude_agl_km" in gp.columns:
                tops=pd.Series([pd.to_numeric(gp["altitude_agl_km"],errors="coerce").max()])
            else:
                tops=pd.Series(dtype=float)
            gas_vertical_c=float((pd.to_numeric(tops,errors="coerce")>=18.0-1e-9).mean()) if len(tops) else 0.0
            if gas_vertical_c>=0.999:
                gas_vertical_status="READY"; gas_vertical_reason=""
            else:
                gas_vertical_status="PARTIAL"; gas_vertical_reason="REAL_PRESSURE_PROFILE_TOP_BELOW_18KM_AT_SOME_ROUTE_POINTS;NO_VERTICAL_EXTRAPOLATION"

        for layer,status,comp,reason,prov in [
            ("FORECAST_CLOUD",forecast_status,forecast_c,"" if forecast_status=="READY" else "BASE_FORECAST_INCOMPLETE","Open-Meteo/GFS"),
            ("NATIVE_AEROSOL",aerosol_status,aerosol_c,aerosol_reason,str(provider.get("provider","CAMS"))),
            ("O3_PROFILE",o3_status,o3_c,o3_reason,str(o3provider.get("provider","CAMS O3"))),
            ("GAS_PROFILE",gas_status,gas_c,gas_reason,"Open-Meteo pressure levels + CAMS O3"),
            ("HITRAN_SPECTROSCOPY",hit_status,hit_c,hit_reason,"Local HITRAN/HAPI"),
            ("GAS_VERTICAL_DOMAIN",gas_vertical_status,gas_vertical_c,gas_vertical_reason,"Real pressure-level profile; no extrapolation"),
            ("SPECTRAL_AEROSOL_PATH",spectral_aerosol_status,spectral_aerosol_c,spectral_aerosol_reason,"CAMS native 3-D aerosol + real multi-wavelength AOD path"),
            ("FULL_SPECTRAL_RT",full_status,full_c,full_reason,"PhysicsCore direct-sunlit Canvas model domain"),
            ("FULL_SPECTRAL_RT_ALL_ROUTE_DIAGNOSTIC",diagnostic_status,diagnostic_full_c,diagnostic_reason,"PhysicsCore all-route diagnostic"),
        ]:
            rows.append({"time":t,"solar_altitude_deg":float(angle),"layer":layer,"status":status,"completeness":comp,"provider":prov,"missing_reason":reason})
    return pd.DataFrame(rows)

def reconstruct_cloud_columns_3d(
    route_at_time: pd.DataFrame, solar_altitude_deg: float, cfg: ModelConfig
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """V8.0.4 coarse Cloud Base/Top/Thickness 3-D reconstruction.

    The forecast provider currently exposes low/mid/high *layer cloud cover*, not
    native model-level condensate or cloud-base/top. We therefore reconstruct a
    0.5-km vertical lattice only inside the provider-supported layer envelopes.
    Each vertical cell inherits that layer's horizontal cloud-cover occupancy.
    This is explicitly a reconstruction proxy, not a measured cloud boundary.

    Returns:
      voxels: angle × direction × distance × 0.5-km vertical cells with Earth
              shadow, upstream transmission and illuminated cloud-volume proxy.
      columns: per direction/distance reconstructed occupied envelope and the
               fraction of reconstructed cloud volume that is illuminated.
    """
    from .config import VOXEL_ALTITUDE_CENTERS_KM, VOXEL_VERTICAL_STEP_KM

    rows = []
    if route_at_time.empty:
        return pd.DataFrame(), pd.DataFrame()
    coarse_index = _build_coarse_route_index(route_at_time)

    for _, r in route_at_time.iterrows():
        d = float(r["distance_km"])
        off = float(r["direction_offset_deg"])
        band = _band_name(d)
        for z in VOXEL_ALTITUDE_CENTERS_KM:
            layer = forecast_layer_for_altitude(z)
            z0 = float(z - VOXEL_VERTICAL_STEP_KM / 2)
            z1 = float(z + VOXEL_VERTICAL_STEP_KM / 2)
            base = {
                "solar_altitude_deg": float(solar_altitude_deg),
                "direction_offset_deg": off,
                "distance_km": d,
                "band": band,
                "voxel_bottom_km": z0,
                "voxel_top_km": z1,
                "voxel_center_km": float(z),
                "voxel_thickness_km": float(VOXEL_VERTICAL_STEP_KM),
                "forecast_layer": layer if layer is not None else "UNSUPPORTED",
            }
            if layer is None:
                rows.append({**base, "cloud_occupancy_proxy": np.nan,
                             "geometric_illuminated_fraction": np.nan,
                             "upstream_transmission_proxy": np.nan,
                             "path_completeness": 0.0,
                             "effective_illuminated_cloud_volume_proxy": np.nan,
                             "voxel_state": "NO_VERTICAL_FORECAST_SUPPORT"})
                continue
            cover = layer_cloud_cover(r, layer)
            if pd.isna(cover):
                rows.append({**base, "cloud_occupancy_proxy": np.nan,
                             "geometric_illuminated_fraction": np.nan,
                             "upstream_transmission_proxy": np.nan,
                             "path_completeness": 0.0,
                             "effective_illuminated_cloud_volume_proxy": np.nan,
                             "voxel_state": "MISSING_CLOUD_FORECAST"})
                continue

            shadow_h = earth_shadow_min_altitude_km(d, solar_altitude_deg, cfg.earth_radius_km)
            geom_frac = cloud_layer_illuminated_fraction(z0, z1, shadow_h)
            if cover <= 0:
                trans, comp, eff, state = np.nan, 1.0, 0.0, "NO_FORECAST_CLOUD"
            elif geom_frac <= 0:
                trans, comp, eff, state = 0.0, 1.0, 0.0, "CLOUD_EARTH_SHADOWED"
            else:
                trans, comp = _upstream_path_transmission_indexed(
                    coarse_index, off, d, float(z), solar_altitude_deg, cfg
                )
                if pd.isna(trans):
                    eff, state = np.nan, "SUNLIT_PATH_UNKNOWN"
                else:
                    # Fractional cloud occupancy × fraction of this vertical cell
                    # above Earth shadow × upstream path transmission.
                    eff = _clamp01(cover * geom_frac * trans)
                    state = "PARTLY_SUNLIT_FORECAST_CLOUD" if geom_frac < 0.999 else "SUNLIT_FORECAST_CLOUD"
            rows.append({**base,
                         "earth_shadow_top_km": float(shadow_h),
                         "cloud_occupancy_proxy": cover,
                         "geometric_illuminated_fraction": float(geom_frac),
                         "upstream_transmission_proxy": trans,
                         "path_completeness": comp,
                         "effective_illuminated_cloud_volume_proxy": eff,
                         "voxel_state": state})

    vox = pd.DataFrame(rows)
    columns = []
    for (off, d), g in vox.groupby(["direction_offset_deg", "distance_km"], sort=False):
        supported = g[g["cloud_occupancy_proxy"].notna()].copy()
        cloudy = supported[supported["cloud_occupancy_proxy"] > 0]
        if cloudy.empty:
            base_km = top_km = thickness_km = np.nan
        else:
            base_km = float(cloudy["voxel_bottom_km"].min())
            top_km = float(cloudy["voxel_top_km"].max())
            thickness_km = top_km - base_km
        total_cloud_volume = float((supported["cloud_occupancy_proxy"] * supported["voxel_thickness_km"]).sum()) if not supported.empty else np.nan
        illum_volume = float((supported["effective_illuminated_cloud_volume_proxy"] * supported["voxel_thickness_km"]).sum(min_count=1)) if not supported.empty else np.nan
        illum_fraction = (illum_volume / total_cloud_volume) if total_cloud_volume and not pd.isna(illum_volume) else (0.0 if total_cloud_volume == 0 else np.nan)
        columns.append({
            "solar_altitude_deg": float(solar_altitude_deg),
            "direction_offset_deg": float(off),
            "distance_km": float(d),
            "band": _band_name(float(d)),
            "reconstructed_cloud_base_km": base_km,
            "reconstructed_cloud_top_km": top_km,
            "reconstructed_cloud_thickness_km": thickness_km,
            "cloud_volume_proxy_km": total_cloud_volume,
            "illuminated_cloud_volume_proxy_km": illum_volume,
            "illuminated_fraction_of_cloud_volume_proxy": illum_fraction,
            "vertical_data_completeness": float(supported["cloud_occupancy_proxy"].notna().mean()) if not supported.empty else 0.0,
            "boundary_quality": "COARSE_LAYER_ENVELOPE_PROXY",
        })
    return vox, pd.DataFrame(columns)
