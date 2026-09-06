# Implementation Status — PhysicsCore V1.0-R5.5

## Completed

- Secondary forecast-native optical provider arbitration.
- ECMWF IFS local/entitled provider retained.
- DWD ICON Global public network fallback implemented.
- Native QC/QI positive-condensate gate.
- T/P/FI fetched only for positive-condensate levels.
- Native-condensate COT derivation with explicit assumed effective-radius provenance.
- No CF/RH/geometry/satellite fabrication.
- Persistent file cache and process run/lead cache.
- CASE provider/download audits.
- R5.4 Brightness/Redness/Area and Penumbra/RT separation preserved.

## Awaiting user-run CASE validation

The first R5.5 CASE should verify:

1. `secondary_provider_audit.csv` selects `DWD_ICON_GLOBAL` when IFS is not configured.
2. `dwd_icon_request_audit.csv` contains `DOWNLOADED`/`CACHE_HIT`/`OK_*` records rather than provider Missing.
3. `v1_secondary_target_optics.csv` becomes non-empty if ICON has positive QC/QI on the route.
4. `v1_target_canvas_optical_evidence.csv` either promotes secondary exact evidence or preserves a primary/secondary disagreement without averaging.
5. If Target optics becomes ready, R5.4 spectral evolution can begin resolving Brightness/Redness/Area, subject to remaining precipitation/path optics.

## Still unresolved after R5.5

- 3-D precipitation optical evidence.
- Full six-band path wherever cloud/precip components remain Missing.
- Ground-truth calibration of effective red illumination and Canvas optical suitability.
- Viewing branch parity with Formation.
- Glow branch completion.
