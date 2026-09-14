# Firecloud Ice Optics Portable Package

This package is a released science artifact generated and validated by Taiwan Firecloud PhysicsCore.

**Runtime architecture:** WINDY does not call PhysicsCore. WINDY loads `ice_optics_lut_v1.json` (or CSV) and evaluates locally with `windy/iceOpticsEvaluator.mjs` or an equivalent TypeScript port.

Rules:
- fixed bands: 550/575/600/650/700/750 nm
- `tau_ice = IWP * k_ext`
- `T = exp(-tau)`
- no effective-radius extrapolation
- no habit/roughness interpolation
- Missing != Clear != Zero
- positive IWP never receives fabricated r_eff/habit/roughness/k_ext

Before a WINDY release, run `node validation/validatePackage.mjs`.

This SDK intentionally contains no optical coefficients. Use `tools/build_ice_optics_portable_package.py` with a calibrated LUT to produce the released consumer ZIP.
