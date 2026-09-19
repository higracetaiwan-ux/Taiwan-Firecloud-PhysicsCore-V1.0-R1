#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
)

def main():
    e = build_fu96_rrtmg_band_weighting_provenance_evidence().set_index("check_id")
    g = build_fu96_rrtmg_band_weighting_provenance_gate().iloc[0]
    lin = str(e.loc["FU96_LINEAGE_LINEAR_COALBEDO_EQUATION", "observed"])
    log = str(e.loc["FU96_LINEAGE_LOG_COALBEDO_EQUATION", "observed"])
    asym = str(e.loc["FU96_LINEAGE_ASYMMETRY_SCATTERING_WEIGHTED_EQUATION", "observed"])
    assert "beta_lambda" in lin and "beta_lambda" in log
    assert "omega_lambda * beta_lambda" in asym
    assert bool(g["FU96_LINEAGE_COALBEDO_BETA_WEIGHTING_TRANSCRIPTION_CORRECTED"])
    assert bool(g["FU96_LINEAGE_ASYMMETRY_SCATTERING_WEIGHTING_QUALIFIED"])
    assert bool(g["FU96_LINEAGE_SIMPLE_SOLAR_ONLY_COALBEDO_WEIGHTING_FORBIDDEN"])
    assert not bool(g["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"])
    assert not bool(g["PRODUCTION_ICE_OPTICS_READY"])
    print("PASS: Fu96-lineage broadband weighting transcription is beta/scattering weighted and fail-closed.")

if __name__ == "__main__":
    main()
