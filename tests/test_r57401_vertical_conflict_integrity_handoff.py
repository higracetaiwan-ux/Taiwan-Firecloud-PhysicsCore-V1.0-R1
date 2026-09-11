from pathlib import Path

import pandas as pd

from firecloud.case_integrity import build_analysis_integrity_audit


def test_model_pre_integrity_handoff_includes_target_canvas_optical_evidence_once():
    root = Path(__file__).resolve().parents[1]
    model = (root / "firecloud" / "model.py").read_text(encoding="utf-8")
    start = model.index("_pre_integrity_result = {")
    end = model.index("analysis_integrity_audit = build_analysis_integrity_audit", start)
    handoff = model[start:end]
    assert handoff.count('"v1_target_canvas_optical_evidence"') == 1


def test_real_shape_conflict_cannot_fall_through_to_allowed_empty_when_qualification_exists():
    target = pd.DataFrame([
        {
            "canvas_id": "C1",
            "evidence_consistency": "CF_CLOUD_CONDENSATE_ZERO",
            "target_optical_truth_state": "DIRECT_EVIDENCE_CONFLICT",
        }
    ])
    qual = pd.DataFrame([
        {
            "canvas_id": "C1",
            "primary_conflict_pressure_hpa": 150.0,
            "primary_cloud_fraction": 0.04,
            "primary_total_condensate_kgkg": 0.0,
            "primary_evidence_consistency": "CF_CLOUD_CONDENSATE_ZERO",
            "below_primary_pressure_hpa": 200.0,
            "above_primary_pressure_hpa": 100.0,
            "below_supplement_pressure_hpa": 175.0,
            "above_supplement_pressure_hpa": 125.0,
            "below_supplement_condensate_state": "ZERO",
            "above_supplement_condensate_state": "ZERO",
            "vertical_conflict_qualification": "ISOLATED_PRIMARY_CF_SPIKE_HYDROMETEOR_UNSUPPORTED",
            "primary_source": "NOAA_GFS_PGRB2_0P25",
            "supplement_source": "NOAA_GFS_PGRB2B_0P25",
            "supplement_cloud_fraction_used": False,
            "rh_used_to_infer_condensate": False,
            "cot_promotion_allowed": False,
            "formation_promotion_allowed": False,
            "qualification_contract": "DIRECT_NATIVE_VERTICAL_CONTEXT;NO_COT_PROMOTION;NO_FORMATION_PROMOTION;NO_RH_CF_TO_CONDENSATE",
        }
    ])
    audit = build_analysis_integrity_audit({
        "canvas_optical_vertical_conflict_qualification_required": True,
        "v1_target_canvas_optical_evidence": target,
        "v1_canvas_vertical_conflict_qualification": qual,
        "v1_canvas_vertical_conflict_qualification_summary": pd.DataFrame([{"rows": 1}]),
        "gfs_canvas_optical_probe_request_audit": pd.DataFrame([{"action": "PROBE_RESULT", "status": "READY"}]),
    })
    row = audit.loc[audit["check_id"].eq("CANVAS_OPTICAL_VERTICAL_CONFLICT_QUALIFICATION")].iloc[0]
    assert row["status"] == "PASS"
    assert "expected_canvases=1" in str(row["observed"])
    assert "observed_canvases=1" in str(row["observed"])
