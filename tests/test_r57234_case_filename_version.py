from pathlib import Path


def test_case_download_filename_uses_runtime_hotfix_version():
    text = Path("app.py").read_text(encoding="utf-8")
    assert 'CASE_FILENAME_PREFIX = "Taiwan-Firecloud-PhysicsCore-V1.0-R5."' in text
    assert "__version__.removeprefix('1.0.0-R5.')" in text
    assert "Taiwan-Firecloud-PhysicsCore-V1.0-R5.7.23_{archive_day}" not in text
