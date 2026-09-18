import json
import pandas as pd


def test_step3p_absent_source_is_explicitly_fail_closed(tmp_path):
    from firecloud.ice_microphysics_yang_full_spectral_source_qualification import (
        build_yang_full_spectral_source_qualification_evidence,
        build_yang_full_spectral_source_qualification_gate,
    )
    evidence = build_yang_full_spectral_source_qualification_evidence(tmp_path / "missing")
    gate = build_yang_full_spectral_source_qualification_gate(evidence).iloc[0]
    assert bool(gate["YANG_FULL_SPECTRAL_SOURCE_CONTRACT_PINNED"])
    assert not bool(gate["YANG_FULL_SPECTRAL_SOURCE_BYTES_AVAILABLE"])
    assert not bool(gate["RRTMG_BAND24_SPECTRAL_COVERAGE_PASS"])
    assert not bool(gate["RRTMG_BAND25_SPECTRAL_COVERAGE_PASS"])
    assert not bool(gate["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"])
    assert not bool(gate["INDEPENDENT_SSA_VALIDATION_PASS"])
    assert not bool(gate["INDEPENDENT_ASYMMETRY_VALIDATION_PASS"])
    assert not bool(gate["TAU_ICE_PRODUCTION_ALLOWED"])
    assert gate["qualification_state"] == "PASS_FAIL_CLOSED_SOURCE_BYTES_UNAVAILABLE"


def test_step3p_band_domain_coverage_helper():
    from firecloud.ice_microphysics_yang_full_spectral_source_qualification import _band_domain_coverage
    raw = pd.DataFrame({"wavelength_um": [0.40, 0.45, 0.50, 0.60, 0.625, 0.65, 0.70, 0.78, 0.80]})
    b25 = _band_domain_coverage(raw, 25)
    b24 = _band_domain_coverage(raw, 24)
    assert b25["domain_covered"] is True
    assert b24["domain_covered"] is True
    assert b25["source_points_inside_band"] >= 2
    assert b24["source_points_inside_band"] >= 2


def test_step3p_contract_is_stable_and_remains_nonproduction(tmp_path):
    from firecloud.ice_microphysics_yang_full_spectral_source_qualification import (
        build_yang_full_spectral_source_qualification_evidence,
        build_yang_full_spectral_source_qualification_gate,
        yang_full_spectral_source_qualification_contract_payload,
        serialize_yang_full_spectral_source_qualification_contract_json_bytes,
    )
    ev = build_yang_full_spectral_source_qualification_evidence(tmp_path / "missing")
    gate = build_yang_full_spectral_source_qualification_gate(ev)
    payload = yang_full_spectral_source_qualification_contract_payload(evidence=ev, gate=gate)
    assert payload["production_guards"]["tau_ice_production_allowed"] is False
    assert payload["production_guards"]["production_ice_optics_ready"] is False
    a = serialize_yang_full_spectral_source_qualification_contract_json_bytes(payload)
    b = serialize_yang_full_spectral_source_qualification_contract_json_bytes(dict(reversed(list(payload.items()))))
    assert a == b
    assert json.loads(a.decode("utf-8"))["contract_version"] == "FIRECLOUD_ICE_YANG_FULL_SPECTRAL_SOURCE_QUALIFICATION_V1"
