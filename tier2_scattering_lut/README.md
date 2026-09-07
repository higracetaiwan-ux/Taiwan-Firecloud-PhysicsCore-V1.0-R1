# Tier-2 Scattering LUT Runtime Contract — R5.7.19

R5.7.19 adds **calibrated LUT ingestion and interpolation-domain auditing**. It still does **not** calculate production Tier-2 cloud radiance.

A runtime installation requires both:

- `tier2_scattering_lut.csv`
- `tier2_scattering_lut_manifest.json`

The CSV keeps the frozen R5.7.18 columns:

- `phase`
- `wavelength_nm` — exactly 550/575/600/650/700/750 nm
- `cot`
- `effective_radius_um`
- `cloud_thickness_km`
- `scattering_angle_deg`
- `response_factor`
- `calibration_state` — every row must be `CALIBRATED`
- `lut_version` — one version per file

The manifest must provide scientific provenance and the SHA256 of the exact CSV. A schema-valid CSV without its calibrated manifest is rejected.

Runtime resolution:

1. `FIRECLOUD_TIER2_SCATTERING_LUT_PATH` (+ optional `FIRECLOUD_TIER2_SCATTERING_LUT_MANIFEST_PATH`)
2. packaged `tier2_scattering_runtime/`

Interpolation-domain readiness is conservative: every required wavelength must have a complete local 4-D cell around the target in `COT × r_eff × cloud thickness × scattering angle`. Range inclusion alone is insufficient.

R5.7.19 never fabricates COT from Cloud Fraction, RH, geometry, or condensate-zero, and it does not execute the final Tier-2 response interpolation.
