# Taiwan Firecloud PhysicsCore V1.0-R5.4 — Spectral Red-Window Evolution

## Purpose
R5.4 adds a diagnostic layer for the observed physical sequence in which high or more distant cloud can remain illuminated at lower solar altitude while the transmitted spectrum becomes progressively warmer/redder.

## Frozen separation
- Penumbra geometry remains `F_sun` only.
- Spectral RT remains `T_lambda` / CloudBase radiance only.
- Geometry never synthesizes spectral radiance.
- Brightness, Redness and Effective Illuminated Area retain separate peak windows; there is no single best angle and no Physics Score.

## New CASE tables
- `v1_canvas_spectral_evolution.csv`
- `v1_canvas_peak_windows.csv`

## Distance roles
- `0–40 km`: `PRIMARY_CANVAS_0_40KM`
- `>40–100 km`: `SECONDARY_CANVAS_40_100KM`
- `>100 km`: `HORIZON_RESIDUAL_100PLUS_DIAGNOSTIC_ONLY`

100+ km is retained only as a low-importance horizon residual diagnostic and does not become a primary photographic Canvas.

## Missing-data behavior
If Target optics / spectral RT are unresolved, the spectral-red window remains `MISSING_SPECTRAL_RT`; finite-solar-disk geometry is preserved separately and is not promoted to a firecloud claim.
