from __future__ import annotations
"""Shared directional scattering geometry for target-cloud response.

R5.7.22 freezes the full target-local directional geometry required by a
multiple-scattering cloud-response LUT.  Geometry only: no cloud phase
function, optical depth, or radiance is inferred here.

Conventions
-----------
* ``solar_zenith_deg`` (theta0): angle from target-local upward zenith to the
  target->Sun direction.  0 deg is overhead; 90 deg is the local horizon.
* ``view_zenith_deg`` (thetav): angle from target-local upward zenith to the
  target->Observer direction.  A ground observer below a cloud generally has
  thetav > 90 deg.
* ``relative_azimuth_deg`` (Delta phi): the smallest horizontal angular
  separation between the target->Sun and target->Observer azimuths, in
  [0, 180] deg.  If either horizontal projection is degenerate, Delta phi is
  canonically set to 0 deg and the degeneracy is recorded.
* ``scattering_angle_deg`` remains a derived diagnostic: angle between the
  incoming photon propagation direction (Sun->Cloud) and outgoing
  Cloud->Observer direction.  0 deg is forward scattering, 180 deg backward.

The event solar altitude/azimuth input is interpreted in the observer-local ENU
frame.  Because the Sun is effectively at infinity, that direction is first
converted to a global ECEF unit vector and then re-projected into the target
local ENU frame.  This removes the former approximation that treated the
observer's solar angles as if they were already target-local.
"""

from dataclasses import dataclass
import math
import numpy as np

from .geodesy import geodetic_to_ecef, ecef_to_enu, enu_to_ecef

DIRECTIONAL_SCATTERING_GEOMETRY_CONTRACT = "R5.7.22_FULL_DIRECTIONAL_SCATTERING_GEOMETRY_V1"


def _unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    if not math.isfinite(n) or n <= 0.0:
        raise ValueError("zero/non-finite vector")
    return v / n


def _wrap_azimuth_deg(v: float) -> float:
    return float(v) % 360.0


def _minimal_azimuth_separation_deg(a: float, b: float) -> float:
    d = abs((_wrap_azimuth_deg(a) - _wrap_azimuth_deg(b) + 180.0) % 360.0 - 180.0)
    return float(d)


def _enu_direction_from_altaz(altitude_deg: float, azimuth_deg: float) -> np.ndarray:
    alt = math.radians(float(altitude_deg))
    az = math.radians(float(azimuth_deg))
    # ENU convention: azimuth clockwise from north.
    e = math.cos(alt) * math.sin(az)
    n = math.cos(alt) * math.cos(az)
    u = math.sin(alt)
    return _unit(np.asarray([e, n, u], dtype=float))


def _enu_direction_to_ecef(direction_enu: np.ndarray, *, lat_deg: float, lon_deg: float, alt_m: float) -> np.ndarray:
    """Rotate an ENU direction vector into ECEF without translating it."""
    origin = np.asarray(geodetic_to_ecef(lat_deg, lon_deg, alt_m), dtype=float)
    # enu_to_ecef returns an absolute point, so subtract the reference origin.
    p = np.asarray(
        enu_to_ecef(
            float(direction_enu[0]), float(direction_enu[1]), float(direction_enu[2]),
            lat_deg, lon_deg, alt_m,
        ),
        dtype=float,
    )
    return _unit(p - origin)


def _ecef_direction_to_enu(direction_ecef: np.ndarray, *, lat_deg: float, lon_deg: float, alt_m: float) -> np.ndarray:
    """Rotate an ECEF direction into the target-local ENU frame."""
    origin = np.asarray(geodetic_to_ecef(lat_deg, lon_deg, alt_m), dtype=float)
    probe = origin + _unit(np.asarray(direction_ecef, dtype=float))
    e, n, u = ecef_to_enu(float(probe[0]), float(probe[1]), float(probe[2]), lat_deg, lon_deg, alt_m)
    return _unit(np.asarray([e, n, u], dtype=float))


def _direction_angles_enu(v: np.ndarray) -> tuple[float, float, float, bool]:
    """Return zenith, elevation, azimuth, and horizontal-degeneracy flag."""
    v = _unit(np.asarray(v, dtype=float))
    u = float(np.clip(v[2], -1.0, 1.0))
    zenith = float(math.degrees(math.acos(u)))
    elevation = 90.0 - zenith
    horizontal = math.hypot(float(v[0]), float(v[1]))
    if horizontal <= 1e-12:
        azimuth = 0.0
        degenerate = True
    else:
        azimuth = _wrap_azimuth_deg(math.degrees(math.atan2(float(v[0]), float(v[1]))))
        degenerate = False
    return zenith, elevation, azimuth, degenerate


@dataclass(frozen=True)
class DirectionalScatteringGeometry:
    solar_zenith_deg: float
    view_zenith_deg: float
    relative_azimuth_deg: float
    scattering_angle_deg: float
    solar_altitude_target_deg: float
    solar_azimuth_target_deg: float
    view_elevation_deg: float
    view_azimuth_target_deg: float
    mu0: float
    mu_view: float
    azimuth_degeneracy_state: str
    geometry_contract_version: str = DIRECTIONAL_SCATTERING_GEOMETRY_CONTRACT


def directional_scattering_geometry(
    *,
    observer_lat_deg: float,
    observer_lon_deg: float,
    observer_alt_km: float,
    target_lat_deg: float,
    target_lon_deg: float,
    target_alt_km: float,
    solar_altitude_deg: float,
    solar_azimuth_deg: float,
) -> DirectionalScatteringGeometry:
    """Return the full target-local directional cloud-scattering geometry.

    ``solar_altitude_deg`` and ``solar_azimuth_deg`` are the event solar angles
    at the observer.  The solar direction is converted to ECEF and reprojected
    at the target before theta0/Delta-phi are evaluated.
    """
    observer_alt_m = float(observer_alt_km) * 1000.0
    target_alt_m = float(target_alt_km) * 1000.0

    observer = np.asarray(
        geodetic_to_ecef(observer_lat_deg, observer_lon_deg, observer_alt_m),
        dtype=float,
    )
    target = np.asarray(
        geodetic_to_ecef(target_lat_deg, target_lon_deg, target_alt_m),
        dtype=float,
    )

    # Target->Sun global direction, using the observer-local event solar vector
    # as the anchor orientation.  Sun rays are parallel across the Canvas scale.
    sunward_observer_enu = _enu_direction_from_altaz(solar_altitude_deg, solar_azimuth_deg)
    sunward_ecef = _enu_direction_to_ecef(
        sunward_observer_enu,
        lat_deg=observer_lat_deg,
        lon_deg=observer_lon_deg,
        alt_m=observer_alt_m,
    )
    sunward_target_enu = _ecef_direction_to_enu(
        sunward_ecef,
        lat_deg=target_lat_deg,
        lon_deg=target_lon_deg,
        alt_m=target_alt_m,
    )

    # Cloud->Observer outgoing photon direction in target-local ENU.
    outgoing_ecef = _unit(observer - target)
    outgoing_target_enu = _ecef_direction_to_enu(
        outgoing_ecef,
        lat_deg=target_lat_deg,
        lon_deg=target_lon_deg,
        alt_m=target_alt_m,
    )

    theta0, solar_alt_target, solar_az_target, sun_az_degenerate = _direction_angles_enu(sunward_target_enu)
    thetav, view_elev, view_az_target, view_az_degenerate = _direction_angles_enu(outgoing_target_enu)

    if sun_az_degenerate and view_az_degenerate:
        rel_az = 0.0
        degeneracy = "SOLAR_AND_VIEW_AZIMUTH_DEGENERATE"
    elif sun_az_degenerate:
        rel_az = 0.0
        degeneracy = "SOLAR_AZIMUTH_DEGENERATE"
    elif view_az_degenerate:
        rel_az = 0.0
        degeneracy = "VIEW_AZIMUTH_DEGENERATE"
    else:
        rel_az = _minimal_azimuth_separation_deg(solar_az_target, view_az_target)
        degeneracy = "NONE"

    # Derive the diagnostic from the same target-local vectors used to define
    # theta0/thetav/Delta-phi, guaranteeing algebraic closure of the contract.
    c = float(np.clip(-np.dot(sunward_target_enu, outgoing_target_enu), -1.0, 1.0))
    scat = float(math.degrees(math.acos(c)))

    return DirectionalScatteringGeometry(
        solar_zenith_deg=theta0,
        view_zenith_deg=thetav,
        relative_azimuth_deg=rel_az,
        scattering_angle_deg=scat,
        solar_altitude_target_deg=solar_alt_target,
        solar_azimuth_target_deg=solar_az_target,
        view_elevation_deg=view_elev,
        view_azimuth_target_deg=view_az_target,
        mu0=float(math.cos(math.radians(theta0))),
        mu_view=float(math.cos(math.radians(thetav))),
        azimuth_degeneracy_state=degeneracy,
    )


def scattering_angle_deg(
    *, observer_lat_deg: float, observer_lon_deg: float, observer_alt_km: float,
    target_lat_deg: float, target_lon_deg: float, target_alt_km: float,
    solar_altitude_deg: float, solar_azimuth_deg: float,
) -> float:
    """Backward-compatible scalar diagnostic from the R5.7.22 geometry."""
    return directional_scattering_geometry(
        observer_lat_deg=observer_lat_deg,
        observer_lon_deg=observer_lon_deg,
        observer_alt_km=observer_alt_km,
        target_lat_deg=target_lat_deg,
        target_lon_deg=target_lon_deg,
        target_alt_km=target_alt_km,
        solar_altitude_deg=solar_altitude_deg,
        solar_azimuth_deg=solar_azimuth_deg,
    ).scattering_angle_deg
