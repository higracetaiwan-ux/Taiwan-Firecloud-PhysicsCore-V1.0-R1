"""Backward-compatible facade for Firecloud Shared Geometry Core V1.0.

New code should prefer ``firecloud.shared_geometry``. Existing imports from
``firecloud.geometry`` remain valid to avoid a risky all-at-once migration.
"""
from dataclasses import dataclass
from typing import Optional
from .shared_geometry import *

@dataclass
class IlluminationState:
    shadow_altitude_km: float
    illuminated_fraction: float
