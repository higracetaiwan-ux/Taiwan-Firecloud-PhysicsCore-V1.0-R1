# Release Notes — V1.0-R5.7.41.3.4.10.9.1

## Glow Gas Spectroscopy Cache Telemetry Diagnostic Hotfix

本版不是新的物理優化，也不是 `.10.10`。它只補 `.10.9` Viewing→Glow Gas Spectroscopy Cache Handoff 在正式 CASE 中缺少的可稽核 telemetry。

### 為何需要 `.10.9.1`

TWS095 2026-09-14 sunset `.10.9` Field CASE 已顯示：

- Volume Assembly：`4.542999 → 2.531329 s`（約 `-44.28%`）
- Glow total：`10.252142 → 8.606167 s`
- Analysis Integrity：70 PASS / 1 N/A / 0 WARN / 0 FAIL
- CASE Integrity：32/32 PASS

但舊 CASE 沒有 export Glow 端 sigma cache 的實際 hit/miss 與 inherited handoff hit，因此無法依原 Field gate 規則宣告最終 FIELD PASS。

### 新增 telemetry

`performance_diagnostics.csv` 新增：

`TWILIGHT_GLOW_GAS_SPECTROSCOPY_CACHE_HANDOFF`

內容包括：

- cache available / reused
- entries before / after / added
- lookups
- hits
- handoff hits
- intra-Glow hits
- misses
- uncached fallbacks
- LUT signature count

`runtime_cache_provenance.csv` 同時增加結構化 internal-runtime row，便於 CASE 稽核。

### Science freeze

本版不修改：

- `gas_rt.py`
- 六波段
- HITRAN/O3 science
- Formation / Viewing / Twilight Glow 定義
- Cloud / aerosol / precipitation / Rayleigh
- Earth Shadow / Penumbra
- Production / Shadow COT
- Photography decision
- Missing semantics

### Regression

- targeted exactness：15/15 PASS
- adjacent Viewing/Glow/Gas：48/48 PASS
- full：695/695 PASS
- only 1 existing pandas FutureWarning

狀態：**REGRESSION PASS / FIELD RETEST CANDIDATE**。
