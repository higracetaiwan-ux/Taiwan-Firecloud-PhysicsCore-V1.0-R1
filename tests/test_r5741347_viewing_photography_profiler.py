from pathlib import Path

import firecloud


EXPECTED_COMPONENT_STAGES = {
    "VIEWING_COMPONENT_PATH_GEOMETRY",
    "VIEWING_COMPONENT_PRECIPITATION_EVIDENCE",
    "VIEWING_COMPONENT_TARGET_OPTICS_RECONCILIATION",
    "VIEWING_COMPONENT_PREPARE_SPECTRAL_RUNTIME_CONTEXT",
    "VIEWING_COMPONENT_SPECTRAL_EXTINCTION",
    "VIEWING_COMPONENT_SPECTRAL_SUMMARY",
    "VIEWING_COMPONENT_ATTACH_SPECTRAL_STATUS",
    "VIEWING_COMPONENT_PATH_SUMMARY",
    "VIEWING_COMPONENT_PHOTOGRAPHY_DECISION",
}


def _model_source():
    return (Path(__file__).resolve().parents[1] / "firecloud" / "model.py").read_text(encoding="utf-8")


def test_version_is_r5741347():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.2"


def test_all_nine_viewing_photography_component_stages_are_present():
    src = _model_source()
    for stage in EXPECTED_COMPONENT_STAGES:
        assert f'"{stage}"' in src


def test_component_profiler_is_explicitly_diagnostic_only():
    src = _model_source()
    assert "R5741347_COMPONENT_PROFILE_ONLY" in src
    assert "AGGREGATION_VIEWING_AND_PHOTOGRAPHY" in src
    assert "excluding Glow" in src


def test_r5741346_aggregation_stage_decomposition_is_retained():
    src = _model_source()
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
        assert f'"{stage}"' in src
