from __future__ import annotations

from datetime import datetime, timezone
import pandas as pd

from firecloud.providers import cams_native


def _points():
    return [{"point_id":"p0","distance_km":0.0,"direction_offset_deg":0.0,"lat":24.1813,"lon":121.2818}]

def _ok(role: str, rid: str):
    df=pd.DataFrame({"point_id":["p0"],"distance_km":[0.0],"direction_offset_deg":[0.0],"lat":[24.1813],"lon":[121.2818],"aod550":[0.1]})
    return {"role":role,"status":"OK","df":df,"meta":{"request_audit":{"ads_request_id":rid,"ads_remote_status":"successful","ads_request_reattached":True,"ads_reattach_only":True}},"inventory":[],"error":"","elapsed_seconds":0.1}

def _timeout(role: str, rid: str, reason: str, remote_status: str):
    return {"role":role,"status":"TIMEOUT_DEFERRED","df":pd.DataFrame(),"meta":{"request_audit":{"ads_request_id":rid,"ads_remote_status":remote_status,"ads_request_recovery_eligible":True,"ads_stateful_timeout_reason":reason}},"inventory":[],"error":reason,"elapsed_seconds":75.0}

def test_adaptive_scheduler_queue_timeout_same_run_reattaches_same_request(monkeypatch):
    calls=[]
    def fake(role, points, valid_time, cache_dir=None, deadline_seconds=90.0, heartbeat_callback=None, reattach_only=False):
        calls.append((role,bool(reattach_only)))
        return _ok(role,"rid-queue") if reattach_only else _timeout(role,"rid-queue","CAMS_ADS_QUEUE_GRACE_EXCEEDED","accepted")
    monkeypatch.setattr(cams_native,"_run_cams_role_isolated",fake)
    monkeypatch.setattr(cams_native.time,"sleep",lambda *_:None)
    monkeypatch.setenv("FIRECLOUD_CAMS_DEFERRED_REATTACH_COUNT","1")
    df,audits,_,stats=cams_native._fetch_cams_role_adaptive(_points(),datetime(2026,9,20,tzinfo=timezone.utc),"SPECTRAL_COLUMN_AOD",deadline_seconds=1.0,max_depth=0)
    assert calls == [("SPECTRAL_COLUMN_AOD",False),("SPECTRAL_COLUMN_AOD",True)]
    assert not df.empty
    assert stats["requests"] == 1
    assert stats["successful_requests"] == 1
    a=audits[0]
    assert a["final_status"] == "OK"
    assert a["deferred_reattach_attempted"] is True
    assert a["deferred_initial_request_id"] == "rid-queue"
    assert a["deferred_initial_remote_status"] == "accepted"
    assert a["deferred_initial_timeout_reason"] == "CAMS_ADS_QUEUE_GRACE_EXCEEDED"
    assert a["deferred_recovery_contract"] == "R5.7.41.3.4.10.30.21_BOUNDED_SAME_REQUEST_ID_REATTACH_OBSERVATION_WINDOW_V1"

def test_adaptive_scheduler_running_timeout_same_run_reattaches(monkeypatch):
    calls=[]
    def fake(role, points, valid_time, cache_dir=None, deadline_seconds=90.0, heartbeat_callback=None, reattach_only=False):
        calls.append(bool(reattach_only))
        return _ok(role,"rid-running") if reattach_only else _timeout(role,"rid-running","CAMS_ADS_RUNNING_GRACE_EXCEEDED","running")
    monkeypatch.setattr(cams_native,"_run_cams_role_isolated",fake)
    monkeypatch.setattr(cams_native.time,"sleep",lambda *_:None)
    monkeypatch.setenv("FIRECLOUD_CAMS_DEFERRED_REATTACH_COUNT","1")
    _,audits,_,_=cams_native._fetch_cams_role_adaptive(_points(),datetime(2026,9,20,tzinfo=timezone.utc),"AEROSOL_SCATTERING_COLUMN_PROPERTIES",deadline_seconds=1.0,max_depth=0)
    assert calls == [False,True]
    assert audits[0]["final_status"] == "OK"
    assert audits[0]["deferred_initial_timeout_reason"] == "CAMS_ADS_RUNNING_GRACE_EXCEEDED"

def test_adaptive_scheduler_bounded_reattach_still_timeout_remains_missing(monkeypatch):
    calls=[]
    def fake(role, points, valid_time, cache_dir=None, deadline_seconds=90.0, heartbeat_callback=None, reattach_only=False):
        calls.append(bool(reattach_only))
        return _timeout(role,"rid-still","CAMS_ADS_QUEUE_GRACE_EXCEEDED","accepted")
    monkeypatch.setattr(cams_native,"_run_cams_role_isolated",fake)
    monkeypatch.setattr(cams_native.time,"sleep",lambda *_:None)
    monkeypatch.setenv("FIRECLOUD_CAMS_DEFERRED_REATTACH_COUNT","1")
    df,audits,_,stats=cams_native._fetch_cams_role_adaptive(_points(),datetime(2026,9,20,tzinfo=timezone.utc),"SPECTRAL_COLUMN_AOD",deadline_seconds=1.0,max_depth=3)
    assert calls == [False,True]
    assert df.empty
    assert audits[0]["final_status"] == "TIMEOUT_DEFERRED"
    assert audits[0]["deferred_reattach_attempted"] is True
    assert stats["failed_requests"] == 1
    assert stats["adaptive_splits"] == 0
