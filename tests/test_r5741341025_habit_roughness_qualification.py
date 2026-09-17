from firecloud.ice_microphysics_yang_habit_roughness_qualification import (
    authoritative_habit_roughness_inventory,
    source_row_habit_roughness_uncertainty,
    single_column_roughness_bulk_ensemble,
    build_yang_habit_roughness_qualification_evidence,
    build_yang_habit_roughness_qualification_gate,
    yang_habit_roughness_qualification_contract_payload,
)


def test_authoritative_inventory_is_complete_and_pinned():
    inv = authoritative_habit_roughness_inventory()
    assert inv["source_dataset"] == "TAMU_ICE_SINGLE_SCATTERING_V2"
    assert inv["habit_count"] == 9
    assert inv["roughness_count"] == 3
    assert inv["wavelength_count"] == 6
    assert inv["particle_size_count"] == 189
    assert inv["row_count"] == 30618
    assert inv["coverage_complete"] is True
    assert inv["roughness_states"] == ["Rough000", "Rough003", "Rough050"]


def test_source_row_uncertainty_proves_habit_and_roughness_are_optically_material():
    q = source_row_habit_roughness_uncertainty()
    assert q["domain_um"] == [10.0, 1000.0]
    assert q["habit_mass_extinction_max_relative_spread"] > 1.0
    assert q["habit_asymmetry_max_absolute_spread"] > 0.1
    assert q["single_column_roughness_asymmetry_max_absolute_spread"] > 0.02
    assert q["single_column_roughness_mass_extinction_max_relative_spread"] > 0.01


def test_single_column_roughness_ensemble_runs_without_selecting_runtime_default():
    report = single_column_roughness_bulk_ensemble(
        temperature_k=253.16,
        iwc_g_m3=0.1,
        grid_points=2049,
        reference_grid_points=8193,
    )
    assert report["numeric_pass"] is True
    assert report["roughness_states"] == ["Rough000", "Rough003", "Rough050"]
    assert len(report["states"]) == 3
    assert all(len(row["bands"]) == 6 for row in report["states"])
    assert report["runtime_roughness_selected"] is False
    assert report["roughness_production_default_allowed"] is False
    assert report["max_bulk_g_spread"] > 0.0


def test_model_family_bridge_can_pass_without_runtime_habit_inference():
    evidence = build_yang_habit_roughness_qualification_evidence().set_index("evidence_id")
    assert evidence.loc["WYSER_YANG_SOLID_COLUMN_HABIT_FAMILY_BRIDGE", "value"] == "true"
    assert evidence.loc["GFS_NATIVE_HABIT_INFERENCE", "value"] == "false"
    assert evidence.loc["RUNTIME_HABIT_DEFAULT", "value"] == "false"
    assert evidence.loc["RUNTIME_ROUGHNESS_DEFAULT", "value"] == "false"
    assert evidence.loc["ROUGHNESS_ENSEMBLE_DIAGNOSTIC", "value"] == "true"

    gate = build_yang_habit_roughness_qualification_gate(evidence).iloc[0]
    assert bool(gate["wyser_yang_solid_column_habit_family_bridge_pass"])
    assert not bool(gate["gfs_native_habit_inference_pass"])
    assert not bool(gate["runtime_habit_default_allowed"])
    assert not bool(gate["runtime_roughness_default_allowed"])
    assert bool(gate["roughness_ensemble_diagnostic_ready"])
    assert not bool(gate["tau_ice_production_allowed"])
    assert not bool(gate["physics_promotion_allowed"])


def test_contract_remains_fail_closed():
    contract = yang_habit_roughness_qualification_contract_payload(
        physicscore_version="1.0.0-R5.7.41.3.4.10.25.1"
    )
    assert contract["contract_version"] == "FIRECLOUD_ICE_YANG_HABIT_ROUGHNESS_QUALIFICATION_V1"
    assert contract["wyser_yang_solid_column_habit_family_bridge_pass"] is True
    assert contract["exact_geometry_equivalence_pass"] is False
    assert contract["gfs_native_habit_inference_pass"] is False
    assert contract["runtime_habit_default_allowed"] is False
    assert contract["runtime_roughness_default_allowed"] is False
    assert contract["roughness_ensemble_diagnostic_ready"] is True
    assert contract["tau_ice_production_allowed"] is False
    assert contract["production_ice_optics_ready"] is False
    assert contract["physics_promotion_allowed"] is False
