from pathlib import Path


def test_app_has_persistent_analysis_journal_and_restore_path():
    app=Path('app.py').read_text(encoding='utf-8')
    assert 'analysis_job_state.json' in app
    assert 'last_analysis_result.pkl' in app
    assert '繼續上次未完成分析' in app
    assert '_save_analysis_job_state(_job_state)' in app
    assert '_save_completed_analysis_result(result)' in app
    assert 'analysis_job_state.json' in app
    assert '_reconcile_persisted_analysis_job' in app


def test_cams_worker_module_does_not_import_streamlit_app():
    worker=Path('firecloud/providers/cams_worker.py').read_text(encoding='utf-8')
    assert 'import streamlit' not in worker.lower()
    assert 'import app' not in worker.lower()
    assert 'from .cams_native import _cams_role_worker' in worker
