import json


def test_step3q1_qualifies_semantic_class_but_keeps_exact_history_fail_closed():
    from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
        build_fu96_rrtmg_band_weighting_provenance_evidence,
        build_fu96_rrtmg_band_weighting_provenance_gate,
    )
    ev = build_fu96_rrtmg_band_weighting_provenance_evidence().set_index("check_id")
    gate = build_fu96_rrtmg_band_weighting_provenance_gate(ev.reset_index()).iloc[0]
    assert ev.loc["FU96_LINEAGE_SOLAR_IRRADIANCE_WEIGHTING_SEMANTIC", "status"] == "PASS_CONFIRMED"
    assert ev.loc["RRTMG_SW_BAND_INTEGRATION_FORMULA_SEMANTIC", "status"] == "PASS_QUALIFIED"
    assert bool(gate["SOLAR_IRRADIANCE_WEIGHTING_SEMANTIC_SUPPORTED"])
    assert bool(gate["LATER_RRTMG_BAND_INTEGRATION_SEMANTIC_CLASS_QUALIFIED"])
    assert bool(gate["RRTMG_BAND24_25_LIMITS_PINNED"])
    assert not bool(gate["PREAVERAGING_SPECTRAL_SAMPLES_RECOVERED"])
    assert not bool(gate["EXACT_HISTORICAL_SOLAR_SPECTRUM_AND_WEIGHTS_RECOVERED"])
    assert not bool(gate["HISTORICAL_EXACT_WEIGHTING_REALIZATION_UNAMBIGUOUS"])
    assert not bool(gate["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"])
    assert not bool(gate["BAND_INTEGRATED_OPTICAL_VALIDATION_READY"])
    assert not bool(gate["TAU_ICE_PRODUCTION_ALLOWED"])
    assert not bool(gate["PRODUCTION_ICE_OPTICS_READY"])
    assert gate["qualification_state"] == "PASS_FAIL_CLOSED_V25_OFFICIAL_ARCHIVE_PUBLICATION_CHAIN_QUALIFIED_ORIGINAL_TARBALL_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED"


def test_step3q1_contract_records_qualified_formulas_without_promoting_exact_weighting():
    from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
        fu96_rrtmg_band_weighting_provenance_contract_payload,
        serialize_fu96_rrtmg_band_weighting_provenance_contract_json_bytes,
    )
    payload = fu96_rrtmg_band_weighting_provenance_contract_payload()
    sem = payload["qualified_weighting_semantic_class"]
    assert payload["step_version"] == "R5.7.41.3.4.10.30.10"
    assert sem["shortwave_weighting_basis"] == "solar_irradiance"
    assert sem["historical_fu96_coalbedo"] == "absorption_dependent_mix_of_solar_weighted_linear_and_logarithmic_averages"
    assert sem["later_rrtmg_band_g_example"] == "scattering_cross_section_weighted_with_solar_spectrum"
    assert sem["historical_exact_solar_spectrum_and_discrete_weights_recovered"] is False
    assert payload["capabilities"]["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"] is False
    assert payload["production_guards"]["production_ice_optics_ready"] is False
    a = serialize_fu96_rrtmg_band_weighting_provenance_contract_json_bytes(payload)
    b = serialize_fu96_rrtmg_band_weighting_provenance_contract_json_bytes(dict(reversed(list(payload.items()))))
    assert a == b
    assert json.loads(a.decode("utf-8"))["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_10"


def test_step3q1_forbids_only_unproven_or_ad_hoc_substitutes():
    from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import build_fu96_rrtmg_band_weighting_provenance_evidence
    ev = build_fu96_rrtmg_band_weighting_provenance_evidence().set_index("check_id")
    for check in (
        "ARBITRARY_EQUAL_WEIGHT_SUBSTITUTE",
        "UNVERSIONED_OR_ASSUMED_SOLAR_SPECTRUM_WEIGHTS",
        "GPOINT_WEIGHT_SUBSTITUTE",
        "AD_HOC_EXTINCTION_OR_SCATTERING_WEIGHT_SUBSTITUTE",
    ):
        assert ev.loc[check, "status"] == "PASS_FORBIDDEN"
        assert ev.loc[check, "observed"] == "false"
