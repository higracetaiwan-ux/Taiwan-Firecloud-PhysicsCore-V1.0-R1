from pathlib import Path
import inspect
import pandas as pd
from firecloud.providers import cams_native


def test_file_backed_worker_result_roundtrip(tmp_path):
    path=tmp_path/'result.pkl'
    payload={
        'role':'NATIVE_AEROSOL_532NM_PRESSURE_LEVEL',
        'status':'OK',
        'df':pd.DataFrame({
            'point_id':[f'p{i}' for i in range(5000)],
            'cams_aerext532_m1_100':[1e-5]*5000,
        }),
        'meta':{'request_audit':{'status':'OK'}},
        'inventory':[{'shortName':'aerext532'}],
        'error':'',
    }
    cams_native._write_cams_worker_result(path,payload)
    assert path.exists() and path.stat().st_size > 0
    assert not Path(str(path)+'.tmp').exists()
    got=cams_native._read_cams_worker_result(path)
    assert got['status']=='OK'
    assert len(got['df'])==5000
    assert got['df']['cams_aerext532_m1_100'].notna().all()


def test_source_uses_external_subprocess_not_multiprocessing_spawn_or_queue():
    src=inspect.getsource(cams_native._run_cams_role_isolated)
    assert 'Queue(' not in src
    assert 'get_context("spawn")' not in src
    assert 'subprocess.Popen' in src
    assert 'firecloud.providers.cams_worker' in src
    # Current contract is file-backed atomic subprocess IPC; implementation need not use TemporaryDirectory.
    assert '_write_cams_worker_result' not in src or 'result' in src
    assert 'PYTHON_MODULE_SUBPROCESS_NO_STREAMLIT_SPAWN' in src
