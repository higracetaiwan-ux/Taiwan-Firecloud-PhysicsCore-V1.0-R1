# Implementation Status — V1.0-R5.7.41.3.4.7

Status: **IMPLEMENTED / REGRESSION PASS / FIELD PROFILER TEST PENDING**.

Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`.

## Implemented

- `AGGREGATION_VIEWING_AND_PHOTOGRAPHY` function-level decomposition；
- 9 Viewing/Photography component timers；
- diagnostic-only profiler contract；
- R5.7.41.3.4.6 aggregation stage decomposition；
- DWD exact-identity persistent raw cache + SHA256 / QC validation；
- DWD detailed API/network telemetry；
- bounded 4 MiB CASE CSV coalescing stream；
- CASE export stage profiler；
- test coverage for raw-cache fail-close, warm hit, byte-exact CSV streaming and profiler stage presence。

## Frozen science audit

核心 Formation / Viewing science / Glow / Optical Path / spectroscopy / Photography science modules 與 `.3.4.5 FULL-CLEAN` SHA256 exact-identical。

## Verification

- Baseline before changes: 619/619 PASS.
- Targeted new/compatibility tests: 15/15 PASS.
- Working tree: 631/631 PASS.
- Existing pandas FutureWarning: 1 (non-failure).

## Not yet claimed

- 尚未從代表 Field CASE 判定九個 component 中的真正最大戶；
- 尚未針對最大戶做第二階段 exact-equivalent optimization；
- 尚未宣稱 `.3.4.7` FIELD PASS / release gate closed。
