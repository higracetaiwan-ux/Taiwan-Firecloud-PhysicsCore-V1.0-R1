import firecloud
from pathlib import Path

def test_r57413410281_release_identity():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.30.13"
    app = Path(__file__).resolve().parents[1].joinpath("app.py").read_text(encoding="utf-8")
    assert "R5.7.41.3.4.10.28.1" in app
    assert "Stable Contract Serialization Hotfix" in app
