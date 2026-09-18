
import json

def test_step3q2_pins_historical_fu96_mixed_coalbedo_semantics_and_keeps_later_formula_separate():
    from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
        build_fu96_rrtmg_band_weighting_provenance_evidence,
        build_fu96_rrtmg_band_weighting_provenance_gate,
    )
    ev = build_fu96_rrtmg_band_weighting_provenance_evidence().set_index("check_id")
    gate = build_fu96_rrtmg_band_weighting_provenance_gate(ev.reset_index()).iloc[0]
    assert ev.loc["FU96_HISTORICAL_COALBEDO_MIXED_LINEAR_LOG_SEMANTIC", "status"] == "PASS_CONFIRMED"
    assert ev.loc["FU96_HISTORICAL_BAND_SPECIFIC_MIXING_REALIZATION", "status"] == "BLOCKED_NOT_RECOVERED"
    assert ev.loc["YI2013_FORMULA_AS_HISTORICAL_FU96_DEFAULT_TABLE_GENERATOR", "status"] == "PASS_FORBIDDEN"
    assert bool(gate["FU96_HISTORICAL_MIXED_LINEAR_LOG_COALBEDO_SEMANTIC_PINNED"])
    assert not bool(gate["FU96_HISTORICAL_BAND_SPECIFIC_LINEAR_LOG_MIXING_RECOVERED"])
    assert not bool(gate["YI2013_FORMULA_PROVEN_AS_HISTORICAL_FU96_TABLE_GENERATOR"])

def test_step3q2_pins_pre_v4_kurucz_runtime_context_without_equating_it_to_table_generator():
    from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import build_fu96_rrtmg_band_weighting_provenance_gate
    g = build_fu96_rrtmg_band_weighting_provenance_gate().iloc[0]
    assert bool(g["RRTMG_PRE_V4_KURUCZ_RUNTIME_SOLAR_SOURCE_PINNED"])
    assert bool(g["RRTMG_BAND24_25_SOLAR_IRRADIANCE_TOTALS_PINNED"])
    assert not bool(g["RUNTIME_SOLAR_SOURCE_IDENTITY_WITH_FU96_TABLE_GENERATOR_PROVEN"])
    assert not bool(g["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"])

def test_step3q2_contract_v12_preserves_fail_close_and_semantic_distinction():
    from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import fu96_rrtmg_band_weighting_provenance_contract_payload
    p = fu96_rrtmg_band_weighting_provenance_contract_payload()
    assert p["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_4"
    assert p["step_version"] == "R5.7.41.3.4.10.30.4"
    sem = p["qualified_weighting_semantic_class"]
    assert sem["historical_fu96_coalbedo"].startswith("absorption_dependent_mix")
    assert sem["later_formula_is_historical_fu96_generator"] is False
    assert p["capabilities"]["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"] is False
    assert p["production_guards"]["tau_ice_production_allowed"] is False
