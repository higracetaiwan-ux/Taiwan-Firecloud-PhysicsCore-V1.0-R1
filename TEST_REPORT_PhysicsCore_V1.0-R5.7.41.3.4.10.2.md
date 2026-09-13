# Test Report — V1.0-R5.7.41.3.4.10.2

## Targeted / compatibility
- Legacy Twilight Glow complete-branch tests：PASS。
- New molecular numeric context unit tests：PASS。
- `.3.4.10` profiler / `.3.4.10.1` aerosol context tests：PASS。

## Actual CASE A/B
TWS134 2026-09-13 sunset，1092 Glow volumes：
- Rayleigh observer path：1092/1092 exact。
- local molecular state：1092/1092 exact。
- molecular boundary diagnostics：1092/1092 exact（NaN-aware）。
- helper runtime：4.0718 s → 0.2971 s，約 13.7×。

## Full regression
- Working tree：659/659 PASS。
- Warning：1 個既有 pandas FutureWarning，非 failure。
- Final fresh-extract gate：659/659 PASS（1 existing pandas FutureWarning）。
