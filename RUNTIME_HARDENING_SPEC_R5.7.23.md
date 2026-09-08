# Taiwan Firecloud PhysicsCore V1.0-R5.7.23｜Runtime Hardening 規格

## 1. 目的

本規格處理長時間 TEST 中「畫面停在某個進度字樣，但無法確認真正執行位置」與「重新 TEST 可能沿用前次殘留 provider cache」兩類問題。

本版只改執行可靠性、診斷、快取安全與 CASE 證據，**不改 Formation / Viewing / Glow、Earth Shadow、六波段、Target Optical Truth、Route Invariance 或 Tier-2 科學權重**。

## 2. 三種執行模式

### `WARM_PRODUCTION`
一般正式分析。允許使用符合 provenance / QC 的既有 provider persistent cache。

### `COLD_ISOLATED_TEST`
診斷模式。每個 analysis `job_id` 使用獨立 provider cache namespace，不能讀取前一次 TEST 的 GFS / CAMS / Open-Meteo / Open-Meteo AQ / DWD ICON 動態資料快取。

DWD ICON 靜態 remap/grid mapping 資源可共用，避免為一次 Cold Test 重複下載大型不隨事件改變的靜態資源。

### `RESUME_SAME_JOB`
只用於接續同一個中斷 job。沿用同一 `job_id` 與 cache namespace；不得偽裝成新的 Cold Test。

## 3. Cache provenance

每個支援的 persistent cache 需保存或推導：

- provider / role
- cache path
- cache created / modified time
- source job id
- current job id
- run mode
- cache age
- `CURRENT_RUN_CACHE` / `PRIOR_RUN_PERSISTENT_CACHE`
- cache 是否早於本次 job
- schema / QC state（可用時）

CASE 彙整輸出：

`runtime_cache_provenance.csv`

因此後續不能再以「第二次 TEST 跑過」直接推論第一次 cold run 正常。

## 4. Atomic cache commit

網路或 decoded cache 採：

`temporary/partial file → 完整寫入 → flush/fsync/validation → atomic replace → CACHE_READY stamp`

半成品不得直接覆蓋正式 cache，也不得在下一次 TEST 被當成成功資料。

目前納入：

- GFS
- CAMS
- Open-Meteo
- Open-Meteo Air Quality / AOD fallback
- DWD ICON 動態 forecast cache

## 5. CAMS global ADS single-flight

Production-safe 預設：

> 同一時間最多一個 CAMS time-bundle 對 ADS 執行遠端請求。

每一時次內仍保持 O₃ / spectral AOD / aerosol 3D 角色串行。

`FIRECLOUD_CAMS_ALLOW_PARALLEL_TIME_BUNDLES=1` 僅作明確 expert opt-in；預設不可因兩個 valid times 同時發送 ADS request 而重新引入 429 / request contention。

下載完成後的本地 decode / interpolation 不受此科學規則限制。

## 6. 真正 Stage Trace 與獨立 Heartbeat

`analysis_worker.py` 不再只依 UI 最後一個 progress 字串判斷執行位置。

每個 stage 保存：

- stage / substage
- solar altitude / angle index（可解析時）
- `STARTED`
- `HEARTBEAT`
- `COMPLETED` / `FAILED`
- stage elapsed
- timestamp
- process resource snapshot

Heartbeat 預設每 5 秒由獨立 thread 更新，即使 production function 暫時沒有 progress callback，也能知道 worker 是否仍活著。

CASE 輸出：

`runtime_stage_trace.csv`

## 7. Resource telemetry

關鍵 physics stage 取樣：

- RSS
- peak RSS
- VM size
- thread count
- child process count
- 主要 DataFrame row count / approximate memory（可得時）

包含至少：

- Forecast voxel illumination
- 0.5 km reconstructed cloud column
- pressure-profile cloud volume
- GFS native cloud volume
- 3D optical blocking
- gas state prepared
- gas + six-band spectral RT
- per-angle physics total
- total analysis core

CASE 輸出：

`runtime_resource_telemetry.csv`

這可直接驗證 13-angle 是否真的有 RAM 累積，而不是從停留的 UI 字樣猜測。

## 8. Execution contract

CASE 另存：

`runtime_execution_contract.csv`

用來區分：

- `NEW_ANALYSIS_REUSING_PROVIDER_CACHE`
- `NEW_ANALYSIS_COLD_ISOLATED`
- `RESUME_INTERRUPTED_ANALYSIS`

Provider cache reuse 與 per-job recovery state 必須分離。

## 9. 驗收原則

同一事件至少保留兩種驗收：

1. **Cold Run**：驗證真正 network / provider / physics runtime bottleneck。
2. **Warm Run**：驗證 production persistent-cache 日常效能。

只有 Warm Run 成功，不得宣稱 Cold Run stall 已修復。
