# IMPLEMENTATION STATUS — PhysicsCore V1.0-R5.7.10

## Completed

- Firecloud Shared Geometry Core V1.2 authoritative voxel/layer intersection plan.
- Proxy-cloud and native-microphysics blocking continue to share the same angle-specific plan.
- Shared plan workload counters are visible in CASE performance diagnostics.
- Exact lattice mismatch fails safe to local legacy-compatible geometry calculation.

## Intentionally deferred

- Persistent cross-event Geometry Atlas / Observer Geometry Library.
- Wavelength-dependent refracted-ray atlas.
- Forced sharing across providers with non-identical vertical/horizontal lattices.
- Gas/Aerosol reuse is enabled only when a future lattice-compatibility contract is explicit; geometry is never coerced to make providers look compatible.

## Scientific invariants preserved

Formation ≠ Viewing ≠ Glow. Geometry ≠ Spectral RT ≠ target optical response. Missing ≠ Clear ≠ Zero. Cloud Fraction ≠ COT. RH ≠ COT.
