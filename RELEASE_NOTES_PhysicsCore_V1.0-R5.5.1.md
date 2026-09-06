# Taiwan Firecloud PhysicsCore V1.0-R5.5.1 Release Notes

## R5.5.1 — Secondary Native Optics + Canvas Optical Suitability Integration

R5.5.1 is a three-way integration built from the frozen **PhysicsCore V1.0-R5.4** baseline plus the two previously separate R5.5 feature branches:

1. Secondary Native Optics Live Chain (ECMWF IFS local/entitled first, DWD ICON Global Open Data fallback)
2. Canvas Optical Suitability / Thin–Suitable–Thick Target Cloud Optical Response

### Integrated physical chain

`GFS / ECMWF IFS / DWD ICON forecast-native microphysics`
→ `Target Optical Evidence`
→ `COT / phase / effective radius / thickness`
→ `Canvas Optical Suitability`
→ `TOO_THIN / OPTICALLY_SUITABLE / TOO_THICK / OPTICS_UNKNOWN`

The final Formation stage may later combine this intrinsic target-cloud response with the independent Penumbra Geometry and six-band Sun→CloudBase Spectral RT tracks.

### Hard separation preserved

R5.5.1 does **not** merge the following layers:

- Penumbra Geometry → `F_sun`
- Spectral RT → wavelength-dependent `T_lambda,path` / `E_lambda,base`
- Target Cloud Optical Response → intrinsic Canvas Optical Suitability

The Canvas Optical Suitability builder consumes neither `F_sun` nor Sun→CloudBase spectral transmission.

### Secondary native optics provider chain

Priority:

1. ECMWF IFS native model-level cloud microphysics when explicitly configured and available.
2. DWD ICON Global model-level QC/QI public network fallback.
3. Otherwise explicit Missing / Unavailable.

No satellite observation, Cloud Fraction, RH, geometry, or cloud type is used to fabricate forecast COT.

DWD ICON audit outputs:

- `dwd_icon_request_audit.csv`
- `secondary_provider_audit.csv`

Existing secondary/target evidence outputs remain:

- `ecmwf_ifs_request_audit.csv`
- `v1_secondary_target_optics.csv`
- `v1_target_canvas_optical_evidence.csv`
- `v1_target_canvas_optical_summary.csv`

### Canvas Optical Suitability

New CASE outputs retained from the suitability branch:

- `v1_canvas_optical_suitability.csv`
- `v1_canvas_optical_suitability_summary.csv`

States:

- `TOO_THIN`
- `OPTICALLY_SUITABLE`
- `TOO_THICK`
- `OPTICS_UNKNOWN`

Exact target COT is required for a categorical optical regime. Missing or bounded-only COT remains `OPTICS_UNKNOWN`.

Tier-1 diagnostic regimes remain explicitly uncalibrated:

- `tau < 0.30` → `TOO_THIN`
- `0.30 <= tau <= 3.00` → `OPTICALLY_SUITABLE`
- `tau > 3.00` → `TOO_THICK`

These are order-of-magnitude diagnostics around `tau ~ O(1)`, not final empirical firecloud thresholds.

### Regression validation

Focused integrated PhysicsCore tests: **25 passed**.

Full suite: **259 passed, 10 failed**.

The same 10 failures were already present in the R5.4 baseline and belong to legacy/stale V8.x, CAMS, HITRAN, and old cloud-optics contracts. R5.4 baseline was 251 passed / 10 failed, therefore the merged R5.5.1 adds 8 passing tests and introduces **0 new regression failures**.

### Scope intentionally unchanged

R5.5.1 does not modify:

- finite-solar-disk / Penumbra algorithms,
- six-band Spectral RT wavelengths or gas spectroscopy,
- Brightness / Redness / Effective Illuminated Area separation,
- Viewing branch,
- Glow branch,
- precipitation 3-D optics.
