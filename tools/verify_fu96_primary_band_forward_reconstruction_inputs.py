#!/usr/bin/env python3
"""Verify Step 3Q.19 Fu96 primary-band forward-reconstruction inputs."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from firecloud.fu96_primary_band_forward_model import coefficient_count,evaluate_fu96_primary_solar_band,PRODUCTION_PROMOTION_ALLOWED
from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import build_fu96_rrtmg_band_weighting_provenance_evidence,build_fu96_rrtmg_band_weighting_provenance_gate,fu96_rrtmg_band_weighting_provenance_contract_payload
def main():
 e=build_fu96_rrtmg_band_weighting_provenance_evidence(); g=build_fu96_rrtmg_band_weighting_provenance_gate(e).iloc[0]; c=fu96_rrtmg_band_weighting_provenance_contract_payload(evidence=e,gate=build_fu96_rrtmg_band_weighting_provenance_gate(e))
 assert coefficient_count()==90
 v=evaluate_fu96_primary_solar_band(1,5.0); assert abs(v.mass_extinction_m2_g-0.503821707938)<1e-14
 assert bool(g['FU96_PRIMARY_BAND_EQ39_COEFFICIENT_INPUT_SET_RECOVERED'])
 assert bool(g['FU96_SOLAR_COEFFICIENT_REPLICATION_90_OF_90_QUALIFIED'])
 assert bool(g['RRTMG_FORWARD_GENERATION_PROCESS_DOCUMENTED'])
 assert not bool(g['RRTMG_BAND25_DIRECT_PRIMARY_BROADBAND_COPY_REPRODUCTION_PASS'])
 assert not bool(g['RRTMG_FINE_SPECTRAL_GRID_REALIZATION_RECOVERED'])
 assert not bool(g['EXACT_FU96_BAND_WEIGHTING_AVAILABLE'])
 assert PRODUCTION_PROMOTION_ALLOWED is False
 assert c['contract_version']=='FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_19'
 print('PASS Step3Q.19 Fu96 primary-band forward-reconstruction input qualification')
 print('evidence_rows=',len(e),'gate_columns=',len(g.index))
 print('qualification_state=',c['qualification_state'])
if __name__=='__main__': main()
