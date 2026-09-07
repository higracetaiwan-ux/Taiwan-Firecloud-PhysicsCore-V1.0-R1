# Taiwan Firecloud PhysicsCore V1.0-R5.7.12

## Firecloud Shared Geometry Core V1.4

- Added `firecloud/shared_geometry/vertical.py` as the single source for vertical-cell indexing.
- Added `VerticalIndexPlan` with nearest-cell, bracketing and closed-interval overlap lookup.
- Preserved the existing midpoint tie rule: exact midpoint chooses the lower vertical cell.
- `VoxelIntersectionPlan` now uses the shared vertical index instead of its own `searchsorted` implementation.
- Native GFS cloud-volume interpolation now uses the same shared bracketing primitive.
- Vertical index plans are built once per direction/profile, not inside target/z hot loops.
- No change to Formation, Viewing, Photography Decision, COT rules or six-band RT formulas.

## Physical data-state semantics correction

- Added explicit `NATIVE_CLOUD_CONDENSATE` readiness auditing for 0–100 km Canvas native CLWMR/ICMR.
- Complete native condensate fields that are physically zero are now `AVAILABLE_PHYSICALLY_ZERO` with completeness 1.0, never Missing.
- Target-dependent `SPECTRAL_AEROSOL_PATH` and `FULL_SPECTRAL_RT` become `NOT_APPLICABLE / NOT_APPLICABLE_NO_CANVAS_TARGET` when Formation has no Canvas target.
- `NOT_APPLICABLE` layers are excluded from the operational completeness denominator instead of forcing headline completeness to 0%.
- `NO_CANVAS_EVIDENCE` angles are excluded from legacy score-based operational selection and are labeled `NO CANVAS EVIDENCE`.
- UI now explicitly distinguishes `PHYSICALLY_ZERO ≠ MISSING` and no longer claims Native CLWMR/ICMR is unavailable when the field is present but zero.
- Missing native evidence remains fail-closed; RH/cloud fraction are still never used to fabricate COT/COD.

## R5.7.11 CASE acceptance (2026-09-07 sunset)

- Cross-angle topology: first angle `MISS_BUILT`, remaining angles `HIT_CROSS_ANGLE`.
- Workload remained fixed at 7,452 target plans and 253,368 segments per angle.
- Shared ray geometry plan total across nine angles: ~1.06 s.
- All-angle physics total: ~55.4 s.
- Total to CASE archive: ~259.7 s.
- 0–180 km route/native cloud data were present and complete; native condensate was physically zero, so `NO_CANVAS_EVIDENCE` was data-supported rather than a reconstruction gap.

## Verification

- 317 tests passed / 0 failed.
