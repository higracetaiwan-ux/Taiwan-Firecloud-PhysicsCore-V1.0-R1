from pathlib import Path
import firecloud


def test_step3m_release_identity_and_ui_milestone():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.26"
    root = Path(__file__).resolve().parents[1]
    src = root.joinpath("app.py").read_text(encoding="utf-8")
    assert 'CURRENT_MILESTONE = "Ice Optics Phase 2 Step 3M — Yang/Bi Matched-Geometry Extinction Validation"' in src
