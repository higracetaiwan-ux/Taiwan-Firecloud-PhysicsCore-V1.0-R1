# RELEASE NOTES — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.23

## R5.7.41.3.4.10.23 — Step 3J Diagnostic PSD × Yang/Bi Cext Bulk Integration

### Added

- Diagnostic six-band `β_ext(λ)=∫n_Wyser(D)C_ext,Yang(D,λ)dD` integration.
- Diagnostic `k_ext(λ)=β_ext/IWC_kg_m3` calculation.
- Source-knot-preserving log(D)-log(Cext) interpolation without extrapolation.
- 18-case T/IWC/grid numerical preflight with 16385-point reference grid.
- PSD numeric mass-closure and bulk grid-convergence gates.
- Step 3J evidence/gate/contract model + Analysis Integrity + CASE archive handoff.

### Numerical result

- 18/18 numeric bulk-extinction cases PASS.
- max mass-closure relative error: `3.552713678800501e-16`.
- max bulk-grid convergence relative error: `2.8615945138814625e-06`.

### Frozen / not promoted

- `single_column/Rough000` remains a diagnostic reference only.
- No runtime habit / roughness selection.
- No scientific bulk-validation claim.
- No production bulk-integration eligibility.
- No production `tau_ice` synthesis.
- No GFSv16 Dmax runtime mapping.
- No Formation/Viewing/Twilight Glow science change.

### Gate state

`DIAGNOSTIC_BETA_KEXT_NUMERIC_READY_SCIENTIFIC_AND_TAU_PROMOTION_BLOCKED`

### Validation

- FIELD validation pending.
