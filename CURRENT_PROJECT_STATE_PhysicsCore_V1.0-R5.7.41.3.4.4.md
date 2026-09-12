# Taiwan Firecloud PhysicsCore — Current Project State

Current candidate: **V1.0-R5.7.41.3.4.4**.

## Development strategy

Shadow Validation CASE 依天氣逐步收集；不為湊樣本停止工程開發，也不因 Ground Truth 尚未齊全而放寬凍結科學規則。

Science baseline 持續凍結：

`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## R5.7.41.3.4.4 focus

Twilight Glow observer-cloud provenance runtime cache hardening：

- 1092-volume 等大型 Glow branch 不再對每個 volume 重建相同 cloud/COT/truth lookup；
- 同一 time/angle/direction transect 的 projected cloud support geometry 可安全共用；
- conflict / Missing 語義與所有物理結果保持不變；
- aggregation telemetry 明確標示舊 `AGGREGATION_AND_MATRIX_BUILD` 包含 Glow，另提供 excluding-Glow 工程診斷列。

## Verification evidence

TWS021 單角度 84-volume offline equivalence replay：baseline 7.743 s → 3.491 s，約 2.22×；detail / summary exact match。

## Next safe engineering targets

在本版 regression / fresh-extract release gate 完成後：

1. profile Glow precipitation / gas / aerosol observer-path 的剩餘重複幾何；
2. profile `AGGREGATION_EXCLUDING_TWILIGHT_GLOW` 的真實剩餘成本；
3. CASE export serialization；
4. 不降低六波段、空間解析度或物理完整度。

## Verification

Working tree **616/616 PASS**；trial fresh-extract **616/616 PASS**；1 個既有 pandas FutureWarning，非失敗。Final candidate fresh-extract **616/616 PASS**；exact final archive fresh-extract **616/616 PASS**；Release Gate CLOSED。
