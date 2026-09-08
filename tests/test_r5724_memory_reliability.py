from pathlib import Path

from firecloud.runtime_memory import collect_and_trim


def _model_src():
    return (Path(__file__).resolve().parents[1] / "firecloud" / "model.py").read_text(encoding="utf-8")


def _app_src():
    return (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")


def test_runtime_memory_trim_is_best_effort_and_nonfatal():
    out = collect_and_trim()
    assert set(out) == {"gc_collected", "malloc_trim_available", "malloc_trim_result"}
    assert isinstance(out["gc_collected"], int)
    assert isinstance(out["malloc_trim_available"], bool)


def test_r5724_spools_atmospheric_and_spectral_angle_frames():
    src = _model_src()
    for key in (
        "spectral_voxels",
        "spectral_columns",
        "gas_profile",
        "aerosol_spectral_snapshot",
        "cams_native_aerosol_snapshot",
    ):
        assert f'"{key}"' in src
    # These frames must not remain resident in details after the angle ends.
    details_block = src[src.index('details[angle] = {'):src.index('_spool_frames.clear()', src.index('details[angle] = {'))]
    assert '"gas_profile": gas_profile' not in details_block
    assert '"spectral_voxels": spectral_voxels' not in details_block
    assert '"cams_native_aerosol_snapshot": cams_aerosol_snap' not in details_block


def test_r5724_worker_uses_glibc_memory_containment_env():
    src = _app_src()
    assert 'env.setdefault("MALLOC_ARENA_MAX", "2")' in src
    assert 'env.setdefault("MALLOC_TRIM_THRESHOLD_", "131072")' in src


def test_r5724_details_keep_only_compact_ui_snapshot():
    src = _model_src()
    assert '"cloud_cover_low", "cloud_cover_mid", "cloud_cover_high"' in src
    assert '"snapshot": _snapshot_ui' in src
    # The full provider snapshot must not be retained in the 13-angle details.
    assert '"snapshot": snap,' not in src


def test_r5724_route_snapshots_are_spooled_not_held_for_13_angles():
    src = _model_src()
    assert '_route_snapshot_spool = AngleFrameSpool(prefix="firecloud-route-snapshot-")' in src
    assert '_route_snapshot_spool.put("route_snapshot", float(_sa), _route_snapshot)' in src
    assert 'snap = _route_snapshot_spool.pop("route_snapshot", float(angle))' in src
    assert 'route_snapshot_cache = {}' not in src
    assert '_angle_frame_spool.put("viewing_route_snapshot", float(angle), _vsnap)' in src
    assert '_drain_spool_matrix("viewing_route_snapshot")' in src


def test_r5724_provider_caches_are_released_before_final_aggregation():
    src = _model_src()
    marker = src.index('POST_ANGLE_PROVIDER_CACHE_RELEASE')
    aggregate = src.index('彙整民用曙暮光時間軸與矩陣…', marker)
    for text in ('native_cache.clear()', 'cams_native_cache.clear()', 'secondary_optics_cache.clear()'):
        assert src.index(text) < aggregate
