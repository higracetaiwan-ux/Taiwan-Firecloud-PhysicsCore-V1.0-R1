# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.35.1

## Scope
A diagnostic-only hotfix on top of R5.7.35 Aerosol Scattering Physics Phase 1.

## Field finding from R5.7.35
The real 2026-09-09 sunset CASE passed all 57 Analysis Integrity checks and all 23 CASE Integrity checks. CAMS native aerosol-scattering AOD/SSA/asymmetry-g retrieval succeeded for both forecast times, six-band scattering arithmetic closed, and 220/1092 Glow volumes produced a complete aerosol single-scattering proxy.

However, the remaining 872 unresolved aerosol rows exported a blank `glow_aerosol_missing_components`, even though the upstream Rayleigh/Glow evidence had explicit path reasons: 862 `SUN_TO_SCATTER_EXTINCTION`, and 10 `SCATTER_TO_OBSERVER_EXTINCTION;SUN_TO_SCATTER_EXTINCTION`.

## Fix
- Inherit upstream `glow_missing_components` into `glow_aerosol_missing_components`.
- Add band-level reasons when AOD, SSA, asymmetry-g, incident irradiance or observer transmission is unavailable.
- Add Integrity guard `TWILIGHT_GLOW_AEROSOL_SCATTERING_MISSING_REASON_COVERAGE`.
- Require `glow_aerosol_missing_components` in the R5.7.35+ aerosol scattering schema.

## Science invariance
No change to AOD, SSA, asymmetry-g, HG phase function, native-3D extinction anchoring, beta-extinction, beta-scattering, aerosol source coefficient, aerosol proxy, Rayleigh+aerosol combined proxy, Formation, Viewing, Photography, angles or six wavelengths.

Offline immutable-CASE replay preserved 220 READY / 872 UNRESOLVED and all numeric/missing patterns; maximum recomputation difference was ~7.2e-16 floating-point noise.

## Regression
- Working tree: **514 passed / 0 failed**.
- FULL-CLEAN extracted regression: pending packaging verification at document creation time.
