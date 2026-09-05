import math
import pandas as pd

from firecloud.config import ModelConfig
from firecloud.model import (
    build_forecast_voxel_illumination,
    forecast_layer_for_altitude,
)


def synthetic_snapshot():
    rows = []
    for off in (-5.0, 0.0, 5.0):
        for d in range(0, 441, 20):
            rows.append({
                "point_id": f"{off:+.1f}_{d:03d}",
                "distance_km": float(d),
                "direction_offset_deg": float(off),
                "cloud_cover_low": 20.0,
                "cloud_cover_mid": 60.0,
                "cloud_cover_high": 80.0,
            })
    return pd.DataFrame(rows)


def test_vertical_layer_mapping_and_unsupported_height():
    assert forecast_layer_for_altitude(2.0) == "mid"
    assert forecast_layer_for_altitude(5.0) == "mid"
    assert forecast_layer_for_altitude(8.0) == "high"
    assert forecast_layer_for_altitude(12.0) == "high"
    assert forecast_layer_for_altitude(18.0) is None


def test_voxel_matrix_shape_and_missing_vertical_support():
    cfg = ModelConfig()
    snap = synthetic_snapshot()
    df = build_forecast_voxel_illumination(snap, -4.0, cfg)
    expected = len(cfg.direction_offsets_deg) * len(cfg.distance_samples_km) * 6
    assert len(df) == expected
    z18 = df[df["cloud_altitude_km"] == 18.0]
    assert set(z18["voxel_state"]) == {"NO_VERTICAL_FORECAST_SUPPORT"}
    assert z18["cloud_cover_fraction"].isna().all()


def test_shadowed_cloud_has_zero_effective_illumination():
    cfg = ModelConfig()
    df = build_forecast_voxel_illumination(synthetic_snapshot(), -4.0, cfg)
    row = df[(df["direction_offset_deg"] == 0.0) & (df["distance_km"] == 0.0) & (df["cloud_altitude_km"] == 5.0)].iloc[0]
    assert row["voxel_state"] == "CLOUD_EARTH_SHADOWED"
    assert row["effective_illuminated_cloud_proxy"] == 0.0


def test_sunlit_cloud_effective_proxy_never_exceeds_cloud_cover():
    cfg = ModelConfig()
    df = build_forecast_voxel_illumination(synthetic_snapshot(), -1.0, cfg)
    valid = df[df["voxel_state"] == "SUNLIT_FORECAST_CLOUD"]
    assert not valid.empty
    assert (valid["effective_illuminated_cloud_proxy"] <= valid["cloud_cover_fraction"] + 1e-12).all()
    assert ((valid["illuminated_fraction_of_present_cloud_proxy"] >= 0) &
            (valid["illuminated_fraction_of_present_cloud_proxy"] <= 1)).all()
