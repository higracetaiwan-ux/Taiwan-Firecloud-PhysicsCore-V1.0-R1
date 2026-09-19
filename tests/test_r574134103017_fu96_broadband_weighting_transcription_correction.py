from firecloud import __version__
from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)

STATE = "PASS_FAIL_CLOSED_FU96_PRIMARY_BAND_FORWARD_RECONSTRUCTION_INPUTS_QUALIFIED_RRTMG_FINE_GRID_AND_EXACT_BAND24_25_REALIZATION_UNRECOVERED"

def test_step3q17_equations_retain_extinction_and_scattering_weights():
    e = build_fu96_rrtmg_band_weighting_provenance_evidence().set_index("check_id")
    lin = str(e.loc["FU96_LINEAGE_LINEAR_COALBEDO_EQUATION", "observed"])
    log = str(e.loc["FU96_LINEAGE_LOG_COALBEDO_EQUATION", "observed"])
    asym = str(e.loc["FU96_LINEAGE_ASYMMETRY_SCATTERING_WEIGHTED_EQUATION", "observed"])
    assert "beta_lambda" in lin
    assert "beta_lambda" in log
    assert "omega_lambda * beta_lambda" in asym

def test_step3q17_gate_is_corrected_but_fail_closed():
    g = build_fu96_rrtmg_band_weighting_provenance_gate().iloc[0]
    assert g["qualification_state"] == STATE
    assert bool(g["FU96_LINEAGE_COALBEDO_BETA_WEIGHTING_TRANSCRIPTION_CORRECTED"])
    assert bool(g["FU96_LINEAGE_ASYMMETRY_SCATTERING_WEIGHTING_QUALIFIED"])
    assert bool(g["FU96_LINEAGE_SIMPLE_SOLAR_ONLY_COALBEDO_WEIGHTING_FORBIDDEN"])
    assert not bool(g["RRTM_SW_PREAVERAGING_GENERATOR_RECOVERED"])
    assert not bool(g["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"])
    assert not bool(g["TAU_ICE_PRODUCTION_ALLOWED"])

def test_step3q17_contract_identity():
    c = fu96_rrtmg_band_weighting_provenance_contract_payload()
    assert __version__ == "1.0.0-R5.7.41.3.4.10.30.20"
    assert c["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_20"
    assert c["qualification_state"] == STATE
    assert c["science_baseline"] == "R5.7.41.2_SHADOW_COT_AB_FROZEN"
    assert c["production_guards"]["physics_promotion_allowed"] is False
