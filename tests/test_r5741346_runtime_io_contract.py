from pathlib import Path


def test_warm_dwd_cache_namespace_is_shared_and_cold_raw_cache_is_isolated():
    text = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
    assert 'provider_cache_shared' in text
    assert 'env["FIRECLOUD_DWD_ICON_CACHE_DIR"] = str(_shared_dwd_raw)' in text
    assert 'env["FIRECLOUD_DWD_ICON_CACHE_DIR"] = str(_provider_root / "dwd_icon")' in text
    assert 'FIRECLOUD_DWD_ICON_REMAP_DIR' in text


def test_aggregation_and_case_export_profile_stages_are_diagnostic_only():
    root = Path(__file__).resolve().parents[1]
    model = (root / "firecloud" / "model.py").read_text(encoding="utf-8")
    app = (root / "app.py").read_text(encoding="utf-8")
    for stage in [
        "AGGREGATION_TIMELINE_AND_GEOMETRY",
        "AGGREGATION_CLOUD_MATRIX_DRAIN",
        "AGGREGATION_SPECTRAL_ATMOS_MATRIX_DRAIN",
        "AGGREGATION_FORMATION_EVIDENCE",
        "AGGREGATION_VIEWING_AND_PHOTOGRAPHY",
        "AGGREGATION_TIER2_AND_CORE_SUMMARY",
        "AGGREGATION_COMPLETENESS_AND_DECISION",
        "AGGREGATION_SPECTRAL_COVERAGE_DIAGNOSTICS",
    ]:
        assert stage in model
    assert "R5741346_DIAGNOSTIC_PROFILE_ONLY" in model
    for stage in ["CASE_PRE_EXPORT_PREPARATION", "CASE_EXPORT_CSV_MEMBERS", "CASE_EXPORT_JSON_MEMBERS"]:
        assert stage in app
