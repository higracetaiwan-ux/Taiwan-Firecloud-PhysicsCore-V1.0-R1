# Taiwan Firecloud PhysicsCore V1.0-R5.7.7


R5.7.7 operational focus: Physics shared-state performance optimization. Angle-specific Sun→cloud ray geometry is prepared once and reused by proxy-cloud and native-microphysics optical blocking branches when they share the same route/vertical lattice. Provider decoded caches and API efficiency auditing from R5.7.5/R5.7.6 remain enabled. No scientific thresholds or physical equations changed.

R5.7 continues from the verified R5.6.1 baseline. It keeps Formation, Viewing and Photography Decision physically separate while adding forecast-native 3-D hydrometeor optics and an independent Cloud→Observer six-band extinction branch.

## R5.7 additions

- GFS native RWMR / SNMR / GRLE hydrometeor fields are requested and preserved as 3-D forecast evidence. Surface rain rate is never converted to optical depth.
- Sun→CloudBase precipitation optical depth is integrated from native hydrometeor volume with an explicit large-particle visible-band Tier-1 optical model.
- Cloud→Observer precipitation extinction is integrated independently along the viewing ray.
- Viewing geometry uses angular-footprint projected cloud volumes and continuous cloud-fraction interpolation only across vertically continuous adjacent forecast nodes.
- Cloud→Observer six-band gas / aerosol / cloud / precipitation diagnostics are exported separately from Formation RT. No Sun→CloudBase transmission is reused.
- Photography Decision receives Viewing spectral readiness as a diagnostic only; no uncalibrated spectral threshold rewrites Formation or the geometry decision.
- Full Six-Band Formation closure now has a forecast-native precipitation path source when native hydrometeor volume is available. Remaining Missing components stay Missing.

Core invariants remain frozen: Formation != Viewing != Glow; Penumbra Geometry != Spectral RT; Missing != Clear != Zero; Cloud Fraction != COT; Satellite Observation != Forecast Input; Brightness != Redness != Effective Illuminated Area.

See `RELEASE_NOTES_PhysicsCore_V1.0-R5.7.md` and `IMPLEMENTATION_STATUS_PhysicsCore_V1.0-R5.7.md`.
