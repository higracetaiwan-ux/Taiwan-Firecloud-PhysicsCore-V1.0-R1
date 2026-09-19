from firecloud import __version__
from firecloud.fu96_primary_band_forward_model import (
    AP, BPS, CP, DPS, SOURCE_BLOB_SHA, coefficient_count,
    evaluate_fu96_primary_solar_band, PRODUCTION_PROMOTION_ALLOWED,
)
from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    STEP3Q_VERSION, build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)

def test_primary_band_coefficients_and_forward_evaluation():
    assert __version__ == "1.0.0-R5.7.41.3.4.10.30.19"
    assert STEP3Q_VERSION == "R5.7.41.3.4.10.30.19"
    assert coefficient_count() == 90
    assert SOURCE_BLOB_SHA == "0711455bbcb94e959c119bcc343db215e1149ecb"
    assert AP[0] == (-2.9172062e-05, 2.5192544, 0.0)
    v=evaluate_fu96_primary_solar_band(1,5.0)
    assert abs(v.mass_extinction_m2_g - 0.503821707938) < 1e-14
    assert abs(v.single_scattering_albedo - 0.9999993699909544) < 1e-14
    assert abs(v.asymmetry_factor - 0.7528826058637125) < 1e-14
    assert abs(v.forward_delta_fraction - 0.11705830388987501) < 1e-14
    assert PRODUCTION_PROMOTION_ALLOWED is False

def test_step3q19_evidence_and_gate_are_fail_closed():
    e=build_fu96_rrtmg_band_weighting_provenance_evidence()
    status=dict(zip(e.check_id,e.status))
    assert status["FU96_EQ39_PRIMARY_SOLAR_COEFFICIENT_INPUT_SET_RECOVERED"] == "PASS_QUALIFIED"
    assert status["FU96_PRIMARY_SOLAR_COEFFICIENT_CROSS_REPOSITORY_REPLICATION_90_OF_90"] == "PASS_QUALIFIED"
    assert status["RRTMG_BAND25_DIRECT_FU_PRIMARY_BROADBAND_COPY_REPRODUCTION"] == "PASS_MISMATCH_QUALIFIED"
    assert status["RRTMG_FINE_SPECTRAL_GRID_REALIZATION_RECOVERED"] == "BLOCKED_NOT_RECOVERED"
    g=build_fu96_rrtmg_band_weighting_provenance_gate(e).iloc[0]
    assert bool(g.FU96_PRIMARY_BAND_EQ39_COEFFICIENT_INPUT_SET_RECOVERED)
    assert bool(g.FU96_PRIMARY_BAND_FORWARD_MODEL_EXECUTABLE)
    assert bool(g.FU96_SOLAR_COEFFICIENT_REPLICATION_90_OF_90_QUALIFIED)
    assert bool(g.RRTMG_FORWARD_GENERATION_PROCESS_DOCUMENTED)
    assert not bool(g.RRTMG_BAND25_DIRECT_PRIMARY_BROADBAND_COPY_REPRODUCTION_PASS)
    assert not bool(g.RRTMG_FINE_SPECTRAL_GRID_REALIZATION_RECOVERED)
    assert not bool(g.EXACT_FU96_BAND_WEIGHTING_AVAILABLE)
    assert not bool(g.PRODUCTION_ICE_OPTICS_READY)

def test_step3q19_contract_scope_and_production_guard():
    p=fu96_rrtmg_band_weighting_provenance_contract_payload()
    assert p["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_19"
    assert p["qualification_state"] == "PASS_FAIL_CLOSED_FU96_PRIMARY_BAND_FORWARD_RECONSTRUCTION_INPUTS_QUALIFIED_RRTMG_FINE_GRID_AND_EXACT_BAND24_25_REALIZATION_UNRECOVERED"
    assert p["capabilities"]["FU96_PRIMARY_BAND_EQ39_COEFFICIENT_INPUT_SET_RECOVERED"] is True
    assert p["capabilities"]["RRTMG_FINE_SPECTRAL_GRID_REALIZATION_RECOVERED"] is False
    assert p["production_guards"]["production_ice_optics_ready"] is False
    assert any("direct_copy_of_fu_primary" in x for x in p["forbidden_substitutes"])
