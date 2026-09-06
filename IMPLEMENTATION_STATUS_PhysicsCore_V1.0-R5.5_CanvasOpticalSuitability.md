# Implementation Status — PhysicsCore V1.0-R5.5

## Completed

- R5.4 retained as the sole baseline.
- Added intrinsic `Canvas Optical Suitability` module.
- Added Thin / Suitable / Thick / Unknown target-cloud states.
- Exact COT only may produce a categorical suitability state.
- Missing and bounded optical evidence fail closed to `OPTICS_UNKNOWN`.
- Added scattering interaction proxy and escape/self-shield weighted response-capacity proxy.
- Added cloud phase, effective radius and physical cloud thickness diagnostics without using them to fabricate COT.
- Added explicit audit flags proving suitability does not consume Penumbra geometry or Spectral RT.
- Added CASE CSV exports and tests.

## Preserved separations

- Formation != Viewing != Glow
- Penumbra Geometry != Spectral RT
- Spectral RT != Target Canvas Optical Response
- Missing != Zero != Clear
- Cloud Fraction != COT
- RH != COT
- Geometry != Optical Evidence
- Brightness != Redness != Effective Illuminated Area

## Still unresolved after R5.5

- Ground-truth calibration of Thin/Suitable/Thick regime boundaries.
- Tier-2 phase-function / effective-radius-aware multiple scattering.
- Tier-3 full target-cloud radiative transfer.
- 3-D precipitation optical evidence.
- Full Formation closure where path optics remain Missing.
- Viewing branch parity and independent Glow branch.
