# R5.7.23.3 CAMS Live Telemetry 規格

## 目的

避免 production ADS single-flight 模式下，第一個 CAMS time bundle 已實際工作，但 UI 仍長時間顯示「時次 1/2｜等待；時次 2/2｜等待」。

## Production single-flight 顯示契約

每一 time bundle 的狀態可依序顯示：

1. `DECODED_ROUTE_CACHE_LOOKUP`
   - `RUNNING`
   - `CACHE_HIT` 或 `MISS`
2. `CAMS_WORKER_STARTUP`
   - `RUNNING`
   - `OK`
3. `O3_PRESSURE_LEVEL`
4. `SPECTRAL_COLUMN_AOD`
5. `NATIVE_AEROSOL_532NM_PRESSURE_LEVEL`
6. `DECODED_ROUTE_CACHE_WRITE`
7. `CAMS_BUNDLE_POSTPROCESS`

Production single-flight 僅允許一個 time bundle 進入 ADS 角色鏈，因此第一個 time bundle 執行期間第二個時次顯示「等待」屬正常狀態。

## 即時刷新規則

- `_cams_parallel_workers == 1`：role callback 直接觸發 progress renderer，確保 heartbeat 即時呈現。
- expert parallel mode：不從 worker thread 直接呼叫 Streamlit UI，維持 scheduler 每 0.5 秒刷新。

## 科學邊界

本 hotfix 不修改：

- CAMS request variables
- 90 秒 role deadline
- adaptive spatial subdivision
- cache evidence / Missing 語義
- Formation / Viewing / Glow
- 六波段 RT
- Tier-2 calibration contract
