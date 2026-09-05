from firecloud.config import ModelConfig, ILLUMINATION_HEIGHTS_KM
from firecloud.geometry import dynamic_rez_entry_distance_km, geometric_illumination_state
from firecloud.model import build_geometry_diagnostics


def test_dynamic_rez_moves_farther_as_sun_sinks():
    d2 = dynamic_rez_entry_distance_km(-2.0, 5.0)
    d4 = dynamic_rez_entry_distance_km(-4.0, 5.0)
    d6 = dynamic_rez_entry_distance_km(-6.0, 5.0)
    assert d2 < d4 < d6


def test_higher_cloud_clears_shadow_closer_to_observer():
    low = dynamic_rez_entry_distance_km(-4.0, 2.0)
    high = dynamic_rez_entry_distance_km(-4.0, 12.0)
    assert high < low


def test_geometric_state_matches_shadow_clearance():
    sunlit, shadow_h, clearance = geometric_illumination_state(0, 18, -4.0)
    assert sunlit is True
    assert clearance > 0
    sunlit2, _, clearance2 = geometric_illumination_state(0, 5, -4.0)
    assert sunlit2 is False
    assert clearance2 < 0


def test_full_matrix_shape_and_angles():
    cfg = ModelConfig()
    matrix, rez = build_geometry_diagnostics(cfg)
    assert len(matrix) == len(cfg.solar_angles_deg) * len(cfg.dynamic_distance_samples_km) * len(ILLUMINATION_HEIGHTS_KM)
    assert len(rez) == len(cfg.solar_angles_deg) * len(ILLUMINATION_HEIGHTS_KM)
    assert set(matrix["geometric_state"].unique()) <= {"ILLUMINATED", "EARTH_SHADOWED"}
