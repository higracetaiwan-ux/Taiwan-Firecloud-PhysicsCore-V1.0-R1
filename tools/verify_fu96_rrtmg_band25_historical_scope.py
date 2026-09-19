from __future__ import annotations

from firecloud.fu96_rrtmg_band25_historical_scope import band25_historical_scope_matrix, pinned_runtime_scope_sources
from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import build_fu96_rrtmg_band_weighting_provenance_evidence, build_fu96_rrtmg_band_weighting_provenance_gate


def main() -> int:
    m=band25_historical_scope_matrix(); s=pinned_runtime_scope_sources()
    e=build_fu96_rrtmg_band_weighting_provenance_evidence()
    g=build_fu96_rrtmg_band_weighting_provenance_gate(e).iloc[0]
    checks = [
        m["FU96_LINEAGE_200_WAVELENGTH_SAMPLE_COUNT_QUALIFIED"] is True,
        m["FU96_LINEAGE_EXACT_200_WAVELENGTH_NODE_GRID_RECOVERED"] is False,
        s["fu96_lineage_single_scattering_wavelength_sample_count"] == 200,
        s["rrtmg_fu96_runtime_dge_step_um"] == 3.0,
        bool(g["RRTMG_FU96_RUNTIME_DGE_3UM_LINEAR_INTERPOLATION_PINNED"]),
        not bool(g["RRTMG_BAND25_RUNTIME_RWGT_IS_CLOUD_PREAVERAGING_SOLAR_WEIGHT_VECTOR"]),
        not bool(g["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"]),
        not bool(g["TAU_ICE_PRODUCTION_ALLOWED"]),
        not bool(g["PRODUCTION_ICE_OPTICS_READY"]),
        not bool(g["physics_promotion_allowed"]),
    ]
    if not all(checks):
        raise SystemExit("Step3Q.21 Band25 historical-scope verification FAILED")
    print("Step3Q.21 Band25 historical-scope verification: PASS")
    print("200-wavelength lineage constraint: qualified; exact wavelength nodes: NOT recovered")
    print("3-um Dge runtime interpolation: pinned; spectral pre-averaging substitution: forbidden")
    print("runtime rwgt/sfluxref -> historical cloud weights: forbidden")
    print("production promotion: fail-closed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
