import json

import firecloud.ice_microphysics_fu96_independent_bulk_validation as step3k


def _grid_a():
    return {
        "case_count": 18,
        "all_fu96_extinction_chain_numeric_pass": True,
        "all_projected_area_numeric_pass": True,
        "max_fu96_unit_chain_relative_error": 1.22441956002415e-05,
        "min_relative_difference_vs_fu96": 0.26212710714149406,
        "max_relative_difference_vs_fu96": 0.31216620726536515,
    }


def _grid_b():
    return {
        "case_count": 18,
        "all_fu96_extinction_chain_numeric_pass": True,
        "all_projected_area_numeric_pass": True,
        "max_fu96_unit_chain_relative_error": 1.224419560031046e-05,
        "min_relative_difference_vs_fu96": 0.262127107141494,
        "max_relative_difference_vs_fu96": 0.31216620726536526,
    }


def _sample_a(**_kwargs):
    return {
        "mass_area_equivalent_dge_um": 51.5726471165019,
        "solid_hex_geometry_dge_um": 113.0846813692464,
    }


def _sample_b(**_kwargs):
    return {
        "mass_area_equivalent_dge_um": 51.57264711650191,
        "solid_hex_geometry_dge_um": 113.08468136924639,
    }


def _build_with(monkeypatch, grid_factory, sample_factory):
    monkeypatch.setattr(step3k, "run_fu96_independent_bulk_validation_grid", grid_factory)
    monkeypatch.setattr(step3k, "diagnostic_fu96_independent_bulk_validation", sample_factory)
    evidence = step3k.build_fu96_independent_bulk_validation_evidence()
    contract = step3k.fu96_independent_bulk_validation_contract_payload(
        physicscore_version="1.0.0-R5.7.41.3.4.10.29"
    )
    numeric_values = dict(zip(evidence["evidence_id"], evidence["value"]))
    return numeric_values, contract


def test_step3k_stable_serializer_collapses_observed_cross_platform_ulp_differences():
    assert hasattr(step3k, "STABLE_STEP3K_EVIDENCE_SIGNIFICANT_DIGITS")
    assert hasattr(step3k, "stable_step3k_evidence_float")
    assert hasattr(step3k, "stable_step3k_evidence_number")

    pairs = [
        (1.22441956002415e-05, 1.224419560031046e-05),
        (0.26212710714149406, 0.262127107141494),
        (0.31216620726536515, 0.31216620726536526),
        (51.5726471165019, 51.57264711650191),
        (113.0846813692464, 113.08468136924639),
    ]
    for a, b in pairs:
        assert step3k.stable_step3k_evidence_float(a) == step3k.stable_step3k_evidence_float(b)
        assert step3k.stable_step3k_evidence_number(a) == step3k.stable_step3k_evidence_number(b)


def test_step3k_evidence_and_contract_are_stable_for_observed_platform_variants(monkeypatch):
    values_a, contract_a = _build_with(monkeypatch, _grid_a, _sample_a)
    values_b, contract_b = _build_with(monkeypatch, _grid_b, _sample_b)

    assert values_a["FU96_PROJECTED_AREA_EXTINCTION_CHAIN"] == values_b["FU96_PROJECTED_AREA_EXTINCTION_CHAIN"]
    assert values_a["FU96_DGE_DUAL_SEMANTICS"] == values_b["FU96_DGE_DUAL_SEMANTICS"]
    assert values_a["FU96_STEP3J_BULK_DIFFERENCE_CHARACTERIZATION"] == values_b["FU96_STEP3J_BULK_DIFFERENCE_CHARACTERIZATION"]

    # Contract numeric fields are JSON numbers, not strings, but must be
    # deterministically rounded before serialization.
    assert contract_a["diagnostic_matrix"] == contract_b["diagnostic_matrix"]
    assert json.dumps(contract_a["diagnostic_matrix"], sort_keys=True) == json.dumps(
        contract_b["diagnostic_matrix"], sort_keys=True
    )
