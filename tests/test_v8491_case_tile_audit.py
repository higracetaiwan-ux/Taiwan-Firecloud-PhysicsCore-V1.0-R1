from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_case_archive_exports_cams_tile_audit():
    app=(ROOT/'app.py').read_text(encoding='utf-8')
    model=(ROOT/'firecloud'/'model.py').read_text(encoding='utf-8')
    assert 'cams_tile_audit.csv' in app
    assert '"cams_tile_audit"' in model
