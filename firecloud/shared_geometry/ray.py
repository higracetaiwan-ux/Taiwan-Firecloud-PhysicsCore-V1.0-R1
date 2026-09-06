from __future__ import annotations
import math
from typing import Optional
import numpy as np
from ..config import EARTH_RADIUS_KM

def ray_altitude_km_at_surface_distance(target_distance_km: float, target_altitude_km: float, sample_distance_km: float, solar_altitude_deg: float, radius_km: float = EARTH_RADIUS_KM) -> Optional[float]:
    alpha=math.radians(float(solar_altitude_deg)); dt=target_distance_km/radius_km; ds=sample_distance_km/radius_km
    rho_t=radius_km+target_altitude_km; px=rho_t*math.cos(dt); py=rho_t*math.sin(dt)
    sx=math.sin(alpha); sy=math.cos(alpha); rx=math.cos(ds); ry=math.sin(ds)
    det=sx*(-ry)-sy*(-rx)
    if abs(det)<1e-12: return None
    b1,b2=-px,-py; t=(b1*(-ry)-b2*(-rx))/det; rho=(sx*b2-sy*b1)/det
    if t < -1e-8 or rho<=0: return None
    return rho-radius_km

def ray_altitudes_vectorized_km(target_distance_km: float, target_altitude_km: float, sample_distances_km, solar_altitude_deg: float, radius_km: float = EARTH_RADIUS_KM) -> np.ndarray:
    ds=np.asarray(sample_distances_km,dtype=float)
    if ds.size==0: return np.empty(0,dtype=float)
    alpha=math.radians(float(solar_altitude_deg)); dt=float(target_distance_km)/float(radius_km); delta_s=ds/float(radius_km)
    rho_t=float(radius_km)+float(target_altitude_km); px=rho_t*math.cos(dt); py=rho_t*math.sin(dt)
    sx=math.sin(alpha); sy=math.cos(alpha); rx=np.cos(delta_s); ry=np.sin(delta_s); det=sx*(-ry)-sy*(-rx)
    good=np.abs(det)>=1e-12; t=np.full(ds.shape,np.nan); rho=np.full(ds.shape,np.nan); b1,b2=-px,-py
    t[good]=(b1*(-ry[good])-b2*(-rx[good]))/det[good]; rho[good]=(sx*b2-sy*b1)/det[good]
    good &= (t>=-1e-8)&(rho>0.0); out=np.full(ds.shape,np.nan); out[good]=rho[good]-float(radius_km); return out

def observer_los_height_agl_km(target_distance_km: float, target_height_agl_km: float, sample_distance_km: float, radius_km: float = EARTH_RADIUS_KM) -> float:
    """Curved-Earth observer→target LOS height above local surface.

    This preserves the existing tangent-parabola approximation used by Viewing
    and precipitation.  It is now one shared implementation so both branches
    cannot silently diverge.
    """
    dt=max(float(target_distance_km),1e-9); d=min(max(float(sample_distance_km),0.0),dt); r=float(radius_km)
    target_tangent=float(target_height_agl_km)-dt*dt/(2.0*r); line=(d/dt)*target_tangent; ground=-(d*d)/(2.0*r)
    return line-ground
