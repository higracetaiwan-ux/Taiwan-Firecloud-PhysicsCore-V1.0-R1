# Taiwan Firecloud PhysicsCore V1.0-R5.7.16

## Target Cloud Optical Response / Tier-1 Closure

### Scope
This release continues from R5.7.15 and closes the conservative Tier-1 target-response contract without changing science thresholds or fabricating cloud optical properties.

### Added
- Exact COT: deterministic six-band Tier-1 response with collapsed lower/upper interval.
- Bounded COT: six-band response lower/upper bounds; exact response remains Missing by contract.
- Brightness and Redness lower/upper bounds for bounded target optics.
- Per-target phase/reff evidence flags and Tier-2 scattering-readiness provenance.
- Stable NO_CANVAS target-optical evidence/summary schemas.
- Stable NO_CANVAS Formation provenance counters (all zero).

### Hard contracts preserved
- Cloud Fraction / RH / geometry never infer COT.
- Native condensate zero is not silently converted to target COT=0 under direct evidence conflict.
- Bounded evidence is not promoted to exact response.
- Conflict/unknown targets remain unresolved.
- No changes to Formation thresholds, Viewing, Photography Decision, six-band wavelengths, Shared Geometry, or Geometry Atlas policy.
- Phase/reff are provenance/readiness only in Tier-1; no uncalibrated spectral scattering multiplier is invented.

### Validation
- Full regression: 329 passed / 0 failed.
