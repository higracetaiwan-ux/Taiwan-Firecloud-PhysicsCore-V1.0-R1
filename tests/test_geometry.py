import math
from firecloud.geometry import earth_shadow_min_altitude_km, cloud_layer_illuminated_fraction, ray_altitude_km_at_surface_distance


def test_shadow_at_observer_minus4():
    h = earth_shadow_min_altitude_km(0, -4.0)
    assert 15.0 < h < 16.5


def test_shadow_near_terminator_minus4():
    # ~4 degrees of Earth arc ~= 444.8 km
    h = earth_shadow_min_altitude_km(444.8, -4.0)
    assert h < 0.02


def test_shadow_decreases_toward_sun():
    vals = [earth_shadow_min_altitude_km(d, -3.0) for d in [0, 100, 200, 300]]
    assert vals[0] > vals[1] > vals[2] > vals[3]


def test_layer_fraction():
    assert cloud_layer_illuminated_fraction(2, 6, 1) == 1
    assert cloud_layer_illuminated_fraction(2, 6, 7) == 0
    assert math.isclose(cloud_layer_illuminated_fraction(2, 6, 4), 0.5)


def test_ray_altitude_is_target_at_target_distance():
    h = ray_altitude_km_at_surface_distance(40, 8, 40, -2.0)
    assert h is not None and abs(h - 8) < 1e-6
