# Taiwan Firecloud PhysicsCore V1.0-R4 Release Notes

## Scope
R4 implements the Stage-3 Canvas Optical Response / Formation foundation on top of the R3.3 geometry, optical-path and performance baseline.

## Implemented
- Added `firecloud/formation.py`.
- Added Stage-3 `CanvasRadiance` and `FormationResult` contracts.
- Retains six spectral channels: 550 / 575 / 600 / 650 / 700 / 750 nm.
- Target cloud optical evidence is required; `GEOMETRY_ONLY` never fabricates target COT/COD.
- Tier-1 source-function proxy uses target vertical optical depth only when native optical evidence exists.
- No fixed Cloud Type multiplier.
- No 0-40 / 40-100 distance weight in Formation.
- No single Formation Score.
- Brightness, Redness and Effective Illuminated Area remain independent outputs.
- 750 nm remains a low-weight deep-red-tail diagnostic for brightness.
- No blue wavelength is invented for Formation.
- Earth-shadowed Canvas can be confirmed zero even when downstream optics are missing.
- CASE archive adds `v1_canvas_radiance_550_750nm.csv` and `v1_formation.csv`.
- UI adds R4 Formation and Canvas Radiance audit tables.

## Intentional limits
- Current R4 Tier-1 response is uncalibrated and is not Full RT.
- Multiple-scattering LUT / refined cloud phase-function response remains future Tier-2/Tier-3 work.
- 550-nm gas remains fail-closed until a verified complete six-band gas spectroscopy LUT is present.
- Viewing / Twilight Glow / Peak Window / Decision are not implemented by R4.
- Existing Legacy V8 compatibility diagnostics remain read-only and are not V1 PhysicsCore outputs.

## Tests
- New R4 tests verify: six-band response when evidence is complete, geometry-only cloud optics remain Unknown, and known Earth-shadow zero remains known zero.
- Full suite at packaging time: 193 passed / 9 failed. The 9 failures are pre-existing Legacy V8 stale-contract expectations.
