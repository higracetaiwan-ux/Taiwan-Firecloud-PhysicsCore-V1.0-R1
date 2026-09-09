"""Data/CASE integrity guards for Taiwan Firecloud PhysicsCore.

This module is deliberately evidence-chain only.  It does not infer Formation,
Viewing, canvas suitability, optical depth, or UI semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Iterable, Mapping

import math
import pandas as pd

from .contracts import SIX_BAND_WAVELENGTHS_NM


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


def _join_text_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.Series:
    """Join heterogeneous audit columns safely as text.

    Pandas/Python combinations may preserve numeric scalars in row-wise
    aggregation even after per-column astype(str).  Integrity auditing must
    never crash because an optional provider-audit field contains NaN/float.
    """
    cols = [c for c in columns if c in df.columns]
    if df.empty or not cols:
        return pd.Series(dtype=str, index=df.index)
    block = df.loc[:, cols].copy()
    for c in cols:
        block[c] = block[c].map(lambda v: "" if pd.isna(v) else str(v))
    return block.apply(lambda row: " ".join(str(v) for v in row.tolist()), axis=1)


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
    text = _join_text_columns(df, cols).str.upper()
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
    role_text = _join_text_columns(df, role_cols).str.upper()
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
    viewing_geometry = _df(result.get("v1_viewing_path_geometry"))
    viewing = _df(result.get("v1_viewing_summary"))
    viewing_precipitation = _df(result.get("v1_viewing_precipitation_evidence"))
    viewing_spectral = _df(result.get("v1_viewing_spectral_extinction_550_750nm"))
    viewing_spectral_summary = _df(result.get("v1_viewing_spectral_summary"))
    photography = _df(result.get("v1_photography_decision"))
    perf = _df(result.get("performance_diagnostics"))
    canvas = _df(result.get("v1_canvas_candidates"))
    spectral = _df(result.get("v1_spectral_optical_paths"))
    completeness = _df(result.get("physics_data_completeness"))
    red_ref = _df(result.get("v1_red_light_reference"))
    red_sum = _df(result.get("v1_red_light_availability_summary"))
    headline = _df(result.get("summary"))

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
            txt = _join_text_columns(gfs_comp, text_cols).str.upper()
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
        aerosol_valid_fraction = _row_any_numeric_valid_fraction(aerosol_spectral, ["aod550", "aod575", "aod600", "aod645", "aod650", "aod670", "aod700", "aod750", "aod800"])
        add("CAMS_AEROSOL_SPECTRAL_PAYLOAD_VALIDITY", PASS if aerosol_valid_fraction >= 0.95 else (FAIL if aerosol_valid_fraction <= 0.0 else WARN), "CAMS_AEROSOL", round(aerosol_valid_fraction, 6), ">=0.95 rows with numeric spectral AOD payload")
        if "spectral_aod_temporal_evidence_state" in aerosol_spectral.columns:
            temporal = aerosol_spectral["spectral_aod_temporal_evidence_state"].fillna("MISSING").astype(str)
            fallback = temporal.eq("REAL_ONE_SIDED_TEMPORAL_FALLBACK")
            exact = temporal.eq("EXACT_VALID_TIME")
            offsets = pd.to_numeric(
                aerosol_spectral.get("spectral_aod_time_offset_hours", pd.Series(float("nan"), index=aerosol_spectral.index)),
                errors="coerce",
            )
            bounds = pd.to_numeric(
                aerosol_spectral.get("spectral_aod_temporal_bound_hours", pd.Series(float("nan"), index=aerosol_spectral.index)),
                errors="coerce",
            )
            fallback_valid = (~fallback) | (offsets.notna() & bounds.notna() & (offsets.abs() <= bounds + 1e-9))
            provenance_ready = exact | fallback
            status = FAIL if not bool(fallback_valid.all()) else (PASS if float(provenance_ready.mean()) >= 0.95 else WARN)
            add(
                "CAMS_AEROSOL_SPECTRAL_TEMPORAL_PROVENANCE",
                status,
                "CAMS_AEROSOL",
                f"exact={float(exact.mean()):.6f};real_bounded_fallback={float(fallback.mean()):.6f};missing={float((~provenance_ready).mean()):.6f}",
                "spectral rows are exact-time or real adjacent-time evidence within their exported bound",
                "R5.7.28 permits only real CAMS one-sided support within one native 3-hour forecast interval; no fixed Angstrom/artificial AOD",
            )
    elif not canvas.empty and aerosol_missing_signal:
        add("CAMS_AEROSOL_SPECTRAL_PAYLOAD_VALIDITY", FAIL, "CAMS_AEROSOL", 0.0, "spectral aerosol payload or explicit provider failure", "Canvas spectral paths report AEROSOL missing while aerosol route payload is empty")
    else:
        add("CAMS_AEROSOL_SPECTRAL_PAYLOAD_VALIDITY", WARN, "CAMS_AEROSOL", 0.0, "payload when required by target spectral RT")

    add("FORMATION_TABLE_PRESENT", PASS if not formation.empty else FAIL, "FORMATION", _rows(formation), ">0 rows")
    add("VIEWING_SUMMARY_PRESENT", PASS if not viewing.empty else WARN, "VIEWING", _rows(viewing), ">0 rows when viewing targets exist")

    # R5.7.29 Viewing Full Six-Band RT evidence-chain closure.  These checks
    # validate target coverage, six-band schema and arithmetic only; they do not
    # introduce a photographic threshold or alter Formation.
    def _view_target_keys(df: pd.DataFrame) -> set[tuple[str,float|None,str,str]]:
        out=set()
        if df.empty: return out
        for _,r in df.iterrows():
            av=pd.to_numeric(pd.Series([r.get("solar_altitude_deg")]),errors="coerce").iloc[0]
            out.add((str(r.get("time")),None if pd.isna(av) else round(float(av),8),str(r.get("canvas_id")),str(r.get("cloud_layer_id"))))
        return out

    if not viewing_geometry.empty:
        eligible=viewing_geometry.get("photographic_target_eligible",pd.Series(False,index=viewing_geometry.index)).fillna(False).astype(bool)
        expected_keys=_view_target_keys(viewing_geometry.loc[eligible])
        observed_keys=_view_target_keys(viewing_spectral)
        missing_keys=expected_keys-observed_keys; extra_keys=observed_keys-expected_keys
        status=PASS if not missing_keys and not extra_keys else FAIL
        add("VIEWING_SIX_BAND_TARGET_COVERAGE",status,"VIEWING_RT",f"expected={len(expected_keys)};observed={len(observed_keys)};missing={len(missing_keys)};extra={len(extra_keys)}","one spectral row per eligible time+angle+target key","Canvas/layer IDs repeat across angles and may never be used as global evidence keys")
    else:
        add("VIEWING_SIX_BAND_TARGET_COVERAGE",WARN,"VIEWING_RT","GEOMETRY_SCHEMA_NOT_AVAILABLE","R5.7.29 viewing target geometry","Legacy/minimal fixtures may omit target geometry")

    # R5.7.29.1 production handoff guard.  Archive-member presence and the
    # downstream spectral schema cannot prove that the native RWMR/SNMR/GRLE
    # snapshots survived the runtime spool.  When GFS reports those three
    # fields READY, every eligible target must have an explicit Viewing
    # precipitation evidence row; local/invalid geometry remains an explicit
    # unresolved row rather than disappearing.
    def _view_precip_keys(df: pd.DataFrame) -> set[tuple[str,float|None,str]]:
        out=set()
        if df.empty: return out
        for _,r in df.iterrows():
            av=pd.to_numeric(pd.Series([r.get("solar_altitude_deg")]),errors="coerce").iloc[0]
            out.add((str(r.get("time")),None if pd.isna(av) else round(float(av),8),str(r.get("canvas_id"))))
        return out

    hydrometeor_ready=False
    if not gfs_comp.empty and {"field","status"}.issubset(gfs_comp.columns):
        ready_fields=set(
            gfs_comp.loc[
                gfs_comp["status"].astype(str).str.upper().eq("READY"),
                "field",
            ].astype(str).str.upper()
        )
        hydrometeor_ready={"RWMR","SNMR","GRLE"}.issubset(ready_fields)
    if not viewing_geometry.empty:
        eligible=viewing_geometry.get("photographic_target_eligible",pd.Series(False,index=viewing_geometry.index)).fillna(False).astype(bool)
        expected_precip_keys=_view_precip_keys(viewing_geometry.loc[eligible])
        observed_precip_keys=_view_precip_keys(viewing_precipitation)
        missing_precip_keys=expected_precip_keys-observed_precip_keys
        extra_precip_keys=observed_precip_keys-expected_precip_keys
        precip_coverage_ok=not missing_precip_keys and not extra_precip_keys
        add(
            "VIEWING_PRECIPITATION_TARGET_COVERAGE",
            PASS if precip_coverage_ok else FAIL,
            "VIEWING_PRECIPITATION",
            f"expected={len(expected_precip_keys)};observed={len(observed_precip_keys)};missing={len(missing_precip_keys)};extra={len(extra_precip_keys)}",
            "one precipitation evidence row per eligible time+angle+canvas key",
            "An empty header-only table is not evidence coverage",
        )
        if hydrometeor_ready:
            statuses=viewing_precipitation.get("view_precipitation_status",pd.Series(dtype=str)).fillna("").astype(str)
            native_handoff_ok=(not viewing_precipitation.empty and precip_coverage_ok and not statuses.eq("VIEW_PRECIPITATION_VOLUME_UNRESOLVED").any())
            add(
                "VIEWING_NATIVE_HYDROMETEOR_HANDOFF",
                PASS if native_handoff_ok else FAIL,
                "VIEWING_PRECIPITATION",
                f"gfs_ready={hydrometeor_ready};rows={len(viewing_precipitation)};volume_unresolved={int(statuses.eq('VIEW_PRECIPITATION_VOLUME_UNRESOLVED').sum())}",
                "RWMR/SNMR/GRLE READY implies preserved per-target Viewing precipitation evidence",
                "Runtime spool cleanup must occur only after viewing_route_snapshot drain",
            )
        else:
            add("VIEWING_NATIVE_HYDROMETEOR_HANDOFF",WARN,"VIEWING_PRECIPITATION",f"gfs_ready={hydrometeor_ready}","explicit provider gap or native hydrometeor evidence")
    else:
        add("VIEWING_PRECIPITATION_TARGET_COVERAGE",WARN,"VIEWING_PRECIPITATION","GEOMETRY_SCHEMA_NOT_AVAILABLE","R5.7.29.1 viewing target geometry")
        add("VIEWING_NATIVE_HYDROMETEOR_HANDOFF",WARN,"VIEWING_PRECIPITATION",f"gfs_ready={hydrometeor_ready}","viewing geometry and provider evidence")

    if not viewing_spectral.empty:
        required_status={"view_gas_status","view_aerosol_status","view_cloud_status","view_precipitation_status","viewing_spectral_status","viewing_missing_components","viewing_spectral_contract"}
        required_bands={
            f"view_tau_{component}_{int(wl)}nm"
            for wl in SIX_BAND_WAVELENGTHS_NM
            for component in ("gas","aerosol","cloud","precip","total")
        } | {f"view_transmission_{int(wl)}nm" for wl in SIX_BAND_WAVELENGTHS_NM} | {f"view_band_evidence_state_{int(wl)}nm" for wl in SIX_BAND_WAVELENGTHS_NM}
        missing_cols=sorted((required_status|required_bands)-set(viewing_spectral.columns))
        add("VIEWING_SIX_BAND_SCHEMA",PASS if not missing_cols else FAIL,"VIEWING_RT",str(missing_cols),"all six gas/aerosol/cloud/precip/total/transmission/evidence columns","Six bands remain explicit and component-separated")
        inconsistent=0
        if not missing_cols:
            for _,r in viewing_spectral[viewing_spectral["viewing_spectral_status"].astype(str).eq("VIEW_FULL_SIX_BAND_RT")].iterrows():
                for wl in SIX_BAND_WAVELENGTHS_NM:
                    vals=[pd.to_numeric(pd.Series([r.get(f"view_tau_{c}_{int(wl)}nm")]),errors="coerce").iloc[0] for c in ("gas","aerosol","cloud","precip")]
                    total=pd.to_numeric(pd.Series([r.get(f"view_tau_total_{int(wl)}nm")]),errors="coerce").iloc[0]
                    trans=pd.to_numeric(pd.Series([r.get(f"view_transmission_{int(wl)}nm")]),errors="coerce").iloc[0]
                    if any(pd.isna(v) for v in vals) or pd.isna(total) or pd.isna(trans) or abs(float(total)-sum(float(v) for v in vals))>1e-9 or abs(float(trans)-math.exp(-float(total)))>1e-9:
                        inconsistent+=1
            nonfull=~viewing_spectral["viewing_spectral_status"].astype(str).eq("VIEW_FULL_SIX_BAND_RT")
            false_total=0
            for wl in SIX_BAND_WAVELENGTHS_NM:
                total=pd.to_numeric(viewing_spectral.get(f"view_tau_total_{int(wl)}nm"),errors="coerce")
                false_total+=int((nonfull & total.notna()).sum())
            inconsistent+=false_total
        add("VIEWING_SIX_BAND_NUMERIC_CLOSURE",PASS if not missing_cols and inconsistent==0 else FAIL,"VIEWING_RT",inconsistent,"0 inconsistent Full rows and 0 partial rows promoted to total transmission","Partial component tau remains diagnostic and cannot become a full transmission")
    elif not viewing_geometry.empty:
        eligible=viewing_geometry.get("photographic_target_eligible",pd.Series(False,index=viewing_geometry.index)).fillna(False).astype(bool)
        add("VIEWING_SIX_BAND_SCHEMA",FAIL if eligible.any() else ALLOWED_EMPTY,"VIEWING_RT",0,"spectral rows when eligible targets exist")

    if not viewing_spectral_summary.empty:
        expected_summary_keys={(k[0],k[1]) for k in _view_target_keys(viewing_spectral)}
        observed_summary_keys=set()
        for _,r in viewing_spectral_summary.iterrows():
            av=pd.to_numeric(pd.Series([r.get("solar_altitude_deg")]),errors="coerce").iloc[0]
            observed_summary_keys.add((str(r.get("time")),None if pd.isna(av) else round(float(av),8)))
        diff=expected_summary_keys.symmetric_difference(observed_summary_keys)
        add("VIEWING_SIX_BAND_SUMMARY_COVERAGE",PASS if not diff else FAIL,"VIEWING_RT",len(diff),"0 missing/extra time-angle summaries")
        handoff_cols={"viewing_spectral_state","viewing_rt_completeness",*[f"mean_view_transmission_{int(w)}nm" for w in SIX_BAND_WAVELENGTHS_NM]}
        handoff_missing=sorted(handoff_cols-set(photography.columns)) if not photography.empty else sorted(handoff_cols)
        add("VIEWING_SIX_BAND_PHOTOGRAPHY_HANDOFF",PASS if not handoff_missing else FAIL,"PHOTOGRAPHY_DECISION",str(handoff_missing),"six-band Viewing summary preserved in Photography rows","Viewing remains a diagnostic photographability modifier and cannot rewrite Formation")
    else:
        add("VIEWING_SIX_BAND_SUMMARY_COVERAGE",WARN,"VIEWING_RT",0,"summary when viewing spectral targets exist")

    # R5.7.27 Formation-first Photography Decision aggregation.  The decision
    # timeline must follow Formation, not the usually sparser Viewing target
    # table, and a resolved Formation NO-GO may never be promoted by Viewing.
    if not formation.empty:
        if photography.empty:
            status = FAIL if not red_sum.empty else WARN
            add("PHOTOGRAPHY_DECISION_FORMATION_ANGLE_COVERAGE", status, "PHOTOGRAPHY_DECISION", 0, "same solar-angle coverage as Formation", "R5.7.27+ requires Formation-driven Photography Decision rows")
        else:
            f_angles = set(pd.to_numeric(formation.get("solar_altitude_deg"), errors="coerce").dropna().round(8).tolist())
            p_angles = set(pd.to_numeric(photography.get("solar_altitude_deg"), errors="coerce").dropna().round(8).tolist())
            missing = sorted(f_angles - p_angles)
            extra = sorted(p_angles - f_angles)
            add("PHOTOGRAPHY_DECISION_FORMATION_ANGLE_COVERAGE", PASS if not missing and not extra else FAIL, "PHOTOGRAPHY_DECISION", f"missing={missing};extra={extra};rows={len(photography)}", "same solar-angle coverage as Formation", "Viewing may be sparse but must not collapse the Photography Decision timeline")

            if {"formation_state","photography_opportunity"}.issubset(photography.columns):
                fs = photography["formation_state"].fillna("").astype(str)
                no_go = (
                    fs.isin([
                        "FORMATION_FAILED","FAILED","NO_FORMATION","NOT_FORMED_EARTH_SHADOW",
                        "ILLUMINATION_BLOCKED","NOT_FORMED_ILLUMINATION_BLOCKED",
                        "CLEAR_RED_PATH_NO_CANVAS","PARTIAL_RED_PATH_NO_CANVAS",
                        "RED_PATH_ATTENUATED_NO_CANVAS","NO_CANVAS_NO_DIRECT_RED_ACCESS",
                        "NO_CANVAS_RED_PATH_CONFLICT","NO_CANVAS_RED_PATH_UNKNOWN",
                    ])
                    | (fs.str.startswith("NO_CANVAS_") & ~fs.eq("NO_CANVAS_EVIDENCE"))
                    | fs.str.endswith("_NO_CANVAS")
                )
                bad = photography.loc[no_go & ~photography["photography_opportunity"].astype(str).eq("NO_GO"), [c for c in ["solar_altitude_deg","formation_state","viewing_state","photography_opportunity"] if c in photography.columns]]
                add("PHOTOGRAPHY_FORMATION_NO_GO_DOMINANCE", PASS if bad.empty else FAIL, "PHOTOGRAPHY_DECISION", int(len(bad)), "0 Formation NO-GO rows with opportunity other than NO_GO", "Viewing remains diagnostic and cannot rewrite Formation")
            else:
                add("PHOTOGRAPHY_FORMATION_NO_GO_DOMINANCE", WARN, "PHOTOGRAPHY_DECISION", "SCHEMA_NOT_AVAILABLE", "formation_state + photography_opportunity columns")

    add("PERFORMANCE_DIAGNOSTICS_PRESENT", PASS if not perf.empty else FAIL, "PERFORMANCE", _rows(perf), ">0 rows")

    if canvas.empty:
        add("TARGET_DEPENDENT_SPECTRAL_EMPTY", ALLOWED_EMPTY if spectral.empty else PASS, "FORMATION_RT", _rows(spectral), "empty allowed when no canvas candidates", "No-canvas is a physical outcome; an empty target-dependent RT table is not CASE corruption")
    else:
        add("TARGET_DEPENDENT_SPECTRAL_EVIDENCE", PASS if not spectral.empty else WARN, "FORMATION_RT", _rows(spectral), ">0 rows when canvas candidates exist", "May remain partial/missing optically, but evidence table should normally exist")

    # R5.7.26 Red-Light Availability / no-Canvas semantic closure.
    if not red_sum.empty:
        add("RED_LIGHT_REFERENCE_EVIDENCE_PRESENT", PASS if not red_ref.empty else FAIL, "RED_LIGHT_AVAILABILITY", _rows(red_ref), ">0 virtual reference-receiver rows", "Reference receivers are not Canvas and must not create Formation")
        separated_reference = {
            "red_light_cloud_evidence_state",
            "red_light_aerosol_evidence_state",
            "red_light_gas_evidence_state",
            "red_light_precipitation_evidence_state",
        }.issubset(red_ref.columns)
        separated_summary = {
            "primary_red_light_cloud_evidence_state",
            "extended_red_light_cloud_evidence_state",
            "primary_red_light_aerosol_evidence_state",
            "extended_red_light_aerosol_evidence_state",
        }.issubset(red_sum.columns)
        add(
            "RED_LIGHT_COMPONENT_EVIDENCE_SEPARATION",
            PASS if separated_reference and separated_summary else WARN,
            "RED_LIGHT_AVAILABILITY",
            f"reference={separated_reference};summary={separated_summary}",
            "cloud/aerosol/gas/precipitation evidence exported separately",
            "Cloud conflict must not hide aerosol temporal Missing, and aerosol Missing must not be mislabeled as cloud conflict",
        )
        if {"solar_altitude_deg","primary_canvas_count","extended_canvas_count","formation_context_state"}.issubset(red_sum.columns):
            no_canvas = red_sum[(pd.to_numeric(red_sum["primary_canvas_count"],errors="coerce").fillna(0)==0) & (pd.to_numeric(red_sum["extended_canvas_count"],errors="coerce").fillna(0)==0)]
            if not no_canvas.empty and not completeness.empty and {"solar_altitude_deg","layer","status"}.issubset(completeness.columns):
                bad=[]
                for a in pd.to_numeric(no_canvas["solar_altitude_deg"],errors="coerce").dropna().tolist():
                    q=completeness[(pd.to_numeric(completeness["solar_altitude_deg"],errors="coerce")-float(a)).abs()<=1e-9]
                    q=q[q["layer"].astype(str).eq("SPECTRAL_CLOUD_PATH")]
                    if q.empty or not q["status"].astype(str).eq("NOT_APPLICABLE").all():
                        bad.append(float(a))
                add("NO_CANVAS_CLOUD_PATH_NOT_APPLICABLE", PASS if not bad else FAIL, "FORMATION_RT", str(bad), "SPECTRAL_CLOUD_PATH=NOT_APPLICABLE for every no-Canvas angle", "Missing != Not Applicable")
            clear = no_canvas[no_canvas["formation_context_state"].astype(str).eq("CLEAR_RED_PATH_NO_CANVAS")]
            if not clear.empty and not headline.empty and {"solar_altitude_deg","operational_decision"}.issubset(headline.columns):
                mismatch=[]
                for a in pd.to_numeric(clear["solar_altitude_deg"],errors="coerce").dropna().tolist():
                    q=headline[(pd.to_numeric(headline["solar_altitude_deg"],errors="coerce")-float(a)).abs()<=1e-9]
                    if q.empty or not q["operational_decision"].astype(str).eq("CLEAR_RED_PATH_NO_CANVAS").all():
                        mismatch.append(float(a))
                add("CLEAR_RED_PATH_NO_CANVAS_SUMMARY_PROPAGATION", PASS if not mismatch else FAIL, "FORMATION_SUMMARY", str(mismatch), "headline summary preserves CLEAR_RED_PATH_NO_CANVAS", "Red-Light Availability != Firecloud Formation")
    else:
        add("RED_LIGHT_REFERENCE_EVIDENCE_PRESENT", WARN, "RED_LIGHT_AVAILABILITY", 0, "R5.7.26+ CASE exports reference-receiver evidence; legacy/minimal fixtures may omit it")

    # R5.7.25: the exported FULL_SPECTRAL_RT readiness must agree with the
    # Canvas-specific V1 Sun→CloudBase OpticalPathResult.  This detects the
    # regression where lower-level spectral voxels reported 100% Full RT while
    # upstream cloud blockers remained conflict/unknown in the V1 path table.
    if (not spectral.empty and not completeness.empty
            and {"solar_altitude_deg","direct_solar_fraction","critical_path_status"}.issubset(spectral.columns)
            and {"solar_altitude_deg","layer","completeness"}.issubset(completeness.columns)):
        diffs=[]; checked=0
        for angle,g in spectral.groupby("solar_altitude_deg",dropna=False):
            fs=pd.to_numeric(g["direct_solar_fraction"],errors="coerce").fillna(0.0)
            req=fs>0.0
            if not req.any():
                continue
            expected=float(g.loc[req,"critical_path_status"].astype(str).eq("FULL_RT").mean())
            cg=completeness[(pd.to_numeric(completeness["solar_altitude_deg"],errors="coerce")-float(angle)).abs()<=1e-9]
            cg=cg[cg["layer"].astype(str).eq("FULL_SPECTRAL_RT")]
            if cg.empty:
                diffs.append(1.0); continue
            observed=float(pd.to_numeric(cg["completeness"],errors="coerce").iloc[0])
            diffs.append(abs(observed-expected)); checked += 1
        maxdiff=max(diffs) if diffs else 0.0
        add("FULL_RT_COMPLETENESS_V1_PATH_CONSISTENCY", PASS if maxdiff<=1e-9 else FAIL, "FORMATION_RT", round(float(maxdiff),9), "<=1e-9 completeness difference", f"checked_angles={checked}; V1 OpticalPathResult is authoritative")
    else:
        add("FULL_RT_COMPLETENESS_V1_PATH_CONSISTENCY", WARN, "FORMATION_RT", "SCHEMA_NOT_AVAILABLE", "R5.7.25+ V1 path/completeness schema", "Legacy/minimal CASE may omit the required columns")

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
        "v1_viewing_precipitation_evidence.csv",
        "v1_viewing_spectral_extinction_550_750nm.csv",
        "v1_viewing_spectral_summary.csv",
        "v1_photography_decision.csv",
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
