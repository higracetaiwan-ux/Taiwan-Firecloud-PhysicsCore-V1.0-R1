# Release Notes — PhysicsCore V1.0-R5.7.13

## Scope
Shared Geometry Core V1.5 — Phase-1 Completion, based directly on R5.7.11 stable baseline. R5.7.12 UI/completeness changes are not included.

## Added canonical geometry primitives
- WGS84 geodetic ↔ ECEF
- ECEF ↔ ENU
- ray–sphere intersection
- canonical `VerticalIndexPlan` with legacy midpoint tie-to-lower rule
- canonical half-level layer bounds

## Migrations
- Gas RT ray-height matrix delegates to Shared Geometry Core.
- Precipitation Sun→CloudBase path uses shared ray sampler and shared sampled-path accumulator.
- Viewing spectral uses shared LOS directly, not a private alias from `viewing.py`.
- Profile-cloud and native-cloud blocking always consume a shared voxel intersection plan; duplicate local ray/nearest-cell fallback code was removed.
- Native cloud and pressure-profile interpolation use the canonical vertical index primitive.
- `optical_path.py` imports the canonical shared ray primitive directly.

## Intentionally deferred
- Taiwan Geometry Atlas
- persistent cross-event geometry warehouse
- all-site permanent precomputation
- full distance×height persistent LUT
- wavelength-dependent refracted geometry atlas

These remain Phase-2 work after route lattice, vertical lattice, refraction strategy and 3-D volume resolution are frozen.

## Scientific invariants
No change to Formation/Viewing separation, six-band definitions, thresholds, weights, COT semantics, Missing semantics, precipitation optics, or Photography Decision rules.

## Verification
- 316 tests passed / 0 failed.
- New contracts verify WGS84/ECEF/ENU round-trip, ray-sphere intersection, vertical midpoint tie rule, contiguous layer bounds, and Gas RT delegation to shared ray geometry.
