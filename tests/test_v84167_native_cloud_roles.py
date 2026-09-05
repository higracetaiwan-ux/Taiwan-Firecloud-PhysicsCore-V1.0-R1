import pandas as pd
import numpy as np

from firecloud.config import ModelConfig
from firecloud.model import apply_native_microphysical_optical_blocking


def _native_rows():
    rows = []
    for distance in (0.0, 20.0):
        for height in (5.0, 8.0):
            rows.append({
                "direction_offset_deg": 0.0,
                "distance_km": distance,
                "voxel_center_km": height,
                "voxel_bottom_km": height - 0.25,
                "voxel_top_km": height + 0.25,
                "total_cloud_condensate_kgkg": 2.0e-6,
                "cloud_fraction": 0.8,
                "cloud_fraction_used": 0.8,
                "total_extinction_m1": 2.0e-5,
            })
    return pd.DataFrame(rows)


def test_native_route_endpoint_is_not_clear_transmission():
    out = apply_native_microphysical_optical_blocking(_native_rows(), 0.0, ModelConfig(), optical_properties_ready=True)
    endpoint = out[out["distance_km"] == 20.0]
    assert not endpoint.empty
    assert endpoint["upstream_path_checked"].eq(False).all()
    assert endpoint["upstream_path_state"].eq("ROUTE_ENDPOINT_NO_UPSTREAM_CHECK").all()
    assert endpoint["native_optical_state"].eq("ROUTE_ENDPOINT_NO_UPSTREAM_CHECK").all()
    assert endpoint["remaining_native_cloud_transmission_estimate"].isna().all()
    assert endpoint["native_target_can_be_effective_canvas"].eq(False).all()


def test_native_sunlit_target_is_explicit_canvas_role_when_path_is_known():
    out = apply_native_microphysical_optical_blocking(_native_rows(), 0.0, ModelConfig(), optical_properties_ready=True)
    target = out[out["distance_km"] == 0.0]
    assert target["upstream_path_checked"].all()
    assert target["native_target_cloud_on_sunlit_path"].all()
    assert target["native_target_role"].eq("ILLUMINATED_NATIVE_CANVAS_CANDIDATE").all()
    assert target["native_target_can_be_effective_canvas"].all()
    assert np.isfinite(target["remaining_native_cloud_transmission_estimate"]).all()
