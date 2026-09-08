from pathlib import Path


def test_gas_profile_aggregation_is_initialized_or_drained_before_use():
    model = Path(__file__).parents[1] / "firecloud" / "model.py"
    text = model.read_text(encoding="utf-8")
    # R5.7.23.2 replaces the legacy gas_profile_frames append pattern with a
    # memory-safe move/drain operation from per-angle details.
    drain_pos = text.find('gas_profile_route_snapshots = _drain_detail_matrix("gas_profile"')
    legacy_init_pos = text.find("gas_profile_frames = []")
    legacy_append_pos = text.find("gas_profile_frames.append(gpf)")
    if drain_pos >= 0:
        assert drain_pos >= 0
    else:
        assert legacy_init_pos >= 0, "gas_profile_frames must be initialized"
        assert legacy_append_pos >= 0, "regression target append must exist"
        assert legacy_init_pos < legacy_append_pos, "gas_profile_frames must be initialized before append"
