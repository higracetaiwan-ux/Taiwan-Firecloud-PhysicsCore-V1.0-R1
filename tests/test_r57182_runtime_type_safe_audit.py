from pathlib import Path

from firecloud.providers import cams_native


def test_cams_request_metadata_safe_join_accepts_float_sequence_item():
    # Regression for Streamlit worker crash:
    # TypeError: sequence item 1: expected str instance, float found
    value = ["1000", 925.0, 850, None]
    out = cams_native._safe_join_request_values(value)
    assert out == "1000|925.0|850|None"


def test_cams_request_metadata_safe_join_handles_scalar_and_none():
    assert cams_native._safe_join_request_values(550.0) == "550.0"
    assert cams_native._safe_join_request_values(None) == ""


def test_cams_audit_paths_use_type_safe_serializer():
    src = (Path(__file__).resolve().parents[1] / "firecloud" / "providers" / "cams_native.py").read_text(encoding="utf-8")
    assert '_safe_join_request_values(request.get("variable"))' in src
    assert '_safe_join_request_values(request.get("pressure_level"))' in src
    assert '"|".join(request.get("variable",[]))' not in src


def test_streamlit_monitor_preserves_inner_worker_traceback():
    app = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
    assert 'Worker traceback:' in app
    assert 'pstate.get("traceback")' in app
