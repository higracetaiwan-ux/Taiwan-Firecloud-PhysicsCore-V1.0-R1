# Taiwan Firecloud PhysicsCore — Current Project State V1.0-R5.7.35

Current production candidate: `Taiwan Firecloud PhysicsCore V1.0-R5.7.35`.

## Closed before R5.7.35
- R5.7.28 adjacent CAMS spectral fallback: FIELD CLOSED.
- R5.7.32 CAMS geopotential normalization / long-range Glow aerosol coverage: FIELD CLOSED.
- R5.7.33 molecular deep-range closure / cloud conflict preservation: FIELD CLOSED.
- R5.7.33.1 native-3D aerosol readiness Integrity hotfix: FIELD CLOSED.

## R5.7.34 runtime status
Stateful phased ADS deadline and request-ID persistence are field-passed. True remote-job reattach/no-duplicate-submit recovery remains FIELD OPEN because the latest real CASE completed all CAMS requests on the first wait and did not trigger a reattach.

## R5.7.35
Aerosol Scattering Physics Phase 1 is code-complete:
- native CAMS AOD / SSA / asymmetry g,
- native 3-D aerext532 vertical anchor,
- bounded six-band interpolation,
- HG phase approximation from native g,
- aerosol and Rayleigh+aerosol relative single-scattering proxies,
- evidence-preserving Integrity closure.

Working-tree regression: 512/512 PASS.
Field validation: OPEN.

## Frozen science
Formation / Viewing / Twilight Glow remain independent. Runtime angles remain 0 to -6 degrees in 0.5-degree steps. Six wavelengths remain 550/575/600/650/700/750 nm. Missing != Clear != Zero != N/A. Glow never promotes Firecloud Formation or Photography Opportunity.

## Next after field validation
Multiple Scattering Foundation and eventual absolute radiometric calibration remain separate future work.
