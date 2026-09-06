# Taiwan Firecloud PhysicsCore V1.0-R5.5.1 Implementation Status

## Status: INTEGRATED / REGRESSION-STABLE AGAINST R5.4

### Implemented

- ECMWF IFS local/entitled secondary forecast-native Target Optics provider retained.
- DWD ICON Global QC/QI secondary fallback integrated.
- Provider arbitration and request audit integrated.
- Target Canvas Optical Evidence consumes the selected forecast-native secondary evidence.
- Canvas Optical Suitability consumes Target Optical Evidence as an independent intrinsic target-cloud layer.
- `TOO_THIN / OPTICALLY_SUITABLE / TOO_THICK / OPTICS_UNKNOWN` retained.
- Missing, conflict, and bounded-only optics remain fail-closed / Unknown.
- CASE packaging includes both provider audit CSVs and Canvas Optical Suitability CSVs.

### Frozen boundaries

- Penumbra Geometry does not determine COT or optical suitability.
- Spectral RT does not determine target-cloud COT regime.
- Canvas Optical Suitability does not consume `F_sun` or Sun→CloudBase transmission.
- Formation / Viewing / Glow remain separate.
- Missing != Clear != Zero.
- Cloud Fraction != COT; RH != COT; Geometry != Optical Evidence.
- Satellite observation is not a future forecast optics input.

### Validation

- Focused integration tests: 25 passed.
- Full suite: 259 passed / 10 pre-existing legacy failures.
- No new R5.5.1 regression failures relative to the R5.4 baseline.

### Remaining work after R5.5.1

1. Operational user-run validation of the DWD ICON live network chain and cache behavior.
2. Ground-truth calibration of thin/suitable/thick optical-depth regimes.
3. Mature Tier-2/Tier-3 target cloud scattering response using phase / effective radius / multiple scattering.
4. Precipitation 3-D optical path closure.
5. Full Formation closure while retaining Brightness / Redness / Effective Illuminated Area separately.
