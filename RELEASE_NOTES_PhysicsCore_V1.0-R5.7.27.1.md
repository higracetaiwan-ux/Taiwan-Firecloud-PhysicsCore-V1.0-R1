# Taiwan Firecloud PhysicsCore V1.0-R5.7.27.1 Release Notes

## 版本主旨

**Photography Integrity Handoff Hotfix**

## 問題

R5.7.27 已建立並回傳完整 13-angle `v1_photography_decision`，但
`model.py` 的 `_pre_integrity_result` 漏掉這張表。因此真實 analysis pipeline
呼叫 Integrity 時會看到空的 Photography Decision；當 Red-Light summary 已
存在時，angle coverage 可能被誤判為 `FAIL`。

此外，CASE 雖會寫出 `v1_photography_decision.csv`，原本的 archive required
member 清單沒有檢查它，無法攔截封存層遺失。

## 修正

- 將正式 `v1_photography_decision` 傳入 `build_analysis_integrity_audit()`。
- CASE Integrity 新增 required member：`v1_photography_decision.csv`。
- 新增 model→integrity wiring regression。
- 新增 CASE photography member presence／absence regression。
- 版本更新為 `1.0.0-R5.7.27.1`。

## 不變的 PhysicsCore 契約

本 hotfix 不修改 Formation、Viewing、Glow、Red-Light Availability、13 angles、
六波段、Earth Shadow、COT truth、Tier-2、route resolution、任何科學權重，
也不改變 Forecast／Observation／Nowcast 的分離。

## 驗收

- 原始 R5.7.27 基線：**461 passed / 0 failed**。
- R5.7.27.1 專項：**16 passed / 0 failed**。
- Working tree 完整 regression：**464 passed / 0 failed**。
- FULL-CLEAN ZIP 解壓後完整 regression：**464 passed / 0 failed**。
