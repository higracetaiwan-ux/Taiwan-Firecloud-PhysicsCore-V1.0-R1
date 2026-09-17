import math

import firecloud

from firecloud.ice_microphysics_wyser_yang_population_bridge import (
    STEP3I_MODE,
    STEP3I_VERSION,
    build_wyser_yang_population_bridge_evidence,
    build_wyser_yang_population_bridge_gate,
    population_bridge_diagnostic,
    reconstruct_yang_single_column_optical_kernel,
    wyser_yang_geometry_mass_comparison,
    wyser_yang_population_bridge_contract_payload,
)


def test_release_identity_and_step3i_identity():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.25.1"
    assert STEP3I_VERSION == "R5.7.41.3.4.10.22"
    assert STEP3I_MODE == "WYSER_POPULATION_YANG_OPTICAL_KERNEL_BRIDGE_DIAGNOSTIC_ONLY_FAIL_CLOSED"


def test_step3i_geometry_mass_comparison_quantifies_non_equivalence_without_remapping():
    report = wyser_yang_geometry_mass_comparison(lengths_um=(10.0, 30.0, 100.0, 1000.0))
    assert report["diagnostic_only"] is True
    assert report["shared_coordinate"] == "maximum_dimension_um"
    assert report["shape_equivalence_pass"] is False
    assert report["projected_area_equivalence_pass"] is False
    assert report["volume_mass_equivalence_pass"] is False
    assert report["wyser_population_mass_semantic"] == "WYSER_EQ6_EMPIRICAL_PARTICLE_MASS"
    assert report["yang_optical_kernel_mass_semantic"] == "YANG_GEOMETRIC_RHO_ICE_TIMES_VOLUME"
    assert report["mass_semantics_interchangeable"] is False
    assert len(report["rows"]) == 4
    assert report["max_relative_projected_area_difference"] > 0.15
    assert report["max_relative_yang_mass_vs_wyser_eq6_difference"] > 1.0


def test_step3i_reconstructs_complete_six_band_yang_single_column_kernel_on_wyser_domain():
    kernel = reconstruct_yang_single_column_optical_kernel()
    assert kernel["diagnostic_only"] is True
    assert kernel["ice_habit"] == "single_column"
    assert kernel["surface_roughness"] == "Rough000"
    assert kernel["runtime_default_selected"] is False
    assert kernel["source_path"] == "firecloud/data/ice_optics/portable_ice_optics_lut_v1.csv"
    assert kernel["dmax_domain_um"] == [10.0, 1000.0]
    assert kernel["dmax_count"] == 109
    assert kernel["row_count"] == 654
    assert kernel["wavelengths_nm"] == [550, 575, 600, 650, 700, 750]
    assert kernel["six_band_coverage_pass"] is True
    assert kernel["cext_reconstruction_pass"] is True
    assert kernel["effective_diameter_reproduction_pass"] is True
    assert kernel["min_reconstructed_qext"] > 0.0
    assert kernel["max_reconstructed_qext"] > kernel["min_reconstructed_qext"]
    assert math.isfinite(kernel["max_effective_diameter_relative_error"])
    assert kernel["max_effective_diameter_relative_error"] <= 1.0e-6


def test_step3i_population_bridge_is_numerically_executable_but_not_scientifically_promoted():
    report = population_bridge_diagnostic()
    assert report["wyser_L_to_yang_dmax_coordinate_validated"] is True
    assert report["yang_bi_single_column_kernel_cext_reconstruction_pass"] is True
    assert report["wyser_yang_dual_mass_semantics_separated_pass"] is True
    assert report["wyser_yang_hybrid_population_bridge_numeric_executable"] is True
    assert report["direct_shape_compatibility_pass"] is False
    assert report["direct_projected_area_equivalence_pass"] is False
    assert report["direct_volume_mass_equivalence_pass"] is False
    assert report["independent_eq6_external_numeric_corroboration_pass"] is False
    assert report["scientific_mass_closure_executed"] is False
    assert report["yang_bi_habit_bridge_validated"] is False
    assert report["yang_bi_roughness_bridge_validated"] is False
    assert report["bulk_yang_bi_psd_integration_eligible"] is False
    assert report["production_ice_optics_ready"] is False
    assert report["physics_promotion_allowed"] is False


def test_step3i_evidence_gate_contract_keep_numeric_bridge_separate_from_production_eligibility():
    evidence = build_wyser_yang_population_bridge_evidence().set_index("evidence_id")
    assert evidence.loc["YANG_SINGLE_COLUMN_CEXT_KERNEL_RECONSTRUCTION", "pin_status"] == "PASS_DIAGNOSTIC_KERNEL_RECONSTRUCTION"
    assert evidence.loc["WYSER_YANG_DUAL_MASS_SEMANTICS", "pin_status"] == "PASS_SEMANTIC_SEPARATION"
    assert evidence.loc["WYSER_YANG_HYBRID_POPULATION_BRIDGE_NUMERIC", "pin_status"] == "PASS_DIAGNOSTIC_NUMERIC_EXECUTABLE"
    assert evidence.loc["WYSER_TO_YANG_PROJECTED_AREA_EQUIVALENCE", "pin_status"] == "BLOCKED_NON_EQUIVALENT_GEOMETRY"
    assert evidence.loc["WYSER_TO_YANG_VOLUME_MASS_EQUIVALENCE", "pin_status"] == "BLOCKED_NON_EQUIVALENT_MASS_SEMANTICS"

    gate = build_wyser_yang_population_bridge_gate(evidence).iloc[0]
    assert bool(gate["YANG_BI_SINGLE_COLUMN_KERNEL_CEXT_RECONSTRUCTION_PASS"]) is True
    assert bool(gate["WYSER_YANG_DUAL_MASS_SEMANTICS_SEPARATED_PASS"]) is True
    assert bool(gate["WYSER_YANG_HYBRID_POPULATION_BRIDGE_NUMERIC_EXECUTABLE"]) is True
    assert bool(gate["WYSER_TO_YANG_PROJECTED_AREA_EQUIVALENCE_PASS"]) is False
    assert bool(gate["WYSER_TO_YANG_VOLUME_MASS_EQUIVALENCE_PASS"]) is False
    assert bool(gate["BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE"]) is False
    assert bool(gate["PRODUCTION_ICE_OPTICS_READY"]) is False
    assert bool(gate["physics_promotion_allowed"]) is False

    contract = wyser_yang_population_bridge_contract_payload(physicscore_version=firecloud.__version__)
    assert contract["contract_version"] == "FIRECLOUD_ICE_WYSER_YANG_POPULATION_BRIDGE_V1"
    assert contract["population_mass_semantic"] == "WYSER_EQ6_EMPIRICAL_PARTICLE_MASS"
    assert contract["optical_kernel_mass_semantic"] == "YANG_GEOMETRIC_RHO_ICE_TIMES_VOLUME"
    assert contract["mass_semantics_interchangeable"] is False
    assert contract["wyser_yang_hybrid_population_bridge_numeric_executable"] is True
    assert contract["bulk_yang_bi_psd_integration_eligible"] is False
    assert contract["production_ice_optics_ready"] is False
    assert contract["physics_promotion_allowed"] is False
    forbidden = set(contract["forbidden_shortcuts"])
    assert "yang_geometric_mass_used_to_normalize_wyser_psd" in forbidden
    assert "wyser_eq6_mass_used_to_invert_yang_mass_extinction_coefficient" in forbidden
    assert "diagnostic_single_column_rough000_kernel_treated_as_runtime_habit_roughness_default" in forbidden
