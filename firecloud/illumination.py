"""PhysicsCore V1.0 illumination foundation (R1).

R1 implements finite-solar-disk G0 DirectSolarFraction and the V1 contract
boundary.  R1/R2 refracted ray integration is intentionally not faked here; it
will be wired in a later checkpoint with explicit provenance/fallback.
"""
from __future__ import annotations
from .contracts import DirectSolarState, GeometryConfidence, RefractionMode
from .geometry import direct_solar_fraction_g0, earth_shadow_min_altitude_km


def direct_solar_state_g0(distance_km: float, altitude_km: float, solar_altitude_deg: float) -> DirectSolarState:
    f = direct_solar_fraction_g0(distance_km, altitude_km, solar_altitude_deg)
    if f <= 0.0:
        status = "FULL_EARTH_SHADOW"
    elif f >= 1.0:
        status = "FULL_SOLAR_DISK"
    else:
        status = "PARTIAL_SOLAR_DISK"
    return DirectSolarState(
        direct_solar_fraction=f,
        solar_disk_visible_fraction=f,
        shadow_diagnostic_height_km=earth_shadow_min_altitude_km(distance_km, solar_altitude_deg),
        refraction_mode_used=RefractionMode.G0_GEOMETRIC,
        ray_status=status,
        confidence=GeometryConfidence.HIGH,
    )
