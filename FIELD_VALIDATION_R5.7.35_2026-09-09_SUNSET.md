# Field Validation — R5.7.35 / 2026-09-09 Sunset

## Integrity
- Analysis Integrity: **57 PASS / 0 WARN / 0 FAIL**.
- CASE Integrity: **23 PASS / 0 WARN / 0 FAIL**.
- All four R5.7.35 aerosol-scattering guards: PASS.

## CAMS aerosol scattering provider
Eight CAMS requests were archived; both `AEROSOL_SCATTERING_COLUMN_PROPERTIES` requests completed successfully. Native AOD/SSA/asymmetry-g fields were present together with native 3-D aerext532. R5.7.34 stateful deadlines remained active (queue 75 s, running 120 s, total 180 s); no reattach was needed in this CASE.

## Six-band aerosol optical properties
All 1092 Glow volumes had AOD/SSA/asymmetry-g values at 550/575/600/650/700/750 nm. Provenance was exact at 550 nm and bounded-native interpolation at 575/600, 650, and 700/750 nm; no extrapolation occurred.

Observed ranges across the Glow evidence included approximately:
- SSA: 0.9609–0.9790 across the six bands.
- asymmetry g: 0.7006–0.7355 across the six bands.
- AOD decreased spectrally from roughly 0.149–0.203 at 550 nm to 0.105–0.148 at 750 nm for the exported target rows.

## Numeric closure
Direct recomputation confirmed:
- beta_ext(lambda) = beta_ext(532) * AOD(lambda)/AOD532.
- beta_sca = beta_ext * SSA.
- HG phase function from native g.
- aerosol proxy = incident * observer transmission * aerosol source coefficient.
- combined proxy = Rayleigh proxy + aerosol proxy.

Maximum residuals were at floating-point scale (HG ~6.7e-16; source/proxy terms ~1e-20 to 1e-21 scale); zero Missing rows were promoted to a final aerosol or combined proxy.

## Readiness
- Aerosol single-scattering proxy READY: **220 / 1092**.
- UNRESOLVED: **872 / 1092**.
- The 220 READY volume identities exactly matched the existing Rayleigh-proxy READY identities.
- Absolute calibrated Glow radiance remained unavailable by contract.

## Diagnostic issue discovered
All 872 unresolved aerosol rows had a blank `glow_aerosol_missing_components` field even though upstream path evidence carried explicit causes. Offline analysis showed 862 were `SUN_TO_SCATTER_EXTINCTION` and 10 were `SCATTER_TO_OBSERVER_EXTINCTION;SUN_TO_SCATTER_EXTINCTION`.

Therefore R5.7.35 aerosol scattering **physics field-passed**, while missing-reason diagnostics required the R5.7.35.1 handoff hotfix. The original CASE remains immutable.
