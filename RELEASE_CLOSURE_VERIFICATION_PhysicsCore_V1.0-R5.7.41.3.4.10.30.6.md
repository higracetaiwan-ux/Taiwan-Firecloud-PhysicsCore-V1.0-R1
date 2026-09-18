# Taiwan Firecloud PhysicsCore — Release Closure Verification

## Release
`1.0.0-R5.7.41.3.4.10.30.6`

## Step
Step 3Q.6 — RRTM/RRTMG Public Archive Availability Boundary Qualification

Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`

Qualification state：
`PASS_FAIL_CLOSED_PUBLIC_ARCHIVE_AVAILABILITY_BOUNDARY_QUALIFIED_EXACT_GENERATOR_UNRECOVERED`

## Scientific closure
- AER RRTMG_SW public README records Version 5.0 as current and states releases before Version 5.0 are not publicly available.
- Pinned public RRTM_SW runtime source preserves post-averaged Fu96 band tables and Dge interpolation, not the historical pre-averaging spectral dataset/generator.
- Public-release absence is not accepted as evidence of generator identity.
- Final runtime tables remain forbidden as a basis for inverse identification of unique historical h, solar grid, or discrete weights.
- Exact weighting and all Production Ice Optics gates remain fail-closed.

## Verification
- Step 3Q targeted: 19/19 PASS
- Full regression: 947/947 PASS
- Existing pandas FutureWarning: 1
- Fresh-extract Step 3Q targeted: 19/19 PASS
- evidence regeneration: BYTE-EXACT PASS — `a2a8cd7ea122cc8e4c44847f44fdae8b5a65259a68db9a16962b6fae5dc2b08b`
- gate regeneration: BYTE-EXACT PASS — `6ed7b1fc942f5aa12c31fd17afe4310835d04c44315d77f41afcdf554879a95c`
- contract regeneration: BYTE-EXACT PASS — `41319ed68a0e16babbbee1d6a940fd529f0993388e0f9718edcb990159370750`

## Decision
**QA PASS / FIELD CASE pending**
