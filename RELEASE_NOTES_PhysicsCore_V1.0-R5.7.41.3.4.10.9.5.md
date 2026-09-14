# Release Notes — V1.0-R5.7.41.3.4.10.9.5

## GFS Hourly Native Valid-Time Alignment Hotfix

本版修正 GFS 0.25° native microphysics 的 forecast valid-time resolver；Frozen PhysicsCore science 不變。

### 問題

`.10.9.4` TWS106 2026-09-14 sunset 正式 CASE：事件約 10:00–10:26 UTC，但 native GFS 實際使用 `2026-09-14 06Z f003`，valid time 09:00 UTC。原因是舊 resolver 把所有 lead 一律 round 到 3 小時。

### 修正

1. `f000–f120` 改為逐小時 forecast-hour resolution。
2. `f123–f384` 維持 3-hour cadence。
3. primary `pgrb2` 與 Canvas diagnostic `pgrb2b` 共用同一 resolver。
4. GFS audit 新增 target time / resolved valid time / offset / cadence provenance。
5. 新增 `GFS_NATIVE_VALID_TIME_ALIGNMENT` Analysis Integrity gate。
6. TWS106 10:00 UTC 現在解析為 `06Z f004`，而非 `06Z f003`。

### 明確沒有變更

- CLWMR / ICMR condensate threshold；
- native 3D cloud reconstruction；
- Missing semantics；
- Canvas；
- Formation / Viewing / Twilight Glow；
- Production / Shadow COT；
- 六波段 RT / color reconstruction；
- Photography Decision。

Science baseline remains `R5.7.41.2_SHADOW_COT_AB_FROZEN`。

### 驗證

- targeted/adjacent: 25/25 PASS（第一輪 13/13 targeted PASS）
- full working-tree regression: 715/715 PASS
- failure: 0
- warning: 1 existing pandas `FutureWarning`

- fresh-extract regression: 715/715 PASS
- clean source files: 805
- cache/compiled contamination: 0

- FULL-CLEAN ZIP entries: **819**
