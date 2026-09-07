# IMPLEMENTATION STATUS — PhysicsCore V1.0-R5.7.20

Status: **COMPLETE / VERIFIED for executable Tier-2 solver software and production calibration gating.**

Physical event-level Tier-2 validation remains intentionally **PENDING an externally generated production calibrated LUT**; the release does not claim that a calibration dataset has been produced or validated.

## Completed software path

`Target Optical Truth`
→ `Tier-2 Input Readiness`
→ `Scattering Geometry`
→ `Calibrated LUT Runtime Ingestion`
→ `Interpolation-Domain Contract`
→ `Production Calibration Gate`
→ `4-D Six-Band Interpolation Solver`
→ `Exact deterministic / Bounded interval Tier-2 response evidence`

## Production gate

A LUT can be R5.7.19 schema/domain-valid yet still be prohibited from solver execution. Production execution additionally requires:

- `calibration_contract = R5.7.20_TIER2_SCATTERING_CALIBRATION_V1`
- `calibration_state = CALIBRATED`
- `qc_state = PASS`
- approved physical RT solver family + version
- cloud optical-property provenance
- phase-function provenance
- multiple scattering enabled
- frozen response definition and units
- frozen scattering-angle convention
- non-empty validation reference
- non-synthetic calibration source

## Solver semantics

### Exact target

`EXACT_* + EXACT_VALUE + domain ready + production calibration ready`
→ deterministic six-band 4-D multilinear interpolation.

For every wavelength:

`L_target,λ = E_base,λ × R_LUT(phase, λ, COT, r_eff, Δz, Θscatter)`

where the LUT response is defined as target directional radiance per unit cloud-base incident irradiance (`sr^-1`).

### Bounded target

`BOUNDED_NATIVE_BRACKET + BOUNDED_INTERVAL`
→ lower/upper six-band response only.

No nominal deterministic COT or radiance is produced. The envelope checks all crossed COT knots and therefore does not assume monotonic scattering response.

### Conflict / unknown

No solver execution. CF, RH and geometry cannot create COT.

## Performance

A `PreparedScatteringLUT` immutable lookup/index is built once per event and reused across all angles.

## No-Canvas behavior

All Tier-2 response outputs preserve fixed schemas with zero rows. `v1_canvas_candidates.csv` is also fixed-schema/zero-row in NO_CANVAS events.

## Regression

Full test suite: **363 passed / 0 failed**.

## Not claimed in this release

- No production calibrated scattering LUT is bundled.
- No event-level Tier-2 radiance validation against photographs/observations is claimed.
- No Tier-2 response is fed into Formation/Photography Decision yet.
- No UI consolidation.
