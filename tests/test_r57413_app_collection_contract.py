from pathlib import Path


def test_app_wires_shared_spot_selector_and_collection_exports():
    text = Path("app.py").read_text(encoding="utf-8")
    for token in [
        '"景點選單"', '"自訂座標"', '"site_id": str(site_id)',
        '"scenic_spot_registry_version"', '"shadow_validation_case_manifest.csv"',
        '"shadow_validation_cohort_summary.csv"', '"shadow_validation_ground_truth_template.csv"',
        '"shadow_validation_runtime_summary.csv"', '"analysis_request.json"',
    ]:
        assert token in text
