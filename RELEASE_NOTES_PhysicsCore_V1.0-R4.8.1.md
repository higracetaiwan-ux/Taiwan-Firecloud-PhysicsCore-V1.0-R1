# Taiwan Firecloud PhysicsCore V1.0-R4.8.1 Release Notes

## Incremental 550 nm LUT Builder

R4.8.1 removes the unnecessary full six-band rebuild when a validated 360-row 575/600/650/700/750 nm derived Runtime LUT is already present.

### Changes
- Strictly validate the existing 360-row derived Runtime LUT before reuse.
- If a manifest is present, verify the CSV SHA-256 against the manifest.
- Require exactly H2O/O2/O3, 575/600/650/700/750 nm, 4 temperatures, 6 pressures, 12.5 nm half-width, non-negative finite coefficients, and no duplicate states.
- Compute **only 550 nm** from the local 535–765 nm H2O/O2 HITRAN tables and O3 Serdyuchenko–Gorshelev XSC.
- New computation = 3 gases × 24 T/P states = **72 rows**. H2O/O2 Voigt work is only 48 T/P states over the 537.5–562.5 nm band; O3 contributes 24 direct band integrations.
- Merge validated legacy 360 rows + new 72 rows → strict **432-row six-band Runtime LUT**.
- Preserve state checkpoint/resume for the new 550 nm H2O/O2 calculations.
- Never interpolate 550 nm from 575/600 nm.
- Streamlit UI now labels the operation as incremental 550 nm completion rather than a full 432-state rebuild.

No Formation weights, thresholds, cloud physics, ray geometry, or decision logic were changed.

## Regression tests
- Focused R4.8.1 / six-band tests: 12 passed.
- Full suite: 228 passed, 8 known legacy failures (unchanged legacy V8/CAMS/cloud-optics expectations).
