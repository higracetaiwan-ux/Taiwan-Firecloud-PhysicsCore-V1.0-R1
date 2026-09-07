from __future__ import annotations
"""WGS84 geodesy primitives for Firecloud Shared Geometry Core.

Geometry only: no cloud/aerosol/gas/optical evidence is carried here.
"""
from dataclasses import dataclass
import math
import numpy as np

WGS84_A_M = 6378137.0
WGS84_F = 1.0 / 298.257223563
WGS84_B_M = WGS84_A_M * (1.0 - WGS84_F)
WGS84_E2 = WGS84_F * (2.0 - WGS84_F)


def geodetic_to_ecef(lat_deg: float, lon_deg: float, alt_m: float = 0.0) -> tuple[float, float, float]:
    lat = math.radians(float(lat_deg)); lon = math.radians(float(lon_deg)); h = float(alt_m)
    s = math.sin(lat); c = math.cos(lat)
    n = WGS84_A_M / math.sqrt(1.0 - WGS84_E2 * s * s)
    x = (n + h) * c * math.cos(lon)
    y = (n + h) * c * math.sin(lon)
    z = (n * (1.0 - WGS84_E2) + h) * s
    return x, y, z


def ecef_to_geodetic(x_m: float, y_m: float, z_m: float) -> tuple[float, float, float]:
    x = float(x_m); y = float(y_m); z = float(z_m)
    lon = math.atan2(y, x)
    p = math.hypot(x, y)
    if p < 1e-12:
        lat = math.copysign(math.pi / 2.0, z)
        alt = abs(z) - WGS84_B_M
        return math.degrees(lat), math.degrees(lon), alt
    lat = math.atan2(z, p * (1.0 - WGS84_E2))
    for _ in range(8):
        s = math.sin(lat)
        n = WGS84_A_M / math.sqrt(1.0 - WGS84_E2 * s * s)
        alt = p / max(1e-15, math.cos(lat)) - n
        lat_new = math.atan2(z, p * (1.0 - WGS84_E2 * n / (n + alt)))
        if abs(lat_new - lat) < 1e-13:
            lat = lat_new; break
        lat = lat_new
    s = math.sin(lat); n = WGS84_A_M / math.sqrt(1.0 - WGS84_E2 * s * s)
    alt = p / max(1e-15, math.cos(lat)) - n
    return math.degrees(lat), math.degrees(lon), alt


def ecef_to_enu(x_m: float, y_m: float, z_m: float, ref_lat_deg: float, ref_lon_deg: float, ref_alt_m: float = 0.0) -> tuple[float,float,float]:
    x0,y0,z0 = geodetic_to_ecef(ref_lat_deg, ref_lon_deg, ref_alt_m)
    dx,dy,dz = float(x_m)-x0, float(y_m)-y0, float(z_m)-z0
    lat=math.radians(float(ref_lat_deg)); lon=math.radians(float(ref_lon_deg))
    sl,cl=math.sin(lat),math.cos(lat); so,co=math.sin(lon),math.cos(lon)
    e = -so*dx + co*dy
    n = -sl*co*dx - sl*so*dy + cl*dz
    u = cl*co*dx + cl*so*dy + sl*dz
    return e,n,u


def enu_to_ecef(e_m: float, n_m: float, u_m: float, ref_lat_deg: float, ref_lon_deg: float, ref_alt_m: float = 0.0) -> tuple[float,float,float]:
    x0,y0,z0 = geodetic_to_ecef(ref_lat_deg, ref_lon_deg, ref_alt_m)
    lat=math.radians(float(ref_lat_deg)); lon=math.radians(float(ref_lon_deg))
    sl,cl=math.sin(lat),math.cos(lat); so,co=math.sin(lon),math.cos(lon)
    e,n,u=float(e_m),float(n_m),float(u_m)
    dx = -so*e - sl*co*n + cl*co*u
    dy = co*e - sl*so*n + cl*so*u
    dz = cl*n + sl*u
    return x0+dx,y0+dy,z0+dz


def ray_sphere_intersections(origin_xyz, direction_xyz, radius: float) -> tuple[float,float] | None:
    """Return parametric intersections t0<=t1 of O+tD with a sphere at origin."""
    o=np.asarray(origin_xyz,dtype=float); d=np.asarray(direction_xyz,dtype=float)
    if o.shape!=(3,) or d.shape!=(3,):
        raise ValueError("origin_xyz and direction_xyz must be length-3")
    a=float(np.dot(d,d))
    if not math.isfinite(a) or a<=0.0: return None
    b=2.0*float(np.dot(o,d)); c=float(np.dot(o,o))-float(radius)**2
    disc=b*b-4.0*a*c
    if disc < 0.0: return None
    root=math.sqrt(max(0.0,disc))
    return ((-b-root)/(2.0*a),(-b+root)/(2.0*a))
