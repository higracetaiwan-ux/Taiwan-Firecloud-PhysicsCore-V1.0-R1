from types import SimpleNamespace
import pandas as pd

from firecloud.model import _select_v1_canvas_rt_targets
from firecloud.gas_rt import prepare_gas_rt_context


def test_canvas_candidate_filter_reduces_to_one_target_per_canvas_base(monkeypatch):
    monkeypatch.delenv("FIRECLOUD_V1_RT_TARGET_MODE", raising=False)
    vox=pd.DataFrame({
        "direction_offset_deg":[0.0]*6+[5.0]*6,
        "distance_km":[20.0]*3+[40.0]*3+[20.0]*3+[40.0]*3,
        "voxel_center_km":[1.0,5.0,10.0]*4,
        "voxel_bottom_km":[0.5,4.5,9.5]*4,
        "voxel_top_km":[1.5,5.5,10.5]*4,
    })
    layers=(
        SimpleNamespace(layer_id="L1",direction_offset_deg=0.0),
        SimpleNamespace(layer_id="L2",direction_offset_deg=5.0),
    )
    canvases=(
        SimpleNamespace(canvas_id="C1",cloud_layer_id="L1",distance_km=20.0,cloud_base_altitude_km=5.1),
        SimpleNamespace(canvas_id="C2",cloud_layer_id="L2",distance_km=40.0,cloud_base_altitude_km=9.8),
    )
    out=_select_v1_canvas_rt_targets(vox,canvases,SimpleNamespace(layers=layers))
    assert len(out)==2
    assert set(out["v1_rt_target_mode"])=={"CANVAS_CANDIDATES"}
    assert sorted(out["voxel_center_km"].tolist())==[5.0,10.0]


def test_all_voxels_mode_preserves_legacy_diagnostic_grid(monkeypatch):
    monkeypatch.setenv("FIRECLOUD_V1_RT_TARGET_MODE","ALL_VOXELS")
    vox=pd.DataFrame({"direction_offset_deg":[0.0,0.0],"distance_km":[0.0,20.0],"voxel_center_km":[1.0,2.0]})
    out=_select_v1_canvas_rt_targets(vox,(),None)
    assert len(out)==2
    assert set(out["v1_rt_target_mode"])=={"ALL_VOXELS"}


def test_prepare_gas_rt_context_fail_closed_without_profile_columns():
    ctx=prepare_gas_rt_context(pd.DataFrame({"distance_km":[0.0]}))
    assert ctx.valid is False
    assert ctx.failure_cause in {"HITRAN_LOCAL_BAND_TABLE_MISSING","ATMOSPHERIC_GAS_PROFILE_INCOMPLETE","HITRAN_BAND_TABLE_INCOMPLETE"}
