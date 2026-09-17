from firecloud.ice_microphysics_yang_matched_geometry_extinction_validation import (
    matched_geometry_single_particle_extinction_reference,
    run_matched_geometry_bulk_extinction_validation_grid,
    build_yang_matched_geometry_extinction_validation_evidence,
    build_yang_matched_geometry_extinction_validation_gate,
    yang_matched_geometry_extinction_validation_contract_payload,
)


def test_single_particle_matched_geometry_reference_is_complete_and_in_geometric_optics_domain():
    report = matched_geometry_single_particle_extinction_reference()
    assert report["ice_habit"] == "single_column"
    assert report["roughness_states"] == ["Rough000", "Rough003", "Rough050"]
    assert report["dmax_count"] == 109
    assert report["wavelength_count"] == 6
    assert report["row_count"] == 1962
    assert report["uses_yang_bi_cext_in_reference_chain"] is False
    assert report["same_yang_geometry_as_test_kernel"] is True
    assert report["minimum_size_parameter"] > 15.0
    assert report["geometric_optics_domain_pass"] is True
    # Regression characterization only, not a production science tolerance.
    assert report["max_single_particle_relative_difference_vs_2A"] < 0.13


def test_matched_geometry_bulk_reference_removes_step3k_geometry_mismatch_without_promoting_science():
    report = run_matched_geometry_bulk_extinction_validation_grid()
    assert report["case_count"] == 18
    assert report["comparison_row_count"] == 324
    assert report["all_geometric_optics_domain_pass"] is True
    assert report["all_reference_chains_numeric_pass"] is True
    # Regression characterization: same-geometry Fu 2A reference is much closer than Step 3K's
    # cross-geometry 26-31% comparison. This is not itself a production acceptance threshold.
    assert report["max_bulk_relative_difference_vs_matched_fu96"] < 0.03
    assert report["full_like_for_like_optical_validation_pass"] is False
    assert report["scientific_bulk_validation_pass"] is False
    assert report["tau_ice_production_allowed"] is False
    assert report["production_ice_optics_ready"] is False
    assert report["physics_promotion_allowed"] is False


def test_step3m_gate_advances_extinction_reference_but_keeps_ssa_g_tau_and_production_fail_closed():
    evidence = build_yang_matched_geometry_extinction_validation_evidence()
    gate = build_yang_matched_geometry_extinction_validation_gate(evidence).iloc[0]
    assert bool(gate["matched_geometry_extinction_reference_ready"])
    assert bool(gate["geometric_optics_domain_pass"])
    assert bool(gate["matched_geometry_bulk_difference_characterized"])
    assert not bool(gate["independent_ssa_validation_pass"])
    assert not bool(gate["independent_asymmetry_validation_pass"])
    assert not bool(gate["full_like_for_like_optical_validation_pass"])
    assert not bool(gate["scientific_bulk_validation_pass"])
    assert not bool(gate["tau_ice_production_allowed"])
    assert not bool(gate["production_ice_optics_ready"])
    assert not bool(gate["physics_promotion_allowed"])


def test_step3m_contract_records_matched_geometry_scope_and_forbidden_promotions():
    contract = yang_matched_geometry_extinction_validation_contract_payload(
        physicscore_version="1.0.0-R5.7.41.3.4.10.26"
    )
    assert contract["contract_version"] == "FIRECLOUD_ICE_YANG_MATCHED_GEOMETRY_EXTINCTION_VALIDATION_V1"
    assert contract["matched_geometry_extinction_reference_ready"] is True
    assert contract["same_yang_geometry_as_test_kernel"] is True
    assert contract["uses_yang_bi_cext_in_reference_chain"] is False
    assert contract["independent_ssa_validation_pass"] is False
    assert contract["independent_asymmetry_validation_pass"] is False
    assert contract["full_like_for_like_optical_validation_pass"] is False
    assert contract["tau_ice_production_allowed"] is False
    assert contract["production_ice_optics_ready"] is False
    assert contract["physics_promotion_allowed"] is False
    forbidden = set(contract["forbidden_shortcuts"])
    assert "Do not treat an extinction-only matched-geometry cross-check as SSA/g validation." in forbidden
    assert "Do not promote diagnostic k_ext to tau_ice production in Step 3M." in forbidden
