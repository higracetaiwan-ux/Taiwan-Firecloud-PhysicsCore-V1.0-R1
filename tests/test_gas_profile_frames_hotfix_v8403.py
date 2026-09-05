from pathlib import Path


def test_gas_profile_frames_initialized_before_append():
    model = Path(__file__).parents[1] / "firecloud" / "model.py"
    text = model.read_text(encoding="utf-8")
    init_pos = text.find("gas_profile_frames = []")
    append_pos = text.find("gas_profile_frames.append(gpf)")
    assert init_pos >= 0, "gas_profile_frames must be initialized"
    assert append_pos >= 0, "regression target append must exist"
    assert init_pos < append_pos, "gas_profile_frames must be initialized before append"
