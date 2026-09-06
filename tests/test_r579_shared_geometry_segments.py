import math
import numpy as np

from firecloud.shared_geometry.ray import (
    observer_los_height_agl_km,
    ray_altitude_km_at_surface_distance,
    sample_observer_los_segment,
    sample_sun_ray_segment,
    sampled_segment_path_km,
)


def test_shared_sun_segment_matches_scalar_geometry_exactly():
    xs, zz = sample_sun_ray_segment(40.0, 15.0, 40.0, 100.0, -2.0, sample_count=121)
    ref = np.array([ray_altitude_km_at_surface_distance(40.0, 15.0, float(x), -2.0) for x in xs], dtype=float)
    assert np.allclose(zz, ref, rtol=0.0, atol=0.0, equal_nan=True)


def test_shared_view_segment_matches_scalar_geometry_exactly():
    xs, zz = sample_observer_los_segment(40.0, 15.0, 0.0, 40.0, sample_count=25)
    ref = np.array([observer_los_height_agl_km(40.0, 15.0, float(x)) for x in xs], dtype=float)
    assert np.allclose(zz, ref, rtol=0.0, atol=0.0, equal_nan=True)


def test_shared_segment_path_preserves_half_boundary_rule():
    xs = np.array([0.0, 1.0, 2.0])
    zz = np.array([0.0, 0.0, 0.0])
    inside = np.array([False, True, False])
    assert math.isclose(sampled_segment_path_km(xs, zz, inside), 1.0, rel_tol=0.0, abs_tol=1e-12)
