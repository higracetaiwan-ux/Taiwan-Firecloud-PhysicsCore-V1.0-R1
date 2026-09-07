# RELEASE NOTES — PhysicsCore V1.0-R5.7.18

## Tier-2 Scattering LUT / Solver Foundation

Baseline: V1.0-R5.7.17 Tier-2 Scattering Readiness Contract.

### Added
- Shared-geometry `scattering_angle_deg()` for the physical Sun→Cloud→Observer scattering angle.
- `firecloud/tier2_scattering_foundation.py`.
- Strict six-band scattering LUT schema/calibration validator.
- CASE outputs:
  - `v1_tier2_scattering_foundation.csv`
  - `v1_tier2_scattering_foundation_summary.csv`
- Versioned LUT contract/template directory `tier2_scattering_lut/`.

### Frozen safety/physics behavior
- No calibrated Tier-2 scattering LUT is bundled.
- No production Tier-2 interpolation or radiance is enabled.
- Exact/bounded input readiness does not by itself authorize a Tier-2 response.
- COT conflict/missing remains blocking.
- Cloud Fraction, RH, geometry, and condensate-zero are never used to manufacture COT.
- Scattering angle is mandatory for future phase-function/LUT response.
- Formation thresholds, Viewing, Photography Decision, Tier-1 response and Shared Geometry Phase-1 behavior are unchanged.

### Foundation states
- `BLOCKED_INPUT_CONTRACT`
- `BLOCKED_SCATTERING_GEOMETRY`
- `INPUTS_AND_GEOMETRY_READY_AWAITING_CALIBRATED_LUT`
- `FOUNDATION_READY_CALIBRATED_LUT_AVAILABLE` (schema/calibration acceptance only; interpolation remains disabled)

### Tests
- 339 passed / 0 failed.
