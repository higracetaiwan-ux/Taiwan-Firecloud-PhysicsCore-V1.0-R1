from datetime import date

from firecloud.config import ModelConfig
from firecloud.solar import find_time_for_solar_altitude


def test_angle_domains_are_separated():
    cfg = ModelConfig()
    assert cfg.solar_angles_deg == (0.0, -0.5, -1.0, -1.5, -2.0, -2.5, -3.0, -3.5, -4.0)
    assert cfg.firecloud_core_angles_deg == (0.0, -0.5, -1.0, -1.5, -2.0, -2.5, -3.0, -3.5, -4.0)
    assert cfg.late_glow_angles_deg == (-4.0, -4.5, -5.0, -5.5, -6.0)
    assert cfg.nautical_twilight_diagnostic_angles_deg == (-7.0, -8.0, -9.0, -10.0, -11.0, -12.0)


def test_sunset_civil_twilight_order_taiwan():
    day = date(2026, 9, 3)
    angles = (0.0, -0.5, -1.0, -2.0, -3.0, -4.0, -5.0, -6.0)
    times = [find_time_for_solar_altitude(24.25, 120.5, day, "sunset", a) for a in angles]
    assert times == sorted(times)


def test_sunrise_civil_twilight_order_taiwan():
    day = date(2026, 9, 3)
    angles = (-6.0, -5.0, -4.0, -3.0, -2.0, -1.0, -0.5, 0.0)
    times = [find_time_for_solar_altitude(24.25, 120.5, day, "sunrise", a) for a in angles]
    assert times == sorted(times)
