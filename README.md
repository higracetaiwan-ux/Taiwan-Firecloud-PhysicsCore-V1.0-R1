# Taiwan Firecloud PhysicsCore V1.0-R5.7.12


R5.7.12 operational focus: Firecloud Shared Geometry Core V1.4. Vertical-cell lookup, nearest-height tie behavior, bracketing and layer-overlap indexing are now centralized in one geometry-only Vertical Index Core and reused by voxel intersections and native-cloud vertical interpolation. Scientific thresholds, Formation/Viewing separation, and six-band RT formulas are unchanged. R5.7.12 additionally fixes data-state semantics so Missing input, physically-zero native condensate, and no-target RT applicability are never conflated.

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
