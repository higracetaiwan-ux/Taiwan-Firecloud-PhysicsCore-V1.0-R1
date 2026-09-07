# RELEASE NOTES — PhysicsCore V1.0-R5.7.18.1

## Spectral Evidence Payload Integrity

Baseline: V1.0-R5.7.18.

### Added
- Payload-level CAMS/O3/Gas/Aerosol integrity checks in `firecloud/case_integrity.py`.
- `CAMS_REQUEST_AUDIT_PRESENT`: a blank CAMS request audit cannot silently coexist with missing CAMS-dependent evidence.
- `CAMS_O3_ROUTE_PAYLOAD_VALIDITY`: row existence is no longer sufficient; numeric O3 payload coverage is measured.
- `CAMS_O3_QUALITY_MISSING_FRACTION`: nearly-all `CAMS_O3_MISSING` rows are a hard failure.
- `GAS_CORE_PAYLOAD_VALIDITY`: checks exported temperature/H2O/O2 payload coverage when those fields are available.
- `CAMS_AEROSOL_SPECTRAL_PAYLOAD_VALIDITY`: detects empty spectral aerosol route payload when target paths report AEROSOL missing.

### Contract behavior
- All-missing O3 payload with a non-empty route table => FAIL.
- Empty CAMS request audit while CAMS-dependent payload is expected => FAIL.
- Empty aerosol spectral payload while Canvas target paths are aerosol-missing => FAIL.
- Partial O3 payload => WARN, not falsely promoted to PASS.
- Legacy/minimal fixtures that do not export new core-gas columns => WARN rather than false hard failure.
- Physics conflicts such as unresolved target-cloud COT remain physics/evidence states and are not reclassified as provider payload corruption.

### Verification
- R5.7.18 failing real CASE replay: 4 payload hard failures detected and overall integrity becomes FAIL.
- Known-good R5.7.17 and R5.7.14 CASE replays remain overall PASS.
- Full regression: 344 passed / 0 failed.

### Unchanged
- Formation / Viewing / Photography Decision
- Six-band definition (550/575/600/650/700/750 nm)
- Target Optical Truth semantics
- Tier-1 response
- Shared Geometry / scattering-angle geometry
- Tier-2 calibrated LUT remains unavailable and production interpolation remains disabled
