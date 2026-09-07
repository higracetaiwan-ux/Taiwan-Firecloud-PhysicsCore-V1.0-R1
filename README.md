# Taiwan Firecloud PhysicsCore V1.0-R5.7.13


R5.7.13 operational focus: Firecloud Shared Geometry Core V1.5 Phase-1 Completion, rebuilt from the proven R5.7.11 stable baseline (not from the regressed R5.7.12 branch). Canonical geometry now includes Earth curvature/great-circle routing, WGS84 geodetic↔ECEF↔ENU transforms, ray–sphere intersection, Sun→CloudBase and Cloud→Observer ray primitives, finite-solar-disk/penumbra geometry, shared voxel topology/intersection plans, canonical vertical indexing/layer bounds, and cross-angle ray-matrix reuse. Formation, Viewing, cloud blocking, precipitation and gas RT consume the same geometry source-of-truth. No UI/completeness redesign and no scientific thresholds/weights are changed.

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
