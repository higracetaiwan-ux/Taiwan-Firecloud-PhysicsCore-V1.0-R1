# RELEASE NOTES — Taiwan Firecloud PhysicsCore V1.0-R5.7.11

## Firecloud Shared Geometry Core V1.3

- Added angle-independent `VoxelIntersectionTopology` and deterministic `voxel_lattice_key()`.
- Identical direction/distance/height lattices are reused across solar-altitude candidates; angle-dependent ray results are never reused across angles.
- Added `ray_altitude_matrix_km()` to evaluate all target heights at one target distance in a single broadcast matrix.
- `materialize_voxel_intersection_plan()` now batches by target distance while preserving legacy nearest-height tie behavior, valid-ray mask, slant-length rule, and compatibility target dictionaries.
- CASE performance diagnostics now separate `SHARED_VOXEL_TOPOLOGY` from `SHARED_RAY_GEOMETRY_PLAN` and record topology cache status plus topology/materialization timing.
- Exact lattice mismatch remains fail-safe: no geometry plan reuse across incompatible provider grids.
- No scientific weights, thresholds, cloud optics, RT equations, Formation/Viewing definitions, or Missing semantics changed.

## Validation

- R5.7.10 CASE vs R5.7.9: Formation, Viewing, Photography, F_sun, penumbra, precipitation, Viewing spectral, and six-band optical-path outputs were numerically identical.
- R5.7.10 geometry workload: 7,452 target plans and 253,368 segments per angle; valid segments decrease physically as solar altitude falls.
- CASE-scale geometry micro-benchmark: nine-angle plan construction reduced from about 2.85 s (target-level materialization) to about 0.49 s using topology reuse + distance-batched ray matrices (~5.9x).
- Full regression: 310 passed / 0 failed.
