# PhysicsCore V1.0-R5.7.27.1 Implementation Status

## 已完成

- [DONE] 補上 `v1_photography_decision` 的 model→Analysis Integrity handoff。
- [DONE] Analysis Integrity 現在檢查主 pipeline 實際回傳／匯出的同一份 decision table。
- [DONE] `v1_photography_decision.csv` 納入 CASE archive required members。
- [DONE] 新增 production wiring regression，避免只測 helper 而漏測 pipeline。
- [DONE] 新增 CASE member presence／absence regression。
- [DONE] 完整保留 R5.7.27 Formation-first 與 13/13 angles 行為。

## Regression

- R5.7.27 原始附件基線：**461 passed / 0 failed**。
- R5.7.27.1 專項：**16 passed / 0 failed**。
- R5.7.27.1 working tree 完整回歸：**464 passed / 0 failed**。
- FULL-CLEAN ZIP 解壓後完整回歸：**464 passed / 0 failed**。

## 尚待真實 CASE

- 真實 R5.7.27.1 部署 CASE 應確認：
  - `PHOTOGRAPHY_DECISION_FORMATION_ANGLE_COVERAGE = PASS`
  - `PHOTOGRAPHY_FORMATION_NO_GO_DOMINANCE = PASS`
  - `ANALYSIS_INTEGRITY_OVERALL` 不再因 decision handoff 缺失誤報 FAIL
  - `ARCHIVE_MEMBER::v1_photography_decision.csv = PASS`
