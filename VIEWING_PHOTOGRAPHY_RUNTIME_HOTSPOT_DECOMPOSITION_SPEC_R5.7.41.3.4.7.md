# R5.7.41.3.4.7 — Viewing / Photography Runtime Hotspot Decomposition

## 目的

本版承接 V1.0-R5.7.41.3.4.6 的 Field warm-run profiler 結果：
`AGGREGATION_VIEWING_AND_PHOTOGRAPHY ≈ 134.6 s` 是目前最大的非 Glow aggregation hotspot。

本版第一階段 **只做 component-level profiler**，不預先假設哪個函式最慢，也不先做任何會影響資料解析度或科學語義的最佳化。

## 凍結科學基線

`R5.7.41.2_SHADOW_COT_AB_FROZEN`

以下不得修改：

- Production / Shadow COT 定義與 eligibility；
- Earth Shadow / finite solar disk / refraction / DirectSolarFraction；
- Formation / Viewing / Twilight Glow 三分支語義；
- 六波段 550 / 575 / 600 / 650 / 700 / 750 nm；
- Missing ≠ Clear ≠ Zero；
- `DIRECT_EVIDENCE_CONFLICT` fail-close；
- 空間、方向、時間、光譜解析度；
- Photography thresholds / weighting。

## 新增 component timers

`AGGREGATION_VIEWING_AND_PHOTOGRAPHY` 內新增九個 diagnostic-only stage：

1. `VIEWING_COMPONENT_PATH_GEOMETRY`
2. `VIEWING_COMPONENT_PRECIPITATION_EVIDENCE`
3. `VIEWING_COMPONENT_TARGET_OPTICS_RECONCILIATION`
4. `VIEWING_COMPONENT_PREPARE_SPECTRAL_RUNTIME_CONTEXT`
5. `VIEWING_COMPONENT_SPECTRAL_EXTINCTION`
6. `VIEWING_COMPONENT_SPECTRAL_SUMMARY`
7. `VIEWING_COMPONENT_ATTACH_SPECTRAL_STATUS`
8. `VIEWING_COMPONENT_PATH_SUMMARY`
9. `VIEWING_COMPONENT_PHOTOGRAPHY_DECISION`

全部標記：

`R5741347_COMPONENT_PROFILE_ONLY`

這些 elapsed 值只寫入 `performance_diagnostics.csv`，不得進入任何 Formation / Viewing / Photography decision gate。

## R5.7.41.3.4.6 runtime/I-O hardening 保留

由於本次接手環境可取得的完整原始碼 archive 是 `.3.4.5 FULL-CLEAN`，而 `.3.4.6` 完整 source ZIP 未在 Library 中找到，本工作樹依 `.3.4.6` 開發記憶檔與 TWS106 Field CASE telemetry 恢復其 runtime-only contract：

- DWD exact-identity persistent raw GRIB cache；
- `FIRECLOUD_STATE_DIR/provider_cache_shared/dwd_icon_raw`；
- identity / byte size / SHA256 / QC stamp validation；
- mismatch/corruption fail-close；
- atomic raw cache commit；
- DWD network attempts/success/failure/bytes audit；
- 4 MiB bounded CASE CSV coalescing buffer；
- CASE export stage profiler；
- aggregation stage decomposition。

上述恢復項目均是 runtime / I-O / diagnostics，不更動 science modules。

## Field test contract

建議重用：

**2026-09-12 Sunset｜TWS106 高美濕地**

Field CASE 回收後先回答：

> 九個 component timer 中，誰是真正最大戶？

只有確認最大戶後，下一步才允許針對該函式做 exact-equivalent optimization。
