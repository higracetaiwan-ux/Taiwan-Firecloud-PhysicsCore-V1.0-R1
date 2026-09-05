import pandas as pd

from firecloud.config import ModelConfig
from firecloud.model import build_pressure_profile_cloud_volume, apply_3d_optical_blocking


def _row(distance, cloud=80.0):
    r = {
        "point_id": f"0_{distance}",
        "direction_offset_deg": 0.0,
        "distance_km": float(distance),
        "model_surface_elevation_m": 0.0,
    }
    # Enough levels to bracket 0.5..12 km. Heights are representative test geometry,
    # not meant to reproduce a standard atmosphere exactly.
    levels = {
        1000: 100.0, 925: 800.0, 850: 1500.0, 700: 3000.0,
        600: 4200.0, 500: 5600.0, 400: 7200.0, 300: 9200.0,
        250: 10400.0, 200: 11800.0, 150: 13500.0, 100: 15800.0,
    }
    for p, gh in levels.items():
        r[f"geopotential_height_{p}hPa"] = gh
        r[f"cloud_cover_{p}hPa"] = cloud
        r[f"relative_humidity_{p}hPa"] = 90.0
    return r


def test_pressure_profile_builds_vertical_voxels_and_columns():
    snap = pd.DataFrame([_row(0), _row(20), _row(40)])
    vox, cols = build_pressure_profile_cloud_volume(snap, -2.0, ModelConfig())
    assert not vox.empty
    assert not cols.empty
    assert vox["cloud_occupancy"].notna().any()
    assert (cols["vertical_profile_completeness"] > 0).all()
    assert cols["profile_cloud_base_km"].notna().any()


def test_vertical_cloud_column_reduces_upstream_transmission():
    snap = pd.DataFrame([_row(0, 70), _row(20, 90), _row(40, 90), _row(60, 90)])
    vox, _ = build_pressure_profile_cloud_volume(snap, -1.0, ModelConfig())
    opt = apply_3d_optical_blocking(vox, -1.0, ModelConfig())
    near = opt[(opt["distance_km"] == 0.0) & (opt["voxel_center_km"].between(5.0, 8.0))]
    far = opt[(opt["distance_km"] == 60.0) & (opt["voxel_center_km"].between(5.0, 8.0))]
    assert not near.empty and not far.empty
    assert near["remaining_transmission_proxy"].dropna().mean() < 1.0
    assert far["remaining_transmission_proxy"].isna().all()
    assert (far["optical_state"] == "ROUTE_ENDPOINT_NO_UPSTREAM_CHECK").all()
    assert (~far["upstream_path_checked"]).all()
    assert near["slant_cloud_optical_depth_proxy"].dropna().mean() > 0.0


def test_shadowed_cloud_can_remain_blocker_capable_state():
    snap = pd.DataFrame([_row(0, 90), _row(20, 90)])
    vox, _ = build_pressure_profile_cloud_volume(snap, -6.0, ModelConfig())
    opt = apply_3d_optical_blocking(vox, -6.0, ModelConfig())
    assert (opt["optical_state"] == "SHADOWED_CLOUD_BLOCKER_CAPABLE").any()
