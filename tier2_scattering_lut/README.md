# Tier-2 Scattering LUT Contract — R5.7.18

R5.7.18 does **not** bundle a calibrated scattering LUT and therefore does not enable production Tier-2 cloud radiance.

Required CSV columns:

- `phase`
- `wavelength_nm` — only 550/575/600/650/700/750 nm
- `cot`
- `effective_radius_um`
- `cloud_thickness_km`
- `scattering_angle_deg` — 0..180°
- `response_factor`
- `calibration_state` — must be `CALIBRATED`
- `lut_version` — one version per file

Cloud Fraction, RH, geometry, or native condensate-zero may not be used to manufacture COT.
A valid schema is not itself proof of scientific calibration. Production interpolation remains disabled in R5.7.18.
