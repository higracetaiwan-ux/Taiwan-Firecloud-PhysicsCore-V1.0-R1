# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.35

## Theme
Aerosol Scattering Physics Phase 1 for independent Twilight Glow.

## Changes
- Added CAMS role `AEROSOL_SCATTERING_COLUMN_PROPERTIES`.
- Added native CAMS AOD 532/550/645/670/800 nm ingestion.
- Added native CAMS SSA 550/645/670/800 nm ingestion.
- Added native CAMS asymmetry factor 550/645/670/800 nm ingestion.
- Added bounded-only six-band spectral interpolation; wavelength extrapolation is prohibited.
- Added HG single-scattering phase approximation driven by native asymmetry g.
- Added native-3D-extinction anchored aerosol scattering coefficient and source proxy.
- Added `v1_twilight_glow_aerosol_scattering_550_750nm.csv`.
- Added Analysis Integrity guards for target coverage, schema, numerical closure, and no-extrapolation provenance.
- Updated Twilight Glow total-radiance state: SSA/phase evidence may now be available, but multiple scattering and absolute calibration are still unresolved.

## Runtime baseline retained
R5.7.34 CAMS ADS Stateful Deadline / Request-ID Recovery remains intact.

## Science intentionally unchanged
Formation Sun->CloudBase, Viewing Cloud->Observer, Photography Formation-first gate, 13 solar angles, six wavelengths, Canvas rules, Route Invariance, Red-Light Availability and Missing semantics are unchanged.

## Validation
- Working-tree regression: 512 passed / 0 failed.
- Field validation: OPEN.
