# Taiwan Firecloud PhysicsCore — Current Project State V1.0-R5.7.33.1

## Current candidate
`Taiwan Firecloud PhysicsCore V1.0-R5.7.33.1`

## Closed before this hotfix
- R5.7.29.1 Viewing precipitation handoff FIELD CLOSED
- R5.7.30.1 Independent Twilight Glow / integrity restore FIELD CLOSED
- R5.7.31 Glow two-leg six-band extinction FIELD CLOSED
- R5.7.32 CAMS geopotential normalization + long-range aerosol coverage FIELD CLOSED under native-ready conditions

## R5.7.33 field result
- 100 km Rayleigh + gas species: 156/156 PASS
- cloud DIRECT_EVIDENCE_CONFLICT: 4/4 preserved Partial/Missing PASS
- real R5.7.28 spectral adjacent-time fallback triggered at -5.5/-6 deg: PASS
- inherited R5.7.32 guard exposed readiness-layer bug (spectral fallback != native 3-D readiness)

## R5.7.33.1
Integrity-only fix for that readiness-layer bug. Field validation requires rerun or immutable CASE re-audit plus new deploy CASE.
