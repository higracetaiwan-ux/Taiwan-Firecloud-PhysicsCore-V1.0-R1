# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.32

## Theme

**Glow Observer-Path Aerosol Coverage Robustness + CAMS Geopotential Unit Normalization**

## Fixed

1. CAMS `z` units `m**2 s**-2` are now correctly divided by standard gravity before export as geopotential height metres.
2. Unknown geopotential units fail closed instead of preserving dimensionally-wrong heights.
3. Glow-only 50 m lowest-native-level endpoint snap closes tiny near-observer pressure-level boundary gaps without AOD extrapolation.
4. Added provider normalization and 60/80/100 km Glow aerosol coverage Integrity guards.
5. Added observer aerosol segment/snap provenance to Glow detail/export.

## Field forensic replay

Using the immutable R5.7.31 2026-09-09 sunset CASE and changing only the known geopotential unit normalization, long-range aerosol coverage became 462/468. Enabling the Glow-only <=50 m endpoint snap closed the remaining six 100 km targets, yielding **468/468**. This is a forensic replay, not R5.7.32 field validation.

## Regression

Working tree: **492 passed / 0 failed**.

## Field status

OPEN — requires a new R5.7.32 CASE. Old CASE files remain immutable.
