# Taiwan Firecloud PhysicsCore V1.0-R3.2 Release Notes

## Scope
R3.2 is the six-band gas-runtime and performance-foundation release. It does not change the frozen Formation/Viewing/Decision physics.

## Changes
- Runtime gas LUT loader now uses an mtime/size keyed process cache, avoiding repeated CSV parsing for every core-angle RT pass.
- Gas-band activation now supports the frozen 550/575/600/650/700/750 nm contract when a complete real six-band H2O/O2/O3 T/P grid is installed.
- 550 nm is fail-closed: it is enabled only when all three gases have a complete real LUT grid. No neighbouring-band interpolation or fabricated coefficient is allowed.
- Runtime LUT validator/importer recognizes a complete six-band table and validates its exact T/P/gas grid.
- Existing CAMS/O3 persistent cache, R3.1 Missing≠Clear≠Zero semantics, native layer support, precipitation fail-closed path and Canvas-specific optical-path contracts are preserved.

## Important deployment note
The packaged legacy runtime LUT may still lack real H2O/O2 550-nm coefficients. In that case 550-nm gas optical depth remains Missing by design until a real six-band LUT is built/imported with the supplied HITRAN builder. R3.2 never synthesizes 550-nm gas absorption.

## Performance target
R3.2 removes repeated runtime LUT I/O/preparation overhead and keeps reusable forecast/CAMS/aerosol/cloud bases cached. Full wall-clock improvement depends on network cache state and the number of unique valid-time atmospheric states; per-angle ray integration remains physically angle-specific.
