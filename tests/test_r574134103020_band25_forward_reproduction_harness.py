from firecloud import __version__
from firecloud.fu96_rrtmg_band25_reproduction import (
    BAND25_WAVELENGTH_MIN_UM,
    BAND25_WAVELENGTH_MAX_UM,
    build_band25_direct_primary_control_residuals,
    summarize_band25_direct_primary_control,
    band25_reproduction_prerequisite_matrix,
    band25_reproduction_diagnostic_payload,
)
from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    STEP3Q_VERSION,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)


def test_step3q20_band25_reference_geometry_and_residual_harness():
    assert __version__ == "1.0.0-R5.7.41.3.4.10.30.20"
    assert STEP3Q_VERSION == "R5.7.41.3.4.10.30.20"
    assert abs(BAND25_WAVELENGTH_MIN_UM - 0.4415011037527594) < 1e-15
    assert BAND25_WAVELENGTH_MAX_UM == 0.625
    r = build_band25_direct_primary_control_residuals()
    assert len(r) == 46
    assert r.dge_um.tolist() == [float(x) for x in range(5, 141, 3)]
    assert not r.exact_reproduction_claim_allowed.any()
    assert not r.physics_promotion_allowed.any()


def test_step3q20_band25_residual_topology_is_deterministic_negative_control():
    s = summarize_band25_direct_primary_control()
    assert s.reference_node_count == 46
    assert s.extinction_residual_monotonic_nonincreasing is True
    assert s.extinction_residual_zero_crossing_count == 1
    assert s.extinction_first_zero_crossing_bracket_um == (107.0, 110.0)
    assert s.ssa_residual_all_negative is True
    assert s.asymmetry_residual_all_negative is True
    assert abs(s.extinction_relative_rmse_over_mean - 0.004781123955386967) < 1e-15
    assert abs(s.ssa_relative_rmse_over_mean - 3.790091528184389e-06) < 1e-18
    assert abs(s.asymmetry_relative_rmse_over_mean - 0.0010955150422100914) < 1e-15
    assert s.exact_band25_reproduction_pass is False
    assert s.production_promotion_allowed is False


def test_step3q20_prerequisite_matrix_and_contract_remain_fail_closed():
    p = band25_reproduction_prerequisite_matrix()
    assert p["RRTMG_BAND25_PINNED_REFERENCE_GRID_46_NODES"] is True
    assert p["RRTMG_BAND25_FORWARD_REPRODUCTION_HARNESS_READY"] is True
    assert p["RRTMG_BAND25_DIRECT_PRIMARY_CONTROL_RESIDUAL_TOPOLOGY_QUALIFIED"] is True
    assert p["RRTMG_BAND25_FINE_SPECTRAL_GRID_REALIZATION_RECOVERED"] is False
    assert p["RRTMG_BAND25_EXACT_HISTORICAL_SOLAR_WEIGHTS_RECOVERED"] is False
    assert p["RRTMG_BAND25_EXACT_REPRODUCTION_PASS"] is False
    assert p["TAU_ICE_PRODUCTION_ALLOWED"] is False
    assert p["PRODUCTION_ICE_OPTICS_READY"] is False

    d = band25_reproduction_diagnostic_payload()
    assert d["schema"] == "twfc.fu96-rrtmg-band25-reproduction-diagnostic.v1"
    assert "fine_spectral_grid_nodes" in d["missing_exact_historical_inputs"]
    assert d["production_promotion_allowed"] is False

    g = build_fu96_rrtmg_band_weighting_provenance_gate().iloc[0]
    assert bool(g["RRTMG_BAND25_FORWARD_REPRODUCTION_HARNESS_READY"])
    assert bool(g["RRTMG_BAND25_DIRECT_PRIMARY_CONTROL_RESIDUAL_TOPOLOGY_QUALIFIED"])
    assert not bool(g["RRTMG_BAND25_EXACT_REPRODUCTION_PASS"])
    assert not bool(g["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"])
    assert not bool(g["PRODUCTION_ICE_OPTICS_READY"])


def test_step3q20_contract_equation_strings_match_corrected_beta_weighting():
    c = fu96_rrtmg_band_weighting_provenance_contract_payload()
    assert c["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_20"
    q = c["qualified_weighting_semantic_class"]
    assert q["historical_fu96_alpha_linear"] == "sum(alpha_lambda*beta_lambda*S_lambda*dLambda)/sum(beta_lambda*S_lambda*dLambda)"
    assert q["historical_fu96_alpha_log"] == "exp(sum(ln(alpha_lambda)*beta_lambda*S_lambda*dLambda)/sum(beta_lambda*S_lambda*dLambda))"
    assert c["production_guards"]["physics_promotion_allowed"] is False
