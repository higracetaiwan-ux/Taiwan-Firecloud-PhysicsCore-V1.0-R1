# TEST REPORT — V1.0-R5.7.41.3.4.10.23.1

## Working-tree verification

- Full regression: **874/874 PASS**
- Runtime: 49.23 s
- Warning: 1 existing pandas FutureWarning
- New `.10.23.1` hotfix tests: **2/2 PASS**

## TDD evidence

Initial RED:
- CAMS isolated child returned `TIMEOUT_DEFERRED` while durable checkpoint remained `STARTED/RUNNING`.
- `stable_evidence_float` did not exist, so Step 3J evidence could preserve platform-dependent final-ULP drift.

GREEN:
- `TIMEOUT_DEFERRED` now writes a terminal durable checkpoint with role, elapsed, PID, exit code, error and worker-file provenance.
- Step 3J evidence floats now use 16 significant digits; the observed pair `35.736078690506133` / `35.736078690506126` serializes identically as `35.73607869050613`.

## Deterministic evidence verification

From the current `.10.23.1` code:

- Step 3J evidence: 12 rows, **byte-exact regeneration PASS**
- Step 3J gate: 1 row, **byte-exact regeneration PASS**
- Step 3J contract: **byte-exact regeneration PASS**

The Step 3J science identifier remains `R5.7.41.3.4.10.23`; `.10.23.1` is a release/archive reproducibility hotfix and does not change the Step 3J equations.

## Candidate FULL-CLEAN verification

- ZIP members: **1129**
- cache / pyc / pyo artifacts: **0**
- fresh-extract version: `1.0.0-R5.7.41.3.4.10.23.1`
- fresh-extract full regression: **874/874 PASS**
- Runtime: 61.09 s
- Warning: 1 existing pandas FutureWarning
- fresh-extract Step 3J evidence/gate/contract regeneration: **all byte-exact PASS**

## FIELD basis

`.10.23` TWS091 + TWS100 established **FIELD SCIENCE PASS** for Step 3J. TWS100 exposed the CAMS archive telemetry defect fixed in `.10.23.1`: request audit reached `TIMEOUT_DEFERRED` while the durable pressure-level-bundle checkpoint remained `RUNNING`.

## Final package gate

The immutable final FULL-CLEAN ZIP is rebuilt after this report update. Final fresh-extract regression and SHA256 are verified after ZIP creation; those immutable-package results are reported alongside the release artifact.
