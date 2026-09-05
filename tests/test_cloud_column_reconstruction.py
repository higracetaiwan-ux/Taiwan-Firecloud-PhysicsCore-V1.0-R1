import pandas as pd
from firecloud.model import reconstruct_cloud_columns_3d
from firecloud.config import ModelConfig

def sample():
    rows=[]
    for d in (0,20,40,100,300,350,440):
        rows.append(dict(distance_km=float(d), direction_offset_deg=0.0,
                         cloud_cover_low=20.0, cloud_cover_mid=60.0, cloud_cover_high=80.0))
    return pd.DataFrame(rows)

def test_half_km_lattice_and_unsupported_upper_air():
    v,c = reconstruct_cloud_columns_3d(sample(), -2.0, ModelConfig(direction_offsets_deg=(0.0,), distance_samples_km=(0,20,40,100,300,350,440)))
    assert 0.5 == v['voxel_thickness_km'].dropna().iloc[0]
    assert (v[v.voxel_center_km > 13].voxel_state == 'NO_VERTICAL_FORECAST_SUPPORT').all()

def test_column_has_volume_and_fraction():
    v,c = reconstruct_cloud_columns_3d(sample(), -2.0, ModelConfig(direction_offsets_deg=(0.0,), distance_samples_km=(0,20,40,100,300,350,440)))
    assert c['cloud_volume_proxy_km'].notna().all()
    assert c['illuminated_fraction_of_cloud_volume_proxy'].dropna().between(0,1).all()
    assert (c['boundary_quality'] == 'COARSE_LAYER_ENVELOPE_PROXY').all()
