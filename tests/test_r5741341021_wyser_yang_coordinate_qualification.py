import firecloud
from firecloud.ice_microphysics_wyser_primary_numeric_recovery import (
    wyser_primary_numeric_recovery_contract_payload,
)
from firecloud.ice_microphysics_wyser_yang_coordinate_qualification import (
    SCIENCE_BASELINE,
    STEP3H_MODE,
    STEP3H_VERSION,
    build_wyser_yang_coordinate_qualification_evidence,
    build_wyser_yang_coordinate_qualification_gate,
    coordinate_qualification_diagnostic,
    validate_yang_v2_single_column_geometry_against_bundled_lut,
    wyser_yang_coordinate_qualification_contract_payload,
    yang_single_column_width_um,
)


def test_release_identity_and_step3h_contract_identity():
    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.23"
    assert STEP3H_VERSION == "R5.7.41.3.4.10.21"
    assert SCIENCE_BASELINE == "R5.7.41.2_SHADOW_COT_AB_FROZEN"
    assert STEP3H_MODE == "WYSER_YANG_MAXIMUM_DIMENSION_COORDINATE_QUALIFICATION_SHAPE_COMPATIBILITY_FAIL_CLOSED"
    c = wyser_yang_coordinate_qualification_contract_payload(physicscore_version=firecloud.__version__)
    assert c["contract_version"] == "FIRECLOUD_ICE_WYSER_YANG_COORDINATE_QUALIFICATION_V1"


def test_yang_v2_source_rows_pin_3_48_geometry_and_reject_0_348_transcription():
    report = validate_yang_v2_single_column_geometry_against_bundled_lut()
    assert report["source_row_count"] == 189
    assert report["source_geometry_reproduction_pass"] is True
    assert report["pinned_large_semiwidth_factor"] == 3.48
    assert report["max_relative_effective_diameter_error"] < 1.0e-6
    assert report["alternative_0_348_max_relative_error"] > 0.5
    assert yang_single_column_width_um(100.0) == 69.6

def test_coordinate_diagnostic_validates_coordinate_but_rejects_shape_equivalence():
    report = coordinate_qualification_diagnostic(lengths_um=(10.0, 30.0, 100.0, 1000.0))
    assert report["wyser_L_is_maximum_dimension_pass"] is True
    assert report["yang_bi_size_coordinate_is_maximum_dimension_pass"] is True
    assert report["wyser_L_to_yang_dmax_coordinate_validated"] is True
    assert report["exact_yang_v2_geometry_law_pinned"] is True
    assert report["shape_width_compatibility_pass"] is False
    assert report["projected_area_compatibility_pass"] is False
    assert report["volume_mass_compatibility_pass"] is False
    assert report["tested_lengths_um"] == [10.0, 30.0, 100.0, 1000.0]
    assert report["max_relative_width_difference"] > 0.1


def test_step3h_evidence_separates_coordinate_identity_from_shape_equivalence():
    ev = build_wyser_yang_coordinate_qualification_evidence().set_index("evidence_id")
    assert ev.loc["WYSER_L_IS_MAXIMUM_DIMENSION", "pin_status"] == "PASS_PRIMARY_GEOMETRY"
    assert ev.loc["YANG_BI_SIZE_COORDINATE_IS_MAXIMUM_DIMENSION", "pin_status"] == "PASS_AUTHORITATIVE_DATABASE_SEMANTIC"
    assert ev.loc["WYSER_L_TO_YANG_DMAX_COORDINATE", "pin_status"] == "PASS_COORDINATE_ONLY"
    assert ev.loc["WYSER_TO_YANG_SOLID_COLUMN_SHAPE_COMPATIBILITY", "pin_status"] == "BLOCKED_GEOMETRY_LAW_MISMATCH"
    assert bool(ev.loc["WYSER_L_TO_YANG_DMAX_COORDINATE", "authoritative_for_runtime_mapping"]) is False


def test_step3h_gate_unlocks_coordinate_only_and_preserves_all_downstream_fail_close():
    gate = build_wyser_yang_coordinate_qualification_gate().iloc[0]
    assert bool(gate["WYSER_L_IS_MAXIMUM_DIMENSION_PASS"]) is True
    assert bool(gate["YANG_BI_SIZE_COORDINATE_IS_MAXIMUM_DIMENSION_PASS"]) is True
    assert bool(gate["WYSER_L_TO_YANG_DMAX_COORDINATE_VALIDATED"]) is True
    assert bool(gate["WYSER_TO_YANG_SOLID_COLUMN_SHAPE_COMPATIBILITY_PASS"]) is False
    assert bool(gate["WYSER_TO_YANG_PROJECTED_AREA_COMPATIBILITY_PASS"]) is False
    assert bool(gate["WYSER_TO_YANG_VOLUME_MASS_COMPATIBILITY_PASS"]) is False
    assert bool(gate["INDEPENDENT_EQ6_EXTERNAL_NUMERIC_CORROBORATION_PASS"]) is False
    assert bool(gate["SCIENTIFIC_MASS_CLOSURE_EXECUTED"]) is False
    assert bool(gate["YANG_BI_HABIT_BRIDGE_VALIDATED"]) is False
    assert bool(gate["YANG_BI_ROUGHNESS_BRIDGE_VALIDATED"]) is False
    assert bool(gate["BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE"]) is False
    assert bool(gate["GFSV16_DMAX_MAPPING_ELIGIBLE"]) is False
    assert bool(gate["PRODUCTION_ICE_OPTICS_READY"]) is False
    assert bool(gate["physics_promotion_allowed"]) is False
    assert gate["qualification_state"] == "WYSER_YANG_DMAX_COORDINATE_VALIDATED_SHAPE_COMPATIBILITY_BLOCKED"


def test_step3h_contract_does_not_retroactively_rewrite_step3g_history():
    old = wyser_primary_numeric_recovery_contract_payload(physicscore_version="historical")
    new = wyser_yang_coordinate_qualification_contract_payload(physicscore_version=firecloud.__version__)
    assert old["wyser_L_to_yang_dmax_coordinate_validated"] is False
    assert new["wyser_L_to_yang_dmax_coordinate_validated"] is True
    assert new["coordinate_validation_scope"] == "SIZE_COORDINATE_IDENTITY_ONLY_NOT_SHAPE_OR_OPTICAL_EQUIVALENCE"
    assert new["wyser_to_yang_solid_column_shape_compatibility_pass"] is False
    assert new["bulk_yang_bi_psd_integration_eligible"] is False
    assert new["production_ice_optics_ready"] is False
    assert new["physics_promotion_allowed"] is False
    forbidden = set(new["forbidden_shortcuts"])
    assert "coordinate_identity_treated_as_shape_equivalence" in forbidden
    assert "coordinate_identity_used_to_enable_bulk_optics_before_shape_habit_roughness_validation" in forbidden


def test_step3h_contract_uses_portable_source_path_not_machine_absolute_path():
    c = wyser_yang_coordinate_qualification_contract_payload(physicscore_version=firecloud.__version__)
    path = c["geometry_diagnostic"]["source_geometry_reproduction"]["source_path"]
    assert path == "firecloud/data/ice_optics/portable_ice_optics_lut_v1.csv"
    assert not path.startswith("/")
