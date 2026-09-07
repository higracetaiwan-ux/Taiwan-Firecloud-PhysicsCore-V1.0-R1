from datetime import date

import pandas as pd
import pytest

from firecloud.config import (
    FIRECLOUD_CORE_ANGLES_DEG,
    REFERENCE_ROUTE_CONTRACT,
    REFERENCE_ROUTE_SOLAR_ALTITUDE_DEG,
    ModelConfig,
)
from firecloud.model import build_route_points, resolve_reference_route_geometry
from firecloud.solar import find_time_for_solar_altitude, solar_azimuth_deg


JAPAN_LAT = 33.376
JAPAN_LON = 130.31
JAPAN_DAY = date(2026, 9, 8)
TZ = "Asia/Tokyo"
NINE_ANGLES = (0.0, -0.5, -1.0, -1.5, -2.0, -2.5, -3.0, -3.5, -4.0)
THIRTEEN_ANGLES = FIRECLOUD_CORE_ANGLES_DEG


def _candidates(angles):
    out = []
    for angle in angles:
        t = find_time_for_solar_altitude(JAPAN_LAT, JAPAN_LON, JAPAN_DAY, "sunset", angle, TZ)
        out.append((angle, t, solar_azimuth_deg(JAPAN_LAT, JAPAN_LON, t)))
    return out


def test_reference_route_angle_is_frozen_at_minus_two_deg():
    assert REFERENCE_ROUTE_SOLAR_ALTITUDE_DEG == pytest.approx(-2.0)
    assert "FIXED_REFERENCE_ROUTE_MINUS2" in REFERENCE_ROUTE_CONTRACT


def test_dynamic_provider_sampling_domain_is_invariant_to_runtime_angle_subset():
    a = ModelConfig(solar_angles_deg=NINE_ANGLES)
    b = ModelConfig(solar_angles_deg=THIRTEEN_ANGLES)
    assert a.dynamic_domain_max_km == pytest.approx(b.dynamic_domain_max_km)
    assert a.dynamic_distance_samples_km == b.dynamic_distance_samples_km
    assert a.dynamic_domain_max_km == pytest.approx(1180.0)


def test_reference_route_geometry_is_identical_for_nine_and_thirteen_angle_runtime():
    c9 = ModelConfig(solar_angles_deg=NINE_ANGLES)
    c13 = ModelConfig(solar_angles_deg=THIRTEEN_ANGLES)
    t9, az9, source9 = resolve_reference_route_geometry(
        JAPAN_LAT, JAPAN_LON, JAPAN_DAY, "sunset", TZ, c9, candidates=_candidates(NINE_ANGLES)
    )
    t13, az13, source13 = resolve_reference_route_geometry(
        JAPAN_LAT, JAPAN_LON, JAPAN_DAY, "sunset", TZ, c13, candidates=_candidates(THIRTEEN_ANGLES)
    )
    assert t9 == t13
    assert az9 == pytest.approx(az13, abs=1e-10)
    assert source9 == source13 == "RUNTIME_CANDIDATE_MATCH"
    assert az9 == pytest.approx(278.565909, abs=5e-4)


def test_route_points_are_identical_when_only_runtime_angle_set_changes():
    c9 = ModelConfig(solar_angles_deg=NINE_ANGLES)
    c13 = ModelConfig(solar_angles_deg=THIRTEEN_ANGLES)
    _, az9, _ = resolve_reference_route_geometry(
        JAPAN_LAT, JAPAN_LON, JAPAN_DAY, "sunset", TZ, c9, candidates=_candidates(NINE_ANGLES)
    )
    _, az13, _ = resolve_reference_route_geometry(
        JAPAN_LAT, JAPAN_LON, JAPAN_DAY, "sunset", TZ, c13, candidates=_candidates(THIRTEEN_ANGLES)
    )
    p9 = pd.DataFrame(build_route_points(JAPAN_LAT, JAPAN_LON, az9, c9))
    p13 = pd.DataFrame(build_route_points(JAPAN_LAT, JAPAN_LON, az13, c13))
    cols = ["point_id", "distance_km", "direction_offset_deg", "bearing_deg", "lat", "lon"]
    pd.testing.assert_frame_equal(p9[cols], p13[cols], check_exact=False, atol=1e-12, rtol=0)
    # Regression against the pre-extension R5.7.21 route bearing.
    row = p13[(p13.direction_offset_deg == -5.0) & (p13.distance_km == 0.0)].iloc[0]
    assert row.bearing_deg == pytest.approx(273.565909, abs=5e-4)


def test_reference_crossing_is_solved_independently_when_minus_two_not_in_runtime_set():
    cfg = ModelConfig(solar_angles_deg=(0.0, -1.0, -3.0, -6.0))
    candidates = _candidates(cfg.solar_angles_deg)
    t, az, source = resolve_reference_route_geometry(
        JAPAN_LAT, JAPAN_LON, JAPAN_DAY, "sunset", TZ, cfg, candidates=candidates
    )
    expected_t = find_time_for_solar_altitude(JAPAN_LAT, JAPAN_LON, JAPAN_DAY, "sunset", -2.0, TZ)
    expected_az = solar_azimuth_deg(JAPAN_LAT, JAPAN_LON, expected_t)
    assert source == "INDEPENDENT_REFERENCE_CROSSING"
    assert t == expected_t
    assert az == pytest.approx(expected_az, abs=1e-10)
