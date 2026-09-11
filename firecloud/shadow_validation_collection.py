"""R5.7.41.3 Shadow Validation collection metadata and freeze guards.

Collection-only layer: it packages repeatable site identity, GFS-cycle provenance,
Shadow COT cohort metrics and a Ground Truth template without changing physics.
"""
from __future__ import annotations

import hashlib
import math
from typing import Any
import pandas as pd

COLLECTION_CONTRACT_VERSION = "R5.7.41.3"
SCIENCE_BASELINE_ID = "R5.7.41.2_SHADOW_COT_AB_FROZEN"
PRODUCTION_COT_SOURCE = "LEGACY_CF_SCALED_GRID_CELL_MEAN"
SHADOW_COT_SOURCE = "IN_CLOUD_EXACT_ENVELOPE_ASSUMED_REFF"
REQUIRED_COLLECTION_ARTIFACTS = {
    "shadow_validation_case_manifest.csv",
    "shadow_validation_cohort_summary.csv",
    "shadow_validation_ground_truth_template.csv",
    "shadow_validation_runtime_summary.csv",
}

PASS = "PASS"
FAIL = "FAIL"


def _frame(value: Any) -> pd.DataFrame:
    return value if isinstance(value, pd.DataFrame) else pd.DataFrame()


def _first(frame: pd.DataFrame, col: str, default: Any = "") -> Any:
    if frame.empty or col not in frame.columns:
        return default
    s = frame[col].dropna()
    return s.iloc[0] if not s.empty else default


def _case_id(request: dict, result: dict) -> str:
    day = str(request.get("day", "UNKNOWN")).replace("-", "")
    event = str(request.get("event", "event")).upper()
    site_id = str(request.get("site_id") or "MANUAL").upper()
    runtime = _frame(result.get("runtime_execution_contract"))
    job_id = str(_first(runtime, "job_id", ""))
    suffix = job_id.split("-")[0].upper() if job_id else hashlib.sha256(
        f"{day}|{event}|{site_id}|{request.get('lat')}|{request.get('lon')}".encode("utf-8")
    ).hexdigest()[:8].upper()
    return f"SV-{day}-{event}-{site_id}-{suffix}"


def build_case_manifest(request: dict, result: dict, *, program_version: str) -> pd.DataFrame:
    gfs = _frame(result.get("gfs_native_request_audit"))
    runtime = _frame(result.get("runtime_execution_contract"))
    summary = _frame(result.get("summary"))
    gfs_runs = []
    if "gfs_run_utc" in gfs.columns:
        gfs_runs = sorted({str(v) for v in gfs["gfs_run_utc"].dropna().tolist() if str(v)})
    fhrs = []
    if "gfs_forecast_hour" in gfs.columns:
        fhrs = sorted({int(float(v)) for v in pd.to_numeric(gfs["gfs_forecast_hour"], errors="coerce").dropna().tolist()})
    return pd.DataFrame([{
        "shadow_validation_case_id": _case_id(request, result),
        "collection_contract_version": COLLECTION_CONTRACT_VERSION,
        "science_baseline_id": SCIENCE_BASELINE_ID,
        "program_version": str(program_version),
        "event_date": str(request.get("day", "")),
        "event": str(request.get("event", "")),
        "site_id": str(request.get("site_id", "MANUAL")),
        "site_name": str(request.get("site_name", "自訂座標")),
        "site_region": str(request.get("site_region", "")),
        "site_county_area": str(request.get("site_county_area", "")),
        "site_event_suitability": str(request.get("site_event_suitability", "")),
        "location_source": str(request.get("location_source", "MANUAL")),
        "scenic_spot_registry_version": str(request.get("scenic_spot_registry_version", "")),
        "latitude": float(request.get("lat")),
        "longitude": float(request.get("lon")),
        "event_timezone": str(_first(summary, "event_timezone", request.get("tz_name", ""))),
        "gfs_run_utc": ";".join(gfs_runs),
        "gfs_forecast_hours": ";".join(str(x) for x in fhrs),
        "analysis_job_id": str(_first(runtime, "job_id", "")),
        "analysis_run_mode": str(_first(runtime, "analysis_run_mode", request.get("requested_runtime_mode", ""))),
        "provider_cycle_resolution_frozen": bool(_first(runtime, "provider_cycle_resolution_frozen", False)),
        "production_cot_source_expected": PRODUCTION_COT_SOURCE,
        "shadow_cot_source_expected": SHADOW_COT_SOURCE,
        "collection_note": "SHADOW_VALIDATION_COLLECTION_ONLY;NO_SCIENCE_CHANGE",
    }])


def build_cohort_summary(request: dict, result: dict, *, program_version: str) -> pd.DataFrame:
    migration = _frame(result.get("v1_canvas_cot_semantic_migration"))
    manifest = build_case_manifest(request, result, program_version=program_version)
    analysis = _frame(result.get("analysis_integrity_audit"))
    total = int(len(migration))
    eligible = int(migration.get("shadow_candidate_eligible", pd.Series(dtype=bool)).fillna(False).astype(bool).sum()) if total else 0
    legacy = pd.to_numeric(migration.get("legacy_grid_cell_mean_cot", pd.Series(dtype=float)), errors="coerce")
    shadow = pd.to_numeric(migration.get("in_cloud_target_cot", pd.Series(dtype=float)), errors="coerce")
    ratio = pd.to_numeric(migration.get("cot_migration_ratio", pd.Series(dtype=float)), errors="coerce")
    delta = pd.to_numeric(migration.get("cot_migration_delta", pd.Series(dtype=float)), errors="coerce")
    def nmean(s):
        s=s.dropna(); return float(s.mean()) if not s.empty else float("nan")
    def nmedian(s):
        s=s.dropna(); return float(s.median()) if not s.empty else float("nan")
    def bcount(col):
        if col not in migration.columns: return 0
        return int(migration[col].fillna(False).astype(bool).sum())
    overall = analysis.loc[analysis.get("check_id", pd.Series(dtype=str)).astype(str).eq("ANALYSIS_INTEGRITY_OVERALL"), "status"] if not analysis.empty else pd.Series(dtype=str)
    base = manifest.iloc[0].to_dict()
    return pd.DataFrame([{**base,
        "target_count": total,
        "shadow_candidate_eligible_count": eligible,
        "shadow_candidate_ineligible_count": total - eligible,
        "eligible_fraction": (eligible / total) if total else float("nan"),
        "mean_legacy_grid_cell_mean_cot": nmean(legacy),
        "mean_in_cloud_target_cot": nmean(shadow),
        "mean_cot_migration_delta": nmean(delta),
        "median_cot_migration_ratio": nmedian(ratio),
        "production_switch_performed_count": bcount("production_switch_performed"),
        "production_target_cot_replaced_count": bcount("production_target_cot_replaced"),
        "cot_promotion_allowed_count": bcount("cot_promotion_allowed"),
        "formation_promotion_allowed_count": bcount("formation_promotion_allowed"),
        "analysis_integrity_overall": str(overall.iloc[-1]) if not overall.empty else "UNKNOWN",
    }])


def build_ground_truth_template(manifest: pd.DataFrame) -> pd.DataFrame:
    base = manifest.iloc[0].to_dict() if not manifest.empty else {}
    return pd.DataFrame([{
        "shadow_validation_case_id": base.get("shadow_validation_case_id", ""),
        "site_id": base.get("site_id", ""),
        "site_name": base.get("site_name", ""),
        "event_date": base.get("event_date", ""),
        "event": base.get("event", ""),
        "actual_firecloud_strength": "",
        "observed_canvas_type": "",
        "viewing_quality": "",
        "photo_reference": "",
        "observer_notes": "",
        "allowed_actual_firecloud_strength": "NONE|WEAK|MODERATE|STRONG|EXTREME|UNKNOWN",
        "allowed_observed_canvas_type": "NO_CANVAS|THIN_HIGH_CLOUD|MID_CLOUD_AC_CC|HIGH_CLOUD|MULTILAYER|OTHER|UNKNOWN",
        "allowed_viewing_quality": "CLEAR|MINOR_OBSTRUCTION|MAJOR_OBSTRUCTION|UNKNOWN",
        "ground_truth_status": "UNFILLED_TEMPLATE",
    }])


def build_runtime_summary(request: dict, result: dict, *, program_version: str) -> pd.DataFrame:
    manifest = build_case_manifest(request, result, program_version=program_version)
    perf = _frame(result.get("performance_diagnostics"))
    runtime = _frame(result.get("runtime_execution_contract"))
    def stage_seconds(name: str) -> float:
        if perf.empty or "stage" not in perf.columns or "elapsed_seconds" not in perf.columns:
            return float("nan")
        rows = perf[perf["stage"].astype(str).eq(name)]
        vals = pd.to_numeric(rows["elapsed_seconds"], errors="coerce").dropna()
        return float(vals.iloc[-1]) if not vals.empty else float("nan")
    base=manifest.iloc[0].to_dict()
    return pd.DataFrame([{**base,
        "total_analysis_core_seconds": stage_seconds("TOTAL_ANALYSIS_CORE"),
        "analysis_run_mode": str(_first(runtime, "analysis_run_mode", request.get("requested_runtime_mode", ""))),
        "provider_cache_reuse_allowed": bool(_first(runtime, "provider_cache_reuse_allowed", False)),
        "provider_cycle_resolution_frozen": bool(_first(runtime, "provider_cycle_resolution_frozen", False)),
        "runtime_monitoring_only": True,
    }])


def build_collection_integrity_audit(archive_manifest: pd.DataFrame, case_manifest: pd.DataFrame, cohort: pd.DataFrame, migration: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    names = set(archive_manifest.get("artifact", pd.Series(dtype=str)).astype(str)) if not archive_manifest.empty else set()
    for name in sorted(REQUIRED_COLLECTION_ARTIFACTS):
        rows.append({"check_id": f"SHADOW_COLLECTION_MEMBER::{name}", "status": PASS if name in names else FAIL,
                     "component":"SHADOW_VALIDATION_COLLECTION", "observed":name in names, "expected":"member present",
                     "detail":"R5.7.41.3 collection artifact"})
    cm = case_manifest.iloc[0].to_dict() if not case_manifest.empty else {}
    rows.append({"check_id":"SHADOW_COLLECTION_BASELINE_FROZEN", "status":PASS if cm.get("science_baseline_id")==SCIENCE_BASELINE_ID else FAIL,
                 "component":"SHADOW_VALIDATION_COLLECTION","observed":cm.get("science_baseline_id"),"expected":SCIENCE_BASELINE_ID,
                 "detail":"Cohort science contract must remain frozen during collection."})
    location_source=str(cm.get("location_source", "")).upper()
    location_ok = bool(cm.get("shadow_validation_case_id")) and math.isfinite(float(cm.get("latitude"))) and math.isfinite(float(cm.get("longitude")))
    if location_source == "PRESET":
        location_ok = location_ok and bool(cm.get("site_id")) and bool(cm.get("site_name")) and bool(cm.get("scenic_spot_registry_version"))
    rows.append({"check_id":"SHADOW_COLLECTION_LOCATION_IDENTITY", "status":PASS if location_ok else FAIL,
                 "component":"SHADOW_VALIDATION_COLLECTION","observed":f"{location_source}:{cm.get('site_id')}:{cm.get('site_name')}",
                 "expected":"stable preset identity or explicit manual coordinates", "detail":"Repeat CASE comparisons require stable location provenance."})
    if migration.empty:
        no_switch = no_promote = False
        production_source_ok = False
    else:
        no_switch = not migration.get("production_switch_performed", pd.Series([True]*len(migration))).fillna(True).astype(bool).any()
        no_promote = not migration.get("cot_promotion_allowed", pd.Series([True]*len(migration))).fillna(True).astype(bool).any() and not migration.get("formation_promotion_allowed", pd.Series([True]*len(migration))).fillna(True).astype(bool).any()
        sources = set(migration.get("production_target_cot_source", pd.Series(dtype=str)).dropna().astype(str))
        production_source_ok = sources == {PRODUCTION_COT_SOURCE}
    for cid, ok, observed, expected, detail in [
        ("SHADOW_COLLECTION_NO_PRODUCTION_SWITCH", no_switch, no_switch, True, "Collection version must remain Shadow-only."),
        ("SHADOW_COLLECTION_NO_PROMOTION", no_promote, no_promote, True, "COT/Formation promotion remains prohibited during cohort collection."),
        ("SHADOW_COLLECTION_PRODUCTION_SOURCE_FROZEN", production_source_ok, sorted(set(migration.get('production_target_cot_source', pd.Series(dtype=str)).dropna().astype(str))) if not migration.empty else [], [PRODUCTION_COT_SOURCE], "Legacy production COT source stays frozen for A/B comparability."),
    ]:
        rows.append({"check_id":cid,"status":PASS if ok else FAIL,"component":"SHADOW_VALIDATION_COLLECTION","observed":observed,"expected":expected,"detail":detail})
    return pd.DataFrame(rows)


def merge_collection_audit(case_audit: pd.DataFrame, collection_audit: pd.DataFrame) -> pd.DataFrame:
    base = _frame(case_audit).copy()
    if not base.empty and "check_id" in base.columns:
        base = base[~base["check_id"].astype(str).eq("CASE_ARCHIVE_INTEGRITY_OVERALL")].copy()
    merged = pd.concat([base, collection_audit], ignore_index=True, sort=False)
    hard_fail = int(merged.get("status", pd.Series(dtype=str)).astype(str).eq(FAIL).sum())
    overall = pd.DataFrame([{"check_id":"CASE_ARCHIVE_INTEGRITY_OVERALL", "status":FAIL if hard_fail else PASS,
                             "component":"OVERALL","observed":hard_fail,"expected":"0 hard failures",
                             "detail":"Archive + R5.7.41.3 Shadow collection integrity."}])
    return pd.concat([merged, overall], ignore_index=True, sort=False)
