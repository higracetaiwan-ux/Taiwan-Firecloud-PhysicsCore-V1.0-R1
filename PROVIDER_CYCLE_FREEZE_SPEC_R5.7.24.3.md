# R5.7.24.3 Provider Cycle Freeze 規格

## 目的

R5.7.24.3 修正單次長時間分析內，Provider cycle availability 隨真實牆鐘跨越發布邊界而改變，造成「前段預取」與「後段 per-angle lookup」使用不同 GFS/CAMS cycle 的可靠性錯誤。

本修正屬於 Runtime / Provider Handoff Reliability，不改變任何火燒雲物理、Formation / Viewing、六波段、Earth Shadow、Missing 語義或 Target Canvas 判定。

## 真實 CASE 觸發條件

R5.7.24.2 於 2026-09-08 12:06:59 UTC 啟動分析。CAMS availability lag 為 12.25 h。

- 12:07 UTC：`now - 12.25 h` 尚落在 2026-09-07，因此預取解析到 `2026-09-07 12Z`，對事件時刻使用 +21 h / +24 h。
- 12:15 UTC：availability boundary 被跨越，resolver 會開始認為 `2026-09-08 00Z` 可用，對相同事件時刻改解析成 +9 h / +12 h。
- 第一個 0° angle 於 12:15:15 UTC 開始，因此 per-angle lookup 已切到新 cycle，與先前 `cams_native_cache` 的 key 不一致。

結果是：CAMS worker 實際已有成功資料，但 per-angle 端查不到預取 payload，O3 / native aerosol / request audit 全部看起來像 Missing。

## 新契約

Analysis worker 啟動時建立不可變的：

`FIRECLOUD_PROVIDER_RESOLUTION_NOW_UTC=<analysis-start UTC>`

同一個 analysis job 內所有依賴「目前時間」判定可用 cycle 的 provider resolver，必須使用這個固定 clock：

- GFS resolver
- CAMS resolver
- CAMS decoded cache key
- CAMS raw request builder
- CAMS external subprocess worker
- per-angle provider lookup

CAMS 子程序繼承 analysis worker environment，因此 request 建立、cache path 與 parent lookup 使用相同 resolution clock。

## 明確不改變

- Forecast valid time 不變。
- Provider availability lag 值不變（CAMS 仍預設 12.25 h）。
- CAMS 90 秒 watchdog 不變。
- Missing ≠ Clear ≠ Zero。
- Timeout 仍為 Missing/Deferred，不使用舊資料或常數補值。
- 13 angles、六波段、Formation / Viewing / Glow 分離不變。

## Runtime Evidence

`runtime_execution_contract.csv` 新增：

- `provider_cycle_resolution_frozen = True`
- `provider_resolution_now_utc`

用於 CASE forensic 證明整次分析採用哪一個 provider availability reference clock。
