# Taiwan Firecloud PhysicsCore V1.0-R5.7.23.3 發行說明

## 版本主旨

**CAMS Single-Flight Live-Telemetry Hotfix**

本版針對 R5.7.23.2 production safe CAMS 預取在第一個 time bundle 執行期間，UI 可能長時間顯示「時次 1/2｜等待；時次 2/2｜等待」的現象進行修正。

## 問題根因

R5.7.23.2 的 global ADS single-flight production 路徑採同步 time-bundle 執行。CAMS role worker heartbeat 已持續更新內部狀態，但 `_render_cams_prefetch_progress()` 只在整個 bundle 執行前／返回後刷新，因此 O₃、Spectral AOD、532 nm aerosol 實際執行時，UI 仍可能停留在兩個時次皆「等待」。

此外，第一個外部 worker 啟動前會先檢查 decoded-route cache；該 cache lookup 原本沒有獨立 telemetry，因此 mounted filesystem 的慢速 pickle/stat I/O 也可能被誤認成 ADS stall。

## 本版修正

- Production global single-flight 模式下，每次 CAMS role heartbeat 立即刷新 UI。
- 新增 `DECODED_ROUTE_CACHE_LOOKUP` 狀態：`RUNNING / CACHE_HIT / MISS`。
- 新增 `CAMS_WORKER_STARTUP` 狀態：worker 啟動前後可見。
- 保留 expert parallel 模式原本 scheduler-side 0.5 秒刷新，避免從 worker thread 直接更新 Streamlit UI。
- 不修改 CAMS 90 秒 deadline、adaptive planner、ADS single-flight、安全 cache 邏輯或任何科學輸出。

## 預期 UI

第一個 time bundle 執行時，不再長時間顯示兩個時次皆等待；應依序可見：

`解碼快取查找 → worker啟動 → O₃ → 光譜AOD → 3D氣膠 → 解碼快取落盤 → 時次後處理`

第二個時次在 single-flight 模式下維持「等待」是正常的，直到第一個 time bundle 完成。

## Regression

- Working tree：415 passed / 0 failed
