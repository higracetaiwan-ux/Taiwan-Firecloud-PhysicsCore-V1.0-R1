import time
import pandas as pd

from firecloud.config import ModelConfig, VOXEL_ALTITUDE_CENTERS_KM
from firecloud.model import apply_3d_optical_blocking


def test_full_route_one_angle_optical_blocking_completes_quickly():
    rows = []
    for off in (-5.0, 0.0, 5.0):
        for d in range(0, 441, 20):
            for z in VOXEL_ALTITUDE_CENTERS_KM:
                rows.append({
                    "direction_offset_deg": off,
                    "distance_km": float(d),
                    "voxel_center_km": float(z),
                    "voxel_bottom_km": float(z - 0.25),
                    "voxel_top_km": float(z + 0.25),
                    "cloud_occupancy": 0.5,
                    "solar_altitude_deg": -2.0,
                })
    df = pd.DataFrame(rows)
    t0 = time.perf_counter()
    out = apply_3d_optical_blocking(df, -2.0, ModelConfig())
    elapsed = time.perf_counter() - t0
    assert len(out) == len(df)
    # This protects against accidentally restoring dataframe filtering inside
    # the innermost ray loop, which previously caused multi-tens-of-seconds runs.
    assert elapsed < 3.0
