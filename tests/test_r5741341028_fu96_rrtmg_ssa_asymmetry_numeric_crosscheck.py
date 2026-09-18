from pathlib import Path
import json
import math
import pandas as pd


def test_step3o_reference_table_is_pinned_and_complete():
    path = Path(__file__).resolve().parents[1] / "firecloud" / "data" / "ice_optics" / "fu96_rrtmg_visible_band24_25_reference_v1.csv"
    assert path.exists()
    df = pd.read_csv(path)
    assert len(df) == 92
    assert set(df["rrtmg_band"].astype(int)) == {24, 25}
    for band in (24, 25):
        sub = df[df["rrtmg_band"].astype(int) == band].sort_values("dge_um")
        assert sub["dge_um"].tolist() == [float(v) for v in range(5, 141, 3)]
        assert sub["single_scattering_albedo"].between(0.0, 1.0).all()
        assert sub["asymmetry_parameter"].between(0.0, 1.0).all()
        assert (sub["extinction_coefficient_per_iwc"] > 0.0).all()
    assert set(df["source_sha"]) == {"0ccf597d6aa3d6ed40ec592560e3ed94b653ef32"}


def test_step3o_numeric_crosscheck_grid_executes_but_stays_fail_closed():
    from firecloud.ice_microphysics_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck import (
        run_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_grid,
        build_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_evidence,
        build_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_gate,
    )
    result = run_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_grid()
    assert result["comparison_row_count"] == 54
    assert result["population_state_count"] == 27
    assert result["dge_domain_pass"] is True
    assert 5.0 <= result["minimum_dge_um"] <= result["maximum_dge_um"] <= 140.0
    assert result["numeric_crosscheck_executed_pass"] is True
    assert math.isfinite(result["max_ssa_sample_mean_absolute_difference"])
    assert math.isfinite(result["max_asymmetry_sample_mean_absolute_difference"])
    assert result["max_ssa_sample_mean_absolute_difference"] < 1.0e-3
    assert result["max_asymmetry_sample_mean_absolute_difference"] < 0.1
    assert result["independent_ssa_validation_pass"] is False
    assert result["independent_asymmetry_validation_pass"] is False
    assert result["full_six_band_like_for_like_optical_validation_pass"] is False
    assert result["tau_ice_production_allowed"] is False
    assert result["production_ice_optics_ready"] is False
    assert result["physics_promotion_allowed"] is False

    evidence = build_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_evidence()
    gate = build_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_gate(evidence)
    assert not evidence.empty
    assert len(gate) == 1
    row = gate.iloc[0].to_dict()
    assert bool(row["NUMERIC_CROSSCHECK_EXECUTED_PASS"])
    assert bool(row["DGE_BRIDGE_EXECUTED_PASS"])
    assert not bool(row["INDEPENDENT_SSA_VALIDATION_PASS"])
    assert not bool(row["INDEPENDENT_ASYMMETRY_VALIDATION_PASS"])
    assert not bool(row["FULL_SIX_BAND_LIKE_FOR_LIKE_OPTICAL_VALIDATION_PASS"])
    assert not bool(row["TAU_ICE_PRODUCTION_ALLOWED"])
    assert not bool(row["PRODUCTION_ICE_OPTICS_READY"])
    assert not bool(row["physics_promotion_allowed"])


def test_step3o_contract_is_deterministic_and_declares_spectral_blocker():
    from firecloud.ice_microphysics_fu96_rrtmg_ssa_asymmetry_numeric_crosscheck import (
        fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_contract_payload,
    )
    a = fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_contract_payload(
        physicscore_version="1.0.0-R5.7.41.3.4.10.28.1"
    )
    b = fu96_rrtmg_ssa_asymmetry_numeric_crosscheck_contract_payload(
        physicscore_version="1.0.0-R5.7.41.3.4.10.28.1"
    )
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert a["contract_version"] == "FIRECLOUD_ICE_FU96_RRTMG_SSA_ASYMMETRY_NUMERIC_CROSSCHECK_V1"
    assert a["numeric_crosscheck_executed_pass"] is True
    assert a["rrtmg_reference_is_broad_band"] is True
    assert a["yang_reference_is_six_monochromatic_samples_only"] is True
    assert a["full_band_spectral_weighting_available"] is False
    assert a["independent_ssa_validation_pass"] is False
    assert a["independent_asymmetry_validation_pass"] is False
    assert a["full_six_band_like_for_like_optical_validation_pass"] is False
    assert a["tau_ice_production_allowed"] is False
    assert a["production_ice_optics_ready"] is False
    assert a["physics_promotion_allowed"] is False
