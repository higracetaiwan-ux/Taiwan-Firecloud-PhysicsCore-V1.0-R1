#!/usr/bin/env python3
"""Deterministic Step 3Q.16 scope verifier for pinned AER RRTM_BAND_GEN evidence.

This verifier intentionally qualifies only the recovered molecular/k-distribution/Planck
pipeline scope. It MUST NOT promote Fu96 cloud pre-averaging generator recovery.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from firecloud.ice_microphysics_fu96_rrtmg_band_weighting_provenance import (
    build_fu96_rrtmg_band_weighting_provenance_evidence,
    build_fu96_rrtmg_band_weighting_provenance_gate,
    fu96_rrtmg_band_weighting_provenance_contract_payload,
)

def main():
    e=build_fu96_rrtmg_band_weighting_provenance_evidence()
    g=build_fu96_rrtmg_band_weighting_provenance_gate(e).iloc[0].to_dict()
    c=fu96_rrtmg_band_weighting_provenance_contract_payload(evidence=e)
    checks={
      "historical_aer_molecular_band_generation_pipeline_recovered": bool(g["AER_HISTORICAL_RRTM_MOLECULAR_BAND_GENERATION_PIPELINE_RECOVERED"]),
      "pipeline_is_fu96_cloud_preaveraging_generator": bool(g["AER_HISTORICAL_RRTM_BAND_GENERATION_PIPELINE_IS_FU96_CLOUD_PREAVERAGING_GENERATOR"]),
      "fu96_cloud_preaveraging_generator_recovered": bool(g["FU96_CLOUD_PREAVERAGING_GENERATOR_RECOVERED"]),
      "production_ice_optics_ready": bool(g["PRODUCTION_ICE_OPTICS_READY"]),
      "physics_promotion_allowed": bool(g["physics_promotion_allowed"]),
    }
    ok=(checks["historical_aer_molecular_band_generation_pipeline_recovered"] and not checks["pipeline_is_fu96_cloud_preaveraging_generator"] and not checks["fu96_cloud_preaveraging_generator_recovered"] and not checks["production_ice_optics_ready"] and not checks["physics_promotion_allowed"])
    print(json.dumps({"ok":ok,"contract_version":c["contract_version"],"step_version":c["step_version"],"qualification_state":c["qualification_state"],"checks":checks},indent=2,sort_keys=True))
    raise SystemExit(0 if ok else 2)

if __name__ == "__main__":
    main()
