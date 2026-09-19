from __future__ import annotations

from datetime import datetime, timezone
import pandas as pd

from firecloud import __version__
from firecloud.fu96_rrtmg_band25_historical_scope import (
    band25_historical_scope_matrix,
    pinned_runtime_scope_sources,
)
from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    STEP3Q_VERSION,
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)
from firecloud.providers import cams_native


def _points():
    return [{"point_id":"p0","distance_km":0.0,"direction_offset_deg":0.0,"lat":24.1813,"lon":121.2818}]


def _timeout(role: str, rid: str):
    return {
        "role": role,
        "status": "TIMEOUT_DEFERRED",
        "df": pd.DataFrame(),
        "meta": {"request_audit": {
            "ads_request_id": rid,
            "ads_remote_status": "running",
            "ads_request_recovery_eligible": True,
            "ads_stateful_timeout_reason": "CAMS_ADS_RUNNING_GRACE_EXCEEDED",
        }},
        "inventory": [],
        "error": "CAMS_ADS_RUNNING_GRACE_EXCEEDED",
        "elapsed_seconds": 210.0,
    }


def _ok(role: str, rid: str):
    return {
        "role": role,
        "status": "OK",
        "df": pd.DataFrame({"point_id":["p0"],"distance_km":[0.0],"direction_offset_deg":[0.0],"lat":[24.1813],"lon":[121.2818],"aod550":[0.1]}),
        "meta": {"request_audit": {"ads_request_id": rid,"ads_remote_status":"successful","ads_request_reattached":True,"ads_reattach_only":True}},
        "inventory": [],
        "error": "",
        "elapsed_seconds": 0.1,
    }


def test_release_identity_and_step3q21_scope_fail_closed():
    assert __version__ == "1.0.0-R5.7.41.3.4.10.30.21"
    assert STEP3Q_VERSION == "R5.7.41.3.4.10.30.21"
    m = band25_historical_scope_matrix()
    assert m["FU96_LINEAGE_200_WAVELENGTH_SAMPLE_COUNT_QUALIFIED"] is True
    assert m["FU96_LINEAGE_EXACT_200_WAVELENGTH_NODE_GRID_RECOVERED"] is False
    assert m["RRTMG_FU96_RUNTIME_DGE_3UM_LINEAR_INTERPOLATION_PINNED"] is True
    assert m["RRTMG_RUNTIME_DGE_INTERPOLATION_IS_SPECTRAL_PREAVERAGING_REALIZATION"] is False
    assert m["RRTMG_BAND25_RUNTIME_RWGT_IS_CLOUD_PREAVERAGING_SOLAR_WEIGHT_VECTOR"] is False
    assert m["RRTMG_BAND25_EXACT_REPRODUCTION_PASS"] is False
    assert m["TAU_ICE_PRODUCTION_ALLOWED"] is False


def test_step3q21_pinned_runtime_scope_sources_are_exactly_identified():
    s = pinned_runtime_scope_sources()
    assert s["fu96_lineage_single_scattering_wavelength_sample_count"] == 200
    assert s["fu96_lineage_solar_primary_band_count"] == 6
    assert s["aer_rrtmg_sw_runtime_scope_commit"] == "286e84ed14f61e2279ba819f4ce512a30b48f0b3"
    assert s["aer_rrtmg_sw_cldprop_blob_sha"] == "71a1d4c86a19fe2de1af7e5682562688da25cde0"
    assert s["aer_rrtmg_sw_init_blob_sha"] == "1236caef0b669f96cb0b2405c723dc2664703595"
    assert s["rrtmg_fu96_runtime_dge_step_um"] == 3.0


def test_step3q21_gate_and_contract_preserve_scope_guards():
    e = build_fu96_rrtmg_band_weighting_provenance_evidence()
    g = build_fu96_rrtmg_band_weighting_provenance_gate(e).iloc[0]
    assert bool(g["FU96_LINEAGE_200_WAVELENGTH_SAMPLE_COUNT_QUALIFIED"])
    assert not bool(g["FU96_LINEAGE_EXACT_200_WAVELENGTH_NODE_GRID_RECOVERED"])
    assert bool(g["RRTMG_FU96_RUNTIME_DGE_3UM_LINEAR_INTERPOLATION_PINNED"])
    assert not bool(g["RRTMG_RUNTIME_DGE_INTERPOLATION_IS_SPECTRAL_PREAVERAGING_REALIZATION"])
    assert bool(g["RRTMG_BAND25_RUNTIME_GPOINT_REDUCTION_SCOPE_QUALIFIED"])
    assert not bool(g["RRTMG_BAND25_RUNTIME_RWGT_IS_CLOUD_PREAVERAGING_SOLAR_WEIGHT_VECTOR"])
    assert not bool(g["RRTMG_BAND25_RUNTIME_SFLUXREF_REDUCTION_PROVES_HISTORICAL_CLOUD_WEIGHTING"])
    assert not bool(g["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"])
    assert not bool(g["TAU_ICE_PRODUCTION_ALLOWED"])
    p = fu96_rrtmg_band_weighting_provenance_contract_payload(evidence=e)
    assert p["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_21"
    assert p["step_version"] == STEP3Q_VERSION
    assert p["qualified_weighting_semantic_class"]["fu96_lineage_exact_200_wavelength_node_grid_recovered"] is False


def test_cams_reattach_observation_window_default_and_override(monkeypatch):
    monkeypatch.delenv("FIRECLOUD_CAMS_DEFERRED_REATTACH_DEADLINE_SECONDS", raising=False)
    assert cams_native._deferred_reattach_deadline_seconds(210.0) == 73.5
    assert cams_native._deferred_reattach_deadline_seconds(90.0) == 31.5
    assert cams_native._deferred_reattach_deadline_seconds(1.0) == 1.0
    monkeypatch.setenv("FIRECLOUD_CAMS_DEFERRED_REATTACH_DEADLINE_SECONDS", "50")
    assert cams_native._deferred_reattach_deadline_seconds(210.0) == 50.0
    monkeypatch.setenv("FIRECLOUD_CAMS_DEFERRED_REATTACH_DEADLINE_SECONDS", "999")
    assert cams_native._deferred_reattach_deadline_seconds(210.0) == 210.0


def test_adaptive_reattach_uses_same_request_and_bounded_observation_deadline(monkeypatch):
    calls=[]
    def fake(role, points, valid_time, cache_dir=None, deadline_seconds=90.0, heartbeat_callback=None, reattach_only=False):
        calls.append((bool(reattach_only), float(deadline_seconds)))
        return _ok(role, "rid-3021") if reattach_only else _timeout(role, "rid-3021")
    monkeypatch.setattr(cams_native, "_run_cams_role_isolated", fake)
    monkeypatch.setattr(cams_native.time, "sleep", lambda *_: None)
    monkeypatch.setenv("FIRECLOUD_CAMS_DEFERRED_REATTACH_COUNT", "1")
    monkeypatch.delenv("FIRECLOUD_CAMS_DEFERRED_REATTACH_DEADLINE_SECONDS", raising=False)
    df,audits,_,stats = cams_native._fetch_cams_role_adaptive(
        _points(), datetime(2026,9,20,tzinfo=timezone.utc),
        "NATIVE_AEROSOL_532NM_PRESSURE_LEVEL", deadline_seconds=210.0, max_depth=0,
    )
    assert calls == [(False,210.0),(True,73.5)]
    assert not df.empty and stats["successful_requests"] == 1
    a=audits[0]
    assert a["deferred_initial_request_id"] == "rid-3021"
    assert a["deferred_initial_deadline_seconds"] == 210.0
    assert a["deferred_reattach_deadline_seconds"] == 73.5
    assert a["deferred_recovery_contract"] == "R5.7.41.3.4.10.30.21_BOUNDED_SAME_REQUEST_ID_REATTACH_OBSERVATION_WINDOW_V1"

def test_serial_reattach_uses_bounded_observation_deadline_without_fresh_submit(monkeypatch):
    calls=[]
    def fake(role, points, valid_time, cache_dir=None, deadline_seconds=90.0, heartbeat_callback=None, reattach_only=False):
        calls.append((role,bool(reattach_only),float(deadline_seconds)))
        if role == "SPECTRAL_COLUMN_AOD" and not reattach_only:
            return _timeout(role,"rid-serial-3021")
        return _ok(role,"rid-serial-3021" if role == "SPECTRAL_COLUMN_AOD" else f"rid-{role}")
    monkeypatch.setattr(cams_native,"_run_cams_role_isolated",fake)
    monkeypatch.setattr(cams_native.time,"sleep",lambda *_:None)
    monkeypatch.setenv("FIRECLOUD_CAMS_ROLE_RETRY_COUNT","0")
    monkeypatch.setenv("FIRECLOUD_CAMS_DEFERRED_REATTACH_COUNT","1")
    monkeypatch.delenv("FIRECLOUD_CAMS_DEFERRED_REATTACH_DEADLINE_SECONDS",raising=False)
    _,meta=cams_native._fetch_route_native_aerosol_bundle_single_tile(
        _points(),datetime(2026,9,20,tzinfo=timezone.utc),deadline_seconds=210.0
    )
    spectral=[c for c in calls if c[0]=="SPECTRAL_COLUMN_AOD"]
    assert spectral == [("SPECTRAL_COLUMN_AOD",False,210.0),("SPECTRAL_COLUMN_AOD",True,73.5)]
    audit=[a for a in meta["cams_request_audit"] if a.get("deferred_reattach_attempted") is True][0]
    assert audit["deferred_initial_deadline_seconds"] == 210.0
    assert audit["deferred_reattach_deadline_seconds"] == 73.5
    assert audit["deferred_recovery_contract"] == "R5.7.41.3.4.10.30.21_BOUNDED_SAME_REQUEST_ID_REATTACH_OBSERVATION_WINDOW_V1"
