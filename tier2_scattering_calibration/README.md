# Tier-2 Scattering Calibration Pipeline — R5.7.20

PhysicsCore does **not** fabricate a calibrated cloud-scattering LUT.
Production Tier-2 response requires an externally computed and validated radiative-transfer grid.

## Physical boundary

The runtime response factor is defined as:

`target directional radiance / cloud-base incident irradiance`, units `sr^-1`.

The frozen independent dimensions are:

- cloud phase
- wavelength: 550 / 575 / 600 / 650 / 700 / 750 nm
- target cloud optical depth (COT)
- effective radius `r_eff`
- cloud geometric thickness
- Sun→Cloud→Observer scattering angle, 0° forward to 180° backward

The production calibration contract requires multiple scattering and explicit optical-property provenance.
A recommended external baseline is libRadtran/uvspec with a validated multiple-scattering solver such as DISORT; water-cloud optical properties may use validated Mie tables and ice clouds must declare the chosen ice optical-property / phase-function parameterization. Other validated external solvers may be used when their provenance and validation reference are recorded.

## Workflow

1. Fill `grid_spec_template.json` with explicitly chosen physical grid axes.
2. Generate RT jobs:

   `python tools/generate_tier2_scattering_calibration_jobs.py grid.json jobs.csv --solver-family LIBRADTRAN_UVSPEC_DISORT`

3. Run those jobs outside PhysicsCore using the declared physical RT solver.
4. Produce a solver result CSV containing the exact grid coordinates plus `response_factor`.
5. Fill `metadata_template.json`, including calibration source, solver version, optical-property sources, QC PASS, and a validation reference.
6. Build the immutable package:

   `python tools/build_tier2_scattering_calibration_package.py solver_samples.csv metadata.json outdir`

7. Install only after the package passes validation:

   `python tools/install_tier2_scattering_lut.py outdir/tier2_scattering_lut.csv outdir/tier2_scattering_lut_manifest.json`

## Safety rules

- Synthetic / dummy / regression-only calibration sources are rejected for production solver execution.
- `calibration_state=CALIBRATED` alone is insufficient.
- `qc_state` must be `PASS`.
- Multiple scattering must be explicitly enabled.
- Response definition, units, and scattering-angle convention must match the frozen contract.
- Every declared phase × wavelength must form a complete Cartesian 4-D tensor grid.
- Missing LUT remains a valid operational state; Tier-1/Formation are not overwritten.
