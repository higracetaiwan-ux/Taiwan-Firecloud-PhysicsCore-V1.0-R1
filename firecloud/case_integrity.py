"""Data/CASE integrity guards for Taiwan Firecloud PhysicsCore.

This module is deliberately evidence-chain only.  It does not infer Formation,
Viewing, canvas suitability, optical depth, or UI semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Iterable, Mapping

import pandas as pd


PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"
ALLOWED_EMPTY = "ALLOWED_EMPTY"
NOT_APPLICABLE = "NOT_APPLICABLE"


def _df(obj: Any) -> pd.DataFrame:
    return obj if isinstance(obj, pd.DataFrame) else pd.DataFrame()


def _rows(obj: Any) -> int:
    return int(len(obj)) if isinstance(obj, pd.DataFrame) else 0


def _contains_any(series: pd.Series, patterns: Iterable[str]) -> pd.Series:
    if series.empty:
        return pd.Series(dtype=bool)
    text = series.astype(str).str.upper()
    mask = pd.Series(False, index=text.index)
    for p in patterns:
        mask |= text.str.contains(str(p).upper(), regex=False, na=False)
    return mask




def _row_any_numeric_valid_fraction(df: pd.DataFrame, columns: Iterable[str]) -> float:
    cols = [c for c in columns if c in df.columns]
    if df.empty or not cols:
        return 0.0
    numeric = pd.concat([pd.to_numeric(df[c], errors="coerce").rename(c) for c in cols], axis=1)
    return float(numeric.notna().any(axis=1).mean()) if len(numeric) else 0.0


def _text_token_fraction(df: pd.DataFrame, columns: Iterable[str], token: str) -> float:
    cols = [c for c in columns if c in df.columns]
    if df.empty or not cols:
        return 0.0
    text = pd.concat([df[c].astype(str) for c in cols], axis=1).agg(" ".join, axis=1).str.upper()
    return float(text.str.contains(str(token).upper(), regex=False, na=False).mean()) if len(text) else 0.0

def _audit_success(df: pd.DataFrame) -> bool:
    """Conservative provider-audit success detector, schema tolerant."""
    if df.empty:
        return False
    cols = [c for c in ["status", "final_status", "network_status", "action", "result"] if c in df.columns]
    if not cols:
        return False
    text = pd.concat([df[c].astype(str) for c in cols], axis=0, ignore_index=True).str.upper()
    bad = text.str.contains("FAILED|ERROR|TIMEOUT|HTTP_4|HTTP_5|429", regex=True, na=False)
    good = text.str.contains("OK|READY|CACHE|DOWNLOAD|DECODED|SUCCESS", regex=True, na=False)
    return bool(good.any() and not (bad.all() if len(bad) else False))


def _cams_role_success(df: pd.DataFrame, tokens: Iterable[str]) -> bool:
    if df.empty:
        return False
    role_cols = [c for c in ["role", "chain", "dataset_role", "request_role", "product", "variable"] if c in df.columns]
    if not role_cols:
        return _audit_success(df)
    role_text = pd.concat([df[c].astype(str) for c in role_cols], axis=1).agg(" ".join, axis=1).str.upper()
    role_mask = pd.Series(False, index=df.index)
    for tok in tokens:
        role_mask |= role_text.str.contains(str(tok).upper(), regex=False, na=False)
    if not role_mask.any():
        return False
    return _audit_success(df.loc[role_mask])


def build_analysis_integrity_audit(result: Mapping[str, Any]) -> pd.DataFrame:
    """Validate provider/decode/evidence handoff without interpreting physics."""
    rows: list[dict[str, Any]] = []

    def add(check_id: str, status: str, component: str, observed: Any, expected: str, detail: str = ""):
        rows.append({
            "check_id": check_id,
            "status": status,
            "component": component,
            "observed": observed,
            "expected": expected,
            "detail": detail,
        })

    route = _df(result.get("route_points"))
    route_ref = _df(result.get("route_reference_contract"))
    forecast = _df(result.get("hourly_raw"))
    gfs_req = _df(result.get("gfs_native_request_audit"))
    gfs_inv = _df(result.get("gfs_grib_message_inventory"))
    gfs_comp = _df(result.get("gfs_native_field_completeness"))
    native_vox = _df(result.get("native_cloud_voxel_matrix"))
    gas = _df(result.get("gas_profile_route_snapshots"))
    ozone = _df(result.get("ozone_profile_route_snapshots"))
    cams_req = _df(result.get("cams_request_audit"))
    aerosol_spectral = _df(result.get("aerosol_spectral_route_snapshots"))
    formation = _df(result.get("v1_formation"))
    viewing = _df(result.get("v1_viewing_summary"))
    perf = _df(result.get("performance_diagnostics"))
    canvas = _df(result.get("v1_canvas_candidates"))
    spectral = _df(result.get("v1_spectral_optical_paths"))

    add("ROUTE_POINTS_PRESENT", PASS if not route.empty else FAIL, "ROUTE", _rows(route), ">0 rows")
    if not route_ref.empty:
        _contract_ok = bool(route_ref.get("route_invariant_to_runtime_angle_set", pd.Series([False])).astype(bool).all())
        add("ROUTE_REFERENCE_CONTRACT_PRESENT", PASS if _contract_ok else FAIL, "ROUTE", _rows(route_ref), "fixed reference-route contract with invariance=true")
        try:
            _ref_az = float(pd.to_numeric(route_ref["reference_azimuth_deg"], errors="coerce").iloc[0])
            _ref_max = float(pd.to_numeric(route_ref["route_domain_max_km"], errors="coerce").iloc[0])
            if not route.empty and {"bearing_deg","direction_offset_deg"}.issubset(route.columns):
                _b = pd.to_numeric(route["bearing_deg"], errors="coerce")
                _o = pd.to_numeric(route["direction_offset_deg"], errors="coerce")
                _expected = (_ref_az + _o) % 360.0
                _err = (((_b - _expected + 180.0) % 360.0) - 180.0).abs()
                _maxerr = float(_err.max()) if len(_err) else float("nan")
                add("ROUTE_REFERENCE_BEARING_INVARIANT", PASS if _maxerr <= 1e-8 else FAIL, "ROUTE", _maxerr, "<=1e-8 deg from fixed reference azimuth + direction offset")
            if not route.empty and "distance_km" in route.columns:
                _route_max = float(pd.to_numeric(route["distance_km"], errors="coerce").max())
                add("ROUTE_REFERENCE_DOMAIN_INVARIANT", PASS if abs(_route_max-_ref_max) <= 1e-8 else FAIL, "ROUTE", _route_max, f"contract route_domain_max_km={_ref_max}")
        except Exception as exc:
            add("ROUTE_REFERENCE_CONTRACT_DECODE", FAIL, "ROUTE", type(exc).__name__, "decodable reference-route provenance", str(exc))
    else:
        add("ROUTE_REFERENCE_CONTRACT_PRESENT", WARN, "ROUTE", 0, "present in R5.7.22.1+ CASE; legacy CASE may omit it")
    add("FORECAST_RAW_PRESENT", PASS if not forecast.empty else FAIL, "FORECAST", _rows(forecast), ">0 rows")

    gfs_requested = not gfs_req.empty or bool(result.get("details"))
    if gfs_requested:
        add("GFS_REQUEST_AUDIT_PRESENT", PASS if not gfs_req.empty else FAIL, "NOAA_GFS_NATIVE", _rows(gfs_req), ">0 rows", "GFS native pipeline must never disappear silently")
        if _audit_success(gfs_req):
            add("GFS_INVENTORY_HANDOFF", PASS if not gfs_inv.empty else FAIL, "NOAA_GFS_NATIVE", _rows(gfs_inv), ">0 rows after successful native request", "Successful request with empty inventory indicates decode/evidence handoff regression")
            add("GFS_COMPLETENESS_HANDOFF", PASS if not gfs_comp.empty else FAIL, "NOAA_GFS_NATIVE", _rows(gfs_comp), ">0 rows after successful native request", "Successful request with empty completeness table is not an allowed clear-sky state")
        else:
            add("GFS_PROVIDER_FAILURE_VISIBLE", WARN, "NOAA_GFS_NATIVE", _rows(gfs_req), "failure must remain visible in request audit")
    else:
        add("GFS_NATIVE_PIPELINE", WARN, "NOAA_GFS_NATIVE", 0, "pipeline audit expected when native GFS is configured")

    if not gfs_comp.empty:
        text_cols = [c for c in ["field", "variable", "short_name", "parameter"] if c in gfs_comp.columns]
        if text_cols:
            txt = pd.concat([gfs_comp[c].astype(str) for c in text_cols], axis=1).agg(" ".join, axis=1).str.upper()
            clwmr = txt.str.contains("CLWMR", regex=False, na=False).any()
            icmr = txt.str.contains("ICMR", regex=False, na=False).any()
            add("GFS_CLWMR_COMPLETENESS_ROW", PASS if clwmr else WARN, "NOAA_GFS_NATIVE", bool(clwmr), "CLWMR row when requested/available")
            add("GFS_ICMR_COMPLETENESS_ROW", PASS if icmr else WARN, "NOAA_GFS_NATIVE", bool(icmr), "ICMR row when requested/available")

    if not gfs_inv.empty and native_vox.empty:
        add("GFS_NATIVE_VOXEL_HANDOFF", FAIL, "NOAA_GFS_NATIVE", 0, ">0 native voxel rows when inventory decoded", "Inventory exists but reconstructed native voxel evidence vanished")
    elif not native_vox.empty:
        add("GFS_NATIVE_VOXEL_HANDOFF", PASS, "NOAA_GFS_NATIVE", _rows(native_vox), ">0 rows")

    o3_success = _cams_role_success(cams_req, ["O3", "OZONE"])
    o3_missing_signal = _text_token_fraction(ozone, ["o3_quality"], "MISSING") > 0.95 or _text_token_fraction(gas, ["o3_quality", "gas_profile_source"], "O3_MISSING") > 0.95
    aerosol_missing_signal = False
    if not spectral.empty and "missing_components" in spectral.columns:
        aerosol_missing_signal = float(spectral["missing_components"].fillna("").astype(str).str.upper().str.contains("AEROSOL", regex=False).mean()) > 0.95
    cams_payload_expected = o3_missing_signal or aerosol_missing_signal or not ozone.empty or not aerosol_spectral.empty
    if cams_payload_expected:
        add("CAMS_REQUEST_AUDIT_PRESENT", PASS if not cams_req.empty else FAIL, "CAMS", _rows(cams_req), ">0 request-audit rows when CAMS-dependent payload is expected", "A blank request audit must not coexist silently with missing O3/aerosol payload")

    if o3_success:
        add("CAMS_O3_ROUTE_HANDOFF", PASS if not ozone.empty else FAIL, "CAMS_O3", _rows(ozone), ">0 rows after successful O3 request")
    elif not ozone.empty:
        add("CAMS_O3_ROUTE_HANDOFF", PASS, "CAMS_O3", _rows(ozone), ">0 rows")
    else:
        add("CAMS_O3_ROUTE_HANDOFF", WARN, "CAMS_O3", 0, "route evidence or explicit failed/deferred audit")

    if not ozone.empty:
        o3_valid_fraction = _row_any_numeric_valid_fraction(ozone, ["o3_mass_mixing_ratio_kgkg", "o3_mole_fraction", "o3_number_density_m3"])
        o3_payload_status = PASS if o3_valid_fraction >= 0.95 else (FAIL if o3_valid_fraction <= 0.0 else WARN)
        add("CAMS_O3_ROUTE_PAYLOAD_VALIDITY", o3_payload_status, "CAMS_O3", round(o3_valid_fraction, 6), ">=0.95 rows with numeric O3 payload", "Table presence is insufficient: O3 numeric payload must be present; all-missing payload is a hard failure")
        o3_missing_fraction = _text_token_fraction(ozone, ["o3_quality"], "MISSING")
        add("CAMS_O3_QUALITY_MISSING_FRACTION", FAIL if o3_missing_fraction >= 0.95 else (WARN if o3_missing_fraction > 0 else PASS), "CAMS_O3", round(o3_missing_fraction, 6), "<0.95; ideally 0", "CAMS_O3_MISSING quality on nearly all route rows is not a valid O3 evidence payload")

    if not gas.empty:
        add("GAS_PROFILE_ROUTE_HANDOFF", PASS, "GAS_PROFILE", _rows(gas), ">0 rows")
        _gas_core_cols = [c for c in ["temperature_k", "h2o_mole_fraction", "o2_mole_fraction"] if c in gas.columns]
        if _gas_core_cols:
            gas_valid_fraction = _row_any_numeric_valid_fraction(gas, _gas_core_cols)
            add("GAS_CORE_PAYLOAD_VALIDITY", PASS if gas_valid_fraction >= 0.95 else (FAIL if gas_valid_fraction <= 0.0 else WARN), "GAS_PROFILE", round(gas_valid_fraction, 6), ">=0.95 rows with core thermodynamic/H2O/O2 payload")
        else:
            add("GAS_CORE_PAYLOAD_VALIDITY", WARN, "GAS_PROFILE", "SCHEMA_NOT_AVAILABLE", "core payload columns when exported", "Legacy/minimal fixtures may omit core gas columns; do not convert schema absence into a false payload hard failure")
    else:
        add("GAS_PROFILE_ROUTE_HANDOFF", WARN, "GAS_PROFILE", 0, "gas evidence may be absent only with explicit upstream failure")

    if not aerosol_spectral.empty:
        aerosol_valid_fraction = _row_any_numeric_valid_fraction(aerosol_spectral, ["aod550", "aod600", "aod645", "aod650", "aod670", "aod700", "aod750", "aod800"])
        add("CAMS_AEROSOL_SPECTRAL_PAYLOAD_VALIDITY", PASS if aerosol_valid_fraction >= 0.95 else (FAIL if aerosol_valid_fraction <= 0.0 else WARN), "CAMS_AEROSOL", round(aerosol_valid_fraction, 6), ">=0.95 rows with numeric spectral AOD payload")
    elif not canvas.empty and aerosol_missing_signal:
        add("CAMS_AEROSOL_SPECTRAL_PAYLOAD_VALIDITY", FAIL, "CAMS_AEROSOL", 0.0, "spectral aerosol payload or explicit provider failure", "Canvas spectral paths report AEROSOL missing while aerosol route payload is empty")
    else:
        add("CAMS_AEROSOL_SPECTRAL_PAYLOAD_VALIDITY", WARN, "CAMS_AEROSOL", 0.0, "payload when required by target spectral RT")

    add("FORMATION_TABLE_PRESENT", PASS if not formation.empty else FAIL, "FORMATION", _rows(formation), ">0 rows")
    add("VIEWING_SUMMARY_PRESENT", PASS if not viewing.empty else WARN, "VIEWING", _rows(viewing), ">0 rows when viewing targets exist")
    add("PERFORMANCE_DIAGNOSTICS_PRESENT", PASS if not perf.empty else FAIL, "PERFORMANCE", _rows(perf), ">0 rows")

    if canvas.empty:
        add("TARGET_DEPENDENT_SPECTRAL_EMPTY", ALLOWED_EMPTY if spectral.empty else PASS, "FORMATION_RT", _rows(spectral), "empty allowed when no canvas candidates", "No-canvas is a physical outcome; an empty target-dependent RT table is not CASE corruption")
    else:
        add("TARGET_DEPENDENT_SPECTRAL_EVIDENCE", PASS if not spectral.empty else WARN, "FORMATION_RT", _rows(spectral), ">0 rows when canvas candidates exist", "May remain partial/missing optically, but evidence table should normally exist")

    hard_fail = any(r["status"] == FAIL for r in rows)
    rows.append({
        "check_id": "ANALYSIS_INTEGRITY_OVERALL",
        "status": FAIL if hard_fail else PASS,
        "component": "OVERALL",
        "observed": sum(r["status"] == FAIL for r in rows),
        "expected": "0 hard failures",
        "detail": "Evidence-chain integrity only; does not judge firecloud physics.",
    })
    return pd.DataFrame(rows)


def dataframe_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def archive_manifest_row(name: str, payload: bytes, row_count: int | None, status: str, detail: str = "") -> dict[str, Any]:
    return {
        "artifact": name,
        "status": status,
        "row_count": row_count,
        "byte_size": len(payload),
        "sha256": sha256(payload).hexdigest(),
        "detail": detail,
    }


def build_archive_integrity_audit(manifest: pd.DataFrame, analysis_audit: pd.DataFrame) -> pd.DataFrame:
    """Second-layer checks over actual serialized CASE members."""
    rows: list[dict[str, Any]] = []
    names = set(manifest.get("artifact", pd.Series(dtype=str)).astype(str)) if not manifest.empty else set()
    required = {
        "summary.csv",
        "route_reference_contract.csv",
        "route_points.csv",
        "forecast_raw.csv",
        "performance_diagnostics.csv",
        "gfs_native_request_audit.csv",
        "gfs_grib_message_inventory.csv",
        "gfs_native_field_completeness.csv",
        "v1_formation.csv",
        "v1_viewing_summary.csv",
        "analysis_integrity_audit.csv",
    }
    for name in sorted(required):
        rows.append({
            "check_id": f"ARCHIVE_MEMBER::{name}",
            "status": PASS if name in names else FAIL,
            "component": "CASE_ARCHIVE",
            "observed": name in names,
            "expected": "member present",
            "detail": "Required evidence member",
        })

    if not analysis_audit.empty and "status" in analysis_audit.columns:
        upstream_fail = int(analysis_audit["status"].astype(str).eq(FAIL).sum())
        rows.append({
            "check_id": "ANALYSIS_INTEGRITY_PROPAGATED",
            "status": FAIL if upstream_fail else PASS,
            "component": "CASE_ARCHIVE",
            "observed": upstream_fail,
            "expected": "0 upstream hard failures",
            "detail": "CASE archive remains downloadable for diagnosis even on FAIL.",
        })

    hard_fail = any(r["status"] == FAIL for r in rows)
    rows.append({
        "check_id": "CASE_ARCHIVE_INTEGRITY_OVERALL",
        "status": FAIL if hard_fail else PASS,
        "component": "OVERALL",
        "observed": sum(r["status"] == FAIL for r in rows),
        "expected": "0 hard failures",
        "detail": "Archive integrity is independent of scientific forecast outcome.",
    })
    return pd.DataFrame(rows)
