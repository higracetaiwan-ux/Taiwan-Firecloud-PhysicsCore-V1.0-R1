# Taiwan Firecloud PhysicsCore V1.0-R5.7.8

## Firecloud Shared Geometry Core V1.0

R5.7.8 establishes a single-source geometry layer without changing scientific decisions.

### Added
- `firecloud/shared_geometry/earth.py` — spherical Earth curvature, shadow altitude, destination point, Dynamic REZ geometry.
- `firecloud/shared_geometry/solar.py` — finite solar disk / G0 penumbra primitives.
- `firecloud/shared_geometry/ray.py` — scalar and vectorized Sun→Cloud ray altitude plus Cloud→Observer curved-Earth LOS height.
- `firecloud/shared_geometry/context.py` — explicit in-analysis geometry reuse scopes (`event_fixed`, `angle_fixed`, `target_fixed`). Persistent Geometry Atlas is intentionally deferred until route/refraction schemas are frozen.

### Migration
- `firecloud.geometry` is now a backward-compatible facade; existing imports continue to work.
- `model.py` no longer owns a second vectorized solar-ray equation.
- `viewing.py` and `precipitation.py` no longer own separate observer LOS equations.
- Legacy private helper aliases remain only for compatibility and point to the shared implementation.

### Scientific invariants
- Geometry remains separate from spectral RT and cloud optical evidence.
- Formation remains Sun→CloudBase; Viewing remains Cloud→Observer.
- Missing != Clear != Zero.
- No COT, CF, RH, extinction, transmission, Brightness or Redness is manufactured by Shared Geometry Core.

### Validation
- 301 tests passed, 0 failed.
- Scalar/vectorized solar-ray equivalence is tested at 1e-12 absolute tolerance.
- Viewing and precipitation are tested to share the same LOS primitive.
