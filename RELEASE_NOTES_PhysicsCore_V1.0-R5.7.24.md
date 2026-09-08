# Taiwan Firecloud PhysicsCore V1.0-R5.7.24 改版說明

## 版本主題

**Runtime Reliability / Completion Guarantee + Memory Containment**

本版以「程式功能能可靠完成」為最高優先。效能最佳化延後，不以減少太陽角度、降低垂直解析度、刪除六波段或減少 CASE 證據換取速度。

## 主要修正

### 1. Streamlit 前端不再長時間阻塞

背景 analysis worker 與 Streamlit UI 監看解耦。啟動或重新連線後，主 script 不再停留於 10–15 分鐘的同步 polling loop；改由短週期、非阻塞 fragment 讀取 worker progress。

頁面 rerun / reload 若原 worker PID 仍存活，UI 會自動重新連線監看，並停用新的「開始分析」，避免重複 worker、重複 CAMS ADS request 與 cache 競爭。

### 2. Recovery journal 冗餘化

分析狀態同時寫入：

- `.firecloud_state/analysis_job_state.json`
- `.firecloud_state/analysis_jobs/<job_id>/job_state.json`
- `.firecloud_state/analysis_jobs/<job_id>/attempts/attempt_NNN/progress.json`

若 master journal 遺失或損壞，啟動時會從 per-job journal 或最新 attempt progress 重建 recovery 狀態。journal 寫入錯誤不再完全靜默，另記錄 `recovery_journal_error.log`。

### 3. Attempt 狀態分離

每次 Resume 建立獨立 attempt 目錄，保存 request / progress / stdout / stderr / result。上一 attempt 的錯誤會保存在 attempt history，不再混入目前成功 worker 的 stderr。

### 4. Route snapshot 記憶體收斂

原流程會先把 13 個太陽高度角的完整 route snapshot 全部內插並常駐 RAM。R5.7.24 仍維持「先完成 13 個時間點內插」的科學/流程契約，但每一份完整 snapshot 立即寫到 worker-local `/tmp` spool，只保留 DWD secondary optics 需要的小型 surface-pressure / elevation anchor。

每個角度只取回自己的一份 snapshot，用完即刪。

### 5. Per-angle atmospheric / spectral evidence spool

除既有 cloud voxel matrices 外，以下 per-angle evidence 也不再累積 13 份於 Python heap：

- gas profile
- CAMS native aerosol route snapshot
- aerosol spectral route snapshot
- spectral RT voxels / columns
- Viewing route snapshot

Physics Data Completeness 改為在該角度 evidence 仍在記憶體時，先建立小型 readiness summary，再把完整 DataFrame 移至 `/tmp`。

### 6. `details` provider snapshot 瘦身

UI 的「太陽方向垂直剖面」只需要：

- direction offset
- distance
- low cloud cover
- mid cloud cover
- high cloud cover

因此 `details` 不再保存含大量 provider/native 欄位的完整 snapshot，只保存上述 UI 契約必要欄位。

### 7. Native allocator memory trim

每個角度完成並完成 spool 後：

1. 解除大型 local references；
2. `gc.collect()`；
3. Linux/glibc 可用時呼叫 `malloc_trim(0)`。

analysis worker 啟動環境另加入：

- `MALLOC_ARENA_MAX=2`
- `MALLOC_TRIM_THRESHOLD_=131072`

目的為減少 Pandas/NumPy 釋放物件後，glibc heap arena 仍長時間映射在 RSS 的情況。

### 8. Aggregation 前釋放 provider cache

13-angle 全部完成後，進入 final aggregation 前釋放不再需要的：

- GFS native in-memory cache
- CAMS native in-memory cache
- Secondary forecast optics in-memory cache
- route snapshot temporary spool / surface anchor

這些變更只調整記憶體生命週期，不改變 provider evidence 或最終輸出。

## 科學契約沒有修改

本版不修改：

- Formation = Sun → CloudBase
- Viewing = Cloud → Observer
- Glow 獨立分支
- 0°～−6°、0.5° 間距 13 angles
- 六波段 550/575/600/650/700/750 nm
- DirectSolarFraction / Earth Shadow / Refraction
- Effective Canvas 定義
- Missing ≠ Clear ≠ Zero
- Forecast / Observation / Nowcast 分離
- Route Invariance
- Full Directional Tier-2 geometry

## Genuine Directional LUT 狀態

本建置環境仍未安裝 `uvspec` / libRadtran，因此：

**CALIBRATED DIRECTIONAL LUT NOT INSTALLED**

R5.7.23 的 genuine liquid-cloud calibration pipeline 保留，但不得使用 synthetic LUT 冒充 genuine calibration。

## Regression

R5.7.24 working tree 完整 regression：**428 passed / 0 failed**。
