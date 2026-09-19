import firecloud.ice_microphysics_yang_habit_roughness_qualification as step3l


def _ensemble_a(**_kwargs):
    return {
        "numeric_pass": True,
        "temperature_k": 253.16,
        "iwc_g_m3": 0.1,
        "max_bulk_k_ext_spread_m2_kg": 0.29651018881,
        "max_bulk_ssa_spread": 2.1492854473e-06,
        "max_bulk_g_spread": 0.016970705674,
        "max_grid_convergence_relative_error": 5.2712977444e-07,
    }


def _ensemble_b(**_kwargs):
    return {
        "numeric_pass": True,
        "temperature_k": 253.16,
        "iwc_g_m3": 0.1,
        "max_bulk_k_ext_spread_m2_kg": 0.29651018881,
        "max_bulk_ssa_spread": 2.1492854470e-06,
        "max_bulk_g_spread": 0.016970705674,
        "max_grid_convergence_relative_error": 5.2712977464e-07,
    }


def _contract_with(monkeypatch, ensemble_factory):
    monkeypatch.setattr(step3l, "single_column_roughness_bulk_ensemble", ensemble_factory)
    return step3l.yang_habit_roughness_qualification_contract_payload(
        physicscore_version="1.0.0-R5.7.41.3.4.10.30"
    )


def test_step3l_contract_sample_serialization_collapses_observed_field_platform_variants(monkeypatch):
    contract_a = _contract_with(monkeypatch, _ensemble_a)
    contract_b = _contract_with(monkeypatch, _ensemble_b)

    assert contract_a["sample_roughness_bulk_ensemble"] == contract_b["sample_roughness_bulk_ensemble"]


def test_step3l_stable_contract_hotfix_release_identity():
    import firecloud

    assert firecloud.__version__ == "1.0.0-R5.7.41.3.4.10.30.20"
    assert step3l.STEP3L_VERSION == "R5.7.41.3.4.10.25.1"
    assert step3l.STABLE_EVIDENCE_SIGNIFICANT_DIGITS == 11
    assert step3l.STABLE_CONTRACT_SAMPLE_SIGNIFICANT_DIGITS == 8
