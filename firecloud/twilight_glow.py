"""Independent PhysicsCore Twilight Glow branch.

R5.7.30 closes the third PhysicsCore branch as an evidence-preserving,
six-band atmospheric single-scattering diagnostic:

    Sun -> atmospheric scatter volume -> observer

The branch deliberately does *not* create a cloud Canvas, alter Firecloud
Formation, or reuse Cloud->Observer results as a Formation score.  With the
current forecast inputs it can resolve molecular (Rayleigh) single-scattering
source coefficients and both extinction paths.  Aerosol source scattering
still requires single-scattering albedo and a phase function, while absolute
sky radiance additionally requires calibrated angular-volume integration and
multiple scattering.  Those unavailable terms remain explicit instead of
being fabricated from AOD or relative humidity.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from .contracts import SIX_BAND_WAVELENGTHS_NM
from .gas_rt import BOLTZMANN, prepare_gas_rt_context, _interp_fast_profile_state, _sigma_fast
from .precipitation import build_viewing_precipitation_evidence
from .shared_geometry import destination_point, directional_scattering_geometry
from .shared_geometry.ray import observer_los_height_agl_km
from .spectral_rt import rayleigh_vertical_optical_depth
from .viewing_spectral import build_viewing_spectral_extinction


TWILIGHT_GLOW_CONTRACT = "R5.7.31_TWILIGHT_GLOW_FULL_SIX_BAND_EXTINCTION_PHASE1_V1"
TWILIGHT_GLOW_EXTINCTION_CONTRACT = "R5.7.31_SUN_SCATTER_OBSERVER_SIX_BAND_EXTINCTION_V1"
TWILIGHT_GLOW_SINGLE_SCATTERING_CONTRACT = "R5.7.31_RAYLEIGH_SINGLE_SCATTERING_SPECTRAL_PROXY_V1"
GLOW_VOLUME_DOMAIN = "FORWARD_ATMOSPHERE_10_100KM_4_12KM"
GLOW_PROXY_UNITS = "RELATIVE_INCIDENT_IRRADIANCE_PER_M_SR"
NO_TOTAL_RADIANCE_CLAIM = "NOT_RESOLVED_AEROSOL_SSA_PHASE_AND_MULTIPLE_SCATTERING_REQUIRED"
NO_AEROSOL_SOURCE_CLAIM = "NOT_RESOLVED_NO_SSA_OR_PHASE_FUNCTION"
NO_MULTIPLE_SCATTERING_CLAIM = "NOT_RESOLVED_NO_CALIBRATED_ATMOSPHERIC_RT"

_STANDARD_PRESSURE_PA = 101325.0
_STANDARD_GRAVITY_M_S2 = 9.80665
_DRY_AIR_MOLAR_MASS_KG_MOL = 0.0289647
_AVOGADRO_MOL = 6.02214076e23


def _finite(value: Any) -> float | None:
    try:
        out = float(value)
        return out if math.isfinite(out) else None
    except Exception:
        return None


def _key(time_value: Any, angle_value: Any, object_id: Any) -> tuple[str, float | None, str]:
    angle = _finite(angle_value)
    return str(time_value), None if angle is None else round(angle, 8), str(object_id)


def rayleigh_cross_section_m2(wavelength_nm: int) -> float:
    """Return the molecular scattering cross-section consistent with the RT OD.

    ``rayleigh_vertical_optical_depth`` supplies the already-frozen Bodhaine-
    style wavelength dependence.  Dividing its standard-pressure column OD by
    the hydrostatic molecular column keeps Glow source and path extinction on
    the same six-band Rayleigh convention used by the Sun-path solver.
    """
    tau = float(rayleigh_vertical_optical_depth(float(wavelength_nm), 1013.25))
    molecular_column_m2 = (
        _STANDARD_PRESSURE_PA
        / (_STANDARD_GRAVITY_M_S2 * _DRY_AIR_MOLAR_MASS_KG_MOL)
        * _AVOGADRO_MOL
    )
    return tau / molecular_column_m2


def rayleigh_phase_function_sr(scattering_angle_deg: float) -> float:
    """Unpolarized Rayleigh phase function normalized over 4 pi steradians."""
    theta = math.radians(float(scattering_angle_deg))
    return 3.0 * (1.0 + math.cos(theta) ** 2) / (16.0 * math.pi)


def _timeline_map(event_timeline: pd.DataFrame) -> dict[tuple[str, float | None], dict[str, Any]]:
    out: dict[tuple[str, float | None], dict[str, Any]] = {}
    if event_timeline is None or event_timeline.empty:
        return out
    for _, row in event_timeline.iterrows():
        angle = _finite(row.get("solar_altitude_deg"))
        out[(str(row.get("time")), None if angle is None else round(angle, 8))] = row.to_dict()
    return out


def _gas_profile_index(gas_profiles: pd.DataFrame) -> dict[tuple[str, float | None, float], dict[float, pd.DataFrame]]:
    out: dict[tuple[str, float | None, float], dict[float, pd.DataFrame]] = {}
    if gas_profiles is None or gas_profiles.empty:
        return out
    required = {"time", "solar_altitude_deg", "direction_offset_deg", "distance_km", "altitude_agl_km", "temperature_k", "pressure_hpa"}
    if not required.issubset(gas_profiles.columns):
        return out
    q = gas_profiles.copy()
    q["solar_altitude_deg"] = pd.to_numeric(q["solar_altitude_deg"], errors="coerce").round(8)
    q["direction_offset_deg"] = pd.to_numeric(q["direction_offset_deg"], errors="coerce").round(8)
    q["distance_km"] = pd.to_numeric(q["distance_km"], errors="coerce")
    for keys, group in q.groupby([q["time"].astype(str), "solar_altitude_deg", "direction_offset_deg", "distance_km"], dropna=False, sort=False):
        time_value, angle, direction, distance = keys
        if pd.isna(angle) or pd.isna(direction) or pd.isna(distance):
            continue
        k = (str(time_value), round(float(angle), 8), round(float(direction), 8))
        profile = group.copy()
        profile["altitude_agl_km"] = pd.to_numeric(profile["altitude_agl_km"], errors="coerce")
        profile["temperature_k"] = pd.to_numeric(profile["temperature_k"], errors="coerce")
        profile["pressure_hpa"] = pd.to_numeric(profile["pressure_hpa"], errors="coerce")
        profile = profile.dropna(subset=["altitude_agl_km", "temperature_k", "pressure_hpa"]).sort_values("altitude_agl_km")
        if not profile.empty:
            out.setdefault(k, {})[float(distance)] = profile
    return out


def _profile_state(profile: pd.DataFrame | None, altitude_km: float) -> tuple[float, float] | None:
    if profile is None or profile.empty:
        return None
    z = pd.to_numeric(profile["altitude_agl_km"], errors="coerce").to_numpy(float)
    t = pd.to_numeric(profile["temperature_k"], errors="coerce").to_numpy(float)
    p = pd.to_numeric(profile["pressure_hpa"], errors="coerce").to_numpy(float)
    valid = np.isfinite(z) & np.isfinite(t) & np.isfinite(p) & (t > 0.0) & (p > 0.0)
    z, t, p = z[valid], t[valid], p[valid]
    if len(z) < 2 or float(altitude_km) < float(z.min()) - 1e-9 or float(altitude_km) > float(z.max()) + 1e-9:
        return None
    order = np.argsort(z)
    z, t, p = z[order], t[order], p[order]
    return float(np.interp(float(altitude_km), z, t)), float(np.interp(float(altitude_km), z, p))


def _rayleigh_observer_path(
    target: pd.Series,
    profiles: dict[float, pd.DataFrame] | None,
    earth_radius_km: float,
) -> tuple[dict[int, float] | None, str, int, int]:
    distance = _finite(target.get("target_distance_km"))
    base = _finite(target.get("target_base_km"))
    top = _finite(target.get("target_top_km"))
    if distance is None or base is None or top is None or distance <= 0.0 or top <= base:
        return None, "GLOW_OBSERVER_RAYLEIGH_GEOMETRY_UNRESOLVED", 0, 0
    if not profiles:
        return None, "GLOW_OBSERVER_RAYLEIGH_PROFILE_MISSING", 0, 0
    target_altitude = 0.5 * (base + top)
    distances = sorted(float(d) for d in profiles if float(d) <= distance + 1e-8)
    if not distances or distances[0] > 1e-8:
        return None, "GLOW_OBSERVER_RAYLEIGH_OBSERVER_ENDPOINT_MISSING", 0, 0
    if distances[-1] < distance - 1e-8:
        distances.append(float(distance))
    tau = {int(w): 0.0 for w in SIX_BAND_WAVELENGTHS_NM}
    required = 0
    resolved = 0
    for d0, d1 in zip(distances[:-1], distances[1:]):
        if d1 <= d0:
            continue
        required += 1
        midpoint = 0.5 * (d0 + d1)
        altitude = observer_los_height_agl_km(distance, target_altitude, midpoint, earth_radius_km)
        nearest = min(profiles, key=lambda d: abs(float(d) - midpoint))
        state = _profile_state(profiles.get(nearest), altitude)
        if state is None:
            continue
        temperature_k, pressure_hpa = state
        number_density_m3 = pressure_hpa * 100.0 / (BOLTZMANN * temperature_k)
        z0 = observer_los_height_agl_km(distance, target_altitude, d0, earth_radius_km)
        z1 = observer_los_height_agl_km(distance, target_altitude, d1, earth_radius_km)
        path_m = math.hypot((d1 - d0) * 1000.0, (z1 - z0) * 1000.0)
        for wavelength in SIX_BAND_WAVELENGTHS_NM:
            tau[int(wavelength)] += rayleigh_cross_section_m2(int(wavelength)) * number_density_m3 * path_m
        resolved += 1
    if required == 0 or resolved < required:
        return (tau if resolved else None), "GLOW_OBSERVER_RAYLEIGH_PATH_PARTIAL", required, resolved
    return tau, "GLOW_OBSERVER_RAYLEIGH_PATH_RESOLVED", required, resolved


def _local_molecular_state(
    target: pd.Series,
    profiles: dict[float, pd.DataFrame] | None,
) -> tuple[float, float, float] | None:
    if not profiles:
        return None
    distance = _finite(target.get("target_distance_km"))
    base = _finite(target.get("target_base_km"))
    top = _finite(target.get("target_top_km"))
    if distance is None or base is None or top is None:
        return None
    nearest = min(profiles, key=lambda d: abs(float(d) - distance))
    state = _profile_state(profiles.get(nearest), 0.5 * (base + top))
    if state is None:
        return None
    temperature_k, pressure_hpa = state
    return temperature_k, pressure_hpa, pressure_hpa * 100.0 / (BOLTZMANN * temperature_k)


def _gas_context_index(gas_profiles: pd.DataFrame) -> dict[tuple[str, float | None, float | None], Any]:
    """Prepare one HITRAN gas context per time/angle/direction route.

    This is Glow-only evidence plumbing.  It reuses the same frozen HITRAN
    coefficients and profile interpolation as the independent Viewing branch,
    but does not write any Viewing result back into Formation or Photography.
    """
    out: dict[tuple[str, float | None, float | None], Any] = {}
    if gas_profiles is None or gas_profiles.empty:
        return out
    q = gas_profiles.copy()
    q["solar_altitude_deg"] = pd.to_numeric(q.get("solar_altitude_deg"), errors="coerce").round(8)
    q["direction_offset_deg"] = pd.to_numeric(q.get("direction_offset_deg"), errors="coerce").round(8)
    tser = q.get("time", pd.Series("", index=q.index)).astype(str)
    for keys, group in q.groupby([tser, "solar_altitude_deg", "direction_offset_deg"], dropna=False, sort=False):
        time_value, angle, direction = keys
        key = (
            str(time_value),
            None if pd.isna(angle) else round(float(angle), 8),
            None if pd.isna(direction) else round(float(direction), 8),
        )
        out[key] = prepare_gas_rt_context(group.copy())
    return out


def _observer_gas_species_path(
    target: pd.Series,
    prepared_context: Any,
    earth_radius_km: float,
) -> tuple[dict[int, dict[str, float]] | None, str, int, int, float]:
    """Integrate O3 and non-O3 molecular absorption on Scatter->Observer.

    The total gas optical depth is intentionally decomposed as O3 + (O2+H2O)
    so the Chappuis contribution remains explicit without double counting.
    """
    distance = _finite(target.get("target_distance_km"))
    base = _finite(target.get("target_base_km"))
    top = _finite(target.get("target_top_km"))
    direction = _finite(target.get("direction_offset_deg"))
    if None in (distance, base, top, direction) or distance <= 0.0 or top <= base:
        return None, "GLOW_OBSERVER_GAS_GEOMETRY_UNRESOLVED", 0, 0, 0.0
    ctx = prepared_context
    if ctx is None or not getattr(ctx, "valid", False):
        return None, "GLOW_OBSERVER_GAS_CONTEXT_MISSING", 0, 0, 0.0
    drec = ctx.prepared_profile.get(float(direction))
    if drec is None:
        return None, "GLOW_OBSERVER_GAS_DIRECTION_MISSING", 0, 0, 0.0
    distances = [float(x) for x in drec["distances"] if float(x) <= float(distance) + 1e-8]
    if not distances or distances[0] > 1e-6:
        return None, "GLOW_OBSERVER_GAS_OBSERVER_ENDPOINT_MISSING", 0, 0, 0.0
    if distances[-1] < float(distance) - 1e-8:
        distances.append(float(distance))
    target_altitude = 0.5 * (float(base) + float(top))
    tau = {int(w): {"o3": 0.0, "non_o3": 0.0, "total": 0.0} for w in SIX_BAND_WAVELENGTHS_NM}
    required = 0
    resolved = 0
    path_km = 0.0
    for d0, d1 in zip(distances[:-1], distances[1:]):
        if d1 <= d0:
            continue
        required += 1
        midpoint = 0.5 * (d0 + d1)
        nearest = min(drec["distances"], key=lambda x: abs(float(x) - midpoint))
        rec = drec["profiles"].get(float(nearest))
        if rec is None:
            continue
        altitude = observer_los_height_agl_km(float(distance), target_altitude, midpoint, float(earth_radius_km))
        state = _interp_fast_profile_state(rec, altitude)
        if state is None:
            continue
        temperature_k = float(state["temperature_k"])
        pressure_hpa = float(state["pressure_hpa"])
        if not (math.isfinite(temperature_k) and math.isfinite(pressure_hpa) and temperature_k > 0.0 and pressure_hpa > 0.0):
            continue
        n_air = pressure_hpa * 100.0 / (BOLTZMANN * temperature_k)
        densities = {
            "O2": float(state["o2_mole_fraction"]) * n_air,
            "H2O": float(state["h2o_mole_fraction"]) * n_air,
            "O3": float(state["o3_mole_fraction"]) * n_air,
        }
        if not all(math.isfinite(v) and v >= 0.0 for v in densities.values()):
            continue
        z0 = observer_los_height_agl_km(float(distance), target_altitude, d0, float(earth_radius_km))
        z1 = observer_los_height_agl_km(float(distance), target_altitude, d1, float(earth_radius_km))
        path_m = math.hypot((d1 - d0) * 1000.0, (z1 - z0) * 1000.0)
        local: dict[int, dict[str, float]] = {}
        ok = True
        for wavelength in SIX_BAND_WAVELENGTHS_NM:
            species_tau: dict[str, float] = {}
            for gas_name, density in densities.items():
                sigma = _sigma_fast(ctx.lut, gas_name, int(wavelength), temperature_k, pressure_hpa)
                if not math.isfinite(float(sigma)):
                    ok = False
                    break
                species_tau[gas_name] = max(0.0, float(sigma) * float(density) * path_m)
            if not ok:
                break
            o3_tau = species_tau["O3"]
            non_o3_tau = species_tau["O2"] + species_tau["H2O"]
            local[int(wavelength)] = {"o3": o3_tau, "non_o3": non_o3_tau, "total": o3_tau + non_o3_tau}
        if not ok:
            continue
        for wavelength, values in local.items():
            for component, value in values.items():
                tau[wavelength][component] += value
        resolved += 1
        path_km += path_m / 1000.0
    if required == 0:
        return None, "GLOW_OBSERVER_GAS_PATH_UNRESOLVED", required, resolved, path_km
    if resolved < required:
        return (tau if resolved else None), "GLOW_OBSERVER_GAS_PATH_PARTIAL", required, resolved, path_km
    return tau, "GLOW_OBSERVER_GAS_PATH_RESOLVED", required, resolved, path_km


def _sun_component_state(source: pd.Series | None) -> dict[str, bool]:
    if source is None:
        return {k: False for k in ("RAYLEIGH", "GAS", "AEROSOL", "CLOUD", "PRECIPITATION")}
    aerosol_state = str(source.get("red_light_aerosol_evidence_state") or "")
    return {
        "RAYLEIGH": all(_finite(source.get(f"rayleigh_tau_{int(w)}nm")) is not None for w in SIX_BAND_WAVELENGTHS_NM),
        "GAS": str(source.get("red_light_gas_evidence_state") or "") == "FULL",
        "AEROSOL": aerosol_state.startswith("FULL_"),
        "CLOUD": str(source.get("red_light_cloud_evidence_state") or "") == "FULL",
        "PRECIPITATION": str(source.get("red_light_precipitation_evidence_state") or "") == "FULL",
    }


def build_twilight_glow_phase1_exports(detail: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Project the composite Glow evidence into three explicit R5.7.31 tables."""
    if detail is None or detail.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    identity = [
        "time", "solar_altitude_deg", "solar_azimuth_deg", "glow_volume_id",
        "reference_receiver_id", "direction_offset_deg", "distance_km",
        "scatter_altitude_km", "scatter_layer_bottom_km", "scatter_layer_top_km",
        "target_lat", "target_lon", "scattering_angle_deg",
    ]
    sun_cols = identity + [
        "glow_direct_solar_fraction", "glow_sun_extinction_state",
        "glow_sun_path_state", "glow_sun_path_evidence_complete",
        "glow_sun_missing_components", "twilight_glow_extinction_contract",
    ]
    observer_cols = identity + [
        "glow_observer_extinction_state", "glow_observer_path_state",
        "glow_observer_path_evidence_complete", "glow_observer_rayleigh_status",
        "glow_observer_gas_species_status", "glow_observer_aerosol_status",
        "glow_observer_aerosol_required_segment_count", "glow_observer_aerosol_resolved_segment_count",
        "glow_observer_aerosol_lowest_endpoint_snap_segment_count", "glow_observer_aerosol_endpoint_tolerance_km",
        "glow_observer_missing_components",
        "twilight_glow_extinction_contract",
    ]
    single_cols = identity + [
        "rayleigh_phase_function_sr", "glow_proxy_state", "glow_proxy_units",
        "glow_result_role", "formation_independent", "viewing_independent",
        "calibrated_glow_radiance_available", "glow_total_radiance_state",
        "glow_missing_components", "twilight_glow_single_scattering_contract",
    ]
    for wavelength in SIX_BAND_WAVELENGTHS_NM:
        w = int(wavelength)
        sun_cols.extend([
            f"glow_sun_tau_rayleigh_{w}nm", f"glow_sun_tau_gas_non_o3_{w}nm",
            f"glow_sun_tau_o3_{w}nm", f"glow_sun_tau_aerosol_{w}nm",
            f"glow_sun_tau_cloud_{w}nm", f"glow_sun_tau_precip_{w}nm",
            f"glow_sun_tau_total_{w}nm", f"glow_sun_transmission_{w}nm",
            f"glow_sun_incident_relative_irradiance_{w}nm",
            f"glow_sun_reference_incident_relative_irradiance_{w}nm",
            f"glow_sun_band_evidence_state_{w}nm",
        ])
        observer_cols.extend([
            f"glow_observer_tau_rayleigh_{w}nm", f"glow_observer_tau_gas_non_o3_{w}nm",
            f"glow_observer_tau_o3_{w}nm", f"glow_observer_tau_aerosol_{w}nm",
            f"glow_observer_tau_cloud_{w}nm", f"glow_observer_tau_precip_{w}nm",
            f"glow_observer_tau_total_{w}nm", f"glow_observer_transmission_{w}nm",
            f"glow_observer_band_evidence_state_{w}nm",
        ])
        single_cols.extend([
            f"glow_sun_incident_relative_irradiance_{w}nm",
            f"glow_rayleigh_scattering_coefficient_m1_{w}nm",
            f"glow_rayleigh_source_coefficient_m1_sr_{w}nm",
            f"glow_observer_transmission_{w}nm",
            f"glow_single_scattering_source_proxy_{w}nm",
            f"glow_band_evidence_state_{w}nm",
        ])
    def project(columns: list[str]) -> pd.DataFrame:
        available = [c for c in columns if c in detail.columns]
        return detail[available].copy()
    return project(sun_cols), project(observer_cols), project(single_cols)


def build_twilight_glow_geometry(
    red_light_reference: pd.DataFrame,
    event_timeline: pd.DataFrame,
    *,
    observer_lat_deg: float,
    observer_lon_deg: float,
    observer_alt_km: float = 0.0,
    earth_radius_km: float = 6371.0,
) -> pd.DataFrame:
    """Convert virtual illuminated-atmosphere receivers into Glow volumes."""
    rows: list[dict[str, Any]] = []
    if red_light_reference is None or red_light_reference.empty:
        return pd.DataFrame()
    timeline = _timeline_map(event_timeline)
    for _, source in red_light_reference.iterrows():
        angle = _finite(source.get("solar_altitude_deg"))
        direction = _finite(source.get("direction_offset_deg"))
        distance = _finite(source.get("distance_km"))
        altitude = _finite(source.get("sampled_receiver_altitude_km"))
        ref_id = str(source.get("reference_receiver_id"))
        time_value = source.get("time")
        event = timeline.get((str(time_value), None if angle is None else round(angle, 8)), {})
        solar_azimuth = _finite(event.get("solar_azimuth_deg"))
        geometry_ready = None not in (angle, direction, distance, altitude, solar_azimuth) and distance > 0.0
        base = _finite(source.get("voxel_bottom_km"))
        top = _finite(source.get("voxel_top_km"))
        if altitude is not None and (base is None or top is None or top <= base):
            base, top = max(0.0, altitude - 0.25), altitude + 0.25
        record: dict[str, Any] = {
            "time": time_value,
            "solar_altitude_deg": angle,
            "solar_azimuth_deg": solar_azimuth,
            "glow_volume_id": ref_id.replace("redref::", "glowvol::", 1),
            "reference_receiver_id": ref_id,
            "direction_offset_deg": direction,
            "distance_km": distance,
            "scatter_altitude_km": altitude,
            "scatter_layer_bottom_km": base,
            "scatter_layer_top_km": top,
            "glow_volume_domain": GLOW_VOLUME_DOMAIN,
            "glow_volume_is_cloud": False,
            "glow_geometry_state": "GLOW_SCATTERING_GEOMETRY_UNRESOLVED",
            "twilight_glow_contract": TWILIGHT_GLOW_CONTRACT,
        }
        if geometry_ready:
            bearing = (float(solar_azimuth) + float(direction)) % 360.0
            target_lat, target_lon = destination_point(
                float(observer_lat_deg), float(observer_lon_deg), bearing,
                float(distance), float(earth_radius_km),
            )
            geom = directional_scattering_geometry(
                observer_lat_deg=float(observer_lat_deg),
                observer_lon_deg=float(observer_lon_deg),
                observer_alt_km=float(observer_alt_km),
                target_lat_deg=float(target_lat),
                target_lon_deg=float(target_lon),
                target_alt_km=float(altitude),
                solar_altitude_deg=float(angle),
                solar_azimuth_deg=float(solar_azimuth),
            )
            record.update({
                "target_lat": float(target_lat),
                "target_lon": float(target_lon),
                "solar_zenith_at_scatter_deg": geom.solar_zenith_deg,
                "view_zenith_at_scatter_deg": geom.view_zenith_deg,
                "relative_azimuth_at_scatter_deg": geom.relative_azimuth_deg,
                "scattering_angle_deg": geom.scattering_angle_deg,
                "rayleigh_phase_function_sr": rayleigh_phase_function_sr(geom.scattering_angle_deg),
                "glow_geometry_state": "GLOW_SCATTERING_GEOMETRY_READY",
            })
        rows.append(record)
    return pd.DataFrame(rows)


def _view_targets_from_glow_geometry(geometry: pd.DataFrame) -> pd.DataFrame:
    if geometry is None or geometry.empty:
        return pd.DataFrame()
    rows = []
    for _, row in geometry.iterrows():
        rows.append({
            "time": row.get("time"),
            "solar_altitude_deg": row.get("solar_altitude_deg"),
            "canvas_id": row.get("glow_volume_id"),
            "cloud_layer_id": row.get("glow_volume_id"),
            "direction_offset_deg": row.get("direction_offset_deg"),
            "target_distance_km": row.get("distance_km"),
            "target_base_km": row.get("scatter_layer_bottom_km"),
            "target_top_km": row.get("scatter_layer_top_km"),
            "photographic_target_eligible": True,
        })
    return pd.DataFrame(rows)


def _observer_precipitation(
    targets: pd.DataFrame,
    route_snapshots: pd.DataFrame,
    *,
    earth_radius_km: float,
) -> pd.DataFrame:
    if targets is None or targets.empty:
        return pd.DataFrame()
    frames = []
    for (time_value, angle), group in targets.groupby(["time", "solar_altitude_deg"], dropna=False, sort=False):
        route = route_snapshots
        if route is None or route.empty:
            route = pd.DataFrame()
        else:
            route = route_snapshots[
                route_snapshots["time"].astype(str).eq(str(time_value))
                & (pd.to_numeric(route_snapshots["solar_altitude_deg"], errors="coerce") - float(angle)).abs().le(1e-8)
            ]
        frame = build_viewing_precipitation_evidence(group, route, earth_radius_km=float(earth_radius_km))
        if frame is not None and not frame.empty:
            frames.append(frame)
    return pd.concat(frames, ignore_index=True, copy=False) if frames else pd.DataFrame()


def build_twilight_glow_branch(
    *,
    red_light_reference: pd.DataFrame,
    event_timeline: pd.DataFrame,
    cloud_layers: pd.DataFrame,
    target_optics: pd.DataFrame,
    aerosol_snapshots: pd.DataFrame,
    gas_profiles: pd.DataFrame,
    route_snapshots: pd.DataFrame,
    observer_lat_deg: float,
    observer_lon_deg: float,
    observer_alt_km: float = 0.0,
    earth_radius_km: float = 6371.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build target-volume evidence and per-angle Twilight Glow summaries."""
    geometry = build_twilight_glow_geometry(
        red_light_reference,
        event_timeline,
        observer_lat_deg=float(observer_lat_deg),
        observer_lon_deg=float(observer_lon_deg),
        observer_alt_km=float(observer_alt_km),
        earth_radius_km=float(earth_radius_km),
    )
    targets = _view_targets_from_glow_geometry(geometry)
    if targets.empty:
        return pd.DataFrame(), summarize_twilight_glow(pd.DataFrame(), event_timeline)
    precipitation = _observer_precipitation(targets, route_snapshots, earth_radius_km=float(earth_radius_km))
    observer_spectral = build_viewing_spectral_extinction(
        targets,
        cloud_layers if isinstance(cloud_layers, pd.DataFrame) else pd.DataFrame(),
        target_optics if isinstance(target_optics, pd.DataFrame) else pd.DataFrame(),
        aerosol_snapshots if isinstance(aerosol_snapshots, pd.DataFrame) else pd.DataFrame(),
        gas_profiles if isinstance(gas_profiles, pd.DataFrame) else pd.DataFrame(),
        precipitation,
        earth_radius_km=float(earth_radius_km),
        aerosol_lowest_endpoint_tolerance_km=0.05,
    )
    source_map = {
        _key(row.get("time"), row.get("solar_altitude_deg"), row.get("reference_receiver_id")): row
        for _, row in red_light_reference.iterrows()
    }
    observer_map = {
        _key(row.get("time"), row.get("solar_altitude_deg"), row.get("canvas_id")): row
        for _, row in observer_spectral.iterrows()
    }
    gas_index = _gas_profile_index(gas_profiles)
    gas_contexts = _gas_context_index(gas_profiles)
    rows: list[dict[str, Any]] = []
    for _, geom in geometry.iterrows():
        angle = _finite(geom.get("solar_altitude_deg"))
        direction = _finite(geom.get("direction_offset_deg"))
        glow_id = str(geom.get("glow_volume_id"))
        source = source_map.get(_key(geom.get("time"), angle, geom.get("reference_receiver_id")))
        observer = observer_map.get(_key(geom.get("time"), angle, glow_id))
        gas_key = (
            str(geom.get("time")),
            None if angle is None else round(angle, 8),
            None if direction is None else round(direction, 8),
        )
        profiles = gas_index.get(gas_key)
        target = pd.Series({
            "direction_offset_deg": direction,
            "target_distance_km": geom.get("distance_km"),
            "target_base_km": geom.get("scatter_layer_bottom_km"),
            "target_top_km": geom.get("scatter_layer_top_km"),
        })
        rayleigh_tau, rayleigh_status, required_segments, resolved_segments = _rayleigh_observer_path(
            target, profiles, float(earth_radius_km)
        )
        observer_gas_species, observer_gas_species_status, gas_required_segments, gas_resolved_segments, gas_path_km = _observer_gas_species_path(
            target, gas_contexts.get(gas_key), float(earth_radius_km)
        )
        local = _local_molecular_state(target, profiles)
        phase = _finite(geom.get("rayleigh_phase_function_sr"))
        direct_fraction = _finite(source.get("v1_direct_solar_fraction")) if source is not None else None
        sun_components = _sun_component_state(source)
        upstream_full = bool(source is not None and source.get("red_light_path_evidence_complete", False) and all(sun_components.values()))
        viewing_row_full = bool(observer is not None and str(observer.get("viewing_spectral_status")) == "VIEW_FULL_SIX_BAND_RT")
        observer_species_full = observer_gas_species_status == "GLOW_OBSERVER_GAS_PATH_RESOLVED"
        geometry_full = str(geom.get("glow_geometry_state")) == "GLOW_SCATTERING_GEOMETRY_READY"
        rayleigh_full = rayleigh_status == "GLOW_OBSERVER_RAYLEIGH_PATH_RESOLVED"
        local_full = local is not None and phase is not None

        sun_missing = [component for component, ready in sun_components.items() if not ready]
        observer_component_state = {
            "RAYLEIGH": rayleigh_full,
            "GAS_SPECIES": observer_species_full,
            "GAS": bool(observer is not None and str(observer.get("view_gas_status")) == "VIEW_GAS_RT_RESOLVED"),
            "AEROSOL": bool(observer is not None and str(observer.get("view_aerosol_status")) == "VIEW_AEROSOL_3D_RESOLVED"),
            "CLOUD": bool(observer is not None and str(observer.get("view_cloud_status")) in {"VIEW_CLOUD_PATH_CLEAR", "VIEW_CLOUD_OPTICS_RESOLVED_OCCUPANCY_EXPECTATION"}),
            "PRECIPITATION": bool(observer is not None and str(observer.get("view_precipitation_status")) == "VIEW_PRECIPITATION_OPTICS_RESOLVED"),
        }
        observer_full = viewing_row_full and all(observer_component_state.values())
        observer_missing = [component for component, ready in observer_component_state.items() if not ready]
        full_proxy = upstream_full and observer_full and geometry_full and local_full

        missing = []
        if not upstream_full:
            missing.append("SUN_TO_SCATTER_EXTINCTION")
        if not observer_full:
            missing.append("SCATTER_TO_OBSERVER_EXTINCTION")
        if not geometry_full:
            missing.append("SCATTERING_GEOMETRY")
        if not local_full:
            missing.append("LOCAL_MOLECULAR_STATE")
        record = geom.to_dict()
        record.update({
            "glow_direct_solar_fraction": direct_fraction,
            "glow_sun_path_state": source.get("red_light_path_state") if source is not None else "GLOW_SUN_PATH_MISSING",
            "glow_sun_path_evidence_complete": upstream_full,
            "glow_sun_extinction_state": "GLOW_SUN_TO_SCATTER_FULL_SIX_BAND_EXTINCTION" if upstream_full else ("GLOW_SUN_TO_SCATTER_PARTIAL_EXTINCTION" if source is not None else "GLOW_SUN_TO_SCATTER_EXTINCTION_UNRESOLVED"),
            "glow_sun_missing_components": ";".join(sorted(set(sun_missing))),
            "glow_observer_path_state": observer.get("viewing_spectral_status") if observer is not None else "GLOW_OBSERVER_PATH_MISSING",
            "glow_observer_path_evidence_complete": observer_full,
            "glow_observer_extinction_state": "GLOW_SCATTER_TO_OBSERVER_FULL_SIX_BAND_EXTINCTION" if observer_full else ("GLOW_SCATTER_TO_OBSERVER_PARTIAL_EXTINCTION" if observer is not None else "GLOW_SCATTER_TO_OBSERVER_EXTINCTION_UNRESOLVED"),
            "glow_observer_aerosol_status": observer.get("view_aerosol_status") if observer is not None else "GLOW_OBSERVER_AEROSOL_MISSING",
            "glow_observer_aerosol_required_segment_count": observer.get("view_aerosol_required_segment_count") if observer is not None else 0,
            "glow_observer_aerosol_resolved_segment_count": observer.get("view_aerosol_resolved_segment_count") if observer is not None else 0,
            "glow_observer_aerosol_lowest_endpoint_snap_segment_count": observer.get("view_aerosol_lowest_endpoint_snap_segment_count") if observer is not None else 0,
            "glow_observer_aerosol_endpoint_tolerance_km": 0.05,
            "glow_observer_missing_components": ";".join(sorted(set(observer_missing))),
            "glow_observer_rayleigh_status": rayleigh_status,
            "glow_observer_rayleigh_required_segment_count": required_segments,
            "glow_observer_rayleigh_resolved_segment_count": resolved_segments,
            "glow_observer_gas_species_status": observer_gas_species_status,
            "glow_observer_gas_species_required_segment_count": gas_required_segments,
            "glow_observer_gas_species_resolved_segment_count": gas_resolved_segments,
            "glow_observer_gas_species_path_km": gas_path_km,
            "glow_local_molecular_state": "RESOLVED" if local_full else "MISSING_OR_PARTIAL",
            "glow_aerosol_scattering_state": NO_AEROSOL_SOURCE_CLAIM,
            "glow_multiple_scattering_state": NO_MULTIPLE_SCATTERING_CLAIM,
            "glow_total_radiance_state": NO_TOTAL_RADIANCE_CLAIM,
            "glow_proxy_units": GLOW_PROXY_UNITS,
            "glow_missing_components": ";".join(sorted(set(missing))),
            "glow_result_role": "INDEPENDENT_DIAGNOSTIC_ONLY",
            "formation_independent": True,
            "viewing_independent": True,
            "calibrated_glow_radiance_available": False,
            "twilight_glow_contract": TWILIGHT_GLOW_CONTRACT,
            "twilight_glow_extinction_contract": TWILIGHT_GLOW_EXTINCTION_CONTRACT,
            "twilight_glow_single_scattering_contract": TWILIGHT_GLOW_SINGLE_SCATTERING_CONTRACT,
        })
        temperature_k, pressure_hpa, number_density_m3 = local if local is not None else (None, None, None)
        record["scatter_temperature_k"] = temperature_k
        record["scatter_pressure_hpa"] = pressure_hpa
        record["scatter_molecular_number_density_m3"] = number_density_m3
        for wavelength in SIX_BAND_WAVELENGTHS_NM:
            w = int(wavelength)
            # Sun -> scatter: decompose the already-computed Red-Light reference
            # path into explicit six-band physical components.  gas_tau includes
            # O3, so O3 is subtracted before the non-O3 gas term is published.
            sun_ray = _finite(source.get(f"rayleigh_tau_{w}nm")) if source is not None else None
            sun_aer = _finite(source.get(f"aerosol_tau_{w}nm")) if source is not None else None
            sun_gas_total = _finite(source.get(f"gas_tau_{w}nm")) if source is not None else None
            sun_o3 = _finite(source.get(f"gas_tau_o3_{w}nm")) if source is not None else None
            sun_gas_non_o3 = max(0.0, sun_gas_total - sun_o3) if sun_gas_total is not None and sun_o3 is not None else None
            sun_cloud = _finite(source.get("resolved_upstream_cloud_tau")) if source is not None else None
            sun_precip = _finite(source.get(f"tau_precip_{w}nm")) if source is not None else None
            sun_band_full = upstream_full and all(v is not None for v in (sun_ray, sun_gas_non_o3, sun_o3, sun_aer, sun_cloud, sun_precip))
            sun_total_tau = (
                max(0.0, sun_ray + sun_gas_non_o3 + sun_o3 + sun_aer + sun_cloud + sun_precip)
                if sun_band_full else None
            )
            sun_transmission = math.exp(-sun_total_tau) if sun_total_tau is not None else None
            sun_incident = (
                max(0.0, float(direct_fraction)) * float(sun_transmission)
                if sun_band_full and direct_fraction is not None else None
            )
            reference_incident = _finite(source.get(f"red_light_availability_{w}nm")) if source is not None else None

            # Scatter -> observer: reuse the independent Viewing path component
            # evidence, add explicit Rayleigh extinction, and independently
            # decompose HITRAN gas into O3 and O2+H2O.
            view_gas_total = _finite(observer.get(f"view_tau_gas_{w}nm")) if observer is not None else None
            view_aer = _finite(observer.get(f"view_tau_aerosol_{w}nm")) if observer is not None else None
            view_cloud = _finite(observer.get(f"view_tau_cloud_{w}nm")) if observer is not None else None
            view_precip = _finite(observer.get(f"view_tau_precip_{w}nm")) if observer is not None else None
            view_ray = rayleigh_tau.get(w) if rayleigh_tau is not None else None
            species = observer_gas_species.get(w) if observer_gas_species is not None else None
            view_o3 = _finite(species.get("o3")) if species is not None else None
            view_gas_non_o3 = _finite(species.get("non_o3")) if species is not None else None
            observer_band_full = observer_full and all(v is not None for v in (view_ray, view_gas_non_o3, view_o3, view_aer, view_cloud, view_precip, view_gas_total))
            # Species breakdown must close to the frozen Viewing total gas tau.
            gas_species_closes = bool(
                observer_band_full
                and abs((float(view_gas_non_o3) + float(view_o3)) - float(view_gas_total)) <= 1e-9
            )
            if observer_band_full and not gas_species_closes:
                observer_band_full = False
            observer_total_tau = (
                max(0.0, view_ray + view_gas_non_o3 + view_o3 + view_aer + view_cloud + view_precip)
                if observer_band_full else None
            )
            observer_transmission = math.exp(-observer_total_tau) if observer_total_tau is not None else None

            beta = (
                rayleigh_cross_section_m2(w) * float(number_density_m3)
                if number_density_m3 is not None else None
            )
            beta_phase = beta * float(phase) if beta is not None and phase is not None else None
            band_full_proxy = full_proxy and sun_band_full and observer_band_full and beta_phase is not None
            source_proxy = (
                max(0.0, float(sun_incident)) * float(observer_transmission) * float(beta_phase)
                if band_full_proxy and sun_incident is not None and observer_transmission is not None else None
            )

            record[f"glow_sun_tau_rayleigh_{w}nm"] = sun_ray
            record[f"glow_sun_tau_gas_non_o3_{w}nm"] = sun_gas_non_o3
            record[f"glow_sun_tau_o3_{w}nm"] = sun_o3
            record[f"glow_sun_tau_aerosol_{w}nm"] = sun_aer
            record[f"glow_sun_tau_cloud_{w}nm"] = sun_cloud
            record[f"glow_sun_tau_precip_{w}nm"] = sun_precip
            record[f"glow_sun_tau_total_{w}nm"] = sun_total_tau
            record[f"glow_sun_transmission_{w}nm"] = sun_transmission
            record[f"glow_sun_incident_relative_irradiance_{w}nm"] = sun_incident
            record[f"glow_sun_reference_incident_relative_irradiance_{w}nm"] = reference_incident
            record[f"glow_sun_band_evidence_state_{w}nm"] = "FULL" if sun_band_full else "MISSING"

            record[f"glow_observer_tau_rayleigh_{w}nm"] = view_ray
            record[f"glow_observer_tau_gas_non_o3_{w}nm"] = view_gas_non_o3
            record[f"glow_observer_tau_o3_{w}nm"] = view_o3
            record[f"glow_observer_tau_aerosol_{w}nm"] = view_aer
            record[f"glow_observer_tau_cloud_{w}nm"] = view_cloud
            record[f"glow_observer_tau_precip_{w}nm"] = view_precip
            record[f"glow_observer_tau_total_{w}nm"] = observer_total_tau
            record[f"glow_observer_transmission_{w}nm"] = observer_transmission
            record[f"glow_observer_band_evidence_state_{w}nm"] = "FULL" if observer_band_full else "MISSING"

            # Backward-compatible R5.7.30 composite aliases remain available.
            record[f"glow_incident_relative_irradiance_{w}nm"] = sun_incident
            record[f"glow_observer_nonrayleigh_tau_{w}nm"] = (view_gas_total + view_aer + view_cloud + view_precip) if band_full_proxy else None
            record[f"glow_observer_rayleigh_tau_{w}nm"] = view_ray
            record[f"glow_observer_total_tau_{w}nm"] = observer_total_tau if band_full_proxy else None
            record[f"glow_observer_total_transmission_{w}nm"] = observer_transmission if band_full_proxy else None
            record[f"glow_rayleigh_scattering_coefficient_m1_{w}nm"] = beta
            record[f"glow_rayleigh_source_coefficient_m1_sr_{w}nm"] = beta_phase
            record[f"glow_single_scattering_source_proxy_{w}nm"] = source_proxy
            record[f"glow_band_evidence_state_{w}nm"] = (
                "FULL_ZERO_DIRECT_SOLAR" if band_full_proxy and direct_fraction is not None and direct_fraction <= 0.0
                else ("FULL_RAYLEIGH_PROXY" if band_full_proxy else "MISSING")
            )
        all_band_full = all(record.get(f"glow_band_evidence_state_{int(w)}nm") in {"FULL_RAYLEIGH_PROXY", "FULL_ZERO_DIRECT_SOLAR"} for w in SIX_BAND_WAVELENGTHS_NM)
        if all_band_full and direct_fraction is not None and direct_fraction > 0.0:
            record["glow_proxy_state"] = "GLOW_RAYLEIGH_SINGLE_SCATTERING_PROXY_READY"
        elif all_band_full:
            record["glow_proxy_state"] = "GLOW_NO_DIRECT_SINGLE_SCATTERING_AT_VOLUME"
        elif any(_finite(record.get(f"glow_sun_incident_relative_irradiance_{int(w)}nm")) is not None for w in SIX_BAND_WAVELENGTHS_NM):
            record["glow_proxy_state"] = "GLOW_RAYLEIGH_SINGLE_SCATTERING_PROXY_PARTIAL"
        else:
            record["glow_proxy_state"] = "GLOW_RAYLEIGH_SINGLE_SCATTERING_UNRESOLVED"
        rows.append(record)
    detail = pd.DataFrame(rows)
    return detail, summarize_twilight_glow(detail, event_timeline)


def summarize_twilight_glow(detail: pd.DataFrame, event_timeline: pd.DataFrame) -> pd.DataFrame:
    """Return one independent Glow evidence row for every runtime angle."""
    rows: list[dict[str, Any]] = []
    timeline = event_timeline if isinstance(event_timeline, pd.DataFrame) else pd.DataFrame()
    if timeline.empty and detail is not None and not detail.empty:
        timeline = detail[[c for c in ["time", "solar_altitude_deg", "solar_azimuth_deg"] if c in detail.columns]].drop_duplicates()
    for _, event in timeline.iterrows():
        time_value = event.get("time")
        angle = _finite(event.get("solar_altitude_deg"))
        if detail is None or detail.empty or angle is None:
            group = pd.DataFrame()
        else:
            group = detail[
                detail["time"].astype(str).eq(str(time_value))
                & (pd.to_numeric(detail["solar_altitude_deg"], errors="coerce") - float(angle)).abs().le(1e-8)
            ]
        ready_states = {"GLOW_RAYLEIGH_SINGLE_SCATTERING_PROXY_READY", "GLOW_NO_DIRECT_SINGLE_SCATTERING_AT_VOLUME"}
        ready = group.get("glow_proxy_state", pd.Series(dtype=str)).astype(str).isin(ready_states)
        partial = group.get("glow_proxy_state", pd.Series(dtype=str)).astype(str).eq("GLOW_RAYLEIGH_SINGLE_SCATTERING_PROXY_PARTIAL")
        direct = pd.to_numeric(group.get("glow_direct_solar_fraction", pd.Series(dtype=float)), errors="coerce").fillna(0.0) > 0.0
        count = int(len(group))
        ready_count = int(ready.sum())
        direct_count = int(direct.sum())
        if count == 0:
            state = "GLOW_EVIDENCE_UNAVAILABLE"
        elif ready_count == count and direct_count == 0:
            state = "GLOW_NO_DIRECT_SINGLE_SCATTERING_VOLUME"
        elif ready_count == count:
            state = "GLOW_RAYLEIGH_PROXY_READY"
        elif ready_count or bool(partial.any()):
            state = "GLOW_RAYLEIGH_PROXY_PARTIAL"
        else:
            state = "GLOW_RAYLEIGH_PROXY_UNRESOLVED"
        missing: set[str] = set()
        for value in group.get("glow_missing_components", pd.Series(dtype=str)).fillna("").astype(str):
            missing.update(x for x in value.split(";") if x)
        record: dict[str, Any] = {
            "time": time_value,
            "solar_altitude_deg": angle,
            "solar_azimuth_deg": _finite(event.get("solar_azimuth_deg")),
            "glow_phase_class": "CORE_LATE_GLOW" if angle is not None and angle <= -4.0 else "CIVIL_TWILIGHT_CONTEXT",
            "glow_volume_count": count,
            "directly_illuminated_glow_volume_count": direct_count,
            "rayleigh_proxy_ready_volume_count": ready_count,
            "rayleigh_proxy_partial_volume_count": int(partial.sum()),
            "rayleigh_proxy_unresolved_volume_count": int(count - ready_count - int(partial.sum())),
            "glow_evidence_completeness": float(ready_count / count) if count else 0.0,
            "twilight_glow_state": state,
            "glow_missing_components": ";".join(sorted(missing)),
            "glow_aerosol_scattering_state": NO_AEROSOL_SOURCE_CLAIM,
            "glow_multiple_scattering_state": NO_MULTIPLE_SCATTERING_CLAIM,
            "glow_total_radiance_state": NO_TOTAL_RADIANCE_CLAIM,
            "calibrated_glow_radiance_available": False,
            "glow_result_role": "INDEPENDENT_DIAGNOSTIC_ONLY",
            "formation_independent": True,
            "viewing_independent": True,
            "twilight_glow_contract": TWILIGHT_GLOW_CONTRACT,
        }
        for wavelength in SIX_BAND_WAVELENGTHS_NM:
            values = pd.to_numeric(
                group.loc[ready, f"glow_single_scattering_source_proxy_{int(wavelength)}nm"]
                if not group.empty and f"glow_single_scattering_source_proxy_{int(wavelength)}nm" in group.columns
                else pd.Series(dtype=float),
                errors="coerce",
            ).dropna()
            record[f"mean_glow_single_scattering_source_proxy_{int(wavelength)}nm"] = float(values.mean()) if len(values) else np.nan
            record[f"max_glow_single_scattering_source_proxy_{int(wavelength)}nm"] = float(values.max()) if len(values) else np.nan
        rows.append(record)
    return pd.DataFrame(rows)
