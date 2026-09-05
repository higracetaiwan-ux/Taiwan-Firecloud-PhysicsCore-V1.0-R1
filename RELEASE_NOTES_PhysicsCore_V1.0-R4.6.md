# Taiwan Firecloud PhysicsCore V1.0-R4.6

## Formation Completion Foundation

- Target Canvas geometry and target optical readiness are now explicit separate states.
- `CF_CLOUD_CONDENSATE_ZERO` remains a geometric Canvas candidate but cannot create COT/radiance.
- Optical Bottleneck now reports the strongest resolved native-condensate slant-cloud tau even when other path components remain uncertain.
- Cloud optical validation names distinguish scene-resolved horizontal support from ray-intersected resolved support.
- Added `v1_formation_prerequisites.csv` to expose unresolved 550 nm gas spectroscopy, precipitation-path optics, target Canvas optics, and full six-band path readiness without fabricating data.
- No distance weighting, cloud-type multiplier, surface-rain-to-tau conversion, or 550 nm interpolation is introduced.
