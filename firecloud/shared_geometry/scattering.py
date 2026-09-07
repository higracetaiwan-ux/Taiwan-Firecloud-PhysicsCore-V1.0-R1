from __future__ import annotations
"""Shared scattering-angle geometry for target-cloud response.

Geometry only.  No cloud phase function, optical depth, or radiance is inferred.
"""
import math
import numpy as np
from .geodesy import geodetic_to_ecef, enu_to_ecef


def _unit(v: np.ndarray) -> np.ndarray:
    n=float(np.linalg.norm(v))
    if not math.isfinite(n) or n <= 0.0:
        raise ValueError("zero/non-finite vector")
    return v/n


def scattering_angle_deg(
    *, observer_lat_deg: float, observer_lon_deg: float, observer_alt_km: float,
    target_lat_deg: float, target_lon_deg: float, target_alt_km: float,
    solar_altitude_deg: float, solar_azimuth_deg: float,
) -> float:
    """Return photon scattering angle at the target cloud in degrees.

    The angle is between the incoming solar photon propagation direction
    (Sun→Cloud) and the outgoing Cloud→Observer direction.  Solar altitude and
    azimuth are expressed in the target-local ENU frame; over Taiwan Firecloud's
    0–100 km Canvas domain the event solar direction is sufficiently common for
    this geometry contract, while future refracted per-target solar vectors may
    replace this input without changing the scattering-angle definition.
    """
    t=np.asarray(geodetic_to_ecef(target_lat_deg,target_lon_deg,float(target_alt_km)*1000.0),dtype=float)
    o=np.asarray(geodetic_to_ecef(observer_lat_deg,observer_lon_deg,float(observer_alt_km)*1000.0),dtype=float)
    outgoing=_unit(o-t)

    alt=math.radians(float(solar_altitude_deg)); az=math.radians(float(solar_azimuth_deg))
    # ENU convention: azimuth clockwise from north.
    e=math.cos(alt)*math.sin(az); n=math.cos(alt)*math.cos(az); u=math.sin(alt)
    p=np.asarray(enu_to_ecef(e,n,u,target_lat_deg,target_lon_deg,float(target_alt_km)*1000.0),dtype=float)
    sunward=_unit(p-t)
    incoming=-sunward
    c=float(np.clip(np.dot(incoming,outgoing),-1.0,1.0))
    return float(math.degrees(math.acos(c)))
