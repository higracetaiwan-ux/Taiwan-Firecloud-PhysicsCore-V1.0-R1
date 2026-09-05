import pandas as pd

from firecloud.config import ModelConfig, FIRECLOUD_CORE_ANGLES_DEG
from firecloud.contracts import CanvasCandidate, CanvasDomain, GeometryConfidence
from firecloud.v1_runtime import build_canvas_solar_ray_g0


def test_r2_runtime_uses_frozen_nine_core_angles():
    cfg = ModelConfig()
    assert tuple(cfg.solar_angles_deg) == tuple(FIRECLOUD_CORE_ANGLES_DEG)
    assert tuple(cfg.solar_angles_deg) == (0.0, -0.5, -1.0, -1.5, -2.0, -2.5, -3.0, -3.5, -4.0)


def test_canvas_specific_ray_has_no_fixed_rez_boundary():
    c = CanvasCandidate(
        canvas_id="C1", cloud_layer_id="L1", latitude=24.0, longitude=120.0,
        cloud_base_altitude_km=8.0, distance_km=40.0, azimuth_deg=270.0,
        operational_domain=CanvasDomain.PRIMARY_CANVAS_0_40,
        geometry_confidence=GeometryConfidence.HIGH,
    )
    ray = build_canvas_solar_ray_g0(
        c, solar_altitude_deg=-2.0, observer_lat=24.0, observer_lon=120.0,
        earth_radius_km=6371.0, route_end_km=700.0, step_km=20.0,
    )
    assert ray.canvas_id == "C1"
    assert len(ray.segments) > 0
    assert all(s.end_distance_km > s.start_distance_km for s in ray.segments)
    # Dynamic REZ is a set of actual ray segment IDs, not the literal 350-440 km band.
    assert all(seg_id.startswith("C1::seg") for seg_id in ray.dynamic_rez_segment_ids)
