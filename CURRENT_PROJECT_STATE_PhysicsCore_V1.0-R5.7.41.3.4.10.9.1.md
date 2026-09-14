# Taiwan Firecloud PhysicsCore — Current Project State

Current release: **V1.0-R5.7.41.3.4.10.9.1 — Glow Gas Spectroscopy Cache Telemetry Diagnostic Hotfix**

Science baseline remains frozen at `R5.7.41.2_SHADOW_COT_AB_FROZEN`.

## 目前狀態

- `.10.8` Viewing→Glow Molecular Context Handoff：FIELD PASS
- `.10.9` Viewing→Glow Gas Spectroscopy Cache Handoff：**FIELD PERFORMANCE PASS / INTEGRITY PASS / FINAL FIELD PASS PENDING CACHE TELEMETRY**
- `.10.9.1`：REGRESSION PASS / FIELD RETEST CANDIDATE

## `.10.9` TWS095 Field evidence

2026-09-14 sunset TWS095：

- Glow Volume Assembly：`2.531329 s`
- `.10.8` baseline：`4.542999 s`
- 改善：`-44.28%`，約 `1.79x`
- Glow total：`8.606167 s`
- `.10.8` Glow total baseline：`10.252142 s`
- Analysis Integrity：`70 PASS + 1 NOT_APPLICABLE`
- CASE Integrity：`32/32 PASS`

效能與 Integrity 已符合 `.10.9` 主要目標，但舊 CASE 缺少 Glow sigma cache hit/miss / inherited handoff hit telemetry，因此不直接宣告 `.10.9 FIELD PASS`。

## `.10.9.1` 修改

只補 diagnostic-only telemetry：

- before / after / added cache entries
- lookup / hit / miss
- inherited Viewing→Glow handoff hits
- intra-Glow hits
- uncached fallbacks
- LUT signature count
- structured runtime cache provenance

不修改任何 science calculation。

## Regression

- targeted exactness：15/15 PASS
- adjacent Viewing/Glow/Gas chain：48/48 PASS
- full working-tree：**695/695 PASS**
- 1 existing pandas FutureWarning only

## 下一步

使用 `.10.9.1` 跑正式 Field CASE。Primary telemetry gate：

- `TWILIGHT_GLOW_GAS_SPECTROSCOPY_CACHE_HANDOFF`
- `reused=True`
- `handoff_hits > 0`
- `entries_before > 0`
- `uncached_fallbacks == 0`（正常 shared-context case）

同時確認 Volume Assembly 與 Glow total 不 regression。通過後即可正式關閉 `.10.9` Field gate。
