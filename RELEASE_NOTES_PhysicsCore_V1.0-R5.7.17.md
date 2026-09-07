# Taiwan Firecloud PhysicsCore V1.0-R5.7.17 Release Notes

## Tier-2 Scattering Readiness Contract

Built directly from the validated R5.7.16 FULL-CLEAN baseline.

### Added
- `firecloud/tier2_scattering_readiness.py`.
- Per-target readiness states for COT truth, phase, effective radius, geometric thickness, and six-band incident illumination.
- `v1_tier2_scattering_readiness.csv`.
- `v1_tier2_scattering_readiness_summary.csv`.
- Explicit `INPUTS_READY_AWAITING_LUT_SOLVER` state.
- Independent blockers: `BLOCKED_COT_CONFLICT`, `BLOCKED_COT_MISSING`, `BLOCKED_PHASE_MISSING`, `BLOCKED_REFF_MISSING`, `BLOCKED_THICKNESS_MISSING`, `BLOCKED_SIX_BAND_INCIDENT_INCOMPLETE`.
- R5.7.17 regression contracts for exact, bounded, conflict, r_eff-missing and summary behavior.

### Hard rules preserved
- Cloud Fraction / RH / geometry never manufacture COT.
- Exact and bounded COT are distinct inputs.
- Conflict/unknown target optics remain unresolved.
- No Tier-2 scattering LUT/solver is claimed ready in this release.
- No phase or r_eff multiplier is applied to Tier-1 response.
- No Formation threshold, Viewing, Photography Decision, Shared Geometry, or UI science changes.

### Validation
- Full regression: **334 passed / 0 failed**.
