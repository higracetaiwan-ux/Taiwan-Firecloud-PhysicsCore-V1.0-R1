# Taiwan Firecloud PhysicsCore V1.0-R5.7.38
## CAMS 遠端成功後下載復原規格

### 1. 問題來源

R5.7.37 真實 CASE 再次觀察到 CAMS ADS 遠端工作已進入 `successful`，但 GRIB 下載階段遭遇 `502 Bad Gateway`。遠端 queue + running 約 21 秒已完成，既有 client downloader 卻進入約 120 秒的 retry sleep，使單一 role worker 延長到約 153 秒。

這不是 ADS queue/running timeout，也不是 remote job failure，因此不得重新 submit 相同 CAMS 工作。

### 2. 凍結原則

1. R5.7.34 的 request fingerprint、request ID journal、queue/running/total phased deadline 完全保留。
2. remote status 到達 terminal success 後，進入獨立 Download Phase。
3. Download retry 永遠沿用同一 `request_id`，不得建立第二個 remote job。
4. 每次 retry 重新向同一 request ID 取得 Results/目前下載位置，以避免固定卡在同一 download node。
5. 暫時性錯誤只包含 HTTP `408/429/500/502/503/504` 與連線/timeout/OSError 類錯誤。
6. 非暫時性 HTTP 錯誤（例如 404）立即 fail-close，不盲目 retry。
7. 下載 URL 可能包含暫時性存取資訊，**不得寫入 request journal、CASE CSV、錯誤 audit 或說明檔**。
8. Download recovery 失敗後，remote successful job 仍保留；下一次相同 request 先 reattach 同一 request ID，再嘗試下載。
9. 不修改任何 Formation、Viewing、Glow、O₃、AOD、SSA/g 或六波段物理。

### 3. 預設有界下載策略

環境變數：

- `FIRECLOUD_CAMS_DOWNLOAD_MAX_ATTEMPTS=4`
- `FIRECLOUD_CAMS_DOWNLOAD_INITIAL_BACKOFF_SECONDS=2`
- `FIRECLOUD_CAMS_DOWNLOAD_MAX_BACKOFF_SECONDS=12`
- `FIRECLOUD_CAMS_DOWNLOAD_HTTP_TIMEOUT_SECONDS=45`

預設 backoff 約為 2 / 4 / 8 秒。若 server 提供 `Retry-After`，只在本地最大 backoff 上限內採用；例如 `Retry-After: 120` 不會重新導入 120 秒 stall，而會被上限約束。

### 4. 下載策略

主要策略：

`DIRECT_RESULTS_LOCATION_BOUNDED_RETRY_V1`

流程：

`remote successful`
→ `Client.get_results(request_id)`
→ 取得目前 Results location
→ 單次直接下載
→ transient failure 時短 backoff
→ 再以同一 request ID 重新取得 Results/location
→ 成功或達到最大 attempts。

若舊版/測試 client 不提供 Results/location，保留：

`CLIENT_NATIVE_DOWNLOAD_FALLBACK_ONCE`

此 fallback 僅執行一次，避免外層 retry 疊加 client 自己的長時間 retry。

### 5. 新增 CASE / audit 欄位

fresh terminal-successful CAMS request 應輸出：

- `ads_download_strategy`
- `ads_download_attempts`
- `ads_download_retry_count`
- `ads_download_url_refresh_count`
- `ads_download_backoff_seconds`
- `ads_download_elapsed_seconds`
- `ads_download_http_timeout_seconds`
- `ads_download_last_error`
- `ads_download_recovery_contract`

契約值：

`R5.7.38_POST_SUCCESS_SAME_REQUEST_ID_BOUNDED_DOWNLOAD_RETRY_V1`

### 6. Integrity

新增：

`CAMS_POST_SUCCESS_DOWNLOAD_RECOVERY_TELEMETRY`

- fresh terminal-successful request：必須存在完整 R5.7.38 download telemetry。
- cache-only run：只能視為未發生 fresh download，不能假裝成 Field Proof。
- retry 發生時可由 `ads_download_retry_count > 0` 直接留下 field evidence。

### 7. Field Validation 目標

最理想 CASE 是再次真實遭遇 502/503/429 等 transient download failure，並確認：

1. `ads_remote_status=successful`
2. `ads_download_retry_count>=1`
3. `ads_download_attempts>=2`
4. request ID 在 retry 前後完全相同
5. 沒有 duplicate submit
6. worker 不再出現固定 120 秒 download backoff
7. 最終 GRIB decode 與科學結果正常
