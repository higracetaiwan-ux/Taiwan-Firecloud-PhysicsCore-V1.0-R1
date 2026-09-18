import json
import pandas as pd


def test_step3n_evidence_and_gate_fail_closed():
    from firecloud.ice_microphysics_fu96_rrtmg_ssa_asymmetry_qualification import (
        build_fu96_rrtmg_ssa_asymmetry_qualification_evidence,
        build_fu96_rrtmg_ssa_asymmetry_qualification_gate,
    )
    evidence = build_fu96_rrtmg_ssa_asymmetry_qualification_evidence()
    assert isinstance(evidence, pd.DataFrame)
    assert len(evidence) >= 8
    status = dict(zip(evidence["evidence_id"], evidence["pin_status"]))
    assert status["FU96_PRIMARY_SOLAR_SSA_G_PROVENANCE"] == "PINNED"
    assert status["RRTMG_FU96_SSAICE3_ASYICE3_PROVENANCE"] == "PINNED"
    assert status["SIX_BAND_TO_RRTMG_BROAD_BAND_MAPPING"] == "PASS_MAPPING_EXPLICIT_NOT_MONOCHROMATIC"
    gate = build_fu96_rrtmg_ssa_asymmetry_qualification_gate(evidence)
    assert len(gate) == 1
    row = gate.iloc[0].to_dict()
    assert row["INDEPENDENT_BULK_BAND_SSA_REFERENCE_AVAILABLE"] is True or bool(row["INDEPENDENT_BULK_BAND_SSA_REFERENCE_AVAILABLE"])
    assert row["INDEPENDENT_BULK_BAND_ASYMMETRY_REFERENCE_AVAILABLE"] is True or bool(row["INDEPENDENT_BULK_BAND_ASYMMETRY_REFERENCE_AVAILABLE"])
    assert not bool(row["INDEPENDENT_SSA_VALIDATION_PASS"])
    assert not bool(row["INDEPENDENT_ASYMMETRY_VALIDATION_PASS"])
    assert not bool(row["FULL_SIX_BAND_LIKE_FOR_LIKE_OPTICAL_VALIDATION_PASS"])
    assert not bool(row["TAU_ICE_PRODUCTION_ALLOWED"])
    assert not bool(row["PRODUCTION_ICE_OPTICS_READY"])
    assert not bool(row["physics_promotion_allowed"])


def test_step3n_band_mapping_is_explicitly_broad_band():
    from firecloud.ice_microphysics_fu96_rrtmg_ssa_asymmetry_qualification import (
        SIX_BAND_RRTMG_MAP,
    )
    assert SIX_BAND_RRTMG_MAP == {550: 25, 575: 25, 600: 25, 650: 24, 700: 24, 750: 24}


def test_step3n_contract_is_deterministic_and_fail_closed():
    from firecloud.ice_microphysics_fu96_rrtmg_ssa_asymmetry_qualification import (
        fu96_rrtmg_ssa_asymmetry_qualification_contract_payload,
    )
    a = fu96_rrtmg_ssa_asymmetry_qualification_contract_payload(
        physicscore_version="1.0.0-R5.7.41.3.4.10.28.1"
    )
    b = fu96_rrtmg_ssa_asymmetry_qualification_contract_payload(
        physicscore_version="1.0.0-R5.7.41.3.4.10.28.1"
    )
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert a["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_SSA_ASYMMETRY_QUALIFICATION_V1"
    assert a["six_band_rrtmg_broad_band_map"] == {"550": 25, "575": 25, "600": 25, "650": 24, "700": 24, "750": 24}
    assert a["broad_band_values_must_not_be_relabelled_monochromatic"] is True
    assert a["full_six_band_like_for_like_optical_validation_pass"] is False
    assert a["tau_ice_production_allowed"] is False
    assert a["production_ice_optics_ready"] is False
    assert a["physics_promotion_allowed"] is False
