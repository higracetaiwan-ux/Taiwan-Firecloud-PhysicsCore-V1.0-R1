import pandas as pd

from firecloud.shadow_validation_collection import (
    SCIENCE_BASELINE_ID, PRODUCTION_COT_SOURCE, SHADOW_COT_SOURCE,
    build_case_manifest, build_cohort_summary, build_ground_truth_template,
    build_runtime_summary, build_collection_integrity_audit, merge_collection_audit,
)


def _result(promote=False, switch=False):
    mig = pd.DataFrame([
        {
            "shadow_candidate_eligible": True,
            "legacy_grid_cell_mean_cot": 0.5,
            "in_cloud_target_cot": 1.0,
            "cot_migration_delta": 0.5,
            "cot_migration_ratio": 2.0,
            "production_target_cot_source": PRODUCTION_COT_SOURCE,
            "shadow_candidate_cot_source": SHADOW_COT_SOURCE,
            "production_switch_performed": switch,
            "production_target_cot_replaced": switch,
            "cot_promotion_allowed": promote,
            "formation_promotion_allowed": promote,
        },
        {
            "shadow_candidate_eligible": False,
            "legacy_grid_cell_mean_cot": 0.25,
            "in_cloud_target_cot": 0.75,
            "cot_migration_delta": 0.5,
            "cot_migration_ratio": 3.0,
            "production_target_cot_source": PRODUCTION_COT_SOURCE,
            "shadow_candidate_cot_source": SHADOW_COT_SOURCE,
            "production_switch_performed": False,
            "production_target_cot_replaced": False,
            "cot_promotion_allowed": False,
            "formation_promotion_allowed": False,
        },
    ])
    return {
        "v1_canvas_cot_semantic_migration": mig,
        "gfs_native_request_audit": pd.DataFrame([
            {"gfs_run_utc":"2026-09-11T06:00:00+00:00", "gfs_forecast_hour":3},
            {"gfs_run_utc":"2026-09-11T06:00:00+00:00", "gfs_forecast_hour":6},
        ]),
        "runtime_execution_contract": pd.DataFrame([{
            "job_id":"12345678-abcd-ef00-1111-222233334444",
            "analysis_run_mode":"WARM_PRODUCTION",
            "provider_cache_reuse_allowed":True,
            "provider_cycle_resolution_frozen":True,
        }]),
        "summary": pd.DataFrame([{"event_timezone":"Asia/Taipei"}]),
        "analysis_integrity_audit": pd.DataFrame([{"check_id":"ANALYSIS_INTEGRITY_OVERALL","status":"PASS"}]),
        "performance_diagnostics": pd.DataFrame([{"stage":"TOTAL_ANALYSIS_CORE","elapsed_seconds":123.4}]),
    }


def _request(source="PRESET"):
    return {
        "lat":24.311902,"lon":120.549789,"day":"2026-09-11","event":"sunset",
        "site_id":"TWS106" if source == "PRESET" else "MANUAL",
        "site_name":"高美濕地" if source == "PRESET" else "自訂座標",
        "site_region":"中部" if source == "PRESET" else "",
        "site_county_area":"台中市" if source == "PRESET" else "",
        "site_event_suitability":"日落" if source == "PRESET" else "",
        "location_source":source,
        "scenic_spot_registry_version":"TAIWAN_DAWN_DUSK_SCENIC_SPOTS_V2.2_187" if source == "PRESET" else "",
    }


def test_manifest_and_cohort_have_stable_identity_and_provenance():
    result = _result()
    manifest = build_case_manifest(_request(), result, program_version="1.0.0-R5.7.41.3")
    row = manifest.iloc[0]
    assert row["shadow_validation_case_id"].startswith("SV-20260911-SUNSET-TWS106-12345678")
    assert row["science_baseline_id"] == SCIENCE_BASELINE_ID
    assert row["gfs_forecast_hours"] == "3;6"
    cohort = build_cohort_summary(_request(), result, program_version="1.0.0-R5.7.41.3")
    assert int(cohort.iloc[0]["target_count"]) == 2
    assert int(cohort.iloc[0]["shadow_candidate_eligible_count"]) == 1
    assert int(cohort.iloc[0]["production_switch_performed_count"]) == 0
    gt = build_ground_truth_template(manifest)
    assert gt.iloc[0]["ground_truth_status"] == "UNFILLED_TEMPLATE"
    runtime = build_runtime_summary(_request(), result, program_version="1.0.0-R5.7.41.3")
    assert float(runtime.iloc[0]["total_analysis_core_seconds"]) == 123.4


def test_collection_guard_passes_shadow_only_and_manual_location_is_allowed():
    result = _result()
    cm = build_case_manifest(_request("MANUAL"), result, program_version="1.0.0-R5.7.41.3")
    cohort = build_cohort_summary(_request("MANUAL"), result, program_version="1.0.0-R5.7.41.3")
    names = [
        "shadow_validation_case_manifest.csv","shadow_validation_cohort_summary.csv",
        "shadow_validation_ground_truth_template.csv","shadow_validation_runtime_summary.csv",
    ]
    archive_manifest = pd.DataFrame([{"artifact":n} for n in names])
    audit = build_collection_integrity_audit(archive_manifest, cm, cohort, result["v1_canvas_cot_semantic_migration"])
    assert set(audit["status"]) == {"PASS"}


def test_collection_guard_fails_if_production_switch_or_promotion_occurs():
    result = _result(promote=True, switch=True)
    cm = build_case_manifest(_request(), result, program_version="1.0.0-R5.7.41.3")
    cohort = build_cohort_summary(_request(), result, program_version="1.0.0-R5.7.41.3")
    archive_manifest = pd.DataFrame([{"artifact":n} for n in [
        "shadow_validation_case_manifest.csv","shadow_validation_cohort_summary.csv",
        "shadow_validation_ground_truth_template.csv","shadow_validation_runtime_summary.csv",
    ]])
    collection = build_collection_integrity_audit(archive_manifest, cm, cohort, result["v1_canvas_cot_semantic_migration"])
    by_id = collection.set_index("check_id")["status"].to_dict()
    assert by_id["SHADOW_COLLECTION_NO_PRODUCTION_SWITCH"] == "FAIL"
    assert by_id["SHADOW_COLLECTION_NO_PROMOTION"] == "FAIL"
    merged = merge_collection_audit(pd.DataFrame([{"check_id":"X","status":"PASS"}]), collection)
    overall = merged.loc[merged.check_id.eq("CASE_ARCHIVE_INTEGRITY_OVERALL"), "status"].iloc[0]
    assert overall == "FAIL"
