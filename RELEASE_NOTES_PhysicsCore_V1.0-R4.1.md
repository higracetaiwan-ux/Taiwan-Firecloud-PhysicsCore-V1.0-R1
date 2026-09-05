# Taiwan Firecloud PhysicsCore V1.0-R4.1 Release Notes

## Native Cloud Optical Evidence Bridge

- Derives `CloudLayer.cot` only from native liquid/ice condensate with native pressure/temperature support.
- Uses the existing bulk visible geometric-optics extinction model with explicit assumed effective radii: liquid 10 µm, ice 30 µm. Assumptions are preserved in provenance.
- Integrates optical depth on native model levels; resampled 0.5-km visualization voxels do not define CloudLayer physics.
- `GEOMETRY_ONLY` and missing condensate remain `cot = Missing`; RH/cloud fraction/base/top never fabricate optical depth.
- `CloudLayer.effective_radius_um`, `cot`, optical-evidence state and derived-physics provenance are exported in V1 CASE tables.
- R4 Formation may consume `CloudLayer.cot` directly; it no longer requires a legacy spectral voxel to carry target vertical COT.
- Ray-cloud intersection audit now exposes layer vertical COT, phase and effective radius.
- Upstream cloud slant optical depth remains fail-closed: route-column COT is not converted into an invented horizontal cloud thickness.
- Existing R3.1 Missing semantics, R3.3 performance foundation, six-band contracts and R4 no-score Formation contract remain unchanged.

## Validation

- New R4.1 bridge tests verify native-condensate COT, geometry-only fail-closed behavior, and Formation consumption of native CloudLayer COT.
- Full suite: 196 passed / 9 known Legacy V8 stale-contract failures.
