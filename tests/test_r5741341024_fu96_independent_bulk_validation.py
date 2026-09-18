import math

import firecloud
from firecloud.ice_microphysics_fu96_independent_bulk_validation import (
    STEP3K_MODE,
    STEP3K_VERSION,
    diagnostic_fu96_independent_bulk_validation,
    run_fu96_independent_bulk_validation_grid,
    build_fu96_independent_bulk_validation_evidence,
    build_fu96_independent_bulk_validation_gate,
    fu96_independent_bulk_validation_contract_payload,
)


def test_step3k_identity_is_independent_optical_crosscheck_and_fail_closed():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.30.5"
    assert STEP3K_VERSION == "R5.7.41.3.4.10.24"
    assert STEP3K_MODE == "FU96_PROJECTED_AREA_INDEPENDENT_BULK_EXTINCTION_CROSSCHECK_FAIL_CLOSED"


def test_step3k_fu96_projected_area_chain_executes_without_yang_cext_kernel():
    report = diagnostic_fu96_independent_bulk_validation(
        temperature_k=253.16,
        iwc_g_m3=0.1,
        grid_points=4097,
        reference_grid_points=16385,
    )
    assert report["diagnostic_only"] is True
    assert report["independent_optical_kernel"] == "FU96_GEOMETRIC_OPTICS_BETA_APPROX_2AC"
    assert report["uses_yang_bi_cext_in_reference_chain"] is False
    assert report["projected_area_numeric_pass"] is True
    assert report["fu96_extinction_chain_numeric_pass"] is True
    assert report["mass_area_equivalent_dge_um"] > 0.0
    assert report["solid_hex_geometry_dge_um"] > 0.0
    assert report["mass_area_equivalent_dge_um"] != report["solid_hex_geometry_dge_um"]
    assert report["fu96_k_ext_m2_kg"] > 0.0
    assert len(report["step3j_bands"]) == 6
    assert all(row["relative_difference_vs_fu96"] > 0.0 for row in report["step3j_bands"])
    assert report["scientific_bulk_validation_pass"] is False
    assert report["tau_ice_production_allowed"] is False
    assert report["physics_promotion_allowed"] is False


def test_step3k_fu96_beta_2ac_and_dge_unit_chain_agree_numerically():
    report = diagnostic_fu96_independent_bulk_validation(
        temperature_k=233.16,
        iwc_g_m3=0.001,
        grid_points=4097,
        reference_grid_points=16385,
    )
    assert math.isclose(
        report["fu96_k_ext_m2_kg"],
        report["fu96_k_ext_via_dge_m2_kg"],
        rel_tol=2.0e-5,
        abs_tol=0.0,
    )
    assert report["fu96_unit_chain_relative_error"] <= 2.0e-5


def test_step3k_18_case_matrix_characterizes_difference_without_promoting_science():
    grid = run_fu96_independent_bulk_validation_grid()
    assert grid["case_count"] == 18
    assert grid["all_fu96_extinction_chain_numeric_pass"] is True
    assert grid["all_projected_area_numeric_pass"] is True
    assert 0.20 < grid["min_relative_difference_vs_fu96"] < 0.40
    assert 0.20 < grid["max_relative_difference_vs_fu96"] < 0.40
    assert grid["scientific_bulk_validation_pass"] is False
    assert grid["bulk_yang_bi_psd_integration_eligible"] is False
    assert grid["tau_ice_production_allowed"] is False
    assert grid["production_ice_optics_ready"] is False


def test_step3k_evidence_gate_contract_record_crosscheck_but_keep_promotion_blocked():
    evidence = build_fu96_independent_bulk_validation_evidence().set_index("evidence_id")
    assert evidence.loc["FU96_PROJECTED_AREA_EXTINCTION_CHAIN", "pin_status"] == "PASS_INDEPENDENT_OPTICAL_CROSSCHECK_EXECUTED"
    assert evidence.loc["FU96_STEP3J_BULK_DIFFERENCE_CHARACTERIZATION", "pin_status"] == "PASS_DIFFERENCE_CHARACTERIZED_NO_PROMOTION"
    assert evidence.loc["SCIENTIFIC_BULK_VALIDATION", "pin_status"] == "BLOCKED_REFERENCE_NOT_LIKE_FOR_LIKE_PRODUCTION_VALIDATION"

    gate = build_fu96_independent_bulk_validation_gate(evidence).iloc[0]
    assert bool(gate["FU96_INDEPENDENT_OPTICAL_CROSSCHECK_EXECUTED"]) is True
    assert bool(gate["FU96_PROJECTED_AREA_CHAIN_NUMERIC_PASS"]) is True
    assert bool(gate["FU96_BULK_DIFFERENCE_CHARACTERIZED"]) is True
    assert bool(gate["SCIENTIFIC_BULK_VALIDATION_PASS"]) is False
    assert bool(gate["BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE"]) is False
    assert bool(gate["TAU_ICE_PRODUCTION_ALLOWED"]) is False
    assert bool(gate["PRODUCTION_ICE_OPTICS_READY"]) is False
    assert bool(gate["physics_promotion_allowed"]) is False

    contract = fu96_independent_bulk_validation_contract_payload(
        physicscore_version="1.0.0-R5.7.41.3.4.10.30"
    )
    assert contract["contract_version"] == "FIRECLOUD_ICE_FU96_INDEPENDENT_BULK_VALIDATION_V1"
    assert contract["uses_yang_bi_cext_in_reference_chain"] is False
    assert contract["scientific_bulk_validation_pass"] is False
    assert contract["tau_ice_production_allowed"] is False
    assert contract["production_ice_optics_ready"] is False
