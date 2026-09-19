from firecloud import __version__
from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    STEP3Q_VERSION,
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)


def test_primary_boundary_and_band_geometry_are_pinned():
    ev = build_fu96_rrtmg_band_weighting_provenance_evidence().set_index("check_id")
    assert ev.loc["FU96_PRIMARY_VISIBLE_NIR_0P700UM_SPECTRAL_BOUNDARY", "status"] == "PASS_PINNED"
    assert ev.loc["RRTMG_BAND25_WITHIN_SINGLE_FU96_PRIMARY_BAND", "status"] == "PASS_QUALIFIED"
    assert ev.loc["RRTMG_BAND24_STRADDLES_FU96_PRIMARY_0P700UM_BOUNDARY", "status"] == "PASS_QUALIFIED"


def test_band24_inverse_reaveraging_remains_nonunique_and_fail_closed():
    gate = build_fu96_rrtmg_band_weighting_provenance_gate().iloc[0]
    assert bool(gate["FU96_PRIMARY_0P700UM_SPECTRAL_BOUNDARY_PINNED"])
    assert bool(gate["RRTMG_BAND25_WITHIN_SINGLE_FU96_PRIMARY_BAND_QUALIFIED"])
    assert bool(gate["RRTMG_BAND24_STRADDLES_FU96_PRIMARY_0P700UM_BOUNDARY_QUALIFIED"])
    assert bool(gate["RRTMG_BAND24_FINAL_TABLE_INVERSE_REAVERAGING_NONUNIQUE_QUALIFIED"])
    assert not bool(gate["RRTMG_BAND24_FINAL_TABLE_INVERSE_REAVERAGING_UNIQUE"])
    assert not bool(gate["FINAL_TABLE_INVERSE_IDENTIFICATION_ALLOWED"])
    assert not bool(gate["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"])
    assert not bool(gate["TAU_ICE_PRODUCTION_ALLOWED"])


def test_step3q18_contract_identity_and_scope():
    c = fu96_rrtmg_band_weighting_provenance_contract_payload()
    assert __version__ == "1.0.0-R5.7.41.3.4.10.30.21"
    assert STEP3Q_VERSION == "R5.7.41.3.4.10.30.21"
    assert c["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_21"
    assert c["capabilities"]["RRTMG_BAND24_FINAL_TABLE_INVERSE_REAVERAGING_NONUNIQUE_QUALIFIED"] is True
    assert c["production_guards"]["tau_ice_production_allowed"] is False
    assert c["production_guards"]["production_ice_optics_ready"] is False
