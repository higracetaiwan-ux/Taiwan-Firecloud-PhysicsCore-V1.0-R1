# Taiwan Firecloud PhysicsCore V1.0-R4.8

## 550 nm Six-Band Spectroscopy Build Completion

- Corrected HITRAN source interval to the declared 535–765 nm coverage. The previous bootstrap constant still stopped at 560 nm, which could not physically support the 550±12.5 nm diagnostic band.
- Manual H2O import validation now requires source support through the 550 nm band. O2 preserves molecule-specific sparse/line-free-band handling: absence of an O2 transition in a diagnostic band is not itself treated as missing spectroscopy coverage.
- Streamlit build workflow now uses H2O_535_765 / O2_535_765 and builds the V1.0 six-band 432-state LUT directly.
- HITRAN readiness now recognizes a complete 432-state six-band grid and exposes six_band_550nm_ready.
- Legacy 288/360-row Runtime LUTs remain readable for diagnostics, but they do not satisfy the V1.0 six-band Formation prerequisite.
- No 550 nm coefficient is interpolated or fabricated. A true 550 nm READY state requires locally imported/downloaded H2O/O2 HITRAN transitions plus validated O3 XSC and a successful LUT build.

## Validation

- Focused R4.8 spectroscopy/build tests: 23 passed.
- Full suite: 224 passed / 8 known legacy failures. The remaining failures are stale V8 version/UI/manifest contracts, the historical CAMS TemporaryDirectory expectation, and the old cloud-optics far-path clear=1 expectation that conflicts with current Missing semantics.
