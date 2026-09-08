from pathlib import Path

import pandas as pd

from firecloud.angle_frame_spool import AngleFrameSpool


def test_angle_frame_spool_roundtrip_and_delete():
    spool = AngleFrameSpool(prefix="firecloud-test-spool-")
    root = spool.root
    src = pd.DataFrame({"solar_altitude_deg": [-5.0, -5.0], "x": [1.25, 2.5], "state": ["A", "B"]})
    size = spool.put("reconstructed_voxels", -5.0, src)
    assert size > 0
    assert spool.has("reconstructed_voxels", -5.0)
    assert spool.pending_frames == 1
    got = spool.pop("reconstructed_voxels", -5.0)
    pd.testing.assert_frame_equal(got, src)
    assert not spool.has("reconstructed_voxels", -5.0)
    assert spool.pending_frames == 0
    spool.cleanup()
    assert not root.exists()


def test_angle_frame_spool_separates_angles_and_families():
    spool = AngleFrameSpool(prefix="firecloud-test-spool-")
    try:
        a = pd.DataFrame({"v": [1, 2]})
        b = pd.DataFrame({"v": [3]})
        c = pd.DataFrame({"v": [4, 5, 6]})
        spool.put("native_voxels", -4.5, a)
        spool.put("native_voxels", -5.0, b)
        spool.put("optical_voxels", -5.0, c)
        assert spool.pending_frames == 3
        pd.testing.assert_frame_equal(spool.pop("native_voxels", -5.0), b)
        pd.testing.assert_frame_equal(spool.pop("native_voxels", -4.5), a)
        pd.testing.assert_frame_equal(spool.pop("optical_voxels", -5.0), c)
    finally:
        spool.cleanup()


def test_r57234_model_spools_heavy_frames_before_next_angle():
    source = Path("firecloud/model.py").read_text(encoding="utf-8")
    assert "ANGLE_HEAVY_EVIDENCE_SPOOL" in source
    assert "_angle_frame_spool.put" in source
    assert "del forecast_voxels, reconstructed_voxels, reconstructed_columns" in source
    assert "_angle_frame_spool.has(key, float(angle))" in source
    assert "_angle_frame_spool.pop(key, float(angle))" in source
    assert "_angle_frame_spool.cleanup()" in source
