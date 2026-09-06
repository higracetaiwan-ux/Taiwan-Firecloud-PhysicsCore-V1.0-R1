from __future__ import annotations
import math
from dataclasses import dataclass
from ..config import EARTH_RADIUS_KM

def arc_angle_rad(distance_km: float, radius_km: float = EARTH_RADIUS_KM) -> float:
    return float(distance_km) / float(radius_km)

def earth_shadow_min_altitude_km(distance_km: float, solar_altitude_deg: float, radius_km: float = EARTH_RADIUS_KM) -> float:
    alpha=math.radians(float(solar_altitude_deg)); delta=arc_angle_rad(distance_km,radius_km); beta=alpha+delta
    if beta>=0: return 0.0
    c=math.cos(abs(beta))
    return float('inf') if c<=0 else radius_km*(1.0/c-1.0)

def cloud_layer_illuminated_fraction(layer_bottom_km: float, layer_top_km: float, shadow_altitude_km: float) -> float:
    if layer_top_km<=layer_bottom_km: return 0.0
    if shadow_altitude_km<=layer_bottom_km: return 1.0
    if shadow_altitude_km>=layer_top_km: return 0.0
    return (layer_top_km-shadow_altitude_km)/(layer_top_km-layer_bottom_km)

def destination_point(lat_deg: float, lon_deg: float, bearing_deg: float, distance_km: float, radius_km: float = EARTH_RADIUS_KM) -> tuple[float,float]:
    lat1=math.radians(lat_deg); lon1=math.radians(lon_deg); brng=math.radians(bearing_deg); ang=distance_km/radius_km
    lat2=math.asin(math.sin(lat1)*math.cos(ang)+math.cos(lat1)*math.sin(ang)*math.cos(brng))
    lon2=lon1+math.atan2(math.sin(brng)*math.sin(ang)*math.cos(lat1), math.cos(ang)-math.sin(lat1)*math.sin(lat2))
    lon2=(lon2+math.pi)%(2*math.pi)-math.pi
    return math.degrees(lat2),math.degrees(lon2)

def dynamic_rez_entry_distance_km(solar_altitude_deg: float, cloud_altitude_km: float, radius_km: float = EARTH_RADIUS_KM) -> float:
    z=max(0.0,float(cloud_altitude_km)); depression=max(0.0,-math.radians(float(solar_altitude_deg)))
    if depression<=0: return 0.0
    gamma=math.acos(radius_km/(radius_km+z)) if z>0 else 0.0
    return max(0.0,radius_km*(depression-gamma))

def geometric_illumination_state(distance_km: float, cloud_altitude_km: float, solar_altitude_deg: float, radius_km: float = EARTH_RADIUS_KM) -> tuple[bool,float,float]:
    h=earth_shadow_min_altitude_km(distance_km,solar_altitude_deg,radius_km); clearance=float(cloud_altitude_km)-h
    return clearance>=-1e-9,h,clearance
