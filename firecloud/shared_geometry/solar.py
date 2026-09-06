from __future__ import annotations
import math
from ..config import EARTH_RADIUS_KM
SOLAR_ANGULAR_DIAMETER_DEG=0.53

def local_solar_center_clearance_above_earth_limb_deg(distance_km: float, altitude_km: float, solar_altitude_deg: float, radius_km: float = EARTH_RADIUS_KM) -> float:
    z=max(0.0,float(altitude_km)); local=float(solar_altitude_deg)+math.degrees(float(distance_km)/float(radius_km))
    limb=math.degrees(math.acos(float(radius_km)/(float(radius_km)+z))) if z>0 else 0.0
    return local+limb

def circular_disk_visible_fraction(center_clearance_deg: float, angular_diameter_deg: float = SOLAR_ANGULAR_DIAMETER_DEG) -> float:
    r=max(1e-12,float(angular_diameter_deg)/2.0); h=float(center_clearance_deg)
    if h<=-r: return 0.0
    if h>=r: return 1.0
    u=max(-1.0,min(1.0,h/r)); return (math.acos(-u)+u*math.sqrt(max(0.0,1.0-u*u)))/math.pi

def direct_solar_fraction_g0(distance_km: float, altitude_km: float, solar_altitude_deg: float, radius_km: float = EARTH_RADIUS_KM, angular_diameter_deg: float = SOLAR_ANGULAR_DIAMETER_DEG) -> float:
    return circular_disk_visible_fraction(local_solar_center_clearance_above_earth_limb_deg(distance_km,altitude_km,solar_altitude_deg,radius_km),angular_diameter_deg)

def solar_disk_transition_altitude_km(distance_km: float, solar_altitude_deg: float, center_clearance_target_deg: float, radius_km: float = EARTH_RADIUS_KM) -> float:
    local=float(solar_altitude_deg)+math.degrees(float(distance_km)/float(radius_km)); req=float(center_clearance_target_deg)-local
    if req<=0: return 0.0
    c=math.cos(math.radians(req)); return float('inf') if c<=0 else float(radius_km)*(1.0/c-1.0)

def finite_solar_disk_penumbra_heights_km(distance_km: float, solar_altitude_deg: float, radius_km: float = EARTH_RADIUS_KM, angular_diameter_deg: float = SOLAR_ANGULAR_DIAMETER_DEG) -> dict:
    sr=float(angular_diameter_deg)/2.0
    ha=solar_disk_transition_altitude_km(distance_km,solar_altitude_deg,-sr,radius_km); hc=solar_disk_transition_altitude_km(distance_km,solar_altitude_deg,0.0,radius_km); hf=solar_disk_transition_altitude_km(distance_km,solar_altitude_deg,+sr,radius_km)
    return {'h_any_sun_km':ha,'h_solar_center_km':hc,'h_full_solar_disk_km':hf,'penumbra_vertical_span_km':max(0.0,hf-ha) if math.isfinite(hf) and math.isfinite(ha) else float('nan'),'solar_angular_radius_deg':sr}
