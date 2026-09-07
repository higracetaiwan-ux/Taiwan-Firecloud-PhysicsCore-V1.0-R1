# IMPLEMENTATION STATUS — PhysicsCore V1.0-R5.7.19

Status: COMPLETE / VERIFIED for Calibrated Scattering LUT Ingestion + Interpolation-Domain Contract.

## Scope
- Resolve one immutable Tier-2 scattering LUT snapshot per event.
- Require CSV + calibrated provenance manifest + matching CSV SHA256.
- Reject mixed LUT versions, duplicate grid coordinates, unsupported phases, incomplete frozen six-band contract, invalid numeric domains, and uncalibrated rows.
- Preserve missing/invalid LUT as explicit evidence rather than synthesizing a response.
- Evaluate each target against phase-specific COT / r_eff / thickness / scattering-angle domains.
- Require a complete local 4-D interpolation cell for every one of 550/575/600/650/700/750 nm; global min/max inclusion alone is insufficient.
- For `BOUNDED_NATIVE_BRACKET`, require continuous COT-interval cell coverage and expose bounded eligibility only.
- Keep `interpolation_executed=False`; production Tier-2 response remains disabled.

## CASE evidence
- `v1_tier2_scattering_lut_audit.csv`
- `v1_tier2_scattering_lut_domain.csv`
- `v1_tier2_scattering_lut_domain_summary.csv`

## Runtime installation
- `tools/install_tier2_scattering_lut.py`
- Environment/secrets: `FIRECLOUD_TIER2_SCATTERING_LUT_PATH` and `FIRECLOUD_TIER2_SCATTERING_LUT_MANIFEST_PATH`
- Packaged runtime directory is intentionally empty except for instructions; no fabricated calibrated LUT is bundled.

## Frozen boundaries
No change to Formation thresholds/weights, Viewing, Photography Decision, six-band definitions, Target Optical Truth semantics, Tier-1 response, Shared Geometry, or CAMS/GFS provider physics. No CF/RH/geometry-to-COT inference.
