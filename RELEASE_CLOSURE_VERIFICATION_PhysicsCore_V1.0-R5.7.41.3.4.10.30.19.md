# Taiwan Firecloud PhysicsCore V1.0 — Release Closure Verification

## R5.7.41.3.4.10.30.19

**Step 3Q.19 — Fu Primary-Band Forward-Reconstruction Input Qualification**

### Closure gates
- Frozen science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`
- Full regression: `993/993 PASS`
- Step3Q lineage: `66/66 PASS`
- New Step3Q.19 tests: `3/3 PASS`
- PRE-CLOSURE ZIP: `1296 members`, CRC PASS, `0` cache/pyc
- PRE-CLOSURE fresh-extract verifier: PASS
- PRE-CLOSURE fresh-extract Step3Q: `66/66 PASS`
- PRE-CLOSURE fresh-extract collection: `993 tests`
- V1_19 evidence/gate/contract regeneration: BYTE-EXACT PASS

### Qualified increment
- Fu Eq.3.9 primary solar coefficient input set recovered: `True`
- Executable Fu primary-band diagnostic forward model: `True`
- Cross-repository solar coefficient replication: `90/90`
- RRTMG forward generation process documented: `True`
- Band25 direct-copy exact reproduction from Fu primary broad coefficients: `False`
- Exact RRTMG fine spectral-grid realization recovered: `False`

### Fail-close
- `PREAVERAGING_SPECTRAL_SAMPLES_RECOVERED=False`
- `RRTM_SW_PREAVERAGING_GENERATOR_RECOVERED=False`
- `RRTMG_FINE_SPECTRAL_GRID_REALIZATION_RECOVERED=False`
- `RRTMG_BAND24_EXACT_REPRODUCTION_PASS=False`
- `RRTMG_BAND25_EXACT_REPRODUCTION_PASS=False`
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`
- `TAU_ICE_PRODUCTION_ALLOWED=False`
- `PRODUCTION_ICE_OPTICS_READY=False`
- `physics_promotion_allowed=False`

Step 3R remains blocked.

### Final FULL-CLEAN verification
- FINAL ZIP members: `1297`
- FINAL ZIP CRC: PASS
- FINAL ZIP cache/pyc: `0`
- FINAL fresh-extract verifier: PASS
- FINAL fresh-extract Step3Q: `66/66 PASS`
- FINAL fresh-extract collection: `993 tests`
- FINAL V1_19 evidence/gate/contract regeneration: BYTE-EXACT PASS
