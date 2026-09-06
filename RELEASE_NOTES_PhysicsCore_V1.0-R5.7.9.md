# PhysicsCore V1.0-R5.7.9 Release Notes

## Firecloud Shared Geometry Core V1.1

- Added shared Sun→Cloud and Cloud→Observer segment samplers.
- Added one shared slant-path accumulator preserving the legacy half-segment boundary rule.
- Migrated `optical_path`, Formation precipitation, Viewing geometry, and Viewing spectral cloud-path integration to the shared geometry primitive.
- Sun→Cloud segment sampling is vectorized.
- Short 17/25-point segment accumulations use an allocation-light loop; larger arrays use vectorized accumulation.
- Legacy geometry outputs remain numerically identical.

## Validation

- 304 tests passed, 0 failed.
- Shared Sun segment versus legacy scalar geometry: max absolute difference 0.
- Shared Viewing segment versus legacy scalar geometry: max absolute difference 0.
- Representative Sun-ray sampling micro-benchmark: about 3.2x faster.
- Representative short Viewing segment workload: about 1.31x faster after adaptive path accumulation.

No scientific thresholds, Formation/Viewing separation, six-band definitions, Missing semantics, COT logic, or Photography Decision rules were changed.
