# Implementation Status — PhysicsCore V1.0-R5.7.21

## Status
**IMPLEMENTED / REGRESSION PASS**

## Implemented
1. Coordinate-aware event timezone resolution.
2. Global IANA resolution via `timezonefinder` when installed.
3. Deterministic no-dependency fallback for Taiwan, western Japan/Ryukyu, then longitude fixed offset.
4. Explicit `AUTO_COORDINATE` / `USER_OVERRIDE` contract.
5. Manual override mismatch warning without silent rewrite.
6. UTC-canonical solar geometry so physical solar state is timezone-representation invariant.
7. Analysis-worker propagation of timezone mode/effective timezone.
8. Streamlit timezone diagnostics / manual override control.
9. CASE evidence:
   - `event_time_contract.csv`
   - `event_timezone_resolution.json`
10. Summary UTC/timezone provenance.

## Japan REAL_CANVAS regression relevance
The user intentionally selected 33.376°N, 130.31°E because that region had suitable cloud coverage. Under R5.7.21, this coordinate resolves to `Asia/Tokyo` instead of inheriting `Asia/Taipei`. A 0° sunset checkpoint is therefore stored with Japan civil time and the corresponding UTC instant rather than a Taiwan clock label.

## Not changed
The R5.7.20 Tier-2 calibration package, production solver gate, 4-D interpolation, exact/bounded semantics, Formation, Viewing, and all science thresholds remain unchanged.

## Regression
**370 passed / 0 failed**

## Next development focus
Return to the Tier-2 science path: generate/ingest the first genuine calibrated liquid-cloud scattering LUT and validate it against the R5.7.20/R5.7.21 Japan REAL_CANVAS regression CASE. Until that calibrated dataset exists, Tier-2 production response remains correctly gated.
