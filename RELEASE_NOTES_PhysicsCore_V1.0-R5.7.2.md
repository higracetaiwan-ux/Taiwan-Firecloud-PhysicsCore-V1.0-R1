# Taiwan Firecloud PhysicsCore V1.0-R5.7.2

## Runtime pipeline ordering fix

- Fixed `UnboundLocalError: cannot access local variable 'v1_target_canvas_optical_evidence'`.
- Root cause: the R5.7 Viewing six-band spectral branch consumed the aggregated target optical evidence before that DataFrame was constructed.
- Target optical evidence aggregation now occurs before `build_viewing_spectral_extinction()` on every path.
- Empty/missing target optics remain an explicit empty DataFrame; Missing is not converted to Clear or Zero.
- No changes to Penumbra Geometry, Formation spectral RT, Viewing physics equations, Canvas Optical Suitability thresholds, or Photography Decision thresholds.
- Added regression test for model pipeline dependency ordering.
- Full regression: 289 passed, 0 failed.
