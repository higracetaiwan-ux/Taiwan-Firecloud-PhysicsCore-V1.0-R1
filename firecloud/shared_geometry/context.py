from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class GeometryIdentity:
    """Stable identity for reusable geometry, independent of optical evidence."""
    observer_lat: float | None = None
    observer_lon: float | None = None
    observer_alt_km: float | None = None
    route_lattice_version: str = 'CURRENT'
    vertical_lattice_version: str = 'CURRENT'
    earth_model: str = 'SPHERICAL_G0'

@dataclass
class SharedGeometryContext:
    """In-analysis geometry cache with explicit reuse scopes.

    V1.0 intentionally stays memory-only. Persistent cross-event Observer/LUT
    caches belong to the later Geometry Atlas phase after route/refraction
    schemas are frozen.
    """
    identity: GeometryIdentity = field(default_factory=GeometryIdentity)
    event_fixed: dict[str, Any] = field(default_factory=dict)
    angle_fixed: dict[float, dict[str, Any]] = field(default_factory=dict)
    target_fixed: dict[tuple, Any] = field(default_factory=dict)

    def angle_bucket(self, solar_altitude_deg: float) -> dict[str, Any]:
        return self.angle_fixed.setdefault(float(solar_altitude_deg), {})
