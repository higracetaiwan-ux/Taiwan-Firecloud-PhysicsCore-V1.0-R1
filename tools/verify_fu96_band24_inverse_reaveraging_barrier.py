#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import build_fu96_rrtmg_band_weighting_provenance_gate

g=build_fu96_rrtmg_band_weighting_provenance_gate().iloc[0]
assert bool(g["FU96_PRIMARY_0P700UM_SPECTRAL_BOUNDARY_PINNED"])
assert bool(g["RRTMG_BAND25_WITHIN_SINGLE_FU96_PRIMARY_BAND_QUALIFIED"])
assert bool(g["RRTMG_BAND24_STRADDLES_FU96_PRIMARY_0P700UM_BOUNDARY_QUALIFIED"])
assert bool(g["RRTMG_BAND24_FINAL_TABLE_INVERSE_REAVERAGING_NONUNIQUE_QUALIFIED"])
assert not bool(g["RRTMG_BAND24_FINAL_TABLE_INVERSE_REAVERAGING_UNIQUE"])
assert not bool(g["FINAL_TABLE_INVERSE_IDENTIFICATION_ALLOWED"])
assert not bool(g["EXACT_FU96_BAND_WEIGHTING_AVAILABLE"])
print("PASS: Fu96 0.700 um boundary and Band-24 inverse re-averaging barrier are qualified; exact historical weighting remains fail-closed.")
