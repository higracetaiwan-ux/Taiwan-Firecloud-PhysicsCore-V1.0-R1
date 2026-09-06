from pathlib import Path


def test_v8441_offline_only_ui_contract():
    app = Path(__file__).resolve().parents[1].joinpath("app.py").read_text(encoding="utf-8")
    assert "進階／Legacy：HAPI 遠端自動下載（預設停用）" in app
    assert "我了解此功能可能 404，仍要啟用 Legacy remote bootstrap" in app
    assert 'disabled=not _hybrid_sources_ready' in app
    assert "這裡的 CSV / manifest 是 Taiwan Firecloud 建立後的衍生 Runtime 成品" in app
    assert "Taiwan-Firecloud-PhysicsCore-V1.0-R5." in app
