# Test Report — V1.0-R5.7.41.3.4.10.11

## Scope

Authoritative Ice LUT Source Intake + QA Build Gate.

## Working-tree regression

- `pytest -q`
- **757/757 PASS**
- 1 existing pandas `FutureWarning`
- 0 failures

## Targeted Ice pipeline tests

- authoritative source manifest / published checksum contract
- missing-source fail-close
- source spectral-grid no-extrapolation rule
- synthetic complete-source source→six-band-LUT build
- LUT release gating and manifest hashing
- existing Ice Optics Phase-1 runtime tests
- portable WINDY evaluator / Node parity / TypeScript strict compile
- UI information architecture tests

Targeted aggregate: **24/24 PASS**.

## Frozen science audit

Compared with `.10.10.2` FIELD PASS baseline:

- 16/16 frozen science source files byte-identical.

See `FROZEN_SCIENCE_SOURCE_AUDIT_R5.7.41.3.4.10.11.csv`.

## Fail-close source readiness check

Running the authoritative builder against an absent source root returns exit code 2, reports 27 missing source files / 162 unavailable target-band checks, `release_ready=false`, and emits no calibrated LUT.

## Fresh-extract regression

- Preliminary FULL-CLEAN fresh extract: **757/757 PASS**
- 1 existing pandas `FutureWarning`
- 0 failures

Final release was rebuilt after this report update and rechecked from a fresh extract.
