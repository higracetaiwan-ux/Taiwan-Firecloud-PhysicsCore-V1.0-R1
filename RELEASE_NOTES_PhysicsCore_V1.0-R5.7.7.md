# Taiwan Firecloud PhysicsCore V1.0-R5.7.7

## Physics Shared-State Performance Optimization

R5.7.7 continues the R5.7 performance line without changing scientific equations, thresholds, evidence semantics, or Formation/Viewing separation.

### Changes
- Adds `prepare_shared_ray_geometry_plan()` for angle-specific Sun→cloud ray geometry.
- Reuses the same Earth-curvature ray heights, upstream segment geometry, slant path lengths, and nearest vertical-voxel mapping between:
  - proxy pressure-profile cloud optical blocking; and
  - native GFS microphysical optical blocking.
- Cloud occupancy, condensate, extinction, tau and transmission remain branch-specific; only geometry is shared.
- Includes strict route/vertical-lattice equality checks. A mismatch automatically falls back to the original independent calculation path.
- Adds `SHARED_RAY_GEOMETRY_PLAN` to performance diagnostics.

### Validation
- R5.7.6 CASE-scale one-angle comparison showed identical proxy/native output values column-by-column.
- Measured combined proxy/native blocker runtime improved from ~1.07 s to ~0.83 s for the representative angle (~22% reduction for these two branches).
- Full regression: 297 passed / 0 failed.

### Frozen science
- Formation remains Sun→CloudBase.
- Viewing remains Cloud→Observer.
- Penumbra Geometry remains independent from Spectral RT.
- Six bands remain 550/575/600/650/700/750 nm.
- Missing != Clear != Zero; CF/RH/geometry never fabricate COT.
