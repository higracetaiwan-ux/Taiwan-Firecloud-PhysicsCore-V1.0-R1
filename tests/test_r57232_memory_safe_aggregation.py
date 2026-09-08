from pathlib import Path


def _src():
    return (Path(__file__).resolve().parents[1] / 'firecloud' / 'model.py').read_text(encoding='utf-8')


def test_memory_safe_aggregation_drains_details_instead_of_copying_all_angles():
    src = _src()
    assert 'def _drain_detail_matrix' in src
    assert 'd.pop(key, pd.DataFrame())' in src
    assert 'pd.concat(frames, ignore_index=True, copy=False)' in src
    # The old peak-RAM pattern copied heavyweight per-angle frames while the
    # originals remained referenced in details.
    assert 'details[angle]["forecast_voxels"].copy()' not in src
    assert 'details[angle]["native_optical_voxels"].copy()' not in src


def test_completeness_audit_is_compacted_before_heavy_frames_are_spooled():
    src = _src()
    # R5.7.24 computes the 9-row readiness summary while the current angle's
    # gas/aerosol/spectral frames are still live, then spools those frames.
    audit = src.index('_angle_completeness = _build_physics_data_completeness(')
    spool = src.index('"gas_profile": gas_profile,', audit)
    assert audit < spool
    assert 'pd.concat(physics_completeness_frames, ignore_index=True, copy=False)' in src


def test_aggregation_exposes_multiple_runtime_checkpoints():
    src = _src()
    assert '彙整民用曙暮光時間軸與矩陣｜' in src
    assert 'AGGREGATION_' in src
    assert 'collect_and_trim()' in src
