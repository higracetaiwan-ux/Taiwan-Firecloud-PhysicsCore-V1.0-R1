# Taiwan Firecloud PhysicsCore V1.0-R5.7.31 Release Notes

## Twilight Glow Full Six-Band Extinction Phase 1

R5.7.31 extends only the independent Twilight Glow branch. The existing atmospheric volume
grid is preserved, but the two optical legs are now exported separately and fail closed:

1. `Sun → Atmospheric Scatter Volume`
2. `Scatter Volume → Observer`

Each leg preserves 550/575/600/650/700/750 nm and publishes explicit Rayleigh, non-O3 gas,
O3, aerosol, cloud and precipitation optical depth. Total optical depth and transmission are
published only when every required component is complete.

O3 is split from the existing HITRAN gas total, so the final total is:

`Rayleigh + (O2+H2O) + O3 + aerosol + cloud + precipitation`

rather than `gas_total + O3`, preventing Chappuis absorption from being double counted.

## New CASE evidence

- `v1_twilight_glow_sun_to_scatter_extinction_550_750nm.csv`
- `v1_twilight_glow_scatter_to_observer_extinction_550_750nm.csv`
- `v1_twilight_glow_single_scattering_550_750nm.csv`

The original Glow volume and 13-angle summary tables remain preserved.

## Integrity hardening

R5.7.31 adds version-gated checks for:

- Sun-to-scatter exact volume coverage;
- scatter-to-observer exact volume coverage;
- six-band component schema;
- Sun-path component-sum / transmission / finite-solar-disk incident closure;
- observer-path component-sum / transmission closure;
- single-scattering source-proxy closure.

Partial evidence may retain diagnostic component tau values but cannot publish final total
transmission or source proxy. R5.7.30 historical CASEs are not reclassified by these new
R5.7.31-only checks.

## Scientific boundary

This release still does not claim absolute sky radiance. Aerosol SSA, aerosol phase function,
multiple scattering, surface coupling, polarization and radiometric calibration remain
unresolved. `calibrated_glow_radiance_available=False` remains mandatory.

Glow remains independent from Firecloud Formation, Viewing and Photography Decision.

## Verification

- focused regression: 12 passed / 0 failed;
- full working-tree regression: 486 passed / 0 failed;
- final FULL-CLEAN unpack regression and SHA256 are recorded after packaging.
