# TEST REPORT — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.23

## Working-tree verification

- Step 3G–3J + UI release-identity focused regression: **53 passed**.
- Full pytest regression: **872 passed, 1 warning, exit code 0**.
- Full-suite runtime in the verified working tree: **43.16 s**.

Warning is the pre-existing pandas `FutureWarning` in `tests/test_r5732_glow_observer_aerosol_coverage.py`; Step 3J introduced no new warning/error.

## Step 3J numerical verification

PASS:

- diagnostic six-band `β_ext(λ)=∫n_Wyser(D) C_ext,Yang(D,λ)dD`
- diagnostic six-band `k_ext(λ)=β_ext/IWC_kg_m3`
- Wyser PSD numerical mass closure
- 1025 / 4097 point grids against 16385-point reference-grid convergence
- 18/18 T/IWC/grid preflight cases
- maximum PSD mass-closure relative error: `3.552713678800501e-16`
- maximum bulk-grid convergence relative error: `2.8615945138814625e-06`

253.16 K / IWC 0.1 g m⁻³ diagnostic reference:

```text
550 nm  k_ext = 35.3398938809 m²/kg
575 nm  k_ext = 35.3560999814 m²/kg
600 nm  k_ext = 35.4978120075 m²/kg
650 nm  k_ext = 35.7360786905 m²/kg
700 nm  k_ext = 35.5681253440 m²/kg
750 nm  k_ext = 35.4106457313 m²/kg
```

These are diagnostic `single_column/Rough000` reference-kernel values only; they are not production runtime `τ_ice` inputs.

## Scientific / production gate verification

Remain false / blocked:

- independent exact numeric corroboration for Wyser Eq.(6)
- scientific bulk-optics validation
- Yang/Bi habit bridge
- Yang/Bi roughness bridge
- bulk Yang/Bi PSD integration production eligibility
- production `tau_ice` synthesis
- GFSv16 Dmax runtime mapping eligibility
- Production Ice Optics
- `physics_promotion_allowed`

Qualification remains:

`DIAGNOSTIC_BETA_KEXT_NUMERIC_READY_SCIENTIFIC_AND_TAU_PROMOTION_BLOCKED`

## Deterministic artifact verification

From a clean candidate FULL-CLEAN fresh extract:

- Step 3J evidence CSV: **exact regeneration match**
- Step 3J gate CSV: **exact regeneration match**
- Step 3J contract JSON: **exact regeneration match**
- evidence rows: **12**
- gate rows: **1**
- contract schema: `FIRECLOUD_ICE_WYSER_YANG_DIAGNOSTIC_BULK_V1`

## Packaging verification

Candidate FULL-CLEAN package:

- **1090 members** before this final test-report file was added
- **0** packaged cache / `pyc` / `pyo` artifacts
- clean fresh-extract full pytest: **872 passed, 1 warning, exit code 0**
- fresh-extract runtime: **57.33 s**

The final delivery package is rebuilt from the same verified tree with this report included, then rechecked for member cleanliness, full fresh-extract regression, deterministic Step 3J artifact regeneration, version identity, and SHA256 before delivery.

## FIELD status

Latest formal FIELD baseline remains:

`V1.0-R5.7.41.3.4.10.22 FIELD PASS`

`V1.0-R5.7.41.3.4.10.23` is **QA PASS / FIELD VALIDATION PENDING** until TWS091 + TWS100 FIELD CASE handoff validation is completed.
