# Implementation Status — V1.0-R5.7.41.3.4.3

Status: IMPLEMENTED / RELEASE GATE CLOSED.

Implemented:
- DWD ICON process-local decoded QC/QI/T/P native-field cache;
- route-geometry-only cache signature, excluding time-varying surface anchors;
- bounded field-cache size;
- exact all-QC/QI-HTTP-404 run/lead negative availability cache;
- fail-closed negative-cache semantics;
- DWD API efficiency telemetry correction;
- regression coverage for decoded-field reuse, all-404 suppression, and mixed-failure non-suppression.

Science baseline remains `R5.7.41.2_SHADOW_COT_AB_FROZEN`.

## Working-tree verification
- Regression: **612/612 PASS**
- Existing pandas FutureWarning: 1 (non-failure)

- Trial fresh-extract regression: **612/612 PASS**
- Final candidate fresh-extract regression: **612/612 PASS**
- Exact final archive fresh-extract regression: **612/612 PASS**
