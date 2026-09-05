"""PhysicsCore V1.0 immutable data contracts (R1 foundation).

These contracts encode the frozen Stage 1 architecture.  They deliberately
separate evidence, physical state, uncertainty and operational/decision layers.
R1 adds the contracts without forcing the legacy V8.4.16.7 execution path to
pretend later V1 stages are already implemented.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Optional, Sequence, Tuple


SIX_BAND_WAVELENGTHS_NM: Tuple[int, ...] = (550, 575, 600, 650, 700, 750)
CORE_FIRECLOUD_ANGLES_DEG: Tuple[float, ...] = (
    0.0, -0.5, -1.0, -1.5, -2.0, -2.5, -3.0, -3.5, -4.0,
)
PRE_SUNSET_DIAGNOSTIC_ANGLES_DEG: Tuple[float, ...] = (2.0, 1.0)
LATE_FIRECLOUD_DIAGNOSTIC_ANGLES_DEG: Tuple[float, ...] = (-4.5, -5.0, -5.5, -6.0)
NAUTICAL_TWILIGHT_DIAGNOSTIC_ANGLES_DEG: Tuple[float, ...] = (-7.0, -8.0, -9.0, -10.0, -11.0, -12.0)


class SourceType(str, Enum):
    NATIVE_FORECAST = "NATIVE_FORECAST"
    INTERPOLATED_FORECAST = "INTERPOLATED_FORECAST"
    DERIVED_PHYSICAL = "DERIVED_PHYSICAL"
    OBSERVATION = "OBSERVATION"
    CALIBRATION = "CALIBRATION"


class EvidenceState(str, Enum):
    FULL = "FULL"
    PARTIAL_OPTICS = "PARTIAL_OPTICS"
    GEOMETRY_ONLY = "GEOMETRY_ONLY"
    MISSING = "MISSING"


class BoundLevel(int, Enum):
    UNBOUNDED = 0
    ONE_SIDED_CONSTRAINT = 1
    PHYSICAL_INTERVAL = 2
    FULL_RT = 3


class GeometryConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class CloudFractionState(str, Enum):
    CLEAR = "CLEAR"
    PARTIAL_OCCUPANCY = "PARTIAL_OCCUPANCY"
    CLOUD_OCCUPIED = "CLOUD_OCCUPIED"
    UNKNOWN = "UNKNOWN"


class RefractionMode(str, Enum):
    G0_GEOMETRIC = "G0_GEOMETRIC"
    R1_STANDARD_REFRACTION = "R1_STANDARD_REFRACTION"
    R2_PROFILE_REFRACTION = "R2_PROFILE_REFRACTION"


class CanvasDomain(str, Enum):
    PRIMARY_CANVAS_0_40 = "PRIMARY_CANVAS_0_40"
    EXTENDED_CANVAS_40_100 = "EXTENDED_CANVAS_40_100"
    OTHER_DIAGNOSTIC = "OTHER_DIAGNOSTIC"


class PrecipitationRole(str, Enum):
    NONE = "NONE"
    ILLUMINATION_BLOCKER = "ILLUMINATION_BLOCKER"
    VIEW_OBSTRUCTION = "VIEW_OBSTRUCTION"
    BOTH = "BOTH"


@dataclass(frozen=True)
class ForecastFieldProvenance:
    provider: str
    model: str = ""
    cycle: Optional[datetime] = None
    valid_time: Optional[datetime] = None
    variable: str = ""
    native_horizontal_resolution: Optional[str] = None
    native_vertical_resolution: Optional[str] = None
    source_type: SourceType = SourceType.NATIVE_FORECAST
    interpolation: Optional[str] = None
    fallback: Optional[str] = None
    missing_reason: Optional[str] = None
    extra: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CloudLayer:
    layer_id: str
    direction_offset_deg: float
    distance_km: float
    z_base_km: float
    z_top_km: float
    cloud_fraction_state: CloudFractionState
    cloud_fraction: Optional[float] = None
    liquid_condensate_kgkg: Optional[float] = None
    ice_condensate_kgkg: Optional[float] = None
    phase: str = "UNKNOWN"
    effective_radius_um: Optional[float] = None
    cot: Optional[float] = None
    geometry_confidence: GeometryConfidence = GeometryConfidence.UNKNOWN
    optical_evidence: EvidenceState = EvidenceState.MISSING
    evidence_consistency: str = "UNKNOWN"
    provenance: Tuple[ForecastFieldProvenance, ...] = ()
    geometry_source: str = "NATIVE_MODEL_LEVELS"


@dataclass(frozen=True)
class CloudScene:
    valid_time: Optional[datetime]
    layers: Tuple[CloudLayer, ...]
    geometry_completeness: Optional[float] = None
    optics_completeness: Optional[float] = None
    provenance: Tuple[ForecastFieldProvenance, ...] = ()


@dataclass(frozen=True)
class SolarGeometryState:
    solar_altitude_geometric_deg: float
    solar_azimuth_deg: float
    solar_depression_deg: float
    refraction_mode_requested: RefractionMode
    refraction_mode_used: RefractionMode
    refraction_data_completeness: str
    refraction_fallback_reason: Optional[str]
    finite_solar_disk_enabled: bool = True
    solar_angular_diameter_deg: float = 0.53


@dataclass(frozen=True)
class CanvasCandidate:
    canvas_id: str
    cloud_layer_id: str
    latitude: float
    longitude: float
    cloud_base_altitude_km: float
    distance_km: float
    azimuth_deg: float
    operational_domain: CanvasDomain
    geometry_confidence: GeometryConfidence
    provenance: Tuple[ForecastFieldProvenance, ...] = ()


@dataclass(frozen=True)
class DirectSolarState:
    direct_solar_fraction: float
    solar_disk_visible_fraction: float
    shadow_diagnostic_height_km: Optional[float]
    refraction_mode_used: RefractionMode
    ray_status: str
    confidence: GeometryConfidence


@dataclass(frozen=True)
class RaySegment:
    segment_id: str
    start_distance_km: float
    end_distance_km: float
    midpoint_lat: float
    midpoint_lon: float
    midpoint_altitude_km: float
    path_length_km: float
    direct_solar_fraction: Optional[float] = None
    provenance: Tuple[ForecastFieldProvenance, ...] = ()


@dataclass(frozen=True)
class SolarRay:
    ray_id: str
    canvas_id: str
    solar_angle_deg: float
    refraction_mode_used: RefractionMode
    segments: Tuple[RaySegment, ...]
    cloud_intersection_ids: Tuple[str, ...] = ()
    precipitation_intersection_ids: Tuple[str, ...] = ()
    dynamic_rez_segment_ids: Tuple[str, ...] = ()
    corridor_segment_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class SpectralOpticalPath:
    wavelength_nm: int
    tau_gas: Optional[float]
    tau_aerosol: Optional[float]
    tau_cloud: Optional[float]
    tau_precip: Optional[float]
    tau_total: Optional[float]
    transmission: Optional[float]
    evidence_state: EvidenceState
    bound_level: BoundLevel
    bottleneck_segment_id: Optional[str] = None


@dataclass(frozen=True)
class PredictionUncertainty:
    dependency: str
    evidence_state: EvidenceState
    bound_level: BoundLevel
    criticality: str
    affected_outputs: Tuple[str, ...]
    reason: str
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    affected_canvas_ids: Tuple[str, ...] = ()
    affected_angles_deg: Tuple[float, ...] = ()
    affected_wavelengths_nm: Tuple[int, ...] = ()
    affected_ray_segment_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class OpticalPathResult:
    """Canvas-specific six-band Sun→CloudBase optical path result."""
    canvas_id: str
    solar_angle_deg: float
    spectral_paths: Tuple[SpectralOpticalPath, ...]
    critical_path_status: str
    uncertainty: Tuple[PredictionUncertainty, ...] = ()
    ray_id: Optional[str] = None
    cloud_intersection_ids: Tuple[str, ...] = ()
    optical_bottleneck_segment_id: Optional[str] = None


@dataclass(frozen=True)
class CloudBaseIllumination:
    """Illumination delivered to one Canvas cloud base.

    irradiance values remain optional in R3 because absolute extraterrestrial
    spectral irradiance calibration is a later contract.  R3 preserves the
    physically required F_sun × T_lambda factor without fabricating radiometry.
    """
    canvas_id: str
    solar_angle_deg: float
    direct_solar_fraction: float
    spectral_transmission: Mapping[int, Optional[float]]
    relative_base_illumination: Mapping[int, Optional[float]]
    illumination_status: str
    illuminated_area_fraction: Optional[float] = None
    uncertain_area_fraction: Optional[float] = None
    confidence: GeometryConfidence = GeometryConfidence.UNKNOWN
    uncertainty: Tuple[PredictionUncertainty, ...] = ()


@dataclass(frozen=True)
class CanvasRadiance:
    """Stage-3 Canvas optical-response contract.

    Radiance values are retained as six-band relative/physical radiance fields;
    no single Canvas score is permitted here.
    """
    canvas_id: str
    solar_angle_deg: float
    spectral_radiance: Mapping[int, Optional[float]]
    brightness: Optional[float]
    redness: Optional[float]
    effective_illuminated_area: Optional[float]
    texture_structure: Optional[float] = None
    rt_tier: str = "TIER1_FAST_SOURCE_PROXY"
    response_status: str = "UNKNOWN"
    confidence: GeometryConfidence = GeometryConfidence.UNKNOWN
    uncertainty: Tuple[PredictionUncertainty, ...] = ()


@dataclass(frozen=True)
class FormationResult:
    """Stage-3 scene Formation contract with independent dimensions."""
    solar_angle_deg: float
    brightness: Optional[float]
    redness: Optional[float]
    effective_illuminated_area: Optional[float]
    formation_state: str
    formation_confidence: GeometryConfidence = GeometryConfidence.UNKNOWN
    canvas_results: Tuple[CanvasRadiance, ...] = ()
    uncertainty: Tuple[PredictionUncertainty, ...] = ()


@dataclass(frozen=True)
class PhysicsCoreResult:
    """Top-level V1 contract.

    R1 intentionally leaves later-stage fields optional.  Crucially, no GO/NO-GO,
    final_score or outing_score field exists here.
    """
    formation: Any = None
    viewing: Any = None
    twilight_glow: Any = None
    peak_window: Any = None
    uncertainty: Tuple[PredictionUncertainty, ...] = ()
    diagnostics: Mapping[str, Any] = field(default_factory=dict)
    provenance: Tuple[ForecastFieldProvenance, ...] = ()
