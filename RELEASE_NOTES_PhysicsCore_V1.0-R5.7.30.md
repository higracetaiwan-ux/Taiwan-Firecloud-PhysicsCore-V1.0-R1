# Taiwan Firecloud PhysicsCore V1.0-R5.7.30 Release Notes

## Independent Twilight Glow third branch

R5.7.30 closes the previously reserved Glow/Twilight Glow architecture as an
independent six-band evidence branch. It evaluates molecular Rayleigh
single-scattering source proxies at forward atmospheric volumes using the
existing Sun-path evidence and a separately integrated atmosphere-to-observer
path.

The release adds:

- `firecloud/twilight_glow.py`;
- `TwilightGlowResult` in the immutable contracts layer;
- 550/575/600/650/700/750 nm incident, extinction, Rayleigh and source-proxy
  fields;
- one volume-level CASE table and one 13-angle summary table;
- six Analysis Integrity guards and two required CASE archive members;
- production pipeline, performance trace and core-summary handoff;
- regression tests for spectral monotonicity, arithmetic closure, missing-data
  behavior, 13-angle retention, branch independence and archive wiring.

## Scientific boundary

This release does not claim absolute sky radiance. Aerosol source scattering,
multiple scattering and calibrated volume integration remain explicitly
unresolved. The Glow output is not a Formation score, not a Canvas, not a
Viewing result and not a Photography modifier.

## Verification

- working tree: 481 passed / 0 failed;
- old R5.7.29.1 CASE replay: 1092 volumes, 13 angles, no false Full result;
- final FULL-CLEAN unpack regression and SHA256 are recorded in the versioned
  current-project state delivered with the archive.
