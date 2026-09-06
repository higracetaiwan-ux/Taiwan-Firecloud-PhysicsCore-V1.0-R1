# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7

## Scope
R5.7 closes the next evidence-chain gaps identified by the 2026-09-06 sunset calibration case without collapsing Formation and Viewing.

## Added
- Forecast-native GFS hydrometeor contract: RWMR, SNMR, GRLE.
- Sun→CloudBase native 3-D precipitation-path optical integration.
- Cloud→Observer native 3-D precipitation-path optical integration.
- Independent Cloud→Observer six-band gas/aerosol/cloud/precipitation extinction tables.
- Angular-footprint Viewing occupancy with CF interpolation only across vertically continuous adjacent forecast nodes.
- New CASE files:
  - `v1_viewing_precipitation_evidence.csv`
  - `v1_viewing_spectral_extinction_550_750nm.csv`
  - `v1_viewing_spectral_summary.csv`

## Scientific boundaries
- Surface rain rate does not define tau_precip.
- Native hydrometeor Missing is never treated as zero.
- Large-particle precipitation extinction uses an explicit Tier-1 assumed-particle optical model and is labelled as such.
- Viewing spectral RT never reuses Sun→CloudBase RT.
- Viewing spectral state does not rewrite Formation.
- Target COT remains unresolved when no exact forecast-native target optical evidence exists.

## Verification
- Full regression suite: 287 passed, 0 failed.
