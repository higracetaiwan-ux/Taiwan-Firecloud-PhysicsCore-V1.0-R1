# Taiwan Firecloud PhysicsCore V1.0-R4.4

## Scope
Cloud Optical Validation + Six-band Spectral Color Foundation.

## Added
- `firecloud/spectral_color.py` for retained-band-only spectral colour diagnostics.
- CIE 1931 2-degree sampled XYZ/x/y integration over 550/575/600/650/700/750 nm only.
- No blue/blue-green extrapolation or invented short-wave energy.
- Deep-red-tail and warm-red spectral-shape diagnostics retained separately from Brightness.
- `firecloud/optical_validation.py` with per-angle condensate/slant-RT validation state.
- CASE outputs:
  - `v1_spectral_colour_550_750nm.csv`
  - `v1_cloud_optical_validation.csv`
- UI audit panels for spectral colour and cloud optical validation.

## Preserved physical boundaries
- Missing six-band radiance → colour remains Missing.
- `GEOMETRY_ONLY` never becomes COT/COD.
- Sampling spacing is not cloud horizontal thickness.
- No fixed cloud-type multiplier, no distance weighting, no single Formation Score.
- Target Canvas COT remains Canvas-response evidence, not upstream path extinction.
- 550 nm gas remains Missing until verified spectroscopy is available.

## Validation
- New R4.4 tests: 4/4 passed.
- R4.4 + R4.3 + R4.2 + R4.1 + R4 Formation focused tests: 15/15 passed.
- Full suite: 205 passed / 9 known Legacy V8 stale-contract failures.
