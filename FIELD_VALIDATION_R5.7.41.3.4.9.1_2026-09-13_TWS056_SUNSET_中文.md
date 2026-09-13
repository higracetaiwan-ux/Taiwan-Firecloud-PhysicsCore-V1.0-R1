# R5.7.41.3.4.9.1 Field Validation — 2026-09-13 Sunset TWS056

## 結論
**NOT FIELD PASS / Optimization hypothesis rejected.**

`.3.4.9.1` 的 native hydrometeor prepared-context cross-angle cache 確實正常命中：第一角度為 `MISS_BUILT`，後續 12 個角度為 `HIT_CROSS_ANGLE`。但是 Red-Light precipitation path runtime 並未實質下降。

## Field runtime
- `.3.4.9` `RED_LIGHT_COMPONENT_PRECIPITATION_PATH`：110.323 s
- `.3.4.9.1`：109.515 s
- 變化：約 -0.7%，不足以宣告有效最佳化。
- `.3.4.9` Red-Light total：149.068 s
- `.3.4.9.1` Red-Light total：152.332 s（執行抖動下反而較高，不能視為 regression，science output 未變）

## Integrity / science equivalence
- Analysis Integrity：71/71 PASS
- CASE Integrity：32/32 PASS
- 132 個 CASE members 中 111 個 byte-for-byte identical。
- 21 個差異僅為 runtime/provider/manifest/audit metadata。
- `summary.csv`、Formation、Viewing、Glow、Photography、Red-Light、Precipitation Path、Earth Shadow、COT 等 science CSV 皆 byte-for-byte identical。

## 根因修正
Field evidence 證明主要耗時不是 native hydrometeor volume preparation，而是 `_integrate_sun_path()` 內部。舊流程在同一 horizontal support 的多個 pressure-level hydrometeor cells 上重複執行完全相同的 17-point curved-Earth ray sampling。

因此下一版改為 R5.7.41.3.4.9.2：horizontal-support ray reuse。
