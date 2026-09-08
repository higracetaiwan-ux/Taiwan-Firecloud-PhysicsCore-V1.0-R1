# Taiwan Firecloud PhysicsCore V1.0-R5.7.23.1 發行說明

## 版本定位

R5.7.23.1 是 R5.7.23 的 Runtime Hotfix，不更動既有科學權重與物理契約。

## 修正內容

1. **CAMS worker 完成後的隱藏停滯可觀測化**
   - 新增 `DECODED_ROUTE_CACHE_WRITE` 進度狀態。
   - 新增 `CAMS_BUNDLE_POSTPROCESS` 進度狀態。
   - UI 不再只停留在「時次 2/2 等待」而看不到父程序實際後處理。

2. **Cold Test 取消非必要 decoded-route 二次落盤**
   - `COLD_ISOLATED_TEST` 仍保存 atomic raw CAMS GRIB。
   - 不再同步寫 decoded-route pickle cache，避免 hosted/mounted filesystem 的第二次同步寫入拖住 analysis worker。
   - Missing / Clear / Zero 與所有 CAMS 科學資料內容均不改變。

3. **Warm / Resume decoded cache 降低 blocking 風險**
   - atomic rename 保留。
   - decoded cache 額外 `fsync` 改為 opt-in：`FIRECLOUD_CAMS_DECODED_CACHE_FSYNC=1`。

4. **Streamlit rerun 自動重新連線存活 worker**
   - 若 persisted analysis job 狀態為 RUNNING 且 PID 仍存活，頁面會自動 reattach。
   - 不再誤顯示「上一次分析未正常完成」。
   - 不會因 reload/rerun 啟動第二個 analysis worker。
   - reattach 時保留原始 job request，不以目前 UI 欄位覆寫原 job。

## 不變項目

- Formation / Viewing / Glow 分離不變。
- 0°～−6° 13-angle 契約不變。
- 六波段 550/575/600/650/700/750 nm 不變。
- Route Invariance −2° reference route 不變。
- Genuine Liquid-Cloud Full Directional Calibration V3 contract 不變。
- Genuine calibrated LUT 仍為 `NOT_YET_GENERATED_EXTERNAL_RT_REQUIRED`。

## Regression

- R5.7.23.1 working tree：**409 passed / 0 failed**。
