# TEST REPORT — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.22

## Working-tree verification

- Step 3I core/handoff/UI focused: **12 passed**.
- Step 3G–3I focused regression: **33 passed**.
- Full pytest regression: **864 passed, 1 warning**.

Warning is the pre-existing pandas `FutureWarning` in `test_r5732_glow_observer_aerosol_coverage.py`; no new test warning/error was introduced by Step 3I.

## Scientific gate verification

PASS:
- coordinate inheritance
- Yang/Bi single-column diagnostic Cext reconstruction
- dual-mass semantic separation
- diagnostic numeric bridge executability

Remain false / blocked:
- direct shape compatibility
- projected-area equivalence
- volume/mass equivalence
- independent Eq.(6) external numeric corroboration
- scientific mass closure
- habit / roughness bridge
- bulk Yang/Bi PSD integration eligibility
- GFSv16 Dmax mapping eligibility
- Production Ice Optics
- physics promotion

## Packaging verification

Final FULL-CLEAN package verification:
- 1078 members
- 0 cache / pyc / pyo artifacts
- required Step 3I code/tests/docs/evidence/gate/contract present
- clean fresh-extract full pytest: **864 passed, 1 warning, exit code 0**
- Step 3I evidence/gate/contract deterministic regeneration: exact match
- package SHA256 is recorded in the matching `.sha256` file.
