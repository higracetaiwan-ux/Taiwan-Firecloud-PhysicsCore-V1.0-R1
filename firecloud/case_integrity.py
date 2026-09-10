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
    gfs_canvas_probe_req = _df(result.get("gfs_canvas_optical_probe_request_audit"))
    gfs_canvas_probe = _df(result.get("v1_canvas_optical_native_probe"))
    gfs_canvas_probe_summary = _df(result.get("v1_canvas_optical_native_probe_summary"))
    canvas_vertical_conflict = _df(result.get("v1_canvas_vertical_conflict_qualification"))
    canvas_vertical_conflict_summary = _df(result.get("v1_canvas_vertical_conflict_qualification_summary"))
    target_canvas_optics = _df(result.get("v1_target_canvas_optical_evidence"))
    native_vox = _df(result.get("native_cloud_voxel_matrix"))
    gas = _df(result.get("gas_profile_route_snapshots"))
    ozone = _df(result.get("ozone_profile_route_snapshots"))
    cams_req = _df(result.get("cams_request_audit"))
    aerosol_spectral = _df(result.get("aerosol_spectral_route_snapshots"))
    formation = _df(result.get("v1_formation"))
    viewing_geometry = _df(result.get("v1_viewing_path_geometry"))
    viewing = _df(result.get("v1_viewing_summary"))
    viewing_spectral = _df(result.get("v1_viewing_spectral_extinction_550_750nm"))
    viewing_spectral_summary = _df(result.get("v1_viewing_spectral_summary"))
    viewing_precipitation = _df(result.get("v1_viewing_precipitation_evidence"))
    twilight_glow = _df(result.get("v1_twilight_glow_scattering_volume_550_750nm"))
    twilight_glow_sun_extinction = _df(result.get("v1_twilight_glow_sun_to_scatter_extinction_550_750nm"))
    twilight_glow_observer_extinction = _df(result.get("v1_twilight_glow_scatter_to_observer_extinction_550_750nm"))
    twilight_glow_single_scattering = _df(result.get("v1_twilight_glow_single_scattering_550_750nm"))
    twilight_glow_aerosol_scattering = _df(result.get("v1_twilight_glow_aerosol_scattering_550_750nm"))
    twilight_glow_summary = _df(result.get("v1_twilight_glow_summary"))
    twilight_glow_required = bool(result.get("twilight_glow_required", False))
    twilight_glow_extinction_phase1_required = bool(result.get("twilight_glow_extinction_phase1_required", False))
    twilight_glow_aerosol_scattering_phase1_required = bool(result.get("twilight_glow_aerosol_scattering_phase1_required", False))
    cams_geopotential_normalization_required = bool(result.get("cams_geopotential_normalization_required", False))
    twilight_glow_observer_aerosol_coverage_required = bool(result.get("twilight_glow_observer_aerosol_coverage_required", False))
    twilight_glow_deep_range_closure_required = bool(result.get("twilight_glow_deep_range_closure_required", False))
    near_surface_molecular_boundary_closure_required = bool(result.get("near_surface_molecular_boundary_closure_required", False))
    cams_post_success_download_recovery_required = bool(result.get("cams_post_success_download_recovery_required", False))
    canvas_optical_truth_pgrb2b_probe_required = bool(result.get("canvas_optical_truth_pgrb2b_probe_required", False))
    canvas_optical_vertical_conflict_qualification_required = bool(result.get("canvas_optical_vertical_conflict_qualification_required", False))
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

    # R5.7.39 Canvas Optical Truth Phase 1. The pgrb2b probe is evidence-only:
    # it may expose intermediate-level native condensate, but it must never
    # promote target COT/Formation in this release. Provider unavailability is
    # therefore visible WARN; a malformed/non-native evidence table is FAIL.
    if canvas_optical_truth_pgrb2b_probe_required:
        _probe_expected_contract = "DIRECT_NATIVE_PGRB2B_INTERMEDIATE_HYDROMETEOR_ONLY;NO_TARGET_COT_PROMOTION;NO_CF_RH_TO_COT"
        _probe_expected_source = "NOAA_GFS_0P25_PGRB2B_CANVAS_OPTICAL_PROBE"
        if gfs_canvas_probe.empty:
            _req_text = _join_text_columns(
                gfs_canvas_probe_req,
                [c for c in ["status", "action", "error", "probe_contract"] if c in gfs_canvas_probe_req.columns],
            ) if not gfs_canvas_probe_req.empty else pd.Series(dtype=str)
            _req_ready = bool(_req_text.str.upper().str.contains("READY|DOWNLOADED|CACHE_HIT", regex=True, na=False).any()) if len(_req_text) else False
            add(
                "CANVAS_OPTICAL_TRUTH_PGRB2B_PROBE_CONTRACT", WARN, "CANVAS_OPTICAL_TRUTH",
                f"probe_rows=0;request_rows={len(gfs_canvas_probe_req)};request_ready={_req_ready}",
                "diagnostic-only pgrb2b native intermediate-level evidence when available",
                "R5.7.39 probe unavailability/empty geometric overlap does not alter Formation or target COT; Missing remains visible",
            )
        else:
            required_cols = {
                "canvas_id", "cloud_layer_id", "probe_pressure_hpa", "probe_altitude_agl_km",
                "probe_cloud_liquid_water_kgkg", "probe_cloud_ice_water_kgkg",
                "probe_total_condensate_kgkg", "probe_condensate_state",
                "probe_evidence_consistency", "probe_positive_condensate",
                "probe_source", "probe_contract",
            }
            missing_cols = sorted(required_cols - set(gfs_canvas_probe.columns))
            prohibited_cols = sorted(set(gfs_canvas_probe.columns).intersection({
                "target_optics_ready", "target_cot_nominal", "target_cot",
                "formation_state", "formation_probability", "photography_outcome",
            }))
            source_ok = bool(gfs_canvas_probe.get("probe_source", pd.Series("", index=gfs_canvas_probe.index)).fillna("").astype(str).eq(_probe_expected_source).all())
            contract_ok = bool(gfs_canvas_probe.get("probe_contract", pd.Series("", index=gfs_canvas_probe.index)).fillna("").astype(str).eq(_probe_expected_contract).all())
            qt = pd.to_numeric(gfs_canvas_probe.get("probe_total_condensate_kgkg", pd.Series(float("nan"), index=gfs_canvas_probe.index)), errors="coerce")
            pos = gfs_canvas_probe.get("probe_positive_condensate", pd.Series(False, index=gfs_canvas_probe.index)).fillna(False).astype(bool)
            state = gfs_canvas_probe.get("probe_condensate_state", pd.Series("", index=gfs_canvas_probe.index)).fillna("").astype(str).str.upper()
            finite = qt.notna()
            numeric_ok = bool((((qt.ge(1e-7) == pos) & finite) | ~finite).all())
            missing_semantics_ok = bool((~state.eq("MISSING") | qt.isna()).all())
            schema_ok = not missing_cols and not prohibited_cols
            ok = schema_ok and source_ok and contract_ok and numeric_ok and missing_semantics_ok
            positive_rows = int(pos.sum())
            positive_canvases = int(gfs_canvas_probe.loc[pos, "canvas_id"].astype(str).nunique()) if "canvas_id" in gfs_canvas_probe.columns else 0
            add(
                "CANVAS_OPTICAL_TRUTH_PGRB2B_PROBE_CONTRACT", PASS if ok else FAIL, "CANVAS_OPTICAL_TRUTH",
                f"rows={len(gfs_canvas_probe)};positive_rows={positive_rows};positive_canvases={positive_canvases};missing_cols={len(missing_cols)};prohibited_cols={len(prohibited_cols)}",
                "direct-native pgrb2b evidence only; exact source/contract; no Formation/COT promotion; native condensate threshold consistency",
                (f"missing_cols={','.join(missing_cols)};prohibited_cols={','.join(prohibited_cols)};"
                 f"source_ok={source_ok};contract_ok={contract_ok};numeric_ok={numeric_ok};missing_semantics_ok={missing_semantics_ok}"),
            )
            if not gfs_canvas_probe_summary.empty:
                add(
                    "CANVAS_OPTICAL_TRUTH_PGRB2B_PROBE_SUMMARY", PASS, "CANVAS_OPTICAL_TRUTH",
                    len(gfs_canvas_probe_summary), ">0 summary rows when probe evidence exists",
                    "Summary is diagnostic-only and does not participate in Formation",
                )
            else:
                add(
                    "CANVAS_OPTICAL_TRUTH_PGRB2B_PROBE_SUMMARY", WARN, "CANVAS_OPTICAL_TRUTH",
                    0, ">0 summary rows when probe evidence exists",
                    "Probe evidence exists but diagnostic summary is absent",
                )

    # R5.7.40: qualify primary pgrb2 CF/native-condensate conflicts with the
    # immediate main pressure-level neighbours and pgrb2b intermediate native
    # hydrometeors. This remains diagnostic-only and is prohibited from
    # carrying COT/Formation promotion fields.
    if canvas_optical_vertical_conflict_qualification_required:
        _expected_conflict_canvases = set()
        if not target_canvas_optics.empty and "canvas_id" in target_canvas_optics.columns:
            _cons = target_canvas_optics.get("evidence_consistency", pd.Series("", index=target_canvas_optics.index)).fillna("").astype(str)
            _truth = target_canvas_optics.get("target_optical_truth_state", pd.Series("", index=target_canvas_optics.index)).fillna("").astype(str)
            _mask = _cons.eq("CF_CLOUD_CONDENSATE_ZERO") | _truth.eq("DIRECT_EVIDENCE_CONFLICT")
            _expected_conflict_canvases = set(target_canvas_optics.loc[_mask, "canvas_id"].astype(str))
        _probe_ready = False
        if not gfs_canvas_probe_req.empty:
            _pst = _join_text_columns(gfs_canvas_probe_req, [c for c in ["status","action"] if c in gfs_canvas_probe_req.columns]).str.upper()
            _probe_ready = bool(_pst.str.contains("READY|DOWNLOADED|CACHE_HIT", regex=True, na=False).any())
        if not _expected_conflict_canvases:
            add(
                "CANVAS_OPTICAL_VERTICAL_CONFLICT_QUALIFICATION", ALLOWED_EMPTY, "CANVAS_OPTICAL_TRUTH",
                0, "0 conflict canvases -> qualifier may be empty",
                "No primary CF/native-condensate conflict requires vertical qualification",
            )
        elif canvas_vertical_conflict.empty:
            add(
                "CANVAS_OPTICAL_VERTICAL_CONFLICT_QUALIFICATION", FAIL if _probe_ready else WARN, "CANVAS_OPTICAL_TRUTH",
                f"expected_conflict_canvases={len(_expected_conflict_canvases)};qualifier_rows=0;probe_ready={_probe_ready}",
                "all primary conflict canvases qualified when pgrb2b native probe is READY",
                "Empty qualifier is not evidence that condensate is zero; provider unavailability remains visible",
            )
        else:
            required_cols = {
                "canvas_id", "primary_conflict_pressure_hpa", "primary_cloud_fraction",
                "primary_total_condensate_kgkg", "primary_evidence_consistency",
                "below_primary_pressure_hpa", "above_primary_pressure_hpa",
                "below_supplement_pressure_hpa", "above_supplement_pressure_hpa",
                "below_supplement_condensate_state", "above_supplement_condensate_state",
                "vertical_conflict_qualification", "primary_source", "supplement_source",
                "supplement_cloud_fraction_used", "rh_used_to_infer_condensate",
                "cot_promotion_allowed", "formation_promotion_allowed", "qualification_contract",
            }
            missing_cols = sorted(required_cols - set(canvas_vertical_conflict.columns))
            prohibited_cols = sorted(set(canvas_vertical_conflict.columns).intersection({
                "target_cot", "target_cot_nominal", "target_optics_ready",
                "formation_state", "formation_probability", "photography_outcome",
            }))
            observed_canvases = set(canvas_vertical_conflict.get("canvas_id", pd.Series(dtype=str)).astype(str))
            coverage_ok = _expected_conflict_canvases.issubset(observed_canvases)
            primary_conflict_ok = bool(canvas_vertical_conflict.get("primary_evidence_consistency", pd.Series("", index=canvas_vertical_conflict.index)).fillna("").astype(str).eq("CF_CLOUD_CONDENSATE_ZERO").all())
            states = set(canvas_vertical_conflict.get("vertical_conflict_qualification", pd.Series(dtype=str)).dropna().astype(str))
            allowed_states = {
                "ISOLATED_PRIMARY_CF_SPIKE_HYDROMETEOR_UNSUPPORTED",
                "INTERMEDIATE_NATIVE_CONDENSATE_SUPPORT_PRESENT",
                "ADJACENT_PRIMARY_NATIVE_CONDENSATE_SUPPORT_PRESENT",
                "PRIMARY_CF_SIGNAL_WITH_ZERO_INTERMEDIATE_HYDROMETEORS",
                "VERTICAL_CONTEXT_INCOMPLETE",
            }
            state_ok = states.issubset(allowed_states) and bool(states)
            no_promotion = True
            for c in ["supplement_cloud_fraction_used","rh_used_to_infer_condensate","cot_promotion_allowed","formation_promotion_allowed"]:
                if c in canvas_vertical_conflict.columns:
                    no_promotion = no_promotion and bool((~canvas_vertical_conflict[c].fillna(False).astype(bool)).all())
            contract_ok = bool(canvas_vertical_conflict.get("qualification_contract", pd.Series("", index=canvas_vertical_conflict.index)).fillna("").astype(str).str.contains("NO_COT_PROMOTION;NO_FORMATION_PROMOTION;NO_RH_CF_TO_CONDENSATE", regex=False).all())
            ok = not missing_cols and not prohibited_cols and coverage_ok and primary_conflict_ok and state_ok and no_promotion and contract_ok
            add(
                "CANVAS_OPTICAL_VERTICAL_CONFLICT_QUALIFICATION", PASS if ok else FAIL, "CANVAS_OPTICAL_TRUTH",
                f"rows={len(canvas_vertical_conflict)};expected_canvases={len(_expected_conflict_canvases)};observed_canvases={len(observed_canvases)};states={','.join(sorted(states))}",
                "direct-native vertical context covers all primary conflicts; no COT/Formation promotion; no RH/CF->condensate",
                f"missing_cols={','.join(missing_cols)};prohibited_cols={','.join(prohibited_cols)};coverage_ok={coverage_ok};primary_conflict_ok={primary_conflict_ok};state_ok={state_ok};no_promotion={no_promotion};contract_ok={contract_ok}",
            )
            if not canvas_vertical_conflict_summary.empty:
                add(
                    "CANVAS_OPTICAL_VERTICAL_CONFLICT_SUMMARY", PASS, "CANVAS_OPTICAL_TRUTH",
                    len(canvas_vertical_conflict_summary), ">0 summary rows when vertical qualification exists",
                    "Summary remains diagnostic-only",
                )
            else:
                add(
                    "CANVAS_OPTICAL_VERTICAL_CONFLICT_SUMMARY", WARN, "CANVAS_OPTICAL_TRUTH",
                    0, ">0 summary rows when vertical qualification exists",
                    "Vertical qualification exists but summary is absent",
                )

    if not gfs_inv.empty and native_vox.empty:
        add("GFS_NATIVE_VOXEL_HANDOFF", FAIL, "NOAA_GFS_NATIVE", 0, ">0 native voxel rows when inventory decoded", "Inventory exists but reconstructed native voxel evidence vanished")
    elif not native_vox.empty:
        add("GFS_NATIVE_VOXEL_HANDOFF", PASS, "NOAA_GFS_NATIVE", _rows(native_vox), ">0 rows")

    o3_success = _cams_role_success(cams_req, ["O3_PRESSURE_LEVEL"])
    o3_missing_signal = _text_token_fraction(ozone, ["o3_quality"], "MISSING") > 0.95 or _text_token_fraction(gas, ["o3_quality", "gas_profile_source"], "O3_MISSING") > 0.95
    aerosol_missing_signal = False
    if not spectral.empty and "missing_components" in spectral.columns:
        aerosol_missing_signal = float(spectral["missing_components"].fillna("").astype(str).str.upper().str.contains("AEROSOL", regex=False).mean()) > 0.95
    cams_payload_expected = o3_missing_signal or aerosol_missing_signal or not ozone.empty or not aerosol_spectral.empty
    if cams_payload_expected:
        add("CAMS_REQUEST_AUDIT_PRESENT", PASS if not cams_req.empty else FAIL, "CAMS", _rows(cams_req), ">0 request-audit rows when CAMS-dependent payload is expected", "A blank request audit must not coexist silently with missing O3/aerosol payload")

    # R5.7.38: a terminal-successful ADS job has entered a distinct download
    # phase.  Fresh successful stateful requests must export bounded download
    # recovery telemetry; cache hits and jobs that never reached remote success
    # are not post-success download attempts and are excluded.
    if cams_post_success_download_recovery_required:
        if cams_req.empty:
            add(
                "CAMS_POST_SUCCESS_DOWNLOAD_RECOVERY_TELEMETRY", FAIL, "CAMS", 0,
                "fresh terminal-successful CAMS rows carry R5.7.38 download recovery telemetry",
                "Request audit is absent, so post-success download behavior cannot be verified",
            )
        else:
            remote_status = cams_req.get("ads_remote_status", pd.Series("", index=cams_req.index)).fillna("").astype(str).str.lower()
            request_id = cams_req.get("ads_request_id", pd.Series("", index=cams_req.index)).fillna("").astype(str).str.strip()
            cache_hit = cams_req.get("cache_hit", pd.Series(False, index=cams_req.index)).fillna(False).astype(bool)
            fresh_success = remote_status.isin({"successful", "succeeded", "completed", "complete"}) & request_id.ne("") & ~cache_hit
            scoped = cams_req.loc[fresh_success].copy()
            if scoped.empty:
                add(
                    "CAMS_POST_SUCCESS_DOWNLOAD_RECOVERY_TELEMETRY", WARN, "CAMS", 0,
                    "fresh terminal-successful CAMS rows when present",
                    "No fresh terminal-successful stateful CAMS download occurred in this run; cache/deferred paths cannot field-prove R5.7.38 download telemetry",
                )
            else:
                contract = scoped.get("ads_download_recovery_contract", pd.Series("", index=scoped.index)).fillna("").astype(str)
                attempts = pd.to_numeric(scoped.get("ads_download_attempts", pd.Series(float("nan"), index=scoped.index)), errors="coerce")
                retries = pd.to_numeric(scoped.get("ads_download_retry_count", pd.Series(float("nan"), index=scoped.index)), errors="coerce")
                refreshes = pd.to_numeric(scoped.get("ads_download_url_refresh_count", pd.Series(float("nan"), index=scoped.index)), errors="coerce")
                elapsed = pd.to_numeric(scoped.get("ads_download_elapsed_seconds", pd.Series(float("nan"), index=scoped.index)), errors="coerce")
                strategy = scoped.get("ads_download_strategy", pd.Series("", index=scoped.index)).fillna("").astype(str)
                contract_ok = contract.eq("R5.7.38_POST_SUCCESS_SAME_REQUEST_ID_BOUNDED_DOWNLOAD_RETRY_V1")
                numeric_ok = attempts.ge(1) & retries.ge(0) & elapsed.ge(0)
                strategy_ok = strategy.isin({"DIRECT_RESULTS_LOCATION_BOUNDED_RETRY_V1", "CLIENT_NATIVE_DOWNLOAD_FALLBACK_ONCE"})
                direct = strategy.eq("DIRECT_RESULTS_LOCATION_BOUNDED_RETRY_V1")
                direct_ok = (~direct) | refreshes.ge(attempts)
                ok = bool((contract_ok & numeric_ok & strategy_ok & direct_ok).all())
                retry_rows = int(retries.fillna(0).gt(0).sum())
                add(
                    "CAMS_POST_SUCCESS_DOWNLOAD_RECOVERY_TELEMETRY", PASS if ok else FAIL, "CAMS",
                    f"fresh_success={len(scoped)};retry_rows={retry_rows};contract={int(contract_ok.sum())}/{len(scoped)}",
                    "all fresh terminal-successful CAMS rows export bounded same-request-ID download recovery telemetry",
                    "Download URLs are intentionally not persisted; direct strategy must reacquire Results/location on every attempt",
                )

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

    # R5.7.32: CAMS `z` is geopotential. ecCodes may report units as
    # `m**2 s**-2`; treating those raw values as metres inflates pressure-level
    # height by ~g0 and causes false long-range aerosol path gaps.  Audit both
    # explicit decoder provenance and pressure-level plausibility.
    if cams_geopotential_normalization_required:
        if aerosol_spectral.empty:
            add("CAMS_GEOPOTENTIAL_HEIGHT_NORMALIZATION", WARN, "CAMS_AEROSOL", 0, "normalized CAMS aerosol payload when provider is available", "No aerosol snapshot: preserve provider missing rather than fabricating height")
        else:
            state = aerosol_spectral.get("cams_geopotential_height_normalization_state", pd.Series("", index=aerosol_spectral.index)).fillna("").astype(str)
            norm_ok = state.isin({"GEOPOTENTIAL_M2_S2_DIV_G0", "GEOPOTENTIAL_HEIGHT_METRES_DIRECT"})
            cols = [c for c in ["cams_geopotential_height_m_1000hPa", "cams_geopotential_height_m_500hPa", "cams_geopotential_height_m_30hPa"] if c in aerosol_spectral.columns]
            plausible = False
            detail = ""
            if len(cols) == 3:
                z1000 = pd.to_numeric(aerosol_spectral[cols[0]], errors="coerce")
                z500 = pd.to_numeric(aerosol_spectral[cols[1]], errors="coerce")
                z30 = pd.to_numeric(aerosol_spectral[cols[2]], errors="coerce")
                valid = z1000.notna() & z500.notna() & z30.notna()
                if valid.any():
                    med = (float(z1000[valid].median()), float(z500[valid].median()), float(z30[valid].median()))
                    ordered = float(((z1000[valid] < z500[valid]) & (z500[valid] < z30[valid])).mean())
                    plausible = (-1500.0 <= med[0] <= 3000.0 and 3000.0 <= med[1] <= 8000.0 and 15000.0 <= med[2] <= 35000.0 and ordered >= 0.95)
                    detail = f"median_m_1000={med[0]:.3f};500={med[1]:.3f};30={med[2]:.3f};ordered_fraction={ordered:.6f}"
            ok = bool(norm_ok.all()) and plausible
            add("CAMS_GEOPOTENTIAL_HEIGHT_NORMALIZATION", PASS if ok else FAIL, "CAMS_AEROSOL", f"provenance={float(norm_ok.mean()):.6f};{detail}", "recognized geopotential units normalized to metres and pressure-level heights physically plausible", "R5.7.32 fail-closes unknown geopotential units; m**2 s**-2 must be divided by g0")

        if twilight_glow_observer_aerosol_coverage_required and not twilight_glow_observer_extinction.empty:
            dist = pd.to_numeric(twilight_glow_observer_extinction.get("distance_km"), errors="coerce")
            long = twilight_glow_observer_extinction[dist.isin([60.0, 80.0, 100.0])].copy()
            if long.empty:
                add("TWILIGHT_GLOW_OBSERVER_AEROSOL_LONG_RANGE_COVERAGE", FAIL, "TWILIGHT_GLOW", 0, "60/80/100 km Glow observer targets present")
            else:
                # R5.7.33.1: readiness must follow the native 3-D aerosol chain,
                # not the column-AOD chain.  R5.7.28 permits a real adjacent-time
                # fallback for spectral column AOD only; that fallback must never
                # make a missing native aerext532 profile look provider-ready.
                native_cols = [c for c in aerosol_spectral.columns if c.startswith("cams_aerext532_m1_")]
                key_cols = [c for c in ("time", "solar_altitude_deg") if c in aerosol_spectral.columns and c in long.columns]
                ready_keys: set[tuple[str, float]] = set()
                if not aerosol_spectral.empty and native_cols and len(key_cols) == 2:
                    work = aerosol_spectral.copy()
                    work["__time_key"] = work["time"].astype(str)
                    work["__angle_key"] = pd.to_numeric(work["solar_altitude_deg"], errors="coerce").round(8)
                    for (t_key, a_key), grp in work.groupby(["__time_key", "__angle_key"], dropna=False):
                        if pd.isna(a_key):
                            continue
                        src = grp.get("cams_native_aerosol_source", pd.Series("", index=grp.index)).fillna("").astype(str).str.strip()
                        source_fraction = float(src.ne("").mean()) if len(src) else 0.0
                        native_fraction = _row_any_numeric_valid_fraction(grp, native_cols)
                        if source_fraction >= 0.95 and native_fraction >= 0.95:
                            ready_keys.add((str(t_key), float(a_key)))

                long["__time_key"] = long.get("time", pd.Series("", index=long.index)).astype(str)
                long["__angle_key"] = pd.to_numeric(long.get("solar_altitude_deg"), errors="coerce").round(8)
                native_ready = pd.Series(
                    [(str(t), float(a)) in ready_keys if pd.notna(a) else False for t, a in zip(long["__time_key"], long["__angle_key"])],
                    index=long.index,
                    dtype=bool,
                )
                required = long.loc[native_ready].copy()
                unavailable = int((~native_ready).sum())

                if required.empty:
                    add(
                        "TWILIGHT_GLOW_OBSERVER_AEROSOL_LONG_RANGE_COVERAGE",
                        WARN,
                        "TWILIGHT_GLOW",
                        f"provider_ready_targets=0/{len(long)};native_unavailable={unavailable}",
                        "evaluate six-band long-range aerosol coverage only where native CAMS 3-D aerosol evidence is ready",
                        "R5.7.33.1 keeps spectral-column fallback separate from native 3-D aerosol readiness; provider Missing remains Missing",
                    )
                else:
                    finite = pd.concat([
                        pd.to_numeric(required.get(f"glow_observer_tau_aerosol_{int(w)}nm"), errors="coerce").notna().rename(str(w))
                        for w in SIX_BAND_WAVELENGTHS_NM
                    ], axis=1).all(axis=1)
                    add(
                        "TWILIGHT_GLOW_OBSERVER_AEROSOL_LONG_RANGE_COVERAGE",
                        PASS if bool(finite.all()) else FAIL,
                        "TWILIGHT_GLOW",
                        f"resolved={int(finite.sum())}/{len(required)};native_unavailable={unavailable}/{len(long)}",
                        "all provider-ready 60/80/100 km targets have six-band aerosol optical depth; native-unavailable targets remain Missing",
                        "No route expansion or synthetic AOD; R5.7.28 spectral fallback does not promote a timed-out native 3-D aerosol chain",
                    )


    # R5.7.33: close the remaining deep-range molecular boundary touch while
    # preserving genuine cloud optical conflicts as Missing rather than clear.
    if twilight_glow_deep_range_closure_required:
        if twilight_glow_observer_extinction.empty:
            add(
                "TWILIGHT_GLOW_OBSERVER_DEEP_RANGE_MOLECULAR_COVERAGE",
                FAIL,
                "TWILIGHT_GLOW_EXTINCTION",
                0,
                "100 km Glow observer molecular rows present",
            )
            add(
                "TWILIGHT_GLOW_OBSERVER_CLOUD_CONFLICT_PRESERVATION",
                FAIL,
                "TWILIGHT_GLOW_EXTINCTION",
                0,
                "explicit cloud conflict/missing provenance with no Missing->zero promotion",
            )
        else:
            dist = pd.to_numeric(twilight_glow_observer_extinction.get("distance_km"), errors="coerce")
            deep = twilight_glow_observer_extinction[dist.eq(100.0)].copy()
            gas_ready = (
                not gas.empty
                and _row_any_numeric_valid_fraction(gas, ["temperature_k", "pressure_hpa"]) >= 0.95
            )
            if deep.empty:
                molecular_status = FAIL
                molecular_observed = "resolved=0/0"
            elif gas_ready:
                ray_ok = deep.get("glow_observer_rayleigh_status", pd.Series("", index=deep.index)).astype(str).eq("GLOW_OBSERVER_RAYLEIGH_PATH_RESOLVED")
                gas_ok = deep.get("glow_observer_gas_species_status", pd.Series("", index=deep.index)).astype(str).eq("GLOW_OBSERVER_GAS_PATH_RESOLVED")
                molecular_numeric = pd.Series(True, index=deep.index)
                for wavelength in SIX_BAND_WAVELENGTHS_NM:
                    w = int(wavelength)
                    for component in ("rayleigh", "gas_non_o3", "o3"):
                        molecular_numeric &= pd.to_numeric(
                            deep.get(
                                f"glow_observer_tau_{component}_{w}nm",
                                pd.Series(float("nan"), index=deep.index),
                            ),
                            errors="coerce",
                        ).notna()
                complete = ray_ok & gas_ok & molecular_numeric
                molecular_status = PASS if bool(complete.all()) else FAIL
                molecular_observed = f"resolved={int(complete.sum())}/{len(deep)};gas_profile_ready=true"
            else:
                molecular_status = WARN
                molecular_observed = f"targets={len(deep)};gas_profile_ready=false"
            add(
                "TWILIGHT_GLOW_OBSERVER_DEEP_RANGE_MOLECULAR_COVERAGE",
                molecular_status,
                "TWILIGHT_GLOW_EXTINCTION",
                molecular_observed,
                "all 100 km Glow observer Rayleigh and six-band gas-species paths resolve when real gas profiles are ready",
                "R5.7.33 reuses only the frozen <=10 m lowest-native pressure-profile boundary tolerance; no gas extrapolation",
            )

            cloud_state = twilight_glow_observer_extinction.get(
                "glow_observer_cloud_evidence_state",
                pd.Series("", index=twilight_glow_observer_extinction.index),
            ).fillna("").astype(str)
            conflict = cloud_state.eq("GLOW_OBSERVER_CLOUD_DIRECT_EVIDENCE_CONFLICT_PRESERVED")
            unresolved_missing = cloud_state.eq("GLOW_OBSERVER_CLOUD_OPTICS_UNRESOLVED_MISSING_PRESERVED")
            missing_components = twilight_glow_observer_extinction.get(
                "glow_observer_missing_components",
                pd.Series("", index=twilight_glow_observer_extinction.index),
            ).fillna("").astype(str)
            cloud_partial = missing_components.str.contains("CLOUD", regex=False)
            classified = ~cloud_partial | conflict | unresolved_missing
            promoted = pd.Series(False, index=twilight_glow_observer_extinction.index)
            for wavelength in SIX_BAND_WAVELENGTHS_NM:
                w = int(wavelength)
                tau = pd.to_numeric(
                    twilight_glow_observer_extinction.get(
                        f"glow_observer_tau_cloud_{w}nm",
                        pd.Series(float("nan"), index=twilight_glow_observer_extinction.index),
                    ),
                    errors="coerce",
                )
                band = twilight_glow_observer_extinction.get(
                    f"glow_observer_band_evidence_state_{w}nm",
                    pd.Series("", index=twilight_glow_observer_extinction.index),
                ).fillna("").astype(str)
                promoted |= (conflict | unresolved_missing) & (tau.notna() | band.eq("FULL"))
            provenance_cols = {
                "glow_observer_cloud_evidence_state",
                "glow_observer_cloud_unresolved_blocker_count",
                "glow_observer_cloud_conflict_blocker_count",
            }
            schema_ok = provenance_cols.issubset(twilight_glow_observer_extinction.columns)
            cloud_ok = schema_ok and bool(classified.all()) and not bool(promoted.any())
            add(
                "TWILIGHT_GLOW_OBSERVER_CLOUD_CONFLICT_PRESERVATION",
                PASS if cloud_ok else FAIL,
                "TWILIGHT_GLOW_EXTINCTION",
                f"conflict_preserved={int(conflict.sum())};missing_preserved={int(unresolved_missing.sum())};unclassified_partial={int((cloud_partial & ~classified).sum())};promoted={int(promoted.sum())}",
                "every unresolved cloud blocker is explicitly classified and no conflict/missing cloud tau is promoted to zero/full evidence",
                "DIRECT_EVIDENCE_CONFLICT remains Partial/Missing; R5.7.33 does not infer COT from cloud fraction or zero condensate",
            )


    # R5.7.37 Near-Surface Molecular Boundary Closure.  This is an evidence
    # bridge, not a wider endpoint extrapolation rule.  The frozen 10 m
    # tolerance remains exactly 0.01 km.
    if near_surface_molecular_boundary_closure_required:
        near_role_success = _cams_role_success(cams_req, ["O3_NEAR_SURFACE_MODEL_LEVEL_137"])
        near_state = gas.get("near_surface_boundary_state", pd.Series("", index=gas.index)).fillna("").astype(str) if not gas.empty else pd.Series(dtype=str)
        anchors = gas.loc[near_state.eq("READY")].copy() if not gas.empty else pd.DataFrame()
        if near_role_success:
            if anchors.empty:
                add(
                    "NEAR_SURFACE_MOLECULAR_BOUNDARY_ANCHOR_PROVENANCE", FAIL, "GAS_PROFILE", 0,
                    "CAMS ML137 request success must hand off evidence-complete near-surface anchors",
                    "Successful native near-surface O3 must not disappear before gas-profile construction",
                )
            else:
                alt = pd.to_numeric(anchors.get("altitude_agl_km"), errors="coerce")
                pres = pd.to_numeric(anchors.get("pressure_hpa"), errors="coerce")
                temp = pd.to_numeric(anchors.get("temperature_k"), errors="coerce")
                o3 = pd.to_numeric(anchors.get("o3_mass_mixing_ratio_kgkg"), errors="coerce")
                contract = anchors.get("near_surface_boundary_contract", pd.Series("", index=anchors.index)).fillna("").astype(str)
                quality = anchors.get("o3_quality", pd.Series("", index=anchors.index)).fillna("").astype(str)
                valid = (
                    alt.between(0.0, 0.05, inclusive="both") & pres.gt(0.0) & temp.gt(0.0) & o3.ge(0.0)
                    & contract.eq("R5.7.37_CAMS_ML137_SURFACE_THERMODYNAMIC_BOUNDARY_CLOSURE_V1")
                    & quality.eq("CAMS_MODEL_LEVEL_137_OZONE_NATIVE_NEAR_SURFACE_ANCHOR")
                )
                add(
                    "NEAR_SURFACE_MOLECULAR_BOUNDARY_ANCHOR_PROVENANCE",
                    PASS if bool(valid.all()) else FAIL, "GAS_PROFILE",
                    f"valid={int(valid.sum())}/{len(anchors)}",
                    "all ML137 anchors have native O3, surface thermodynamics, valid 0-50 m height and exact R5.7.37 provenance",
                    "No pressure-level O3 downward extrapolation and no synthetic ozone fallback",
                )
        else:
            add(
                "NEAR_SURFACE_MOLECULAR_BOUNDARY_ANCHOR_PROVENANCE", WARN, "GAS_PROFILE",
                f"near_surface_role_success=false;anchors={len(anchors)}",
                "native ML137 O3 request success plus anchors when provider is available",
                "Missing provider evidence remains Missing; deep-range molecular coverage still fail-closes when the bridge is required",
            )

        if twilight_glow_observer_extinction.empty:
            add(
                "NEAR_SURFACE_MOLECULAR_BOUNDARY_FROZEN_10M_TOLERANCE", WARN, "TWILIGHT_GLOW_EXTINCTION",
                "observer_table_empty", "observer export reports the frozen 0.01 km tolerance when present",
            )
            add(
                "NEAR_SURFACE_MOLECULAR_BOUNDARY_BRIDGE_PROVENANCE", NOT_APPLICABLE, "TWILIGHT_GLOW_EXTINCTION",
                "observer_table_empty", "bridge provenance evaluated when observer rows exist",
            )
        else:
            tol = pd.to_numeric(
                twilight_glow_observer_extinction.get(
                    "glow_observer_molecular_lowest_endpoint_tolerance_km",
                    pd.Series(float("nan"), index=twilight_glow_observer_extinction.index),
                ), errors="coerce"
            )
            tol_ok = tol.notna().all() and bool((tol.sub(0.01).abs() <= 1e-12).all())
            add(
                "NEAR_SURFACE_MOLECULAR_BOUNDARY_FROZEN_10M_TOLERANCE",
                PASS if tol_ok else FAIL, "TWILIGHT_GLOW_EXTINCTION",
                f"min={tol.min() if tol.notna().any() else 'nan'};max={tol.max() if tol.notna().any() else 'nan'}",
                "molecular lowest-endpoint tolerance remains exactly 0.01 km (10 m)",
                "R5.7.37 must close gaps with real ML137/surface evidence, never by widening tolerance",
            )

            bridge = pd.to_numeric(
                twilight_glow_observer_extinction.get(
                    "glow_observer_near_surface_boundary_bridge_segment_count",
                    pd.Series(0, index=twilight_glow_observer_extinction.index),
                ), errors="coerce"
            ).fillna(0).gt(0)
            if bridge.any():
                bridged = twilight_glow_observer_extinction.loc[bridge].copy()
                pressure_gap = pd.to_numeric(
                    bridged.get("glow_observer_pressure_level_only_raw_max_gap_km"), errors="coerce"
                )
                contract = bridged.get(
                    "glow_observer_near_surface_boundary_contract", pd.Series("", index=bridged.index)
                ).fillna("").astype(str)
                ray_ok = bridged.get("glow_observer_rayleigh_status", pd.Series("", index=bridged.index)).astype(str).eq("GLOW_OBSERVER_RAYLEIGH_PATH_RESOLVED")
                gas_ok = bridged.get("glow_observer_gas_species_status", pd.Series("", index=bridged.index)).astype(str).eq("GLOW_OBSERVER_GAS_PATH_RESOLVED")
                use_ok = (pressure_gap.gt(0.0) & contract.eq("R5.7.37_CAMS_ML137_SURFACE_THERMODYNAMIC_BOUNDARY_CLOSURE_V1") & ray_ok & gas_ok)
                add(
                    "NEAR_SURFACE_MOLECULAR_BOUNDARY_BRIDGE_PROVENANCE",
                    PASS if bool(use_ok.all()) else FAIL, "TWILIGHT_GLOW_EXTINCTION",
                    f"bridged_rows={len(bridged)};resolved={int(use_ok.sum())}",
                    "every used near-surface bridge preserves the former pressure-level-only gap and resolves Rayleigh+gas via exact R5.7.37 provenance",
                    "A genuine bracket closes the gap; endpoint tolerance remains independent",
                )
            else:
                add(
                    "NEAR_SURFACE_MOLECULAR_BOUNDARY_BRIDGE_PROVENANCE", NOT_APPLICABLE, "TWILIGHT_GLOW_EXTINCTION",
                    "bridged_rows=0", "bridge provenance is required only when an LOS sample falls below the lowest pressure-level anchor",
                )


    # R5.7.36 Formation Canvas eligibility: low cloud remains CloudScene blocker
    # evidence but must never be promoted into v1_canvas_candidates.
    if not canvas.empty:
        cb = pd.to_numeric(canvas.get("cloud_base_altitude_km", pd.Series(index=canvas.index, dtype=float)), errors="coerce")
        low_promoted = cb.notna() & (cb < 2.0 - 1e-12)
        explicit_eligible = canvas.get("formation_canvas_eligible", pd.Series(True, index=canvas.index)).fillna(False).astype(bool)
        role = canvas.get("formation_cloud_role", pd.Series("FORMATION_CANVAS_TARGET", index=canvas.index)).astype(str)
        bad_role = (~explicit_eligible) | (~role.eq("FORMATION_CANVAS_TARGET"))
        ok = not low_promoted.any() and not bad_role.any()
        add(
            "FORMATION_CANVAS_LOW_CLOUD_ROLE_SEPARATION",
            PASS if ok else FAIL,
            "FORMATION_CANVAS",
            f"rows={len(canvas)};below_2km_promoted={int(low_promoted.sum())};non_target_role={int(bad_role.sum())}",
            "v1_canvas_candidates contains only cloud-base >=2 km FORMATION_CANVAS_TARGET rows",
            "Low cloud remains in CloudScene and may still be an illumination/view blocker",
        )
    else:
        add(
            "FORMATION_CANVAS_LOW_CLOUD_ROLE_SEPARATION",
            ALLOWED_EMPTY,
            "FORMATION_CANVAS",
            "rows=0",
            "empty Canvas table is allowed when no eligible Formation Canvas exists",
            "No-Canvas is a physical outcome when cloud geometry is resolved",
        )

    add("FORMATION_TABLE_PRESENT", PASS if not formation.empty else FAIL, "FORMATION", _rows(formation), ">0 rows")
    add("VIEWING_SUMMARY_PRESENT", PASS if not viewing.empty else WARN, "VIEWING", _rows(viewing), ">0 rows when viewing targets exist")

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
            eligible_target_count=int(eligible.sum())
            if eligible_target_count == 0:
                # R5.7.35.2: native hydrometeor readiness is not, by itself, a
                # reason to require per-target precipitation evidence.  When
                # Viewing has no photographic targets, the empty table is a
                # physical Not-Applicable outcome rather than a spool-handoff
                # failure.  This does not weaken the non-empty requirement
                # when one or more eligible targets exist.
                add(
                    "VIEWING_NATIVE_HYDROMETEOR_HANDOFF",
                    NOT_APPLICABLE,
                    "VIEWING_PRECIPITATION",
                    f"gfs_ready={hydrometeor_ready};eligible_targets=0;rows={len(viewing_precipitation)}",
                    "native hydrometeor handoff is required only when eligible Viewing targets exist",
                    "Zero eligible Viewing targets -> precipitation evidence is correctly not applicable",
                )
            else:
                native_handoff_ok=(not viewing_precipitation.empty and precip_coverage_ok and not statuses.eq("VIEW_PRECIPITATION_VOLUME_UNRESOLVED").any())
                add(
                    "VIEWING_NATIVE_HYDROMETEOR_HANDOFF",
                    PASS if native_handoff_ok else FAIL,
                    "VIEWING_PRECIPITATION",
                    f"gfs_ready={hydrometeor_ready};eligible_targets={eligible_target_count};rows={len(viewing_precipitation)};volume_unresolved={int(statuses.eq('VIEW_PRECIPITATION_VOLUME_UNRESOLVED').sum())}",
                    "RWMR/SNMR/GRLE READY implies preserved per-target Viewing precipitation evidence when eligible targets exist",
                    "Runtime spool cleanup must occur only after viewing_route_snapshot drain",
                )
        else:
            add("VIEWING_NATIVE_HYDROMETEOR_HANDOFF",WARN,"VIEWING_PRECIPITATION",f"gfs_ready={hydrometeor_ready}","explicit provider gap or native hydrometeor evidence")
    else:
        if canvas.empty and not formation.empty:
            add("VIEWING_PRECIPITATION_TARGET_COVERAGE",NOT_APPLICABLE,"VIEWING_PRECIPITATION","eligible_targets=0;geometry_rows=0","no eligible Formation/Viewing target exists")
            add("VIEWING_NATIVE_HYDROMETEOR_HANDOFF",NOT_APPLICABLE,"VIEWING_PRECIPITATION",f"gfs_ready={hydrometeor_ready};eligible_targets=0","native hydrometeor handoff is not applicable without an eligible Viewing target")
        else:
            add("VIEWING_PRECIPITATION_TARGET_COVERAGE",WARN,"VIEWING_PRECIPITATION","GEOMETRY_SCHEMA_NOT_AVAILABLE","R5.7.29.1 viewing target geometry")
            add("VIEWING_NATIVE_HYDROMETEOR_HANDOFF",WARN,"VIEWING_PRECIPITATION",f"gfs_ready={hydrometeor_ready}","viewing geometry and provider evidence")

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

    # R5.7.30 independent Sun -> atmosphere -> observer Twilight Glow branch.
    # These checks constrain evidence coverage and arithmetic only.  They do
    # not introduce a Glow score, a photographic threshold, or a Formation
    # handoff.  Absolute sky radiance remains explicitly unresolved.
    if twilight_glow_required:
        def _time_angle_keys(df: pd.DataFrame) -> set[tuple[str, float | None]]:
            keys: set[tuple[str, float | None]] = set()
            if df.empty:
                return keys
            for _, row in df.iterrows():
                angle = pd.to_numeric(pd.Series([row.get("solar_altitude_deg")]), errors="coerce").iloc[0]
                keys.add((str(row.get("time")), None if pd.isna(angle) else round(float(angle), 8)))
            return keys

        expected_angles = _time_angle_keys(formation)
        observed_angles = _time_angle_keys(twilight_glow_summary)
        angle_diff = expected_angles.symmetric_difference(observed_angles)
        add(
            "TWILIGHT_GLOW_ANGLE_COVERAGE",
            PASS if expected_angles and not angle_diff else FAIL,
            "TWILIGHT_GLOW",
            f"expected={len(expected_angles)};observed={len(observed_angles)};difference={len(angle_diff)}",
            "same time-angle coverage as Formation",
            "Glow is an independent third branch but must retain the common 13-angle runtime timeline",
        )

        key_columns = {"time", "solar_altitude_deg", "glow_volume_id"}
        duplicate_count = -1
        if not twilight_glow.empty and key_columns.issubset(twilight_glow.columns):
            duplicate_count = int(twilight_glow.duplicated(list(key_columns), keep=False).sum())
        add(
            "TWILIGHT_GLOW_VOLUME_KEY_UNIQUENESS",
            PASS if duplicate_count == 0 else FAIL,
            "TWILIGHT_GLOW",
            duplicate_count,
            "0 duplicate time+angle+glow_volume_id rows",
            "Atmospheric receiver IDs repeat across angles and may not be treated as global keys",
        )

        required_status = {
            "glow_proxy_state", "glow_sun_path_state", "glow_observer_path_state",
            "glow_observer_rayleigh_status", "glow_missing_components",
            "glow_total_radiance_state", "calibrated_glow_radiance_available",
            "formation_independent", "viewing_independent", "twilight_glow_contract",
        }
        required_bands = {
            f"glow_{field}_{int(wavelength)}nm"
            for wavelength in SIX_BAND_WAVELENGTHS_NM
            for field in (
                "incident_relative_irradiance",
                "observer_nonrayleigh_tau",
                "observer_rayleigh_tau",
                "observer_total_tau",
                "observer_total_transmission",
                "rayleigh_scattering_coefficient_m1",
                "rayleigh_source_coefficient_m1_sr",
                "single_scattering_source_proxy",
                "band_evidence_state",
            )
        }
        missing_glow_columns = sorted((required_status | required_bands) - set(twilight_glow.columns))
        add(
            "TWILIGHT_GLOW_SIX_BAND_SCHEMA",
            PASS if not twilight_glow.empty and not missing_glow_columns else FAIL,
            "TWILIGHT_GLOW",
            str(missing_glow_columns),
            "six explicit incident/path/Rayleigh/source-proxy bands and evidence states",
        )

        inconsistent = 0
        if not twilight_glow.empty and not missing_glow_columns:
            full_states = {
                "GLOW_RAYLEIGH_SINGLE_SCATTERING_PROXY_READY",
                "GLOW_NO_DIRECT_SINGLE_SCATTERING_AT_VOLUME",
            }
            full_mask = twilight_glow["glow_proxy_state"].astype(str).isin(full_states)
            for _, row in twilight_glow.loc[full_mask].iterrows():
                for wavelength in SIX_BAND_WAVELENGTHS_NM:
                    incident = pd.to_numeric(pd.Series([row.get(f"glow_incident_relative_irradiance_{int(wavelength)}nm")]), errors="coerce").iloc[0]
                    total_tau = pd.to_numeric(pd.Series([row.get(f"glow_observer_total_tau_{int(wavelength)}nm")]), errors="coerce").iloc[0]
                    transmission = pd.to_numeric(pd.Series([row.get(f"glow_observer_total_transmission_{int(wavelength)}nm")]), errors="coerce").iloc[0]
                    coefficient = pd.to_numeric(pd.Series([row.get(f"glow_rayleigh_source_coefficient_m1_sr_{int(wavelength)}nm")]), errors="coerce").iloc[0]
                    source_proxy = pd.to_numeric(pd.Series([row.get(f"glow_single_scattering_source_proxy_{int(wavelength)}nm")]), errors="coerce").iloc[0]
                    if any(pd.isna(value) for value in (incident, total_tau, transmission, coefficient, source_proxy)):
                        inconsistent += 1
                    elif abs(float(transmission) - math.exp(-float(total_tau))) > 1e-9:
                        inconsistent += 1
                    elif abs(float(source_proxy) - max(0.0, float(incident)) * float(transmission) * float(coefficient)) > 1e-15:
                        inconsistent += 1
            nonfull_mask = ~full_mask
            for wavelength in SIX_BAND_WAVELENGTHS_NM:
                for field in ("observer_total_tau", "observer_total_transmission", "single_scattering_source_proxy"):
                    values = pd.to_numeric(twilight_glow.get(f"glow_{field}_{int(wavelength)}nm"), errors="coerce")
                    inconsistent += int((nonfull_mask & values.notna()).sum())
        add(
            "TWILIGHT_GLOW_NUMERIC_CLOSURE",
            PASS if not missing_glow_columns and inconsistent == 0 else FAIL,
            "TWILIGHT_GLOW",
            inconsistent,
            "0 arithmetic inconsistencies and 0 partial rows promoted to a final source proxy",
            "Missing evidence remains Missing; no fabricated extinction or source strength",
        )

        if twilight_glow_extinction_phase1_required:
            # R5.7.31 closes both six-band extinction legs explicitly.  Coverage
            # and arithmetic are verified on the exported evidence tables so CASE
            # consumers cannot silently lose a subset while the composite table
            # remains present.
            def _volume_keys(df: pd.DataFrame) -> set[tuple[str, float | None, str]]:
                keys: set[tuple[str, float | None, str]] = set()
                if df.empty:
                    return keys
                for _, row in df.iterrows():
                    angle = pd.to_numeric(pd.Series([row.get("solar_altitude_deg")]), errors="coerce").iloc[0]
                    keys.add((
                        str(row.get("time")),
                        None if pd.isna(angle) else round(float(angle), 8),
                        str(row.get("glow_volume_id")),
                    ))
                return keys

            expected_volume_keys = _volume_keys(twilight_glow)
            sun_volume_keys = _volume_keys(twilight_glow_sun_extinction)
            observer_volume_keys = _volume_keys(twilight_glow_observer_extinction)
            single_volume_keys = _volume_keys(twilight_glow_single_scattering)
            sun_diff = expected_volume_keys.symmetric_difference(sun_volume_keys)
            observer_diff = expected_volume_keys.symmetric_difference(observer_volume_keys)
            single_diff = expected_volume_keys.symmetric_difference(single_volume_keys)
            add(
                "TWILIGHT_GLOW_SUN_TO_SCATTER_TARGET_COVERAGE",
                PASS if expected_volume_keys and not sun_diff else FAIL,
                "TWILIGHT_GLOW_EXTINCTION",
                f"expected={len(expected_volume_keys)};observed={len(sun_volume_keys)};difference={len(sun_diff)}",
                "exact time+angle+glow-volume coverage",
            )
            add(
                "TWILIGHT_GLOW_SCATTER_TO_OBSERVER_TARGET_COVERAGE",
                PASS if expected_volume_keys and not observer_diff else FAIL,
                "TWILIGHT_GLOW_EXTINCTION",
                f"expected={len(expected_volume_keys)};observed={len(observer_volume_keys)};difference={len(observer_diff)}",
                "exact time+angle+glow-volume coverage",
            )

            sun_required = {
                "glow_sun_extinction_state", "glow_sun_missing_components",
                "twilight_glow_extinction_contract",
                *{f"glow_sun_{field}_{int(w)}nm" for w in SIX_BAND_WAVELENGTHS_NM for field in (
                    "tau_rayleigh", "tau_gas_non_o3", "tau_o3", "tau_aerosol",
                    "tau_cloud", "tau_precip", "tau_total", "transmission",
                    "incident_relative_irradiance", "reference_incident_relative_irradiance",
                    "band_evidence_state",
                )},
            }
            observer_required = {
                "glow_observer_extinction_state", "glow_observer_gas_species_status",
                "glow_observer_missing_components", "twilight_glow_extinction_contract",
                *{f"glow_observer_{field}_{int(w)}nm" for w in SIX_BAND_WAVELENGTHS_NM for field in (
                    "tau_rayleigh", "tau_gas_non_o3", "tau_o3", "tau_aerosol",
                    "tau_cloud", "tau_precip", "tau_total", "transmission",
                    "band_evidence_state",
                )},
            }
            single_required = {
                "glow_proxy_state", "glow_result_role", "calibrated_glow_radiance_available",
                "twilight_glow_single_scattering_contract",
                *{f"glow_{field}_{int(w)}nm" for w in SIX_BAND_WAVELENGTHS_NM for field in (
                    "sun_incident_relative_irradiance", "rayleigh_source_coefficient_m1_sr",
                    "observer_transmission", "single_scattering_source_proxy", "band_evidence_state",
                )},
            }
            phase1_missing_columns = sorted(
                (sun_required - set(twilight_glow_sun_extinction.columns))
                | (observer_required - set(twilight_glow_observer_extinction.columns))
                | (single_required - set(twilight_glow_single_scattering.columns))
            )
            add(
                "TWILIGHT_GLOW_SIX_BAND_EXTINCTION_SCHEMA",
                PASS if not phase1_missing_columns and not sun_diff and not observer_diff and not single_diff else FAIL,
                "TWILIGHT_GLOW_EXTINCTION",
                str(phase1_missing_columns),
                "six explicit component taus, total tau, transmission, and evidence states on both path legs",
            )

            sun_inconsistent = 0
            if not twilight_glow_sun_extinction.empty and not (sun_required - set(twilight_glow_sun_extinction.columns)):
                for _, row in twilight_glow_sun_extinction.iterrows():
                    fsun = pd.to_numeric(pd.Series([row.get("glow_direct_solar_fraction")]), errors="coerce").iloc[0]
                    for wavelength in SIX_BAND_WAVELENGTHS_NM:
                        w = int(wavelength)
                        state = str(row.get(f"glow_sun_band_evidence_state_{w}nm") or "")
                        components = [
                            pd.to_numeric(pd.Series([row.get(f"glow_sun_tau_{name}_{w}nm")]), errors="coerce").iloc[0]
                            for name in ("rayleigh", "gas_non_o3", "o3", "aerosol", "cloud", "precip")
                        ]
                        total = pd.to_numeric(pd.Series([row.get(f"glow_sun_tau_total_{w}nm")]), errors="coerce").iloc[0]
                        trans = pd.to_numeric(pd.Series([row.get(f"glow_sun_transmission_{w}nm")]), errors="coerce").iloc[0]
                        incident = pd.to_numeric(pd.Series([row.get(f"glow_sun_incident_relative_irradiance_{w}nm")]), errors="coerce").iloc[0]
                        reference_incident = pd.to_numeric(pd.Series([row.get(f"glow_sun_reference_incident_relative_irradiance_{w}nm")]), errors="coerce").iloc[0]
                        if state == "FULL":
                            if pd.isna(fsun) or any(pd.isna(v) for v in components) or any(pd.isna(v) for v in (total, trans, incident)):
                                sun_inconsistent += 1
                                continue
                            expected_total = sum(float(v) for v in components)
                            if abs(float(total) - expected_total) > 1e-9:
                                sun_inconsistent += 1
                            elif abs(float(trans) - math.exp(-float(total))) > 1e-9:
                                sun_inconsistent += 1
                            elif abs(float(incident) - max(0.0, float(fsun)) * float(trans)) > 1e-12:
                                sun_inconsistent += 1
                            elif not pd.isna(reference_incident) and abs(float(incident) - float(reference_incident)) > 1e-9:
                                sun_inconsistent += 1
                        elif any(not pd.isna(v) for v in (total, trans, incident)):
                            sun_inconsistent += 1
            add(
                "TWILIGHT_GLOW_SUN_PATH_NUMERIC_CLOSURE",
                PASS if not phase1_missing_columns and sun_inconsistent == 0 else FAIL,
                "TWILIGHT_GLOW_EXTINCTION",
                sun_inconsistent,
                "0 component-sum / exp(-tau) / Fsun*transmission inconsistencies; partial bands keep final values Missing",
            )

            observer_inconsistent = 0
            if not twilight_glow_observer_extinction.empty and not (observer_required - set(twilight_glow_observer_extinction.columns)):
                for _, row in twilight_glow_observer_extinction.iterrows():
                    for wavelength in SIX_BAND_WAVELENGTHS_NM:
                        w = int(wavelength)
                        state = str(row.get(f"glow_observer_band_evidence_state_{w}nm") or "")
                        components = [
                            pd.to_numeric(pd.Series([row.get(f"glow_observer_tau_{name}_{w}nm")]), errors="coerce").iloc[0]
                            for name in ("rayleigh", "gas_non_o3", "o3", "aerosol", "cloud", "precip")
                        ]
                        total = pd.to_numeric(pd.Series([row.get(f"glow_observer_tau_total_{w}nm")]), errors="coerce").iloc[0]
                        trans = pd.to_numeric(pd.Series([row.get(f"glow_observer_transmission_{w}nm")]), errors="coerce").iloc[0]
                        if state == "FULL":
                            if any(pd.isna(v) for v in components) or any(pd.isna(v) for v in (total, trans)):
                                observer_inconsistent += 1
                                continue
                            expected_total = sum(float(v) for v in components)
                            if abs(float(total) - expected_total) > 1e-9:
                                observer_inconsistent += 1
                            elif abs(float(trans) - math.exp(-float(total))) > 1e-9:
                                observer_inconsistent += 1
                        elif any(not pd.isna(v) for v in (total, trans)):
                            observer_inconsistent += 1
            add(
                "TWILIGHT_GLOW_OBSERVER_PATH_NUMERIC_CLOSURE",
                PASS if not phase1_missing_columns and observer_inconsistent == 0 else FAIL,
                "TWILIGHT_GLOW_EXTINCTION",
                observer_inconsistent,
                "0 component-sum / exp(-tau) inconsistencies; partial bands keep total/transmission Missing",
            )

            single_inconsistent = 0
            if not twilight_glow_single_scattering.empty and not (single_required - set(twilight_glow_single_scattering.columns)):
                full_states = {"FULL_RAYLEIGH_PROXY", "FULL_ZERO_DIRECT_SOLAR"}
                for _, row in twilight_glow_single_scattering.iterrows():
                    for wavelength in SIX_BAND_WAVELENGTHS_NM:
                        w = int(wavelength)
                        state = str(row.get(f"glow_band_evidence_state_{w}nm") or "")
                        incident = pd.to_numeric(pd.Series([row.get(f"glow_sun_incident_relative_irradiance_{w}nm")]), errors="coerce").iloc[0]
                        coeff = pd.to_numeric(pd.Series([row.get(f"glow_rayleigh_source_coefficient_m1_sr_{w}nm")]), errors="coerce").iloc[0]
                        trans = pd.to_numeric(pd.Series([row.get(f"glow_observer_transmission_{w}nm")]), errors="coerce").iloc[0]
                        proxy = pd.to_numeric(pd.Series([row.get(f"glow_single_scattering_source_proxy_{w}nm")]), errors="coerce").iloc[0]
                        if state in full_states:
                            if any(pd.isna(v) for v in (incident, coeff, trans, proxy)):
                                single_inconsistent += 1
                            elif abs(float(proxy) - max(0.0, float(incident)) * float(trans) * float(coeff)) > 1e-15:
                                single_inconsistent += 1
                        elif not pd.isna(proxy):
                            single_inconsistent += 1
            add(
                "TWILIGHT_GLOW_SINGLE_SCATTERING_NUMERIC_CLOSURE",
                PASS if not phase1_missing_columns and single_inconsistent == 0 else FAIL,
                "TWILIGHT_GLOW",
                single_inconsistent,
                "0 source-proxy inconsistencies and no partial band promoted to a final proxy",
            )

        else:
            add(
                "TWILIGHT_GLOW_FULL_EXTINCTION_PHASE1",
                NOT_APPLICABLE,
                "TWILIGHT_GLOW_EXTINCTION",
                "not required",
                "required beginning with R5.7.31",
            )

        if twilight_glow_aerosol_scattering_phase1_required:
            def _aero_volume_keys(df: pd.DataFrame):
                keys=set()
                if df is None or df.empty: return keys
                for _,r in df.iterrows():
                    a=pd.to_numeric(pd.Series([r.get("solar_altitude_deg")]),errors="coerce").iloc[0]
                    keys.add((str(r.get("time")),None if pd.isna(a) else round(float(a),8),str(r.get("glow_volume_id"))))
                return keys
            exp=_aero_volume_keys(twilight_glow); obs=_aero_volume_keys(twilight_glow_aerosol_scattering); diff=exp.symmetric_difference(obs)
            add("TWILIGHT_GLOW_AEROSOL_SCATTERING_TARGET_COVERAGE", PASS if exp and not diff else FAIL,
                "TWILIGHT_GLOW_AEROSOL_SCATTERING", f"expected={len(exp)};observed={len(obs)};difference={len(diff)}",
                "exact time+angle+glow-volume coverage")
            base_required={"glow_aerosol_scattering_state","glow_aerosol_scattering_contract","aerosol_phase_function_model",
                           "aerosol_vertical_property_contract","aerosol_local_extinction_532_m1","aerosol_aod532_anchor",
                           "calibrated_glow_radiance_available","glow_total_radiance_state","glow_aerosol_missing_components"}
            band_required={f"{name}_{int(w)}nm" for w in SIX_BAND_WAVELENGTHS_NM for name in (
                "aerosol_aod","aerosol_aod_provenance","aerosol_ssa","aerosol_ssa_provenance","aerosol_asymmetry_g",
                "aerosol_asymmetry_provenance","aerosol_hg_phase_function_sr","aerosol_extinction_coefficient_m1",
                "aerosol_scattering_coefficient_m1","aerosol_source_coefficient_m1_sr",
                "aerosol_single_scattering_source_proxy","rayleigh_plus_aerosol_source_proxy","aerosol_band_evidence_state")}
            missing_cols=sorted((base_required|band_required)-set(twilight_glow_aerosol_scattering.columns))
            add("TWILIGHT_GLOW_AEROSOL_SCATTERING_SCHEMA", PASS if not missing_cols and not diff else FAIL,
                "TWILIGHT_GLOW_AEROSOL_SCATTERING", str(missing_cols),
                "native 3D extinction + CAMS AOD/SSA/g + HG + six-band single-scattering proxy")
            bad=0; extrap=0; missing_reason_gaps=0
            if not twilight_glow_aerosol_scattering.empty and not missing_cols:
                for _,r in twilight_glow_aerosol_scattering.iterrows():
                    aerosol_state=str(r.get("glow_aerosol_scattering_state") or "")
                    missing_reason=str(r.get("glow_aerosol_missing_components") or "").strip()
                    if aerosol_state != "GLOW_AEROSOL_SINGLE_SCATTERING_PROXY_READY" and (not missing_reason or missing_reason.lower() in {"nan","none"}):
                        missing_reason_gaps += 1
                    beta532=pd.to_numeric(pd.Series([r.get("aerosol_local_extinction_532_m1")]),errors="coerce").iloc[0]
                    a532=pd.to_numeric(pd.Series([r.get("aerosol_aod532_anchor")]),errors="coerce").iloc[0]
                    for w in SIX_BAND_WAVELENGTHS_NM:
                        w=int(w); state=str(r.get(f"aerosol_band_evidence_state_{w}nm") or "")
                        provs=[str(r.get(f"aerosol_aod_provenance_{w}nm") or ""),str(r.get(f"aerosol_ssa_provenance_{w}nm") or ""),str(r.get(f"aerosol_asymmetry_provenance_{w}nm") or "")]
                        if any("EXTRAP" in x.upper() for x in provs): extrap+=1
                        vals={k:pd.to_numeric(pd.Series([r.get(f"{k}_{w}nm")]),errors="coerce").iloc[0] for k in (
                            "aerosol_aod","aerosol_ssa","aerosol_asymmetry_g","aerosol_hg_phase_function_sr",
                            "aerosol_extinction_coefficient_m1","aerosol_scattering_coefficient_m1","aerosol_source_coefficient_m1_sr",
                            "aerosol_single_scattering_source_proxy")}
                        if state=="FULL_AEROSOL_SINGLE_SCATTERING_PROXY":
                            if pd.isna(beta532) or pd.isna(a532) or float(a532)<=0 or any(pd.isna(v) for v in vals.values()): bad+=1; continue
                            ext=float(beta532)*float(vals["aerosol_aod"])/float(a532)
                            if abs(float(vals["aerosol_extinction_coefficient_m1"])-ext)>1e-12: bad+=1; continue
                            sca=float(vals["aerosol_extinction_coefficient_m1"])*float(vals["aerosol_ssa"])
                            if abs(float(vals["aerosol_scattering_coefficient_m1"])-sca)>1e-12: bad+=1; continue
                            src=float(vals["aerosol_scattering_coefficient_m1"])*float(vals["aerosol_hg_phase_function_sr"])
                            if abs(float(vals["aerosol_source_coefficient_m1_sr"])-src)>1e-12: bad+=1; continue
                        elif not pd.isna(vals["aerosol_single_scattering_source_proxy"]): bad+=1
            add("TWILIGHT_GLOW_AEROSOL_SCATTERING_NUMERIC_CLOSURE", PASS if not missing_cols and bad==0 else FAIL,
                "TWILIGHT_GLOW_AEROSOL_SCATTERING", bad, "0 beta_ext/beta_sca/HG/source inconsistencies and no partial proxy promotion")
            add("TWILIGHT_GLOW_AEROSOL_SCATTERING_PROVENANCE", PASS if not missing_cols and extrap==0 else FAIL,
                "TWILIGHT_GLOW_AEROSOL_SCATTERING", extrap, "0 extrapolated SSA/g/AOD provenance; exact or bounded-native only")
            add("TWILIGHT_GLOW_AEROSOL_SCATTERING_MISSING_REASON_COVERAGE", PASS if not missing_cols and missing_reason_gaps==0 else FAIL,
                "TWILIGHT_GLOW_AEROSOL_SCATTERING", missing_reason_gaps, "0 unresolved/partial aerosol rows without an explicit missing/conflict reason")

        forbidden = {
            column for column in twilight_glow.columns
            if any(token in column.lower() for token in ("formation_state", "photography_opportunity", "decision", "score"))
        }
        independence_ok = (
            not twilight_glow.empty
            and not forbidden
            and twilight_glow.get("formation_independent", pd.Series(False, index=twilight_glow.index)).fillna(False).astype(bool).all()
            and twilight_glow.get("viewing_independent", pd.Series(False, index=twilight_glow.index)).fillna(False).astype(bool).all()
        )
        add(
            "TWILIGHT_GLOW_BRANCH_INDEPENDENCE",
            PASS if independence_ok else FAIL,
            "TWILIGHT_GLOW",
            f"forbidden_columns={sorted(forbidden)}",
            "independent diagnostic flags true and no Formation/Photography decision fields",
        )

        no_radiance_claim = (
            not twilight_glow.empty
            and not twilight_glow.get("calibrated_glow_radiance_available", pd.Series(True, index=twilight_glow.index)).fillna(True).astype(bool).any()
            and twilight_glow.get("glow_total_radiance_state", pd.Series("", index=twilight_glow.index)).astype(str).eq(
                "NOT_RESOLVED_MULTIPLE_SCATTERING_AND_ABSOLUTE_CALIBRATION_REQUIRED"
            ).all()
        )
        add(
            "TWILIGHT_GLOW_NO_FALSE_RADIANCE_CLAIM",
            PASS if no_radiance_claim else FAIL,
            "TWILIGHT_GLOW",
            bool(no_radiance_claim),
            "calibrated radiance unavailable until multiple scattering and absolute radiometric calibration are resolved",
        )
    else:
        add(
            "TWILIGHT_GLOW_BRANCH",
            NOT_APPLICABLE,
            "TWILIGHT_GLOW",
            "not required",
            "required beginning with R5.7.30",
        )

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
        "v1_twilight_glow_scattering_volume_550_750nm.csv",
        "v1_twilight_glow_sun_to_scatter_extinction_550_750nm.csv",
        "v1_twilight_glow_scatter_to_observer_extinction_550_750nm.csv",
        "v1_twilight_glow_single_scattering_550_750nm.csv",
        "v1_twilight_glow_aerosol_scattering_550_750nm.csv",
        "v1_twilight_glow_summary.csv",
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
