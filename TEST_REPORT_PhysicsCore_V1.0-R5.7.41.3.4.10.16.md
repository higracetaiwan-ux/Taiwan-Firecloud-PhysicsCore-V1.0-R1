# TEST REPORT — V1.0-R5.7.41.3.4.10.16

## TDD
Initial Step 3C test was written before production implementation and failed at collection with:
`ModuleNotFoundError: firecloud.ice_microphysics_gfsv16_rei_dmax_bridge`

After minimal implementation/wiring:
- primary Step 3C: **7/7 PASS**
- targeted Phase2/Step2/Step3/Step3B/Ice optics: **60/60 PASS** after current-version assertion synchronization

## Full regression
- **807 passed**
- **0 failed**
- **1 existing pandas FutureWarning**
- elapsed: ~27.7 s

## Serialization sanity check
Step 3C release-static serialization:
- evidence: 13 rows / 7040 bytes
- gate: 1 row / 1389 bytes
- contract: 1999 bytes
- archive-content gates: 3/3 PASS

## Fresh extract — first packaged ZIP
- extracted version: `1.0.0-R5.7.41.3.4.10.16`
- 210 test files split into three groups to avoid execution-time ceiling
- group 1: 254 passed
- group 2: 363 passed, 1 existing pandas FutureWarning
- group 3: 190 passed
- total: **807 passed, 0 failed**

The report was then written back into the release tree; the final ZIP must be rebuilt and re-verified after this documentation update.
