from pathlib import Path

def test_model_imports_time_for_cams_watchdog():
    src = (Path(__file__).parents[1] / "firecloud" / "model.py").read_text(encoding="utf-8")
    assert "time.monotonic()" in src
    assert "import time" in src

