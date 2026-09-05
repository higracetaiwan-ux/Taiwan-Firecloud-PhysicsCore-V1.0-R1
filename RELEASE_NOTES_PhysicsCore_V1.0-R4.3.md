# Taiwan Firecloud PhysicsCore V1.0-R4.3

## Native Condensate Slant RT + Full Optical Path Bridge + Performance Indexing

R4.3 continues the R4.2 adaptive-sampling / native-condensate slant-blocker architecture without changing the frozen PhysicsCore V1.0 causality.

### Changes
- Added direction/distance spatial indexing for Canvas-specific ray/cloud intersection to avoid scanning every CloudLayer for every Canvas.
- Cached centre-point ray altitude per Canvas/distance for unresolved-support audit intersections.
- Preserved the R4.2 rule that sampling spacing is NOT cloud horizontal thickness.
- Added `v1_native_condensate_support_diagnostics.csv` with native optical layer count, resolved multi-column support count, resolved slant-intersection count, and unknown horizontal-support count.
- Added an end-to-end synthetic native-condensate regression case proving `RESOLVED_NATIVE_CONDENSATE_SLANT_RT` propagates into six-band cloud-path optical depth.
- Fixed the full-path completion bridge: when gas + aerosol + resolved upstream cloud + precipitation optical depths are all evidenced, R4.3 now computes `tau_total`, `transmission`, and `relative_base_illumination` rather than leaving them unset.
- `CloudBaseIllumination` now becomes `CONFIRMED_ILLUMINATED_FULL_PATH` only when all six spectral transmissions are complete and DirectSolarFraction > 0.
- Missing/geometry-only cloud optics remain fail-closed. No RH/cloud-fraction/base/top COT fabrication was introduced.

### Validation
- R4.3/R4.2/R4.1/R4 focused regression suite: 11 passed.
- Full suite: 201 passed, 9 known Legacy V8 stale-contract failures.
