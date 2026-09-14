# Glow Gas Spectroscopy Cache Telemetry Hotfix Spec — R5.7.41.3.4.10.9.1

## 目的

本版只補上 `.10.9` Viewing→Glow Gas Spectroscopy Cache Handoff 的可稽核 runtime telemetry。不得改變任何 PhysicsCore 科學規則、光譜計算、路徑幾何、Missing semantics、Formation / Viewing / Twilight Glow 定義或 COT / Shadow contract。

Science baseline 維持：`R5.7.41.2_SHADOW_COT_AB_FROZEN`。

## 背景

`.10.9` 已把 Main Viewing 的 `gas_sigma_cache` 與 exact route LUT signature 交給 Twilight Glow。TWS095 2026-09-14 sunset Field CASE 顯示：

- `TWILIGHT_GLOW_COMPONENT_VOLUME_ASSEMBLY = 2.531329 s`
- `.10.8` baseline = `4.542999 s`
- 改善約 `44.28%`
- Glow total = `8.606167 s`，低於 `.10.8` 的 `10.252142 s`
- Analysis Integrity = `70 PASS / 1 NOT_APPLICABLE / 0 WARN / 0 FAIL`
- CASE Integrity = `32/32 PASS`

但 CASE 只輸出 `shared_gas_context=SHARED_VIEWING_RUNTIME_CONTEXT`，未輸出 Glow gas sigma cache 的實際 hit/miss 與 inherited handoff hit，因此無法完成 `.10.9` 原先凍結的最終 Field telemetry gate。

## 修改範圍

### `firecloud/twilight_glow.py`

只增加 diagnostic counters：

- `shared_gas_sigma_lookup_count`
- `shared_gas_sigma_cache_hit_count`
- `shared_gas_sigma_cache_miss_count`
- `shared_gas_sigma_cache_handoff_hit_count`
- `shared_gas_sigma_cache_intra_glow_hit_count`
- `shared_gas_sigma_uncached_fallback_count`
- `shared_gas_sigma_cache_entry_count_before_volume`
- `shared_gas_sigma_cache_entry_count_after_volume`
- `shared_gas_sigma_cache_entry_count_added_volume`
- `shared_gas_lut_signature_count`

其中：

- `handoff_hit_count`：lookup key 在 Glow Volume Assembly 開始前已存在於 Viewing shared cache。
- `intra_glow_hit_count`：key 在 Glow 執行期間建立，之後被 Glow 自己再次命中。
- `miss_count`：有 shared cache + LUT signature，但 lookup 當下不存在，依原路徑執行 `_sigma_fast()` 後寫入 cache。
- `uncached_fallback_count`：shared cache 或 LUT signature 不可用，完整走原 `_sigma_fast()` fallback。

### `firecloud/model.py`

只增加輸出：

1. `performance_diagnostics.csv` 新增 stage：
   `TWILIGHT_GLOW_GAS_SPECTROSCOPY_CACHE_HANDOFF`
2. `TWILIGHT_GLOW_INDEPENDENT_BRANCH` detail 增加 gas cache 摘要。
3. `runtime_cache_provenance.csv` 增加 `INTERNAL_RUNTIME / TWILIGHT_GLOW_GAS_SPECTROSCOPY_CACHE_HANDOFF` 結構化 row。

## 嚴格不變項

- 六波段仍為 `550/575/600/650/700/750 nm`。
- cache key 不變：`LUT content signature + gas + wavelength + exact T + exact P`。
- 不做 T/P rounding。
- `_sigma_fast()` 本體不修改。
- `sigma × density × path_length` 不修改。
- O2 / H2O / O3 計算與累加順序不修改。
- LOS / pressure levels / cloud / aerosol / precipitation / Rayleigh 不修改。
- Missing ≠ Clear ≠ Zero。
- Production COT 與 Shadow COT contract 不修改。
- Formation / Viewing / Glow 三軌不修改。

## Field Gate

`.10.9.1` Field CASE 必須看到：

- `cache_available=True`
- `reused=True`
- `entries_before > 0`
- `handoff_hits > 0`
- `lut_signature_count >= 1`
- `uncached_fallbacks == 0`（正常 shared-context case）
- Analysis / CASE Integrity 不 regression
- Volume Assembly 維持 `.10.9` 改善量級，不得明顯反向退化

通過後，才可正式關閉 `.10.9` cache handoff Field telemetry gate。
