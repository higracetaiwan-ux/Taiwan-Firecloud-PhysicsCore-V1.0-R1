# Field Validation — R5.7.41.3.4.10.9 — TWS095 2026-09-14 Sunset

## 結論

`.10.9` 在 TWS095 實跑已達到 **FIELD PERFORMANCE PASS + INTEGRITY PASS**，但因 CASE 未輸出 Glow gas sigma cache hit/miss / inherited handoff hit telemetry，最終 `.10.9 FIELD PASS` 暫不關閉。

## Runtime

- `.10.8` Volume Assembly baseline：`4.542999 s`
- `.10.9` TWS095 Volume Assembly：`2.531329 s`
- 改善：約 `44.28%`
- 加速：約 `1.79x`
- `.10.8` Glow total：`10.252142 s`
- `.10.9` Glow total：`8.606167 s`
- Glow total 改善：約 `16.05%`

## Integrity

- Analysis Integrity：70 PASS / 1 NOT_APPLICABLE / 0 WARN / 0 FAIL
- CASE Integrity：32/32 PASS
- Glow targets：1092/1092
- 六波段 closure：正常
- Missing/conflict preservation：正常
- Shadow COT promotion guard：正常

## Telemetry 缺口

CASE 可看到 Main Viewing `gas_sigma_cache_entry_count_before=0`、`after=2754`，Glow 也標示 `shared_gas_context=SHARED_VIEWING_RUNTIME_CONTEXT`，但沒有 Glow Volume Assembly 的：

- cache hit count
- cache miss count
- inherited Viewing→Glow handoff hit count
- Glow before / after cache entries 的正式 export row

依原 `.10.9` Field gate，不應憑推論直接宣告 cache handoff 已在 Field telemetry 中證實。

## 後續

以 `.10.9.1` diagnostic-only hotfix 補 telemetry，再跑 Field CASE。若 handoff hits > 0、Integrity 正常且 runtime 不 regression，即可正式關閉 `.10.9` Field gate。
