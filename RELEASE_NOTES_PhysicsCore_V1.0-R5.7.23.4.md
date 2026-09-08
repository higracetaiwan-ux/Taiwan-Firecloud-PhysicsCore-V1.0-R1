# Taiwan Firecloud PhysicsCore V1.0-R5.7.23.4 發行說明

## 版本定位

R5.7.23.4 是 R5.7.23.3 的 Integrity-Audit Robustness Hotfix。此版不修改 Formation、Viewing、Glow、六波段 RT、Earth Shadow、Route Invariance、CAMS 90 秒 watchdog 或 Tier-2 directional calibration 科學計算。

## 修正問題

實際 COLD TEST 在 CAMS 某角色發生 90 秒 timeout 後，`firecloud/case_integrity.py::_cams_role_success()` 對 `cams_request_audit` mixed-type 欄位做 row-wise 字串拼接時，在 Python 3.14 / pandas runtime 觸發：

`TypeError: sequence item 1: expected str instance, float found`

因此原本應只是 CAMS evidence/completeness 降級的 provider timeout，反而在 Analysis Integrity 階段造成整個 analysis worker FAILED，CASE 無法正常完成。

## R5.7.23.4 修正

1. 新增 type-safe row text normalization；每一個 float、NaN、None、字串 scalar 都在 row boundary 明確正規化後才 join。
2. `case_integrity.py` 不再使用 `DataFrame.agg(" ".join, axis=1)` 處理 mixed-type CAMS/GFS audit 欄位。
3. 同一 CAMS role 若任一時次出現 `TIMEOUT / FAILED / ERROR / 429 / HTTP 4xx/5xx`，該 role 不得被誤提升為完整成功。
4. 新增 `CAMS_PROVIDER_TIMEOUT_VISIBLE` Integrity Audit 項目；provider timeout 會保留為 WARN/completeness evidence，而不是造成 audit exception。
5. CAMS timeout 仍遵守既有 Missing / Partial 規則，不以常數或零值補造 optical evidence。

## 回歸測試

完整 regression：**418 passed / 0 failed**。

新增測試涵蓋：
- mixed float / NaN CAMS role 欄位；
- 同一 role 一個時次 OK、另一時次 timeout；
- aerosol 90 秒 timeout 後 Analysis Integrity 仍能完成；
- timeout 在 CASE integrity 中明確可見。
