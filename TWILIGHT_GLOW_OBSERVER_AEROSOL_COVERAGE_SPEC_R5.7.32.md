# R5.7.32 — Twilight Glow Observer-Path Aerosol Coverage Robustness

## Scope

This release fixes an evidence-geometry defect exposed by the R5.7.31 2026-09-09 sunset CASE. It does **not** add aerosol SSA, aerosol phase function, multiple scattering, or absolute radiance calibration.

## Root cause

CAMS GRIB pressure-level field `z` is geopotential. ecCodes reported units as `m**2 s**-2`. The former decoder matched spellings such as `m2` / `m^2` / `s-2` but missed the `**` spelling, so raw geopotential was sometimes stored as `cams_geopotential_height_m_*`. This inflated vertical coordinates by approximately `g0`.

## Frozen normalization

`H_gpm = geopotential / 9.80665` when provider units express energy per unit mass (`m**2 s**-2`, equivalent variants). Direct metres/gpm are retained. Unknown units fail closed.

## Glow-only endpoint tolerance

After correct unit normalization, a long `Scatter→Observer` segment midpoint can be a few metres below the lowest native CAMS pressure surface. Glow may snap only when the gap is `<= 0.05 km`, using the nearest lowest **native** `aerext532`. No AOD reconstruction, no fixed Angstrom, no route extension. Normal Viewing keeps tolerance `0.0 km`.

## Integrity

- `CAMS_GEOPOTENTIAL_HEIGHT_NORMALIZATION`: decoder provenance plus broad physical plausibility for 1000/500/30 hPa heights.
- `TWILIGHT_GLOW_OBSERVER_AEROSOL_LONG_RANGE_COVERAGE`: when real six-band CAMS payload is ready, all 60/80/100 km Glow observer targets must expose finite six-band aerosol optical depth.

## Non-goals

Formation, Viewing decision semantics, Photography, Glow single-scattering source physics, 13 solar angles, six wavelengths, provider route domain/resolution, and Forecast/Observation separation are unchanged.
