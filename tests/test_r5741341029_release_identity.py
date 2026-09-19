import firecloud
from pathlib import Path


def test_r5741341029_release_identity():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.30.10"
    root = Path(__file__).resolve().parents[1]
    app = root.joinpath("app.py").read_text(encoding="utf-8")
    assert "R5.7.41.3.4.10.29" in app
    assert "Step 3P" in app
    assert "Full-Spectral" in app
