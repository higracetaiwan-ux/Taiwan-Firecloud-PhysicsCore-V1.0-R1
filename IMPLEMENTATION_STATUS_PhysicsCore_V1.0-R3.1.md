# PhysicsCore V1.0-R3.1 Implementation Status

## Completed in R3.1
- GEOMETRY_ONLY cloud optics remain Unknown; legacy transmission=1 no longer means tau_cloud=0.
- Ray-cloud intersections with unresolved optics expose POTENTIAL_BLOCKER_OPTICS_UNKNOWN.
- Single native occupied pressure/model levels receive finite half-level support from neighbouring native levels; multi-level clear-gap segmentation remains unchanged.
- Precipitation path branch connected fail-closed. Surface rain rate is not converted to 3-D optical depth.
- V1 six-band gas LUT build path added via `build_hitran_band_coefficients.py --v1-six-band`; local HITRAN tables expanded to the 535–765 nm naming contract. Existing embedded compatibility LUT remains fail-closed at 550 until a true six-band LUT is built/imported.
- CAMS native 3-D aerosol/O3 path and persistent cache retained.
- Gas-profile and aerosol spectral-derivation per-run/lead caches added.

## Not yet completed
- A packaged validated 550-nm H2O/O2 HITRAN LUT is not included; 550 gas remains Missing unless the user builds/imports the expanded local LUT.
- Precipitation 3-D volume/optical depth remains unresolved until a supported hydrometeor vertical source is connected.
- Formation/Canvas multiple-scattering response is intentionally deferred to R4.

## Regression
- New R3.1 + R3 + multilayer tests: 8/8 passed.
- Full suite: 185 passed, 9 failed. The 9 failures are the same Legacy V8/HITRAN/CAMS stale-contract set already present before R3.1; R3.1 introduced no new full-suite failures.
