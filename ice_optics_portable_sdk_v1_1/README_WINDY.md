# Firecloud Ice Optics Portable Package — Dmax-first V1.1

This package is a released science artifact generated and validated by Taiwan Firecloud PhysicsCore.

**Runtime architecture:** WINDY does not call PhysicsCore. WINDY loads `ice_optics_lut_v1.json` (or CSV) and evaluates locally with `windy/iceOpticsEvaluator.mjs` or an equivalent TypeScript port.

Rules:
- fixed bands: 550/575/600/650/700/750 nm
- authoritative runtime size axis: `maximum_dimension_um` (Dmax)
- `effective_radius_um` is source-row-derived diagnostic/mapping metadata, not the six-band lookup key
- `tau_ice = IWP * k_ext`
- `T = exp(-tau)`
- Dmax interpolation only within the same habit + roughness
- no Dmax extrapolation; no habit/roughness interpolation
- Missing != Clear != Zero
- positive IWP never receives a fabricated Dmax, r_eff->Dmax conversion, habit, roughness, or k_ext

If WINDY does not have a native/calibrated Dmax or a separately validated microphysics mapping, positive-IWP evaluation must remain `ICE_MAXIMUM_DIMENSION_MISSING`.

Before a WINDY release, run `node validation/validatePackage.mjs`.

This SDK intentionally contains no optical coefficients. Build the released consumer ZIP only from a calibrated authoritative LUT.
