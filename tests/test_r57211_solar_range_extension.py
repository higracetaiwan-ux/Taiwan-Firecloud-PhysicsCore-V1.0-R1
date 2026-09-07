from firecloud.config import ModelConfig
from firecloud.contracts import CORE_FIRECLOUD_ANGLES_DEG

EXPECTED = (0.0, -0.5, -1.0, -1.5, -2.0, -2.5, -3.0, -3.5, -4.0, -4.5, -5.0, -5.5, -6.0)

def test_full_core_grid_reaches_minus6_at_half_degree_resolution():
    cfg = ModelConfig()
    assert tuple(cfg.solar_angles_deg) == EXPECTED
    assert tuple(cfg.firecloud_core_angles_deg) == EXPECTED
    assert CORE_FIRECLOUD_ANGLES_DEG == EXPECTED
    assert len(EXPECTED) == 13
    assert EXPECTED[-1] == -6.0

def test_late_glow_classification_can_overlap_core_without_extending_below_minus6():
    cfg = ModelConfig()
    assert set(cfg.late_glow_angles_deg).issubset(set(cfg.firecloud_core_angles_deg))
    assert min(cfg.firecloud_core_angles_deg) == -6.0
    assert min(cfg.nautical_twilight_diagnostic_angles_deg) < -6.0
