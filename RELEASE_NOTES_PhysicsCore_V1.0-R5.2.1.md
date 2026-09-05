# Taiwan Firecloud PhysicsCore V1.0-R5.2.1 — Full 0–100 km Penumbra Matrix

## Scope
R5.2.1 extends the finite-solar-disk Earth-shadow / penumbra diagnostic from the previous 10/20/30/40 km sample to the complete shared adaptive Canvas grid from 0 to 100 km.

## Shared distance grid
- 0–40 km: 5 km spacing
- 40–100 km: 10 km spacing
- Effective points: 0, 5, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 90, 100 km
- Sampling spacing is numerical support only and is never interpreted as cloud horizontal width.

## Physics retained
For every core solar altitude (0 to −4 deg, 0.5 deg step) and every shared distance point the CASE now exports:
- H_any_sun: lower finite-solar-disk penumbra boundary
- H_solar_center: traditional center-of-Sun Earth-shadow diagnostic height
- H_full_solar_disk: upper penumbra boundary / full disk visible

Formation still uses F_sun and Sun→CloudBase spectral transmission. No fixed effective-red-height threshold is invented.

## CASE
`v1_earth_shadow_penumbra_matrix.csv` now contains 9 × 15 = 135 rows for the core angle window.

## Compatibility
R5.2.1 contains the R5.2 finite-solar-disk penumbra/red-illumination logic and the R5.1 secondary forecast-native cloud microphysics contract.
