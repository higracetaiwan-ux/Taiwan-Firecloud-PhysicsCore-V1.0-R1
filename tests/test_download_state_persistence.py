from pathlib import Path


def test_app_persists_analysis_across_reruns_and_ignores_download_rerun():
    app = (Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8")
    assert 'st.session_state.analysis_result = result' in app
    assert 'if run or st.session_state.analysis_result is not None:' in app
    assert 'on_click="ignore"' in app
    assert 'key="download_case_zip"' in app
