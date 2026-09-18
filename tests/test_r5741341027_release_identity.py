import firecloud
from pathlib import Path


def test_r5741341027_release_identity():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.30.9"
    root = Path(__file__).resolve().parents[1]
    app = root.joinpath("app.py").read_text(encoding="utf-8")
    assert "R5.7.41.3.4.10.27" in app
    assert "Step 3N" in app
