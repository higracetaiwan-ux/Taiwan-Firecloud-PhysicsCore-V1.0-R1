# Taiwan Firecloud PhysicsCore V1.0-R5.7.39
## 2026-09-10 Sunset CASE 實地驗證報告

### 結論

R5.7.39 程式主體沒有造成 Formation / Viewing / Glow 回歸，但本版新增的 GFS `pgrb2b.0p25` Canvas Optical Truth probe **沒有取得任何 evidence row**。

Analysis Integrity：**62 PASS / 1 WARN**。唯一 WARN：

`CANVAS_OPTICAL_TRUTH_PGRB2B_PROBE_CONTRACT`

實際 request audit 共 2 rows，f003 / f006 均為 HTTP 500；`v1_canvas_optical_native_probe.csv` 與 summary 都為空。

### Root Cause

R5.7.39 對 secondary-parameter product `gfs.tCCz.pgrb2b.0p25.fFFF` 錯用了主 GFS product 的 Grib Filter endpoint：

`filter_gfs_0p25.pl`

NOMADS 對 GFS 0.25° Secondary Parameters 使用獨立 endpoint：

`filter_gfs_0p25b.pl`

因此本 CASE 的空 probe **不能解讀為 intermediate pressure levels condensate = 0**，只能解讀為 provider request failure / evidence unavailable。

### 其他科學鏈

- Formation Canvas：432 rows。
- `<2 km` 低雲錯誤升格：0。
- Target optical evidence：432/432 仍為 `CF_CLOUD_CONDENSATE_ZERO`；R5.7.39 probe 沒有改寫它們。
- Formation：10 rows `UNCERTAIN_OPTICS`、3 rows `NOT_FORMED_EARTH_SHADOW`。
- Near-Surface Molecular anchor：990/990 valid。
- Near-Surface bridge：42/42 resolved。
- Frozen molecular tolerance：0.01 km = 10 m。
- CAMS Post-success Download telemetry：PASS；本 CASE retry rows = 0。

### 正式判定

- R5.7.39 code/regression：PASS。
- R5.7.39 science isolation：PASS。
- R5.7.39 pgrb2b provider handoff：**FIELD FAIL / provider routing bug**。
- 不得把本 CASE 的空 probe 當成「原生 condensate 為零」。
- 修正版本：R5.7.39.1，僅將 pgrb2b endpoint 改為 `filter_gfs_0p25b.pl`，Formation/COT science 不變。
