import time
import numpy as np
import pandas as pd

from firecloud.config import ModelConfig
from firecloud.model import (
    _build_coarse_route_index,
    _upstream_path_transmission_indexed,
    upstream_path_transmission_proxy,
    reconstruct_cloud_columns_3d,
)


def _route():
    rows=[]
    for off in (-5.0,0.0,5.0):
        for d in np.arange(0.0, 441.0, 20.0):
            rows.append({
                'direction_offset_deg':off,'distance_km':float(d),
                'cloud_cover_low':25.0,'cloud_cover_mid':55.0,'cloud_cover_high':70.0,
            })
    return pd.DataFrame(rows)


def test_indexed_upstream_matches_legacy():
    df=_route(); cfg=ModelConfig(); idx=_build_coarse_route_index(df)
    for off in (-5.0,0.0,5.0):
        for d in (0.0,40.0,100.0,300.0,440.0):
            for z in (1.0,4.0,8.0,12.0):
                old=upstream_path_transmission_proxy(df,off,d,z,-2.0,cfg)
                new=_upstream_path_transmission_indexed(idx,off,d,z,-2.0,cfg)
                assert np.allclose(old,new,equal_nan=True,rtol=0,atol=1e-12)


def test_reconstructed_cloud_builder_finishes_quickly():
    df=_route(); cfg=ModelConfig()
    t0=time.perf_counter()
    vox,cols=reconstruct_cloud_columns_3d(df,-1.0,cfg)
    elapsed=time.perf_counter()-t0
    assert not vox.empty and not cols.empty
    assert elapsed < 3.0
