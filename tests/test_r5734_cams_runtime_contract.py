from pathlib import Path


def test_r5734_runtime_contract_source_and_dependency():
    root = Path(__file__).resolve().parents[1]
    src = (root/"firecloud/providers/cams_native.py").read_text()
    stateful = (root/"firecloud/providers/cams_ads_stateful.py").read_text()
    req = (root/"requirements.txt").read_text()
    assert 'FIRECLOUD_CAMS_ADS_QUEUE_GRACE_SECONDS' in src
    assert 'FIRECLOUD_CAMS_ADS_RUNNING_GRACE_SECONDS' in src
    assert 'FIRECLOUD_CAMS_ADS_TOTAL_DEADLINE_SECONDS' in src
    assert 'get_remote' in stateful
    assert 'request_fingerprint' in stateful
    assert 'ecmwf-datastores-client>=0.5.3' in req
    assert 'FIRECLOUD_CAMS_DEADLINE_SECONDS","210"' in src
