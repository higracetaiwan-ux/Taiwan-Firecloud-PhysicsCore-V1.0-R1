# RELEASE NOTES — PhysicsCore V1.0-R5.7.20

## Calibrated Scattering Solver + Calibration Package Contract

R5.7.20 continues directly from the accepted R5.7.19 calibrated-LUT ingestion/domain baseline and completes the executable Tier-2 interpolation software path without bundling or fabricating a production calibration dataset.

### Production calibration package

- Adds `firecloud/tier2_scattering_calibration.py`.
- Separates **schema-valid LUT** from **production-solver-eligible calibration**.
- Adds the production calibration contract `R5.7.20_TIER2_SCATTERING_CALIBRATION_V1`.
- Requires explicit RT-solver provenance, solver version, cloud-optics source, phase-function source, multiple-scattering declaration, response normalization, geometry convention, QC PASS, validation reference, calibration ID/source/date, LUT version and frozen six-band declaration.
- Synthetic / dummy / regression-only calibration sources cannot become production solver eligible.
- A production calibration package must form a complete Cartesian 4-D tensor for every declared phase × frozen wavelength.
- Adds external-RT job generation and calibration-package build tools; PhysicsCore never invents missing response values.

### Tier-2 interpolation solver

- Adds `firecloud/tier2_scattering_solver.py`.
- Executes strict 4-D multilinear interpolation in `COT × r_eff × cloud thickness × scattering angle` independently for 550/575/600/650/700/750 nm.
- Exact optical truth may produce deterministic Tier-2 response only when the R5.7.19 domain gate and R5.7.20 production calibration gate both pass.
- Bounded COT produces lower/upper response envelopes only; no nominal exact response is manufactured.
- Bounded envelopes probe every crossed COT knot, so no monotonic response assumption is imposed.
- Conflict / unknown target optics remain blocked before solver execution.
- Six-band cloud-base incident irradiance remains a hard prerequisite.
- Interpolated `response_factor` is multiplied by the corresponding cloud-base incident irradiance to produce the independent Tier-2 directional-radiance branch.
- Tier-2 Brightness/Redness diagnostics are exported separately; R5.7.20 does **not** replace Tier-1 or Formation outputs.

### Performance

- Adds one immutable prepared LUT index per event, shared across all solar angles.
- Interpolation no longer rescans the entire LUT DataFrame for every target × band.

### CASE evidence

Adds:

- `v1_tier2_scattering_response_550_750nm.csv`
- `v1_tier2_scattering_response_summary.csv`

The existing `v1_tier2_scattering_lut_domain.csv` now marks `interpolation_executed=True` only where the solver actually executed.

### No-Canvas schema closure

- `v1_canvas_candidates.csv` now retains its fixed schema with 0 rows for genuine NO_CANVAS events instead of exporting a 1-byte headerless file.

### Calibration tools

- `tools/generate_tier2_scattering_calibration_jobs.py`
- `tools/build_tier2_scattering_calibration_package.py`
- existing `tools/install_tier2_scattering_lut.py`
- templates and workflow under `tier2_scattering_calibration/`

### Frozen boundaries

No changes to Formation thresholds/weights, Viewing, Photography Decision, Target Optical Truth semantics, six-band definitions, Shared Geometry, CAMS/GFS provider physics, or CF/RH/geometry-to-COT rules. No calibrated LUT is bundled.
