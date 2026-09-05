from firecloud.config import ModelConfig
from firecloud.model import build_route_points, build_geometry_diagnostics


def test_dynamic_domain_expands_beyond_legacy_440():
    cfg=ModelConfig()
    assert cfg.dynamic_domain_max_km > 667
    assert cfg.dynamic_domain_max_km == 1180
    assert max(cfg.dynamic_distance_samples_km) == 1180
    assert max(cfg.distance_samples_km) == 440


def test_route_points_use_dynamic_domain():
    cfg=ModelConfig()
    pts=build_route_points(25.0,121.0,270.0,cfg)
    assert max(p['distance_km'] for p in pts) == 1180


def test_dynamic_rez_diagnostic_is_not_capped_at_440():
    cfg=ModelConfig()
    _, rez=build_geometry_diagnostics(cfg)
    r=rez[(rez.solar_altitude_deg==-6.0) & (rez.cloud_altitude_km==2.0)].iloc[0]
    assert r.dynamic_rez_entry_distance_km > 440
    assert bool(r.within_dynamic_domain)
    assert not bool(r.legacy_within_440km_domain)
