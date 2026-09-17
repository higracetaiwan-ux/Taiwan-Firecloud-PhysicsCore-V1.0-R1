# Test Report — PhysicsCore V1.0-R5.7.41.3.4.10.21

## QA Regression

Full working-tree regression:

```text
856 passed, 1 warning
```

Warning is the existing pandas `FutureWarning` in `test_r5732_glow_observer_aerosol_coverage.py`; it is not a failure.

## Step 3G / 3H Focused Regression

Core coordinate qualification, CASE handoff and Step 3G compatibility:

```text
27 passed
```

## Yang/Bi V2 source-row geometry reproduction

- authoritative-derived `single_column / Rough000 / 600 nm` size rows: `189`
- pinned large-column coefficient: `3.48`
- max relative `effective_diameter` reproduction error: `5.837278235773654e-07`
- alternative `0.348` max relative error: `0.8972957458507573`
- source geometry reproduction: PASS
- Wyser↔Yang shape compatibility: NO
- Production Ice Optics: NO

## FIELD Status

Latest formal FIELD baseline is `.10.20.1 FIELD PASS` from TWS091 / 2026-09-17 sunrise. `.10.21` has not yet been run as a new FIELD CASE and therefore remains **QA PASS / FIELD validation pending**.

## Release package verification

A preflight package exposed a deterministic-contract issue: the Step 3H contract embedded an absolute machine path for the bundled LUT. A new regression test was added and the contract now records the portable path `firecloud/data/ice_optics/portable_ice_optics_lut_v1.csv`.

After this fix, working-tree regression is `856 passed, 1 warning`. A rebuilt cache-free candidate FULL-CLEAN package contained `1063` members and its fresh-extract regression also completed with `856 passed, 1 warning`. In that extracted package, Step 3H evidence CSV, gate CSV and contract JSON all regenerated **exactly** from the packaged builders; Yang/Bi source-geometry reproduction also remained PASS. The final delivery ZIP is rebuilt from the same verified tree after recording this report and is rechecked before delivery.
