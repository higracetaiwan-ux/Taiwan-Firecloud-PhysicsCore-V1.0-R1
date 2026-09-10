# Taiwan Firecloud PhysicsCore V1.0-R5.7.38
## 2026-09-10 Sunset CASE 實地驗證報告

### 一、總結

本次 CASE 的 Analysis Integrity 為 **62/62 PASS**，Case Integrity 為 **23/23 PASS**。
R5.7.38 新增的 `CAMS_POST_SUCCESS_DOWNLOAD_RECOVERY_TELEMETRY` 為 **PASS**，10 個 fresh terminal-successful CAMS requests 全部帶出 R5.7.38 download recovery telemetry 與 contract。

但本次沒有實際遇到 HTTP 502/503/504/429 或 connection download failure，因此：

- **R5.7.38 telemetry / baseline path：FIELD PASS**
- **真正 post-success download retry/recovery branch：FIELD OPEN**
- 不把 `retry_rows=0` 的 CASE 宣稱為 recovery field-close。

### 二、CAMS Post-success Download Recovery

本次 CAMS 共 **10 requests**（5 roles × 2 forecast times），全部：

- `status=OK`
- `ads_remote_status=successful`
- `ads_request_reattached=False`
- `cache_hit=False`
- `ads_download_strategy=DIRECT_RESULTS_LOCATION_BOUNDED_RETRY_V1`
- `ads_download_recovery_contract=R5.7.38_POST_SUCCESS_SAME_REQUEST_ID_BOUNDED_DOWNLOAD_RETRY_V1`

所有 request：

- `ads_download_attempts=1`
- `ads_download_retry_count=0`
- `ads_download_backoff_seconds=0`
- `ads_download_url_refresh_count=1`
- `ads_download_last_error` 為空

最慢下載僅約 **3.343 s**，本次沒有隱藏的 120 s download sleep。

新 Integrity：

`CAMS_POST_SUCCESS_DOWNLOAD_RECOVERY_TELEMETRY = PASS`

Observed：

`fresh_success=10;retry_rows=0;contract=10/10`

### 三、R5.7.37 Near-Surface Molecular Boundary 無回歸

以下全部 PASS：

- `TWILIGHT_GLOW_OBSERVER_DEEP_RANGE_MOLECULAR_COVERAGE`
  - resolved = **156/156**
- `NEAR_SURFACE_MOLECULAR_BOUNDARY_ANCHOR_PROVENANCE`
  - valid = **990/990**
- `NEAR_SURFACE_MOLECULAR_BOUNDARY_FROZEN_10M_TOLERANCE`
  - min = **0.01 km**
  - max = **0.01 km**
- `NEAR_SURFACE_MOLECULAR_BOUNDARY_BRIDGE_PROVENANCE`
  - bridged = **42**
  - resolved = **42/42**

因此 10 m frozen tolerance 仍未放寬，ML137 + surface thermodynamic bridge 正常工作。

### 四、Formation / Viewing / Aerosol 無回歸

Formation Canvas：

- candidates = **432**
- `<2 km` promoted = **0**
- non-target role = **0**
- `FORMATION_CANVAS_LOW_CLOUD_ROLE_SEPARATION = PASS`

Viewing precipitation：

- eligible targets = **432**
- precipitation rows = **432**
- missing = **0**
- volume unresolved = **0**
- `VIEWING_PRECIPITATION_TARGET_COVERAGE = PASS`
- `VIEWING_NATIVE_HYDROMETEOR_HANDOFF = PASS`

Glow Scatter→Observer：

- **1092/1092 FULL six-band extinction**
- observer missing components = 0

Aerosol single-scattering：

- READY = **127**
- UNRESOLVED = **965**
- 965 unresolved 全部明確為 `SUN_TO_SCATTER_EXTINCTION`
- unresolved missing-reason gap = **0**

### 五、Runtime

Run mode：`WARM_PRODUCTION`

- `CAMS_PREFETCH_TOTAL` = **487.674 s**
- `ALL_ANGLES_PHYSICS_TOTAL` = **364.820 s**
- `TWILIGHT_GLOW_INDEPENDENT_BRANCH` = **95.320 s**
- `AGGREGATION_AND_MATRIX_BUILD` = **153.172 s**
- `TOTAL_ANALYSIS_CORE` = **1171.662 s**
- `CASE_EXPORT_SERIALIZATION` = **28.138 s**
- `TOTAL_TO_CASE_ARCHIVE` = **1199.801 s**（約 19 分 59.8 秒）
- peak RSS = **907.785 MB**

R5.7.37 到 CASE 約 1139.378 s，本次 R5.7.38 約增加 60.4 s，但兩次使用不同 CAMS forecast cycles：

- R5.7.37：2026-09-09 12Z，lead 21/24
- R5.7.38：2026-09-10 00Z，lead 9/12

而 R5.7.38 CAMS queue/running 合計也明顯較高，因此不能把約 60 秒差異歸因為 R5.7.38 recovery code regression。

本次最慢 CAMS request 為 AEROSOL_SCATTERING_COLUMN_PROPERTIES lead 12：

- queue ≈ **52.730 s**
- running ≈ **10.020 s**
- download ≈ **1.450 s**
- total worker elapsed ≈ **72.235 s**

沒有 120 秒 post-success download sleep。

### 六、Field-close 判定

- **R5.7.38 Code / Regression / FULL-CLEAN：CLOSED**
- **R5.7.38 download telemetry contract：FIELD PASS**
- **R5.7.38 no-error baseline download path：FIELD PASS**
- **R5.7.38 actual 502/503/429 same-request download retry：FIELD OPEN**（本 CASE 未觸發）
- **R5.7.34 true request-ID reattach：仍 FIELD OPEN**（本 CASE `ads_request_reattached=False`）
- **R5.7.37 Near-Surface Molecular Boundary：維持 FIELD CLOSED**
- **Overall CASE：62/62 Analysis PASS；23/23 CASE PASS**

### 七、下一步

不需要因本次沒有 retry 而修改 R5.7.38 科學或 runtime policy。下一個真實 CASE 若自然遇到 post-success 502/503/429，檢查：

1. `ads_download_attempts > 1`
2. `ads_download_retry_count > 0`
3. `ads_download_backoff_seconds` 為 bounded short backoff
4. request ID 前後一致
5. `submit` 沒有重複
6. 最終 download 成功且 CASE Integrity PASS

達成後才能把 R5.7.38 actual recovery branch 正式 FIELD CLOSED。
