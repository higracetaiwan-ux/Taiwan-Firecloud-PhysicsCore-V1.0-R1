# Taiwan Firecloud PhysicsCore — Current Project State V1.0-R5.7.35.1

Current production candidate: `Taiwan Firecloud PhysicsCore V1.0-R5.7.35.1`.

## Field-closed foundations
- R5.7.28 adjacent CAMS spectral fallback: FIELD CLOSED.
- R5.7.32 CAMS geopotential normalization / long-range Glow aerosol coverage: FIELD CLOSED.
- R5.7.33 molecular deep-range closure / cloud conflict preservation: FIELD CLOSED.
- R5.7.33.1 native-3D aerosol readiness Integrity hotfix: FIELD CLOSED.
- R5.7.34 phased stateful ADS deadline + request-ID persistence: FIELD PASS; true reattach/no-duplicate-submit remains FIELD OPEN until a real timeout/recovery event occurs.

## R5.7.35 field result
Aerosol Scattering Physics Phase 1 passed the 2026-09-09 sunset CASE:
- Analysis Integrity 57/57 PASS.
- CASE Integrity 23/23 PASS.
- Both CAMS aerosol-scattering column-property requests succeeded.
- 1092/1092 rows had six-band AOD/SSA/asymmetry-g evidence with exact/bounded-native provenance and no extrapolation.
- 220/1092 aerosol single-scattering proxies were READY; 872 remained unresolved due upstream path extinction availability.
- Direct arithmetic replay passed; no Missing row was promoted.

R5.7.35 physics is FIELD PASS. A diagnostic gap was found: unresolved aerosol rows did not export their inherited path missing reason.

## R5.7.35.1
Diagnostic-only hotfix:
- hand off upstream `glow_missing_components` into aerosol evidence,
- add band-level aerosol-property/path reasons,
- add `TWILIGHT_GLOW_AEROSOL_SCATTERING_MISSING_REASON_COVERAGE`.

Offline immutable R5.7.35 CASE replay:
- 220 READY / 872 UNRESOLVED unchanged,
- 872/872 unresolved rows now have reasons (862 Sun→Scatter only; 10 Sun→Scatter + Scatter→Observer),
- numeric/missing patterns unchanged except ~7.2e-16 floating-point recomputation noise.

Working-tree regression: **514/514 PASS**.
R5.7.35.1 field validation: OPEN.

## Frozen science
Formation / Viewing / Twilight Glow remain independent. Runtime angles remain 0 to -6 degrees in 0.5-degree steps. Six wavelengths remain 550/575/600/650/700/750 nm. Missing != Clear != Zero != N/A. Column SSA/g are never promoted to a 3-D profile. Glow never promotes Firecloud Formation or Photography Opportunity.

## Next science
After R5.7.35.1 field confirmation: Canvas Optical Truth/COT closure and calibrated Tier2 cloud directional scattering remain higher firecloud-formation priorities; Multiple Scattering Foundation and absolute radiometric calibration remain future Glow work.
