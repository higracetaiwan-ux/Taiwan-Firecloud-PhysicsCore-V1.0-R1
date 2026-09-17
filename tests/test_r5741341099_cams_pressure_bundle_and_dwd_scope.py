from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import firecloud
from firecloud.providers import cams_native, dwd_icon_native as icon
from firecloud.case_integrity import build_analysis_integrity_audit


def _points():
    return [
        {"point_id":"p0","distance_km":0.0,"direction_offset_deg":0.0,"lat":23.86,"lon":120.91},
        {"point_id":"p1","distance_km":40.0,"direction_offset_deg":0.0,"lat":23.86,"lon":120.50},
    ]


def _bundle_frame():
    rows=[]
    for p in _points():
        row=dict(p)
        for level in cams_native.DEFAULT_PRESSURE_LEVELS_HPA:
            row[f"cams_ozone_kgkg_{int(level)}hPa"] = 1e-6
            row[f"cams_aerext532_m1_{int(level)}hPa"] = 1e-5
            row[f"cams_geopotential_height_m_{int(level)}hPa"] = float(1000-level)*10.0
        rows.append(row)
    return pd.DataFrame(rows)


def test_1099_version():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.24.1"


def test_pressure_level_bundle_is_exact_union_of_legacy_requests():
    t=datetime(2026,9,14,10,0,tzinfo=timezone.utc)
    b,bm=cams_native.build_ads_pressure_level_chemistry_optics_bundle_request(_points(),t)
    o,om=cams_native.build_ads_ozone_request(_points(),t)
    a,am=cams_native.build_ads_native_aerosol_request(_points(),t)
    assert b["date"] == o["date"] == a["date"]
    assert b["time"] == o["time"] == a["time"]
    assert b["leadtime_hour"] == o["leadtime_hour"] == a["leadtime_hour"]
    assert b["area"] == o["area"] == a["area"]
    assert b["pressure_level"] == o["pressure_level"] == a["pressure_level"]
    assert set(b["variable"]) == set(o["variable"]) | set(a["variable"])
    assert bm["request_role"] == "PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE"


def test_pressure_level_bundle_exactly_reuses_both_legacy_logical_roles():
    t=datetime(2026,9,14,10,0,tzinfo=timezone.utc)
    frame=_bundle_frame()
    o=cams_native._exact_pressure_level_component_reuse_from_bundle(frame,_points(),t,"O3_PRESSURE_LEVEL")
    a=cams_native._exact_pressure_level_component_reuse_from_bundle(frame,_points(),t,"NATIVE_AEROSOL_532NM_PRESSURE_LEVEL")
    assert o is not None and a is not None
    odf,oa=o; adf,aa=a
    assert len(odf)==len(_points()) and len(adf)==len(_points())
    assert oa["final_status"] == aa["final_status"] == "EXACT_SOURCE_REUSE"
    assert oa["exact_source_role"] == aa["exact_source_role"] == "PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE"
    assert oa["elapsed_seconds"] == aa["elapsed_seconds"] == 0.0


def test_pressure_level_bundle_reuse_fails_closed_if_one_expected_level_is_missing():
    t=datetime(2026,9,14,10,0,tzinfo=timezone.utc)
    frame=_bundle_frame().drop(columns=["cams_ozone_kgkg_1000hPa"])
    assert cams_native._exact_pressure_level_component_reuse_from_bundle(frame,_points(),t,"O3_PRESSURE_LEVEL") is None
    assert cams_native._exact_pressure_level_component_reuse_from_bundle(frame,_points(),t,"NATIVE_AEROSOL_532NM_PRESSURE_LEVEL") is not None


def test_dwd_app_default_state_handoff_uses_user_level_cross_release_cache(monkeypatch, tmp_path):
    # The app passes a concrete FIRECLOUD_STATE_DIR to workers even when the
    # operator did not configure one. Marker=0 must not convert that handoff
    # into an explicit state-scoped provider cache.
    monkeypatch.setenv("FIRECLOUD_STATE_DIR", str(tmp_path / "release-state"))
    monkeypatch.setenv("FIRECLOUD_STATE_DIR_EXPLICIT_USER_OVERRIDE", "0")
    monkeypatch.delenv("FIRECLOUD_DWD_ICON_SHARED_CACHE_DIR", raising=False)
    monkeypatch.delenv("FIRECLOUD_DWD_ICON_RAW_CACHE_DIR", raising=False)
    assert icon._state_dir_is_explicit_user_override() is False
    assert icon._shared_cache_scope_label() == "USER_LEVEL_CROSS_RELEASE_EXACT_IDENTITY"
    assert str(icon._persistent_raw_cache_dir()).endswith(".cache/taiwan_firecloud/dwd_icon/raw_grib")


def test_dwd_true_user_state_override_remains_state_scoped(monkeypatch, tmp_path):
    state=tmp_path/"operator-state"
    monkeypatch.setenv("FIRECLOUD_STATE_DIR", str(state))
    monkeypatch.setenv("FIRECLOUD_STATE_DIR_EXPLICIT_USER_OVERRIDE", "1")
    monkeypatch.delenv("FIRECLOUD_DWD_ICON_SHARED_CACHE_DIR", raising=False)
    monkeypatch.delenv("FIRECLOUD_DWD_ICON_RAW_CACHE_DIR", raising=False)
    assert icon._state_dir_is_explicit_user_override() is True
    assert icon._shared_cache_scope_label() == "EXPLICIT_STATE_DIR_SCOPED_EXACT_IDENTITY"
    assert icon._persistent_raw_cache_dir() == state/"provider_cache_shared"/"dwd_icon_raw"


def test_integrity_accepts_pressure_bundle_exact_reuse_provenance():
    cams=pd.DataFrame([
        {"request_role":"PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE","status":"OK","final_status":"OK","elapsed_seconds":55.0},
        {"request_role":"O3_PRESSURE_LEVEL","status":"OK_EXACT_SOURCE_REUSE","final_status":"EXACT_SOURCE_REUSE","exact_source_reuse":True,"exact_source_role":"PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE","elapsed_seconds":0.0},
        {"request_role":"NATIVE_AEROSOL_532NM_PRESSURE_LEVEL","status":"OK_EXACT_SOURCE_REUSE","final_status":"EXACT_SOURCE_REUSE","exact_source_reuse":True,"exact_source_role":"PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE","elapsed_seconds":0.0},
    ])
    audit=build_analysis_integrity_audit({"cams_request_audit":cams})
    row=audit.loc[audit["check_id"].eq("CAMS_PRESSURE_LEVEL_BUNDLE_EXACT_REUSE_PROVENANCE")]
    assert len(row)==1
    assert row.iloc[0]["status"]=="PASS"
