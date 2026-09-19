#!/usr/bin/env python3
"""Verify Step 3Q.20 Band25 forward-reproduction harness and fail-close gates."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from firecloud.fu96_rrtmg_band25_reproduction import (
    build_band25_direct_primary_control_residuals,
    summarize_band25_direct_primary_control,
    band25_reproduction_prerequisite_matrix,
    band25_reproduction_diagnostic_payload,
)
from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)


def main() -> None:
    residuals = build_band25_direct_primary_control_residuals()
    summary = summarize_band25_direct_primary_control()
    prereq = band25_reproduction_prerequisite_matrix()
    diag = band25_reproduction_diagnostic_payload()
    contract = fu96_rrtmg_band_weighting_provenance_contract_payload()

    assert len(residuals) == 46
    assert summary.extinction_residual_monotonic_nonincreasing
    assert summary.extinction_residual_zero_crossing_count == 1
    assert summary.extinction_first_zero_crossing_bracket_um == (107.0, 110.0)
    assert summary.ssa_residual_all_negative
    assert summary.asymmetry_residual_all_negative
    assert abs(summary.extinction_relative_rmse_over_mean - 0.004781123955386967) < 1e-15
    assert abs(summary.asymmetry_relative_rmse_over_mean - 0.0010955150422100914) < 1e-15
    assert prereq["RRTMG_BAND25_FORWARD_REPRODUCTION_HARNESS_READY"] is True
    assert prereq["RRTMG_BAND25_EXACT_REPRODUCTION_PASS"] is False
    assert prereq["PRODUCTION_ICE_OPTICS_READY"] is False
    assert diag["production_promotion_allowed"] is False

    sem = contract["qualified_weighting_semantic_class"]
    assert "beta_lambda" in sem["historical_fu96_alpha_linear"]
    assert "beta_lambda" in sem["historical_fu96_alpha_log"]
    assert contract["production_guards"]["physics_promotion_allowed"] is False

    print("PASS Step3Q.20 Band25 forward-reproduction harness")
    print("reference_nodes=", len(residuals))
    print("ext_rel_rmse_over_mean=", summary.extinction_relative_rmse_over_mean)
    print("ssa_rel_rmse_over_mean=", summary.ssa_relative_rmse_over_mean)
    print("asy_rel_rmse_over_mean=", summary.asymmetry_relative_rmse_over_mean)
    print("ext_zero_crossing_bracket_um=", summary.extinction_first_zero_crossing_bracket_um)
    print("exact_band25_reproduction_pass=", prereq["RRTMG_BAND25_EXACT_REPRODUCTION_PASS"])


if __name__ == "__main__":
    main()
