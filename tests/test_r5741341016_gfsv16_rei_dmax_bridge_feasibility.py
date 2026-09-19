from pathlib import Path

import pandas as pd
import firecloud

from firecloud.case_integrity import build_analysis_integrity_audit, build_archive_integrity_audit, PASS, FAIL
from firecloud.ice_microphysics_gfsv16_rei_dmax_bridge import (
    SCIENCE_BASELINE,
    STEP3C_MODE,
    build_gfsv16_rei_dmax_bridge_evidence,
    build_gfsv16_rei_dmax_bridge_gate,
    gfsv16_rei_dmax_bridge_contract_payload,
)

EVIDENCE = "ice_microphysics_gfsv16_rei_dmax_bridge_evidence.csv"
GATE = "ice_microphysics_gfsv16_rei_dmax_bridge_gate.csv"
CONTRACT = "ice_microphysics_gfsv16_rei_dmax_bridge_contract.json"


def test_release_and_step3c_mode():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.30.12"
    assert SCIENCE_BASELINE == "R5.7.41.2_SHADOW_COT_AB_FROZEN"
    assert STEP3C_MODE == "GFSV16_REI_DMAX_BRIDGE_FEASIBILITY_AUDIT_ONLY"


def test_evidence_records_source_documentation_mismatch_and_bulk_semantics():
    ev = build_gfsv16_rei_dmax_bridge_evidence().set_index("evidence_id")
    assert ev.loc["GFSV16_REIFLAG2_SOURCE_FORMULA", "pin_status"] == "PINNED_WYSER_BULK_REI_FORMULA"
    assert ev.loc["REIFLAG2_DOCUMENTATION_SOURCE_LABEL_CONSISTENCY", "pin_status"] == "MISMATCH"
    assert ev.loc["WYSER_REI_BULK_SEMANTIC", "semantic_role"] == "BULK_EFFECTIVE_RADIUS_NOT_SINGLE_PARTICLE_DIMENSION"
    assert ev.loc["YANG_BI_PRIMARY_SIZE_AXIS", "value"] == "maximum_dimension_um"
    assert ev.loc["DIRECT_REI_TO_DMAX_ONE_TO_ONE_BRIDGE", "pin_status"] == "REJECTED_SEMANTIC_MISMATCH"
    assert ev.loc["BULK_YANG_BI_PSD_INTEGRATION_PATH", "pin_status"] == "IDENTIFIED_NOT_QUALIFIED"


def test_gate_rejects_direct_dmax_but_identifies_bulk_psd_path():
    g = build_gfsv16_rei_dmax_bridge_gate().iloc[0]
    assert bool(g["GFSV16_REIFLAG2_SOURCE_FORMULA_PINNED"])
    assert not bool(g["REIFLAG2_DOCUMENTATION_LABEL_CONSISTENT"])
    assert bool(g["GFDL_REI_IS_BULK_EFFECTIVE_RADIUS"])
    assert bool(g["YANG_BI_SIZE_AXIS_IS_MAXIMUM_DIMENSION"])
    assert not bool(g["DIRECT_REI_TO_DMAX_ONE_TO_ONE_ELIGIBLE"])
    assert bool(g["BULK_PSD_INTEGRATION_PATH_IDENTIFIED"])
    assert not bool(g["WYSER_PSD_RECONSTRUCTION_PINNED"])
    assert not bool(g["YANG_BI_HABIT_BRIDGE_VALIDATED"])
    assert not bool(g["YANG_BI_ROUGHNESS_BRIDGE_VALIDATED"])
    assert not bool(g["BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE"])
    assert not bool(g["GFSV16_DMAX_MAPPING_ELIGIBLE"])
    assert not bool(g["PRODUCTION_ICE_OPTICS_READY"])
    assert not bool(g["physics_promotion_allowed"])
    assert g["qualification_state"] == "DIRECT_DMAX_BRIDGE_REJECTED_BULK_PSD_PATH_IDENTIFIED_NOT_QUALIFIED"


def test_contract_forbids_all_shortcut_conversions_and_defaults():
    c = gfsv16_rei_dmax_bridge_contract_payload(physicscore_version=firecloud.__version__)
    assert c["effective_radius_is_dmax"] is False
    assert c["direct_rei_to_dmax_one_to_one_eligible"] is False
    assert c["bulk_psd_integration_path_identified"] is True
    assert c["bulk_yang_bi_psd_integration_eligible"] is False
    forbidden = set(c["forbidden_shortcuts"])
    required = {
        "GFDL_rei_treated_as_Yang_Bi_Dmax",
        "Dmax_equal_2_times_rei",
        "generalized_effective_diameter_treated_as_Dmax",
        "GFDL_MPv3_PSD_substituted_for_GFSv16_v1",
        "Yang_Bi_solid_column_habit_silently_selected",
        "Yang_Bi_surface_roughness_silently_selected",
        "reimin_reimax_used_as_Dmax_bounds",
        "production_promotion_before_independent_bulk_optics_validation",
    }
    assert required.issubset(forbidden)


def _result():
    ev = build_gfsv16_rei_dmax_bridge_evidence()
    gate = build_gfsv16_rei_dmax_bridge_gate(ev)
    return {
        "ice_microphysics_gfsv16_rei_dmax_bridge_required": True,
        "v1_ice_microphysics_gfsv16_rei_dmax_bridge_evidence": ev,
        "v1_ice_microphysics_gfsv16_rei_dmax_bridge_gate": gate,
        "ice_microphysics_gfsv16_rei_dmax_bridge_contract": gfsv16_rei_dmax_bridge_contract_payload(
            physicscore_version=firecloud.__version__
        ),
    }


def test_analysis_integrity_enforces_step3c_evidence_contract_and_fail_close():
    a = build_analysis_integrity_audit(_result()).set_index("check_id")
    ids = [
        "ICE_MICROPHYSICS_GFSV16_REI_DMAX_BRIDGE_EVIDENCE_PRESENT",
        "ICE_MICROPHYSICS_GFSV16_REI_DMAX_BRIDGE_CONTRACT_FREEZE",
        "ICE_MICROPHYSICS_GFSV16_REI_DMAX_BRIDGE_FAIL_CLOSED",
    ]
    assert all(a.loc[i, "status"] == PASS for i in ids)

    broken = _result()
    broken["ice_microphysics_gfsv16_rei_dmax_bridge_contract"] = {}
    b = build_analysis_integrity_audit(broken).set_index("check_id")
    assert b.loc[ids[0], "status"] == FAIL


def test_archive_requires_step3c_members_and_content():
    manifest = pd.DataFrame([
        {"artifact": EVIDENCE, "row_count": 13, "byte_size": 6000},
        {"artifact": GATE, "row_count": 1, "byte_size": 1200},
        {"artifact": CONTRACT, "row_count": float("nan"), "byte_size": 1800},
    ])
    a = build_archive_integrity_audit(manifest, pd.DataFrame()).set_index("check_id")
    for name in (EVIDENCE, GATE, CONTRACT):
        assert a.loc[f"ARCHIVE_MEMBER::{name}", "status"] == PASS
    assert a.loc["ARCHIVE_CONTENT::ICE_MICROPHYSICS_GFSV16_REI_DMAX_BRIDGE_EVIDENCE_NONEMPTY", "status"] == PASS
    assert a.loc["ARCHIVE_CONTENT::ICE_MICROPHYSICS_GFSV16_REI_DMAX_BRIDGE_GATE_NONEMPTY", "status"] == PASS
    assert a.loc["ARCHIVE_CONTENT::ICE_MICROPHYSICS_GFSV16_REI_DMAX_BRIDGE_CONTRACT_NONEMPTY", "status"] == PASS


def test_app_case_export_rebuilds_step3c_static_evidence_from_running_release():
    app = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
    assert "_case_gfsv16_rei_dmax_bridge_evidence = build_gfsv16_rei_dmax_bridge_evidence()" in app
    assert "_case_gfsv16_rei_dmax_bridge_gate = build_gfsv16_rei_dmax_bridge_gate(" in app
    assert "_case_gfsv16_rei_dmax_bridge_contract = gfsv16_rei_dmax_bridge_contract_payload(" in app
    assert f'("{EVIDENCE}", _case_gfsv16_rei_dmax_bridge_evidence)' in app
    assert f'("{GATE}", _case_gfsv16_rei_dmax_bridge_gate)' in app
    assert f'("{CONTRACT}", _case_gfsv16_rei_dmax_bridge_contract)' in app
