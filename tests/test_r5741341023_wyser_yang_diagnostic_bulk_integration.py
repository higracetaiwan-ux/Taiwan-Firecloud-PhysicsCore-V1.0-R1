import math

import numpy as np

import firecloud
from firecloud.ice_microphysics_wyser_yang_diagnostic_bulk_integration import (
    STEP3J_MODE,
    STEP3J_VERSION,
    diagnostic_bulk_extinction,
    run_diagnostic_bulk_extinction_grid,
    build_wyser_yang_diagnostic_bulk_evidence,
    build_wyser_yang_diagnostic_bulk_gate,
    wyser_yang_diagnostic_bulk_contract_payload,
)


def test_step3j_identity_is_diagnostic_only_and_fail_closed():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.30.7"
    assert STEP3J_VERSION == "R5.7.41.3.4.10.23"
    assert STEP3J_MODE == "WYSER_PSD_YANG_CEXT_DIAGNOSTIC_BULK_INTEGRATION_FAIL_CLOSED"


def test_step3j_computes_six_band_beta_ext_and_kext_with_correct_units():
    report = diagnostic_bulk_extinction(
        temperature_k=253.16,
        iwc_g_m3=0.1,
        grid_points=4097,
        reference_grid_points=16385,
    )
    assert report["diagnostic_only"] is True
    assert report["tau_ice_computed"] is False
    assert report["runtime_habit_roughness_selected"] is False
    assert report["wavelengths_nm"] == [550, 575, 600, 650, 700, 750]
    assert report["mass_closure_numeric_pass"] is True
    assert report["bulk_extinction_numeric_pass"] is True
    assert report["grid_convergence_pass"] is True
    assert report["scientific_bulk_validation_pass"] is False
    assert report["production_ice_optics_ready"] is False
    assert report["physics_promotion_allowed"] is False

    rows = report["bands"]
    assert len(rows) == 6
    for row in rows:
        assert row["beta_ext_m_inv"] > 0.0
        assert row["k_ext_m2_kg"] > 0.0
        assert math.isfinite(row["beta_ext_m_inv"])
        assert math.isfinite(row["k_ext_m2_kg"])
        # k_ext = beta / IWC_kg_m3, IWC=0.1 g/m3 = 1e-4 kg/m3
        assert math.isclose(row["k_ext_m2_kg"], row["beta_ext_m_inv"] / 1.0e-4, rel_tol=1e-12)
        assert row["convergence_relative_error"] <= 5e-4


def test_step3j_beta_ext_scales_with_number_population_but_kext_remains_finite():
    low = diagnostic_bulk_extinction(temperature_k=253.16, iwc_g_m3=0.01, grid_points=4097, reference_grid_points=16385)
    high = diagnostic_bulk_extinction(temperature_k=253.16, iwc_g_m3=1.0, grid_points=4097, reference_grid_points=16385)
    assert low["bulk_extinction_numeric_pass"] is True
    assert high["bulk_extinction_numeric_pass"] is True
    assert all(r["beta_ext_m_inv"] > 0 for r in low["bands"])
    assert all(r["beta_ext_m_inv"] > 0 for r in high["bands"])
    assert all(math.isfinite(r["k_ext_m2_kg"]) and r["k_ext_m2_kg"] > 0 for r in low["bands"])
    assert all(math.isfinite(r["k_ext_m2_kg"]) and r["k_ext_m2_kg"] > 0 for r in high["bands"])
    # PSD exponent depends on IWC, so k_ext is not required to be identical.
    assert not np.allclose(
        [r["k_ext_m2_kg"] for r in low["bands"]],
        [r["k_ext_m2_kg"] for r in high["bands"]],
        rtol=1e-12,
        atol=0.0,
    )


def test_step3j_grid_matrix_passes_numeric_preflight_without_scientific_promotion():
    grid = run_diagnostic_bulk_extinction_grid(
        temperatures_k=(233.16, 253.16, 273.16),
        iwc_values_g_m3=(0.001, 0.1, 10.0),
        grid_points=(1025, 4097),
        reference_grid_points=16385,
    )
    assert grid["case_count"] == 18
    assert grid["all_numeric_bulk_extinction_pass"] is True
    assert grid["all_grid_convergence_pass"] is True
    assert grid["max_mass_closure_relative_error"] <= 1e-12
    assert grid["max_bulk_convergence_relative_error"] <= 5e-4
    assert grid["scientific_bulk_validation_pass"] is False
    assert grid["bulk_yang_bi_psd_integration_eligible"] is False
    assert grid["production_ice_optics_ready"] is False


def test_step3j_evidence_gate_contract_keep_diagnostic_bulk_separate_from_tau_production():
    evidence = build_wyser_yang_diagnostic_bulk_evidence().set_index("evidence_id")
    assert evidence.loc["DIAGNOSTIC_SIX_BAND_BULK_EXTINCTION", "pin_status"] == "PASS_DIAGNOSTIC_BETA_KEXT_NUMERIC"
    assert evidence.loc["DIAGNOSTIC_BULK_GRID_CONVERGENCE", "pin_status"] == "PASS_DIAGNOSTIC_GRID_CONVERGENCE"
    assert evidence.loc["TAU_ICE_PRODUCTION_PROMOTION", "pin_status"] == "BLOCKED_NOT_COMPUTED_IN_STEP3J"

    gate = build_wyser_yang_diagnostic_bulk_gate(evidence).iloc[0]
    assert bool(gate["DIAGNOSTIC_SIX_BAND_BULK_EXTINCTION_PASS"]) is True
    assert bool(gate["DIAGNOSTIC_BULK_GRID_CONVERGENCE_PASS"]) is True
    assert bool(gate["SCIENTIFIC_BULK_VALIDATION_PASS"]) is False
    assert bool(gate["BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE"]) is False
    assert bool(gate["TAU_ICE_PRODUCTION_ALLOWED"]) is False
    assert bool(gate["PRODUCTION_ICE_OPTICS_READY"]) is False
    assert bool(gate["physics_promotion_allowed"]) is False

    contract = wyser_yang_diagnostic_bulk_contract_payload(physicscore_version="1.0.0-R5.7.41.3.4.10.30")
    assert contract["contract_version"] == "FIRECLOUD_ICE_WYSER_YANG_DIAGNOSTIC_BULK_V1"
    assert contract["beta_ext_definition"] == "integral[n_wyser(D)*Cext_yang(D,lambda)dD]"
    assert contract["k_ext_definition"] == "beta_ext/IWC_kg_m3"
    assert contract["tau_ice_computed"] is False
    assert contract["diagnostic_reference_habit"] == "single_column"
    assert contract["diagnostic_reference_roughness"] == "Rough000"
    assert contract["runtime_habit_roughness_selected"] is False
    assert contract["bulk_yang_bi_psd_integration_eligible"] is False
    assert contract["production_ice_optics_ready"] is False
