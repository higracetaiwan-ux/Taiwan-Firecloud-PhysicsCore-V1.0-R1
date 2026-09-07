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


def ray_altitude_matrix_km(target_distance_km: float, target_altitudes_km, sample_distances_km, solar_altitude_deg: float, radius_km: float = EARTH_RADIUS_KM) -> np.ndarray:
    """Broadcast Sun-ray heights for all target altitudes at one target distance.

    Output shape is (n_target_altitudes, n_sample_distances). This is the
    batch primitive used by Shared Geometry Core V1.3 to remove thousands of
    target-level Python calls while preserving the scalar/vector equations.
    """
    zs=np.asarray(target_altitudes_km,dtype=float)
    ds=np.asarray(sample_distances_km,dtype=float)
    if zs.size==0 or ds.size==0:
        return np.empty((zs.size,ds.size),dtype=float)
    r=float(radius_km); alpha=math.radians(float(solar_altitude_deg)); dt=float(target_distance_km)/r
    delta_s=ds/r
    rho_t=(r+zs)[:,None]
    px=rho_t*math.cos(dt); py=rho_t*math.sin(dt)
    sx=math.sin(alpha); sy=math.cos(alpha)
    rx=np.cos(delta_s)[None,:]; ry=np.sin(delta_s)[None,:]
    det=sx*(-ry)-sy*(-rx)
    good=np.abs(det)>=1e-12
    b1=-px; b2=-py
    t=np.full((zs.size,ds.size),np.nan,dtype=float)
    rho=np.full((zs.size,ds.size),np.nan,dtype=float)
    # det is 1xS and broadcasts across target heights.
    num_t=b1*(-ry)-b2*(-rx)
    num_rho=sx*b2-sy*b1
    np.divide(num_t,det,out=t,where=np.broadcast_to(good,t.shape))
    np.divide(num_rho,det,out=rho,where=np.broadcast_to(good,rho.shape))
    good2=np.broadcast_to(good,t.shape)&(t>=-1e-8)&(rho>0.0)
    out=np.full_like(t,np.nan)
    out[good2]=rho[good2]-r
    return out

def observer_los_height_agl_km(target_distance_km: float, target_height_agl_km: float, sample_distance_km: float, radius_km: float = EARTH_RADIUS_KM) -> float:
    """Curved-Earth observer→target LOS height above local surface.

    This preserves the existing tangent-parabola approximation used by Viewing
    and precipitation.  It is now one shared implementation so both branches
    cannot silently diverge.
    """
    dt=max(float(target_distance_km),1e-9); d=min(max(float(sample_distance_km),0.0),dt); r=float(radius_km)
    target_tangent=float(target_height_agl_km)-dt*dt/(2.0*r); line=(d/dt)*target_tangent; ground=-(d*d)/(2.0*r)
    return line-ground


def observer_los_heights_vectorized_agl_km(target_distance_km: float, target_height_agl_km: float, sample_distances_km, radius_km: float = EARTH_RADIUS_KM) -> np.ndarray:
    ds=np.asarray(sample_distances_km,dtype=float)
    if ds.size==0: return np.empty(0,dtype=float)
    dt=max(float(target_distance_km),1e-9); r=float(radius_km)
    d=np.clip(ds,0.0,dt)
    target_tangent=float(target_height_agl_km)-dt*dt/(2.0*r)
    line=(d/dt)*target_tangent
    ground=-(d*d)/(2.0*r)
    return line-ground

def sampled_segment_path_km(sample_distances_km, sample_heights_km, inside_mask) -> float:
    ds=np.asarray(sample_distances_km,dtype=float); zz=np.asarray(sample_heights_km,dtype=float); inside=np.asarray(inside_mask,dtype=bool)
    if ds.size<2 or zz.size!=ds.size or inside.size!=ds.size: return 0.0
    # Small deterministic ray samplers dominate PhysicsCore hot paths (17/25 points).
    # A tight Python loop is faster than allocating several temporary NumPy arrays
    # at this scale while preserving exactly the legacy half-segment boundary rule.
    if ds.size <= 64:
        path=0.0
        for j in range(ds.size-1):
            if not (inside[j] or inside[j+1]): continue
            if not (math.isfinite(float(ds[j])) and math.isfinite(float(ds[j+1])) and math.isfinite(float(zz[j])) and math.isfinite(float(zz[j+1]))): continue
            frac=1.0 if inside[j] and inside[j+1] else 0.5
            path += frac*math.hypot(float(ds[j+1]-ds[j]),float(zz[j+1]-zz[j]))
        return float(path)
    valid=np.isfinite(ds)&np.isfinite(zz)
    segmask=(inside[:-1]|inside[1:])&valid[:-1]&valid[1:]
    if not np.any(segmask): return 0.0
    frac=np.where(inside[:-1]&inside[1:],1.0,0.5)
    lengths=np.hypot(np.diff(ds),np.diff(zz))*frac
    return float(np.sum(lengths[segmask]))

def sample_sun_ray_segment(target_distance_km: float, target_altitude_km: float, start_km: float, end_km: float, solar_altitude_deg: float, *, sample_count: int=17, radius_km: float = EARTH_RADIUS_KM):
    xs=np.linspace(float(start_km),float(end_km),max(2,int(sample_count)))
    zz=ray_altitudes_vectorized_km(target_distance_km,target_altitude_km,xs,solar_altitude_deg,radius_km)
    return xs,zz

def sample_observer_los_segment(target_distance_km: float, target_height_agl_km: float, start_km: float, end_km: float, *, sample_count: int=17, radius_km: float = EARTH_RADIUS_KM):
    xs=np.linspace(float(start_km),float(end_km),max(2,int(sample_count)))
    zz=observer_los_heights_vectorized_agl_km(target_distance_km,target_height_agl_km,xs,radius_km)
    return xs,zz
