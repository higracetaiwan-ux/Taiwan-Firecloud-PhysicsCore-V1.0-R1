# R5.7.35.2：零有效 Viewing Target 的降水 Integrity 語義規格

## 問題

2026-09-10 日本 sunset CASE 中，`v1_viewing_path_geometry` 有 585 列，但全部都是 `FOREGROUND_LOW_CLOUD_OBSTRUCTION_ONLY`，因此 `photographic_target_eligible=False` 共 585/585。此時 `v1_viewing_precipitation_evidence` 為 0 列是正確結果。

舊 Integrity 邏輯只要看到 GFS 原生 `RWMR/SNMR/GRLE` 為 READY，就要求 precipitation table 非空，造成假 FAIL。

## R5.7.35.2 規則

1. 先由 `photographic_target_eligible` 建立 expected target keys。
2. 若 expected target 數量為 0：
   - `VIEWING_PRECIPITATION_TARGET_COVERAGE = PASS`（expected=0, observed=0）。
   - `VIEWING_NATIVE_HYDROMETEOR_HANDOFF = NOT_APPLICABLE`。
3. 若 expected target 數量大於 0：
   - 原有 per-target coverage 與 native hydrometeor handoff 硬規則全部保留。
   - header-only/empty evidence、漏列、額外列、`VIEW_PRECIPITATION_VOLUME_UNRESOLVED` 仍不得升格。
4. `Missing != Not Applicable` 的既有原則不變。

## 科學影響

無。此版本只修 Integrity 語義，不改任何 Formation / Viewing / Glow / aerosol / precipitation 數值。
