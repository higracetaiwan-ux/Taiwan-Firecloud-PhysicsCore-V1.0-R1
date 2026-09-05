# Taiwan Firecloud PhysicsCore V1.0-R4.9.1

## Packaged Six-Band Runtime LUT

- Embedded the user-validated 432-row Runtime gas spectroscopy LUT under `hitran_runtime/`.
- Embedded its matching manifest and SHA-256 provenance.
- Bands: 550, 575, 600, 650, 700, 750 nm.
- Gases: H2O, O2, O3.
- Grid: 4 temperatures × 6 pressures = 24 states per gas-band.
- CSV SHA-256: `5422d6e6414351acce99ffd1552807a82fad40bd2388af13ccecd5563909cb75`.
- 550 nm is direct spectroscopy output, not interpolation from 575/600 nm.
- Keeps all R4.9 Target Canvas Optical Evidence Resolver logic unchanged.

## Deployment behavior

A clean deployment can load the packaged 432-row LUT directly and report six-band Runtime spectroscopy READY without requiring the expensive LUT rebuild step.
