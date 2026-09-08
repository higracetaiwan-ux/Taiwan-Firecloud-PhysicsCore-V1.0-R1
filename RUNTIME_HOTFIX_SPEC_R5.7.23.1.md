# R5.7.23.1 Runtime Hotfix 規格

## 問題 1：CAMS 外部 worker 已完成，但下一時次仍顯示等待

實測恢復紀錄顯示最後 CAMS worker `NATIVE_AEROSOL_532NM_PRESSURE_LEVEL` 已 `COMPLETED`、exit code 0，但父 analysis worker 仍為 RUNNING。R5.7.23 在 worker checkpoint 完成後還有 decoded-route cache write 與 bundle merge/audit 後處理，原 UI 未覆蓋這段。

### 修正

- `DECODED_ROUTE_CACHE_WRITE`：顯示 decoded-route cache 落盤階段。
- `CAMS_BUNDLE_POSTPROCESS`：顯示時次 bundle merge / audit / completeness 階段。
- Cold isolated test 不做 decoded-route 二次落盤；raw GRIB 已是可恢復的原始 provider cache。

## 問題 2：Streamlit rerun 誤判仍存活 worker 為未完成

原 UI 只看 persisted job status，RUNNING 也直接進 recovery warning。若頁面 reload/rerun 時 detached worker 仍在執行，使用者可能被誘導再啟動一個 job。

### 修正

- 讀取 progress PID 並以 `_pid_alive()` 確認。
- `STARTING/RUNNING + PID alive` 視為 active detached job。
- 自動 reattach 到原 worker 的 progress/result file。
- 不啟動第二個 worker。
- reattach 使用原 job request。

## 安全邊界

本 hotfix 不修改任何 Formation、Viewing、Cloud Optical Truth、Spectral RT、Earth Shadow、Route Geometry 或 Tier-2 response 數值。
