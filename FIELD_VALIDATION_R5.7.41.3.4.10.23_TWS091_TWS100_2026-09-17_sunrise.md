# FIELD VALIDATION — V1.0-R5.7.41.3.4.10.23

## 測試案例

- TWS091｜2026-09-17 sunrise
- TWS100｜2026-09-17 sunrise

## Step 3J 科學結果

- Step 3J evidence：12 rows
- Step 3J gate：1 row
- Contract：`FIRECLOUD_ICE_WYSER_YANG_DIAGNOSTIC_BULK_V1`
- TWS091 / TWS100 的 Step 3J evidence / gate / contract 內容一致。
- Diagnostic six-band `beta_ext` / `k_ext`、PSD mass closure、grid convergence：PASS。
- Scientific bulk validation、habit bridge、roughness bridge、bulk production eligibility、`tau_ice` production、Production Ice Optics、`physics_promotion_allowed`：全部維持 false。

## CASE integrity

### TWS091

- Analysis Integrity：127 PASS / 1 NOT_APPLICABLE / 0 FAIL
- CASE Integrity：107/107 PASS
- CAMS pressure-level bundle：COMPLETED

### TWS100

- Analysis Integrity：126 PASS / 1 NOT_APPLICABLE / 0 FAIL
- CASE Integrity：107/107 PASS
- CAMS request audit：`PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE = TIMEOUT_DEFERRED`
- fallback `O3_PRESSURE_LEVEL` 與 `NATIVE_AEROSOL_532NM_PRESSURE_LEVEL` 後續成功，最終科學資料鏈未因此失效。

## 發現的 archive telemetry 問題

TWS100 的 `cams_request_audit.csv` 已正確記錄 pressure-level bundle 為 `TIMEOUT_DEFERRED`，但 `cams_worker_checkpoints.json` 對同一 worker 仍殘留：

- status = `RUNNING`
- exit_code = null

這是 archive telemetry / durable checkpoint reconciliation 問題，不是 Frozen Science 或 Step 3J 數值物理錯誤。

## 判定

`V1.0-R5.7.41.3.4.10.23`：**FIELD SCIENCE PASS / archive telemetry hotfix required**。

後續 hotfix：`V1.0-R5.7.41.3.4.10.23.1`，只修 CAMS terminal checkpoint reconciliation 與 Step 3J stable evidence serialization；不改 Step 3J 方程式與 Frozen Science。
