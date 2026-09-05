from dataclasses import dataclass, field
from typing import Dict, Tuple
import math

EARTH_RADIUS_KM = 6371.0
# Full civil-twilight diagnostic timeline. 0° is the geometric horizon crossing.
# -0.5° is deliberately retained because it resolves the transition into the
# principal second-burn window better than integer-degree sampling alone.
# PhysicsCore V1.0 frozen angle contracts.
# Core Formation uses 0°..-4° at 0.5° resolution.  The broader windows are
# diagnostic branches and are kept separate from the R1 legacy execution loop
# so this first refactor checkpoint does not multiply expensive provider/RT calls.
FIRECLOUD_CORE_ANGLES_DEG = (0.0, -0.5, -1.0, -1.5, -2.0, -2.5, -3.0, -3.5, -4.0)
PRE_SUNSET_DIAGNOSTIC_ANGLES_DEG = (2.0, 1.0)
LATE_GLOW_ANGLES_DEG = (-4.0, -4.5, -5.0, -5.5, -6.0)
NAUTICAL_TWILIGHT_DIAGNOSTIC_ANGLES_DEG = (-7.0, -8.0, -9.0, -10.0, -11.0, -12.0)

# R2 runtime: execute the frozen 0°..-4° Core Formation grid at 0.5°.
# Extended/Late/Nautical diagnostics remain separate contracts and are not
# multiplied into the expensive RT scheduler until their dependency-aware
# branches are connected.
TWILIGHT_DIAGNOSTIC_ANGLES_DEG = FIRECLOUD_CORE_ANGLES_DEG

# Backward-compatible alias used by older code paths.
SOLAR_ANGLES_DEG = TWILIGHT_DIAGNOSTIC_ANGLES_DEG
DIRECTION_OFFSETS_DEG = (-5.0, 0.0, 5.0)
LEGACY_DISTANCE_MAX_KM = 440
LEGACY_DISTANCE_SAMPLES_KM = tuple(range(0, LEGACY_DISTANCE_MAX_KM + 1, 20))
# Dynamic RT route length is derived from the deepest atmosphere component that
# must be traversed by a directly sunlit Canvas ray. Cloud targets are modeled to
# 18 km, but native CAMS aerosol integration is defined through the 30-km
# atmosphere-top checkpoint. Therefore the provider/RT route must continue until
# the ray reaches 30 km; 18 km is NOT a safe route-termination ceiling.
RT_MODEL_TOP_KM = 18.0
RT_ROUTE_TERMINATION_TOP_KM = 30.0
RT_CANVAS_MAX_DISTANCE_KM = 100.0
RT_ROUTE_SEARCH_LIMIT_KM = 2500.0
DISTANCE_SAMPLES_KM = LEGACY_DISTANCE_SAMPLES_KM

# Geometric cloud-layer envelopes used by the coarse forecast provider.
# They are not WMO cloud-type definitions; they are modeling bins.
CLOUD_LAYERS_KM: Dict[str, Tuple[float, float]] = {
    "low": (0.0, 2.0),
    "mid": (2.0, 6.0),
    "high": (6.0, 13.0),
}

BANDS = (
    (0, 40, "Primary Canvas"),
    (40, 100, "Extended Canvas"),
    (100, 300, "Corridor"),
    (300, 350, "Strong Blocking"),
    (350, 440, "REZ"),
)

@dataclass(frozen=True)
class ModelConfig:
    solar_angles_deg: tuple = TWILIGHT_DIAGNOSTIC_ANGLES_DEG
    firecloud_core_angles_deg: tuple = FIRECLOUD_CORE_ANGLES_DEG
    late_glow_angles_deg: tuple = LATE_GLOW_ANGLES_DEG
    pre_sunset_diagnostic_angles_deg: tuple = PRE_SUNSET_DIAGNOSTIC_ANGLES_DEG
    nautical_twilight_diagnostic_angles_deg: tuple = NAUTICAL_TWILIGHT_DIAGNOSTIC_ANGLES_DEG
    direction_offsets_deg: tuple = DIRECTION_OFFSETS_DEG
    # Kept as the legacy diagnostic/scoring lattice for backward compatibility.
    distance_samples_km: tuple = DISTANCE_SAMPLES_KM
    earth_radius_km: float = EARTH_RADIUS_KM
    dynamic_route_step_km: float = 20.0
    rt_model_top_km: float = RT_MODEL_TOP_KM
    rt_route_termination_top_km: float = RT_ROUTE_TERMINATION_TOP_KM
    rt_canvas_max_distance_km: float = RT_CANVAS_MAX_DISTANCE_KM
    rt_route_search_limit_km: float = RT_ROUTE_SEARCH_LIMIT_KM

    @staticmethod
    def _shadow_top_km(distance_km: float, solar_altitude_deg: float, radius_km: float) -> float:
        beta = math.radians(float(solar_altitude_deg)) + float(distance_km) / float(radius_km)
        if beta >= 0.0:
            return 0.0
        c = math.cos(abs(beta))
        return float("inf") if c <= 0.0 else float(radius_km) * (1.0 / c - 1.0)

    @staticmethod
    def _ray_altitude_km(target_distance_km: float, target_altitude_km: float, sample_distance_km: float, solar_altitude_deg: float, radius_km: float) -> float:
        alpha = math.radians(float(solar_altitude_deg))
        dt = float(target_distance_km) / float(radius_km)
        ds = float(sample_distance_km) / float(radius_km)
        rho_t = float(radius_km) + float(target_altitude_km)
        px, py = rho_t * math.cos(dt), rho_t * math.sin(dt)
        sx, sy = math.sin(alpha), math.cos(alpha)
        rx, ry = math.cos(ds), math.sin(ds)
        det = sx * (-ry) - sy * (-rx)
        if abs(det) < 1e-12:
            return float("nan")
        b1, b2 = -px, -py
        t = (b1 * (-ry) - b2 * (-rx)) / det
        rho = (sx * b2 - sy * b1) / det
        if t < -1e-8 or rho <= 0.0:
            return float("nan")
        return rho - float(radius_km)

    @property
    def dynamic_domain_max_km(self) -> float:
        """Physics-derived Dynamic route domain.

        No legacy 440-km or fixed-margin cap is used. For each solar angle, Canvas
        distance checkpoint, and 0.5-km target height, only geometrically sunlit
        targets are considered. The Sunward route is extended until the ray rises
        above ``rt_route_termination_top_km``. The largest required exit distance is then
        rounded to the route lattice. Dynamic-REZ entry distances are also forced
        inside the domain even when late-twilight Canvas targets are fully shadowed.
        """
        step = max(1.0, float(self.dynamic_route_step_km))
        r = float(self.earth_radius_km)
        top = max(0.1, float(self.rt_route_termination_top_km))
        search_max = max(float(LEGACY_DISTANCE_MAX_KM), float(self.rt_route_search_limit_km))
        required = float(LEGACY_DISTANCE_MAX_KM)

        target_distances = list(range(0, int(round(float(self.rt_canvas_max_distance_km))) + 1, int(round(step))))
        target_altitudes = [0.25 + 0.5 * i for i in range(int(18.0 / 0.5))]

        # Route-domain geometry must cover the late-firecloud diagnostic branch
        # even though the expensive R2 runtime executes only the nine Core angles.
        _runtime_angles = tuple(float(x) for x in self.solar_angles_deg)
        _default_core = tuple(float(x) for x in FIRECLOUD_CORE_ANGLES_DEG)
        _domain_angles = (tuple(dict.fromkeys((*self.firecloud_core_angles_deg, *self.late_glow_angles_deg)))
                          if _runtime_angles == _default_core else _runtime_angles)
        for angle in _domain_angles:
            a = float(angle)
            # Dynamic-REZ entries for the operational diagnostic cloud heights must
            # always fit inside the route domain, even if no 0–100 km Canvas cloud
            # remains directly sunlit at the deepest twilight angle.
            depression = max(0.0, -math.radians(a))
            for z in (2.0, 4.0, 5.0, 8.0, 12.0, 18.0):
                gamma = math.acos(r / (r + z)) if z > 0 else 0.0
                required = max(required, r * max(0.0, depression - gamma))

            for td in target_distances:
                shadow = self._shadow_top_km(td, a, r)
                for z in target_altitudes:
                    if z + 1e-9 < shadow:
                        continue  # no direct solar ray; RT is not applicable
                    d = float(td)
                    while d <= search_max + 1e-9:
                        rz = self._ray_altitude_km(td, z, d, a, r)
                        if math.isfinite(rz) and rz >= top:
                            required = max(required, d)
                            break
                        d += step
                    else:
                        # Preserve auditable failure rather than silently truncating.
                        required = max(required, search_max)

        return math.ceil(required / step) * step

    @property
    def dynamic_distance_samples_km(self) -> tuple:
        step = max(1, int(round(float(self.dynamic_route_step_km))))
        return tuple(range(0, int(round(self.dynamic_domain_max_km)) + 1, step))

    # Cloud-cover-to-obstruction proxy. Cloud cover is not optical depth, so this
    # is deliberately labeled an empirical proxy rather than physical COD/COT.
    obstruction_scale: Dict[str, float] = field(default_factory=lambda: {
        "low": 1.00,
        "mid": 0.75,
        "high": 0.35,
    })

    # Direction aggregation; can be calibrated later.
    direction_weights: Dict[float, float] = field(default_factory=lambda: {
        -5.0: 0.20,
        0.0: 0.60,
        5.0: 0.20,
    })

    # Canvas visual contribution. The model reports each component separately;
    # these are only used for a secondary magnitude index.
    canvas_weights: Dict[str, float] = field(default_factory=lambda: {
        "primary": 0.60,
        "extended": 0.40,
    })

    min_data_completeness: float = 0.70
    go_physics_threshold: float = 0.55
    conditional_physics_threshold: float = 0.35

# Fixed cloud-height checkpoints for the geometric illumination matrix. These are
# diagnostic heights, not forecast cloud-type boundaries.
ILLUMINATION_HEIGHTS_KM = (2.0, 4.0, 5.0, 8.0, 12.0, 18.0)

# V8.0.4 resolved vertical lattice for reconstructed cloud columns. The current
# provider remains coarse low/mid/high cloud cover, so this grid increases the
# geometric resolution but does not claim native model-level cloud boundaries.
VOXEL_VERTICAL_STEP_KM = 0.5
VOXEL_MAX_ALTITUDE_KM = 18.0
VOXEL_ALTITUDE_CENTERS_KM = tuple(
    round(VOXEL_VERTICAL_STEP_KM / 2 + i * VOXEL_VERTICAL_STEP_KM, 3)
    for i in range(int(VOXEL_MAX_ALTITUDE_KM / VOXEL_VERTICAL_STEP_KM))
)


# V8.1.0 pressure-profile / optical-blocking diagnostics. These values are
# engineering defaults, not calibrated cloud microphysics. The new engine is
# diagnostic-only in V8.1.0 and does not alter existing Final Score thresholds.
PROFILE_CLOUD_OCCUPANCY_THRESHOLD = 0.05
PROFILE_RH_SUPPORT_THRESHOLD_PCT = 80.0
# Extinction proxy per km for a fully occupied cloud voxel. This converts the
# pressure-level cloud-cover field into a monotonic optical-depth proxy until
# native liquid/ice water content or COT/COD is connected.
CLOUD_EXTINCTION_PROXY_PER_KM = 0.18
RAY_HORIZONTAL_STEP_KM = 20.0
