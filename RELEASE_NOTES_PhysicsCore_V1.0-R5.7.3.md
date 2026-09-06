# Taiwan Firecloud PhysicsCore V1.0-R5.7.3

## Scope
Performance-stability hotfix for the post-angle aggregation stage. No scientific equations, thresholds, or Formation/Viewing separation are changed.

## Fixed
- Fixed apparent hang at progress message `彙整民用曙暮光時間軸與矩陣…` (0.93).
- `build_viewing_path_geometry()` no longer re-filters the full cloud-layer table for every target or recomputes projected support / continuous-CF neighbour searches repeatedly.
- `build_viewing_spectral_extinction()` now pre-indexes aerosol/gas/cloud route groups by time/angle/direction.
- Gas RT contexts are prepared once per route group instead of once per photographic target.
- Exact target COT lookup and cloud projected-support calculations are cached.

## Runtime verification
Using the prior full 2026-09-06 CASE-scale tables (594 canvas targets, 2520 cloud-layer rows, 35397 gas-profile rows):
- Viewing projected geometry aggregation: ~3.8 s.
- Viewing six-band spectral aggregation: ~2.9 s.
- Combined heavy R5.7 post-0.93 modules: <7 s in the local verification environment.

## Regression
- 289 tests passed, 0 failed.
- Numerical comparison on a complete single-angle slice matched R5.7.2 exactly for viewing state and obstruction fraction.

## Frozen science rules
- Penumbra Geometry remains independent of Spectral RT.
- Formation remains independent of Viewing.
- Missing != Zero != Clear.
- Viewing CF occupancy remains distinct from cloud COT.
