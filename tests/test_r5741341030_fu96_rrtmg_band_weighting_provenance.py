import json


def test_step3q_pins_lineage_but_keeps_exact_weighting_fail_closed():
    from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
        build_fu96_rrtmg_band_weighting_provenance_evidence,
        build_fu96_rrtmg_band_weighting_provenance_gate,
    )
    ev = build_fu96_rrtmg_band_weighting_provenance_evidence()
    gate = build_fu96_rrtmg_band_weighting_provenance_gate(ev).iloc[0]
    assert bool(gate["FU96_PRIMARY_SOURCE_PINNED"])
    assert bool(gate["RRTMG_FU96_DGE_LINEAGE_PINNED"])
    assert bool(gate["RRTMG_FINAL_FU96_BAND_TABLES_PINNED"])
    assert not bool(gate["PREAVERAGING_SPECTRAL_SAMPLES_RECOVERED"])
    assert not bool(gate["EXACT_HISTORICAL_SOLAR_SPECTRUM_AND_WEIGHTS_RECOVERED"])
    assert not bool(gate["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"])
    assert not bool(gate["BAND_INTEGRATED_OPTICAL_VALIDATION_READY"])
    assert not bool(gate["TAU_ICE_PRODUCTION_ALLOWED"])
    assert not bool(gate["PRODUCTION_ICE_OPTICS_READY"])
    assert gate["qualification_state"] == "PASS_FAIL_CLOSED_V25_EXTERNAL_DISTRIBUTION_LINEAGE_QUALIFIED_PREAVERAGING_GENERATOR_UNRECOVERED"


def test_step3q_forbids_all_unproven_weighting_substitutes():
    from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
        build_fu96_rrtmg_band_weighting_provenance_evidence,
    )
    ev = build_fu96_rrtmg_band_weighting_provenance_evidence().set_index("check_id")
    for check in (
        "ARBITRARY_EQUAL_WEIGHT_SUBSTITUTE",
        "UNVERSIONED_OR_ASSUMED_SOLAR_SPECTRUM_WEIGHTS",
        "GPOINT_WEIGHT_SUBSTITUTE",
        "AD_HOC_EXTINCTION_OR_SCATTERING_WEIGHT_SUBSTITUTE",
    ):
        assert ev.loc[check, "status"] == "PASS_FORBIDDEN"
        assert ev.loc[check, "observed"] == "false"


def test_step3q_contract_is_stable_nonproduction_and_versioned():
    from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
        build_fu96_rrtmg_band_weighting_provenance_evidence,
        build_fu96_rrtmg_band_weighting_provenance_gate,
        fu96_rrtmg_band_weighting_provenance_contract_payload,
        serialize_fu96_rrtmg_band_weighting_provenance_contract_json_bytes,
    )
    ev = build_fu96_rrtmg_band_weighting_provenance_evidence()
    gate = build_fu96_rrtmg_band_weighting_provenance_gate(ev)
    payload = fu96_rrtmg_band_weighting_provenance_contract_payload(evidence=ev, gate=gate)
    assert payload["step_version"] == "R5.7.41.3.4.10.30.8"
    assert payload["production_guards"]["tau_ice_production_allowed"] is False
    assert payload["production_guards"]["production_ice_optics_ready"] is False
    a = serialize_fu96_rrtmg_band_weighting_provenance_contract_json_bytes(payload)
    b = serialize_fu96_rrtmg_band_weighting_provenance_contract_json_bytes(dict(reversed(list(payload.items()))))
    assert a == b
    assert json.loads(a.decode("utf-8"))["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_8"
