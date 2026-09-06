# Taiwan Firecloud PhysicsCore V1.0-R5.5 Release Notes

## R5.5 — Canvas Optical Suitability / Thin–Suitable–Thick Cloud Optical Response

R5.5 is built strictly from **PhysicsCore V1.0-R5.4**. It does not adopt unrelated provider changes.

### New intrinsic Target-Canvas optical layer

New CASE outputs:

- `v1_canvas_optical_suitability.csv`
- `v1_canvas_optical_suitability_summary.csv`

Per exact target optical evidence, R5.5 exposes:

- `target_cot`
- `cloud_phase`
- `effective_radius_um`
- `cloud_thickness_km`
- `single_scattering_proxy`
- `multiple_scattering_flag`
- `source_radiance_proxy` (intrinsic escape-weighted response capacity; **not actual radiance**)
- `canvas_optical_suitability_state`

States:

- `TOO_THIN`
- `OPTICALLY_SUITABLE`
- `TOO_THICK`
- `OPTICS_UNKNOWN`

### Hard separation preserved

`Canvas Optical Suitability` consumes **no** Penumbra geometry and **no** Sun→CloudBase Spectral RT. It is an intrinsic target-cloud response layer.

The evidence order remains:

1. Penumbra Geometry → `F_sun`
2. Spectral RT → wavelength-dependent Sun→CloudBase transmission / `E_lambda,base`
3. Target Canvas Optical Suitability → intrinsic cloud scattering/escape capacity
4. Formation later combines the independent evidence tracks

No single Physics Score is introduced.

### Missing / bounded evidence

- COT Missing is never converted to thin cloud.
- A bounded adjacent-native COT hypothesis remains `OPTICS_UNKNOWN`; bounds are exported but are not promoted to exact suitability.
- Cloud Fraction, RH, geometry, cloud type and satellite observation do not fabricate target COT.

### Tier-1 optical regimes

R5.5 uses explicit **uncalibrated order-of-magnitude optical-depth regimes around tau~O(1)** for diagnostics:

- tau < 0.30 → `TOO_THIN`
- 0.30 <= tau <= 3.00 → `OPTICALLY_SUITABLE`
- tau > 3.00 → `TOO_THICK`

These are not final empirical firecloud thresholds. Ground-truth calibration remains required.

### Scope intentionally not changed

R5.5 does not change:

- finite-solar-disk / Penumbra algorithms,
- six-band Spectral RT,
- CAMS/HITRAN/O3 logic,
- Secondary Target Optics provider priority,
- Viewing branch,
- Glow branch,
- precipitation 3-D optics.

### Regression validation

- R5.5 full suite: **254 passed, 10 failed**.
- R5.4 baseline full suite: **251 passed, the same 10 failed**.
- Therefore R5.5 adds 3 passing tests and introduces **0 new regression failures**.
- The 10 remaining failures are pre-existing legacy/stale V8.x/CAMS/HITRAN/cloud-optics contract tests retained from the R5.4 baseline.
