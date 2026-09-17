import math

import firecloud
import firecloud.ice_microphysics_wyser_primary_numeric_recovery as w


def test_patch_release_identity_and_contract_version():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.23.1"
    assert w.STEP3G_VERSION == "R5.7.41.3.4.10.20.1"
    assert w.STEP3G_MODE == "WYSER_PRIMARY_EQ5_EQ6_NUMERIC_RECOVERY_DIAGNOSTIC_MASS_CLOSURE_EXTERNAL_EQ6_CORROBORATION_PENDING"
    assert w.wyser_primary_numeric_recovery_contract_payload()["contract_version"] == "FIRECLOUD_ICE_WYSER_PRIMARY_NUMERIC_RECOVERY_V3"


def test_eq5_primary_piecewise_aspect_ratio_and_width_are_numeric_and_continuous():
    assert math.isclose(w.wyser_eq5_aspect_ratio(10.0), 1.0)
    assert math.isclose(w.wyser_eq5_aspect_ratio(30.0), 1.0)
    assert math.isclose(w.wyser_eq5_aspect_ratio(100.0), 1.21)
    assert math.isclose(w.wyser_eq5_width_um(10.0), 10.0)
    assert math.isclose(w.wyser_eq5_width_um(30.0), 30.0)
    assert math.isclose(w.wyser_eq5_width_um(100.0), 100.0 / 1.21)
    assert math.isclose(w.wyser_eq5_width_um(30.0 - 1e-9), w.wyser_eq5_width_um(30.0 + 1e-9), rel_tol=0, abs_tol=2e-9)


def test_eq6_primary_mass_law_matches_recovered_numeric_equation():
    expected = {
        10.0: 1.192065023482097e-10,
        30.0: 2.4794046515723696e-09,
        100.0: 6.899219232319399e-08,
        1000.0: 3.993005840953671e-05,
    }
    for length_um, mass_g in expected.items():
        assert math.isclose(w.wyser_eq6_mass_g(length_um), mass_g, rel_tol=2e-14, abs_tol=0.0)


def test_eq6_um_and_si_reproductions_are_equivalent():
    for length_um in (10.0, 30.0, 100.0, 363.3333333333, 1000.0):
        primary_g = w.wyser_eq6_mass_g(length_um)
        expanded_g = w.wyser_eq6_mass_g_expanded_um(length_um)
        si_kg = w.wyser_eq6_mass_kg_si(length_um * 1e-6)
        assert math.isclose(primary_g, expanded_g, rel_tol=2e-14, abs_tol=0.0)
        assert math.isclose(primary_g * 1e-3, si_kg, rel_tol=2e-14, abs_tol=0.0)


def test_primary_recovery_evidence_separates_wyser_eq5_from_wyser_yang_lineage():
    ev = w.build_wyser_primary_numeric_recovery_evidence().set_index("evidence_id")
    assert ev.loc["WYSER_EQ5_PRIMARY_MACHINE_NUMERIC_RECOVERY", "pin_status"] == "PINNED_PRIMARY_NUMERIC_WITH_INDEPENDENT_TRANSCRIPTION"
    assert "L/D=1" in ev.loc["WYSER_EQ5_PRIMARY_MACHINE_NUMERIC_RECOVERY", "value"]
    assert ev.loc["WYSER_EQ6_PRIMARY_MACHINE_NUMERIC_RECOVERY", "pin_status"] == "PINNED_PRIMARY_NUMERIC_INDEX_RECOVERY"
    assert "2.311e-2" in ev.loc["WYSER_EQ6_PRIMARY_MACHINE_NUMERIC_RECOVERY", "value"]
    assert ev.loc["WYSER_YANG_1998_GEOMETRY_LINEAGE", "pin_status"] == "SEPARATE_REFERENCE_NOT_WYSER_1998_EQ5"
    assert "D=2.5*L^0.6" in ev.loc["WYSER_YANG_1998_GEOMETRY_LINEAGE", "value"]


def test_gate_advances_primary_numeric_and_unit_consistency_but_keeps_science_fail_closed():
    gate = w.build_wyser_primary_numeric_recovery_gate().iloc[0]
    assert bool(gate["WYSER_EQ5_PRIMARY_MACHINE_NUMERIC_RECOVERED"]) is True
    assert bool(gate["WYSER_EQ6_PRIMARY_MACHINE_NUMERIC_RECOVERED"]) is True
    assert bool(gate["EQ5_EQ6_UNIT_CONSISTENCY_PASS"]) is True
    assert bool(gate["INDEPENDENT_EQ5_TRANSCRIPTION_PASS"]) is True
    assert bool(gate["INDEPENDENT_EQ6_EXTERNAL_NUMERIC_CORROBORATION_PASS"]) is False
    assert bool(gate["INDEPENDENT_TRANSCRIPTION_REPRODUCTION_PASS"]) is False
    assert bool(gate["SCIENTIFIC_MASS_CLOSURE_EXECUTED"]) is False
    assert bool(gate["ABSOLUTE_PSD_RECONSTRUCTION_EXECUTABLE"]) is False
    assert bool(gate["PRODUCTION_ICE_OPTICS_READY"]) is False
    assert bool(gate["physics_promotion_allowed"]) is False
    assert gate["qualification_state"] == "WYSER_PRIMARY_EQ5_EQ6_NUMERIC_RECOVERED_DIAGNOSTIC_MASS_CLOSURE_PASS_EXTERNAL_EQ6_CORROBORATION_BLOCKED"


def test_contract_records_exact_equations_and_keeps_l_to_dmax_unvalidated():
    c = w.wyser_primary_numeric_recovery_contract_payload(physicscore_version="test")
    assert c["wyser_eq5_primary_machine_numeric_recovered"] is True
    assert c["wyser_eq6_primary_machine_numeric_recovered"] is True
    assert c["eq5_eq6_unit_consistency_pass"] is True
    assert c["independent_eq5_transcription_pass"] is True
    assert c["independent_eq6_external_numeric_corroboration_pass"] is False
    assert c["independent_transcription_reproduction_pass"] is False
    assert c["scientific_mass_closure_executed"] is False
    assert c["absolute_psd_reconstruction_executable"] is False
    assert c["wyser_L_to_yang_dmax_coordinate_validated"] is False
    assert c["production_ice_optics_ready"] is False
    assert c["wyser_eq5_primary_numeric"]["transition_length_um"] == 30.0
    assert c["wyser_eq6_primary_numeric"]["coefficient_g"] == 2.311e-2
    assert c["wyser_eq6_primary_numeric"]["reference_length_um"] == 1.0e4
    assert c["wyser_eq6_primary_numeric"]["exponent"] == 2.7625
    assert c["separate_wyser_yang_1998_geometry_lineage"] == "D=2.5*L^0.6"


def test_wyser_mixed_psd_shape_is_continuous_at_20_um_and_uses_pinned_b_formula():
    temperature_k = 253.16
    iwc_g_m3 = 0.1
    b = w.wyser_powerlaw_exponent(temperature_k=temperature_k, iwc_g_m3=iwc_g_m3)
    expected_b = -2.0 + 1e-3 * math.log10(iwc_g_m3 / 50.0) * max(0.0, 273.16 - temperature_k) ** 1.5
    assert math.isclose(b, expected_b, rel_tol=0.0, abs_tol=1e-15)
    left = w.wyser_mixed_psd_shape(20.0, temperature_k=temperature_k, iwc_g_m3=iwc_g_m3)
    right = w.wyser_mixed_psd_shape(20.0 + 1e-10, temperature_k=temperature_k, iwc_g_m3=iwc_g_m3)
    assert math.isclose(left, right, rel_tol=2e-10, abs_tol=0.0)


def test_primary_eq6_diagnostic_mass_closure_reconstructs_iwc_and_reports_convergence():
    result = w.diagnostic_wyser_primary_mass_closure_reproduction(
        temperature_k=253.16,
        iwc_g_m3=0.1,
        grid_points=4097,
        reference_grid_points=32769,
    )
    assert result["diagnostic_only"] is True
    assert result["input_contract"] == "WYSER_PRIMARY_EQ6_WITH_PINNED_MIXED_PSD_DIAGNOSTIC_ONLY"
    assert result["domain_um"] == [10.0, 1000.0]
    assert result["branch_switch_um"] == 20.0
    assert math.isclose(result["target_iwc_g_m3"], 0.1)
    assert result["mass_closure_relative_error"] <= 1e-12
    assert result["branch_continuity_relative_error"] <= 1e-9
    assert result["normalization_convergence_relative_error"] <= 5e-5
    assert result["numeric_mass_closure_pass"] is True
    assert result["scientific_mass_closure_pass"] is False


def test_primary_eq6_diagnostic_grid_spans_temperature_iwc_and_resolution_without_promotion():
    report = w.run_diagnostic_wyser_primary_mass_closure_grid(
        temperatures_k=(233.16, 253.16, 273.16),
        iwc_values_g_m3=(0.001, 0.1, 10.0),
        grid_points=(1025, 4097),
        reference_grid_points=32769,
    )
    assert report["diagnostic_only"] is True
    assert report["grid_scope"] == "NUMERICAL_PREFLIGHT_NOT_OPERATIONAL_VALIDITY_DOMAIN"
    assert report["case_count"] == 18
    assert report["all_numeric_mass_closure_pass"] is True
    assert report["max_mass_closure_relative_error"] <= 1e-12
    assert report["max_branch_continuity_relative_error"] <= 1e-9
    assert report["max_normalization_convergence_relative_error"] <= 2e-4
    assert report["scientific_mass_closure_pass"] is False
    assert report["absolute_psd_reconstruction_executable"] is False
    assert report["production_ice_optics_ready"] is False


def test_gate_records_diagnostic_primary_mass_closure_pass_without_scientific_promotion():
    gate = w.build_wyser_primary_numeric_recovery_gate().iloc[0]
    assert bool(gate["DIAGNOSTIC_PRIMARY_EQ6_PSD_MASS_CLOSURE_EXECUTED"]) is True
    assert bool(gate["DIAGNOSTIC_PRIMARY_EQ6_PSD_MASS_CLOSURE_NUMERIC_PASS"]) is True
    assert bool(gate["DIAGNOSTIC_PRIMARY_EQ6_PSD_CONVERGENCE_PASS"]) is True
    assert bool(gate["SCIENTIFIC_MASS_CLOSURE_EXECUTED"]) is False
    assert bool(gate["PSD_MASS_CLOSURE_VALIDATION_PASS"]) is False
    assert gate["qualification_state"] == "WYSER_PRIMARY_EQ5_EQ6_NUMERIC_RECOVERED_DIAGNOSTIC_MASS_CLOSURE_PASS_EXTERNAL_EQ6_CORROBORATION_BLOCKED"
