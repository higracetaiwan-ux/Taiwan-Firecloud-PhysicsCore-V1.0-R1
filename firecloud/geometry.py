import math
from dataclasses import dataclass
from typing import Optional

from .config import EARTH_RADIUS_KM


def arc_angle_rad(distance_km: float, radius_km: float = EARTH_RADIUS_KM) -> float:
    return float(distance_km) / float(radius_km)


def earth_shadow_min_altitude_km(
    distance_km: float,
    solar_altitude_deg: float,
    radius_km: float = EARTH_RADIUS_KM,
) -> float:
    """Minimum local altitude required for direct solar illumination.

    2-D spherical-Earth geometry in the vertical plane containing the Sun.
    distance_km is positive from the observer *toward the Sun* along the surface.

    At distance d, local surface angle is delta=d/R.  If alpha+delta >= 0,
    the surface point lies on the sunlit side of the geometric terminator and the
    minimum altitude is 0.  Otherwise the ray must clear the spherical Earth:

        h_min = R * (sec(|alpha + delta|) - 1)

    Refraction and atmospheric extinction are intentionally not folded into this
    geometric function; they belong in later optical corrections.
    """
    alpha = math.radians(float(solar_altitude_deg))
    delta = arc_angle_rad(distance_km, radius_km)
    beta = alpha + delta
    if beta >= 0:
        return 0.0
    c = math.cos(abs(beta))
    if c <= 0:
        return float("inf")
    return radius_km * (1.0 / c - 1.0)


def cloud_layer_illuminated_fraction(
    layer_bottom_km: float,
    layer_top_km: float,
    shadow_altitude_km: float,
) -> float:
    """Fraction of a vertical cloud layer geometrically above Earth's shadow."""
    if layer_top_km <= layer_bottom_km:
        return 0.0
    if shadow_altitude_km <= layer_bottom_km:
        return 1.0
    if shadow_altitude_km >= layer_top_km:
        return 0.0
    return (layer_top_km - shadow_altitude_km) / (layer_top_km - layer_bottom_km)


def destination_point(lat_deg: float, lon_deg: float, bearing_deg: float, distance_km: float,
                      radius_km: float = EARTH_RADIUS_KM) -> tuple[float, float]:
    """Great-circle destination point."""
    lat1 = math.radians(lat_deg)
    lon1 = math.radians(lon_deg)
    brng = math.radians(bearing_deg)
    ang = distance_km / radius_km

    lat2 = math.asin(math.sin(lat1) * math.cos(ang) +
                     math.cos(lat1) * math.sin(ang) * math.cos(brng))
    lon2 = lon1 + math.atan2(math.sin(brng) * math.sin(ang) * math.cos(lat1),
                             math.cos(ang) - math.sin(lat1) * math.sin(lat2))
    lon2 = (lon2 + math.pi) % (2 * math.pi) - math.pi
    return math.degrees(lat2), math.degrees(lon2)


def ray_altitude_km_at_surface_distance(
    target_distance_km: float,
    target_altitude_km: float,
    sample_distance_km: float,
    solar_altitude_deg: float,
    radius_km: float = EARTH_RADIUS_KM,
) -> Optional[float]:
    """Altitude of a straight solar ray above the local spherical surface.

    The target cloud point is at target_distance_km from observer toward the Sun.
    We trace the ray from that point toward the Sun and intersect it with the radial
    line at sample_distance_km. This is a 2-D section in the Sun vertical plane.

    Returns None when the forward solar ray does not cross the requested radial line.
    """
    alpha = math.radians(float(solar_altitude_deg))
    delta_t = target_distance_km / radius_km
    delta_s = sample_distance_km / radius_km

    # Point P at target cloud location.
    rho_t = radius_km + target_altitude_km
    px = rho_t * math.cos(delta_t)
    py = rho_t * math.sin(delta_t)

    # Unit vector from target toward the Sun, defined using observer-local frame.
    sx = math.sin(alpha)
    sy = math.cos(alpha)

    # Radial unit vector at sample surface angle.
    rx = math.cos(delta_s)
    ry = math.sin(delta_s)

    # Solve P + t*s = rho*r. 2x2 linear system.
    # [sx, -rx] [t  ] = [-px]
    # [sy, -ry] [rho]   [-py]
    det = sx * (-ry) - sy * (-rx)
    if abs(det) < 1e-12:
        return None
    b1, b2 = -px, -py
    t = (b1 * (-ry) - b2 * (-rx)) / det
    rho = (sx * b2 - sy * b1) / det

    if t < -1e-8 or rho <= 0:
        return None
    return rho - radius_km


@dataclass
class IlluminationState:
    shadow_altitude_km: float
    illuminated_fraction: float


def dynamic_rez_entry_distance_km(
    solar_altitude_deg: float,
    cloud_altitude_km: float,
    radius_km: float = EARTH_RADIUS_KM,
) -> float:
    """Nearest surface distance toward the Sun where altitude z is directly sunlit.

    This is the geometric Dynamic-REZ boundary for a chosen altitude. It is
    derived from earth_shadow_min_altitude_km(d, alpha) == cloud_altitude_km.
    A return value of 0 means that altitude is already sunlit above the observer.

    Refraction/extinction are intentionally excluded.
    """
    z = max(0.0, float(cloud_altitude_km))
    depression = max(0.0, -math.radians(float(solar_altitude_deg)))
    if depression <= 0:
        return 0.0
    gamma = math.acos(radius_km / (radius_km + z)) if z > 0 else 0.0
    return max(0.0, radius_km * (depression - gamma))


def geometric_illumination_state(
    distance_km: float,
    cloud_altitude_km: float,
    solar_altitude_deg: float,
    radius_km: float = EARTH_RADIUS_KM,
) -> tuple[bool, float, float]:
    """Return (is_sunlit, shadow_top_km, clearance_km)."""
    shadow_h = earth_shadow_min_altitude_km(distance_km, solar_altitude_deg, radius_km)
    clearance = float(cloud_altitude_km) - shadow_h
    return clearance >= -1e-9, shadow_h, clearance

# ---------------------------------------------------------------------------
# PhysicsCore V1.0 R1 finite-solar-disk geometry primitives.
# Legacy earth_shadow_min_altitude_km() remains for diagnostics only.
# ---------------------------------------------------------------------------
SOLAR_ANGULAR_DIAMETER_DEG = 0.53


def local_solar_center_clearance_above_earth_limb_deg(
    distance_km: float,
    altitude_km: float,
    solar_altitude_deg: float,
    radius_km: float = EARTH_RADIUS_KM,
) -> float:
    """Angular clearance of the solar-disk center above the geometric Earth limb.

    Positive means the disk center is above the limb as seen from the target
    point.  This is the G0 spherical-Earth primitive.  R1/R2 refracted geometry
    will replace the straight-ray solar-center direction rather than applying a
    hidden post-hoc correction.
    """
    z = max(0.0, float(altitude_km))
    local_center_elev = float(solar_altitude_deg) + math.degrees(float(distance_km) / float(radius_km))
    limb_depression = math.degrees(math.acos(float(radius_km) / (float(radius_km) + z))) if z > 0.0 else 0.0
    return local_center_elev + limb_depression


def circular_disk_visible_fraction(center_clearance_deg: float, angular_diameter_deg: float = SOLAR_ANGULAR_DIAMETER_DEG) -> float:
    """Fraction of a circular solar disk above a locally straight occulting limb."""
    r = max(1e-12, float(angular_diameter_deg) / 2.0)
    h = float(center_clearance_deg)
    if h <= -r:
        return 0.0
    if h >= r:
        return 1.0
    u = max(-1.0, min(1.0, h / r))
    return (math.acos(-u) + u * math.sqrt(max(0.0, 1.0 - u*u))) / math.pi


def direct_solar_fraction_g0(
    distance_km: float,
    altitude_km: float,
    solar_altitude_deg: float,
    radius_km: float = EARTH_RADIUS_KM,
    angular_diameter_deg: float = SOLAR_ANGULAR_DIAMETER_DEG,
) -> float:
    """Finite-solar-disk DirectSolarFraction for the G0 geometric mode."""
    clearance = local_solar_center_clearance_above_earth_limb_deg(
        distance_km, altitude_km, solar_altitude_deg, radius_km
    )
    return circular_disk_visible_fraction(clearance, angular_diameter_deg)

# ---------------------------------------------------------------------------
# PhysicsCore V1.0-R5.2 finite-solar-disk penumbra height diagnostics.
# These are geometry diagnostics only. They do not substitute for spectral
# Sun→CloudBase transmission or an effective-red radiometric threshold.
# ---------------------------------------------------------------------------
def solar_disk_transition_altitude_km(
    distance_km: float,
    solar_altitude_deg: float,
    center_clearance_target_deg: float,
    radius_km: float = EARTH_RADIUS_KM,
) -> float:
    """Altitude where solar-center clearance above the Earth limb reaches target.

    center_clearance_target_deg=-solar_radius: upper solar limb first appears
    (any direct solar disk visible); 0: disk center clears limb; +solar_radius:
    full disk clears the limb.  Returns 0 when the surface already satisfies the
    target geometry.
    """
    local_center_elev = float(solar_altitude_deg) + math.degrees(float(distance_km) / float(radius_km))
    required_limb_depression_deg = float(center_clearance_target_deg) - local_center_elev
    if required_limb_depression_deg <= 0.0:
        return 0.0
    gamma = math.radians(required_limb_depression_deg)
    c = math.cos(gamma)
    if c <= 0.0:
        return float("inf")
    return float(radius_km) * (1.0 / c - 1.0)


def finite_solar_disk_penumbra_heights_km(
    distance_km: float,
    solar_altitude_deg: float,
    radius_km: float = EARTH_RADIUS_KM,
    angular_diameter_deg: float = SOLAR_ANGULAR_DIAMETER_DEG,
) -> dict:
    """Return G0 any-sun / center / full-disk transition heights.

    The traditional geometric Earth-shadow height is the solar-center boundary,
    not the top of the finite-disk penumbra.  The interval [H_any, H_full] is the
    solar-disk transition zone where 0 < F_sun < 1 (except endpoints).
    """
    sr = float(angular_diameter_deg) / 2.0
    h_any = solar_disk_transition_altitude_km(distance_km, solar_altitude_deg, -sr, radius_km)
    h_center = solar_disk_transition_altitude_km(distance_km, solar_altitude_deg, 0.0, radius_km)
    h_full = solar_disk_transition_altitude_km(distance_km, solar_altitude_deg, +sr, radius_km)
    return {
        "h_any_sun_km": h_any,
        "h_solar_center_km": h_center,
        "h_full_solar_disk_km": h_full,
        "penumbra_vertical_span_km": max(0.0, h_full - h_any) if math.isfinite(h_full) and math.isfinite(h_any) else float("nan"),
        "solar_angular_radius_deg": sr,
    }
