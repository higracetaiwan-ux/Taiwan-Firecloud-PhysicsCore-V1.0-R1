# R5.7.35.1 — Aerosol Scattering Missing-Reason Handoff

## Contract
An aerosol-scattering row may be `GLOW_AEROSOL_SINGLE_SCATTERING_PROXY_READY` only when all required six-band evidence is complete. Any unresolved or partial row must expose at least one explicit missing/conflict reason.

## Inherited path reasons
The aerosol branch inherits path-level causes already established by the independent Glow extinction chain:
- `SUN_TO_SCATTER_EXTINCTION`
- `SCATTER_TO_OBSERVER_EXTINCTION`

## Aerosol-property reasons
When applicable, the row may additionally expose:
- `NATIVE_3D_EXTINCTION_532`
- `AOD532_ANCHOR`
- `AOD_<WAVELENGTH>NM`
- `SSA_<WAVELENGTH>NM`
- `ASYMMETRY_G_<WAVELENGTH>NM`
- `AOD532_VS_NATIVE_3D_EXTINCTION_CONFLICT`

## Non-negotiable invariants
- Missing != Clear != Zero != N/A.
- No fixed SSA or asymmetry-g.
- No wavelength extrapolation.
- Column SSA/g are not a 3-D profile.
- No aerosol proxy is promoted when incident or observer-path evidence is missing.
- This hotfix changes diagnostics only, not the R5.7.35 scattering numbers.

## Integrity
`TWILIGHT_GLOW_AEROSOL_SCATTERING_MISSING_REASON_COVERAGE` fails if any non-READY aerosol scattering row has an empty reason field.
