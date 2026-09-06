# RELEASE NOTES — Taiwan Firecloud PhysicsCore V1.0-R5.7.10

## Firecloud Shared Geometry Core V1.2

- Added authoritative `firecloud/shared_geometry/intersections.py`.
- Added `VoxelIntersectionPlan` and `LatticeSignature`.
- Moved Sun→voxel nearest-height / upstream-segment geometry out of `model.py`; `prepare_shared_ray_geometry_plan()` is now a compatibility wrapper.
- Exact lattice guard prevents reuse across mismatched distance/height grids.
- Plan remains geometry-only: it contains no cloud fraction, condensate, COT, aerosol, gas, optical depth, or transmission.
- `performance_diagnostics.csv` now records `geometry_plan_type`, `target_plan_count`, `segment_count`, and `valid_segment_count` for `SHARED_RAY_GEOMETRY_PLAN`.
- Added R5.7.10 contract tests for geometry-only plan content, nearest-height tie behavior, workload counters, and lattice mismatch fallback.
- No changes to Formation, Viewing, Photography Decision, six-band wavelengths, Missing semantics, or scientific thresholds.

## Validation

- Full regression suite: **307 passed / 0 failed**.
