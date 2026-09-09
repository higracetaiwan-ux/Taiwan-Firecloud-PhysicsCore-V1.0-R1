from pathlib import Path

import pandas as pd

from firecloud.photography_decision import build_photography_decision
from firecloud.case_integrity import (
    build_analysis_integrity_audit,
    build_archive_integrity_audit,
)


ANGLES = [0.0, -0.5, -1.0, -1.5, -2.0, -2.5, -3.0, -3.5, -4.0, -4.5, -5.0, -5.5, -6.0]


def _formation_13():
    rows = []
    for a in ANGLES:
        if a >= -4.5:
            state = "NO_CANVAS_RED_PATH_CONFLICT"
        elif a == -5.0:
            state = "NO_CANVAS_NO_DIRECT_RED_ACCESS"
        else:
            state = "NOT_FORMED_EARTH_SHADOW"
        rows.append({"time": f"t{a}", "solar_altitude_deg": a, "formation_state": state})
    return pd.DataFrame(rows)


def test_photography_decision_uses_full_formation_13_angle_timeline_when_viewing_has_two_rows():
    formation = _formation_13()
    viewing = pd.DataFrame([
        {"time":"t-5.5", "solar_altitude_deg":-5.5, "viewing_state":"VIEWING_MINOR_OBSTRUCTION"},
        {"time":"t-6.0", "solar_altitude_deg":-6.0, "viewing_state":"VIEWING_MINOR_OBSTRUCTION"},
    ])
    d = build_photography_decision(formation, viewing)
    assert len(d) == 13
    assert d["solar_altitude_deg"].tolist() == ANGLES
    assert set(d["photography_opportunity"]) == {"NO_GO"}
    assert d.loc[d.solar_altitude_deg.eq(-5.5), "viewing_state"].iloc[0] == "VIEWING_MINOR_OBSTRUCTION"
    assert d.loc[d.solar_altitude_deg.eq(0.0), "viewing_state"].iloc[0] == "VIEWING_NOT_APPLICABLE_NO_FORMED_TARGET"


def test_formation_earth_shadow_no_go_overrides_minor_viewing_fair():
    formation = pd.DataFrame([{"time":"t", "solar_altitude_deg":-5.5, "formation_state":"NOT_FORMED_EARTH_SHADOW"}])
    viewing = pd.DataFrame([{"time":"t", "solar_altitude_deg":-5.5, "viewing_state":"VIEWING_MINOR_OBSTRUCTION"}])
    d = build_photography_decision(formation, viewing)
    r = d.iloc[0]
    assert r["formation_gate_state"] == "FORMATION_HARD_NO_GO"
    assert r["photography_opportunity"] == "NO_GO"
    assert r["photography_outcome"] == "NO_FIRECLOUD_EARTH_SHADOW"
    assert r["viewing_state"] == "VIEWING_MINOR_OBSTRUCTION"
    assert r["viewing_decision_role"] == "DIAGNOSTIC_ONLY_FORMATION_NO_GO"


def test_clear_red_path_no_canvas_is_no_go_not_fair_even_with_good_viewing():
    formation = pd.DataFrame([{"time":"t", "solar_altitude_deg":-1.0, "formation_state":"CLEAR_RED_PATH_NO_CANVAS"}])
    viewing = pd.DataFrame([{"time":"t", "solar_altitude_deg":-1.0, "viewing_state":"VIEWING_GEOMETRY_GOOD"}])
    d = build_photography_decision(formation, viewing)
    r = d.iloc[0]
    assert r["photography_opportunity"] == "NO_GO"
    assert r["photography_outcome"] == "NO_FIRECLOUD_NO_CANVAS_RED_PATH_OPEN"


def test_no_canvas_evidence_is_not_silently_promoted_to_physical_no_go():
    formation = pd.DataFrame([{"time":"t", "solar_altitude_deg":-1.0, "formation_state":"NO_CANVAS_EVIDENCE"}])
    viewing = pd.DataFrame()
    d = build_photography_decision(formation, viewing)
    assert d.iloc[0]["formation_gate_state"] == "FORMATION_NOT_CONFIRMED"
    assert d.iloc[0]["photography_opportunity"] == "UNKNOWN"


def test_integrity_detects_sparse_photo_rows_and_viewing_override():
    formation = _formation_13()
    bad_photo = pd.DataFrame([
        {"solar_altitude_deg":-5.5, "formation_state":"NOT_FORMED_EARTH_SHADOW", "viewing_state":"VIEWING_MINOR_OBSTRUCTION", "photography_opportunity":"FAIR"},
        {"solar_altitude_deg":-6.0, "formation_state":"NOT_FORMED_EARTH_SHADOW", "viewing_state":"VIEWING_MINOR_OBSTRUCTION", "photography_opportunity":"FAIR"},
    ])
    result = {
        "v1_formation": formation,
        "v1_photography_decision": bad_photo,
        "v1_red_light_availability_summary": pd.DataFrame([{"solar_altitude_deg":0.0}]),
    }
    a = build_analysis_integrity_audit(result)
    cov = a[a.check_id.eq("PHOTOGRAPHY_DECISION_FORMATION_ANGLE_COVERAGE")].iloc[0]
    dom = a[a.check_id.eq("PHOTOGRAPHY_FORMATION_NO_GO_DOMINANCE")].iloc[0]
    assert cov.status == "FAIL"
    assert dom.status == "FAIL"


def test_integrity_passes_complete_formation_first_decision_table():
    formation = _formation_13()
    viewing = pd.DataFrame([
        {"time": "t-5.5", "solar_altitude_deg": -5.5, "viewing_state": "VIEWING_MINOR_OBSTRUCTION"},
        {"time": "t-6.0", "solar_altitude_deg": -6.0, "viewing_state": "VIEWING_MINOR_OBSTRUCTION"},
    ])
    photography = build_photography_decision(formation, viewing)
    audit = build_analysis_integrity_audit({
        "v1_formation": formation,
        "v1_photography_decision": photography,
        "v1_red_light_availability_summary": pd.DataFrame([{"solar_altitude_deg": 0.0}]),
    })
    assert audit.loc[
        audit.check_id.eq("PHOTOGRAPHY_DECISION_FORMATION_ANGLE_COVERAGE"), "status"
    ].iloc[0] == "PASS"
    assert audit.loc[
        audit.check_id.eq("PHOTOGRAPHY_FORMATION_NO_GO_DOMINANCE"), "status"
    ].iloc[0] == "PASS"


def test_model_hands_photography_decision_to_pre_export_integrity_audit():
    """Guard the production pipeline wiring, not only the audit helper."""
    model_text = (Path(__file__).resolve().parents[1] / "firecloud" / "model.py").read_text(encoding="utf-8")
    start = model_text.index("_pre_integrity_result = {")
    end = model_text.index("analysis_integrity_audit = build_analysis_integrity_audit", start)
    handoff = model_text[start:end]
    assert '"v1_photography_decision": v1_photography_decision' in handoff


def test_case_integrity_requires_photography_decision_member():
    required_names = [
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
    ]
    analysis = pd.DataFrame([{"check_id": "UPSTREAM", "status": "PASS"}])
    complete = pd.DataFrame({"artifact": required_names})
    complete_audit = build_archive_integrity_audit(complete, analysis)
    assert complete_audit.loc[
        complete_audit.check_id.eq("ARCHIVE_MEMBER::v1_photography_decision.csv"), "status"
    ].iloc[0] == "PASS"
    assert complete_audit.loc[
        complete_audit.check_id.eq("CASE_ARCHIVE_INTEGRITY_OVERALL"), "status"
    ].iloc[0] == "PASS"

    missing = complete[complete.artifact.ne("v1_photography_decision.csv")]
    missing_audit = build_archive_integrity_audit(missing, analysis)
    assert missing_audit.loc[
        missing_audit.check_id.eq("ARCHIVE_MEMBER::v1_photography_decision.csv"), "status"
    ].iloc[0] == "FAIL"
    assert missing_audit.loc[
        missing_audit.check_id.eq("CASE_ARCHIVE_INTEGRITY_OVERALL"), "status"
    ].iloc[0] == "FAIL"
