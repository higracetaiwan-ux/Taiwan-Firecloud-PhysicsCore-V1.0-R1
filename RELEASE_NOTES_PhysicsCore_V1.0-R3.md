# Taiwan Firecloud PhysicsCore V1.0-R3

## Scope

R3 connects the R2 CloudScene / Canvas-specific geometry runtime to the first formal V1.0 spectral optical-path and cloud-base illumination contracts. It is still a checkpoint release: Formation, Viewing, Twilight Glow, Peak Window and Decision Layer are not yet connected.

## Implemented in R3

- Added V1 `OpticalPathResult` and `CloudBaseIllumination` contracts.
- Added native-CloudScene-based Canvas-specific `Sun→CloudBase` ray/cloud intersection audit. Fixed 100–440 km Legacy bands are not used to decide intersections.
- Preserved the frozen six spectral channels: **550 / 575 / 600 / 650 / 700 / 750 nm**.
- Existing route-resolved gas/aerosol/cloud RT is exposed only as `LEGACY_RT_EVIDENCE_BRIDGE_R3`; interpolated RT voxels do not rewrite native cloud geometry.
- Missing gas/aerosol/cloud evidence stays Missing. Missing is never converted to zero or clear.
- R3 does **not** invent precipitation optical depth. Until 3-D precipitation is connected, `tau_precip` remains Missing and the formal full `tau_total/transmission` cannot be claimed.
- A separate `known_component_tau / known_component_transmission` diagnostic is retained for the optical components that are actually known; it is not labelled Full RT.
- Earth-shadow dependency is propagated correctly: when `F_sun = 0`, direct cloud-base illumination is known zero even if downstream optical components are Missing.
- Added explicit V1 uncertainty rows and unresolved Optical Bottleneck diagnostics. No fake bottleneck segment is invented without segment-resolved full component optical depth.
- CASE archive now saves the R3 V1 tables.

## New CASE files

- `v1_ray_cloud_intersections.csv`
- `v1_spectral_optical_paths_550_750nm.csv`
- `v1_cloud_base_illumination_550_750nm.csv`
- `v1_prediction_uncertainty.csv`
- `v1_optical_bottlenecks.csv`

## Deliberately not yet implemented

- R1/R2 refracted geometry modes as the V1 main ray engine.
- Segment-resolved four-component optical bottleneck.
- 3-D precipitation volume and precipitation optical depth.
- Canvas multiple-scattering response / FormationResult.
- Viewing, Twilight Glow, Peak Window and Decision Layer.

The inherited V8 score/completeness/GO-NO-GO path remains only as a Legacy diagnostic compatibility branch and is not a V1 PhysicsCore result.
