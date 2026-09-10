# Taiwan Firecloud PhysicsCore V1.0-R5.7.35.2 發行說明

## 本版變更

- 修正零有效 Viewing target 時的 precipitation Integrity false FAIL。
- 新增回歸測試，確保 `eligible=0` 時為 `NOT_APPLICABLE`。
- 保留反向測試：只要有 eligible target，原生 RWMR/SNMR/GRLE READY 而 precipitation evidence 空白時仍必須 FAIL。

## 不變項目

- 13 個太陽高度角與六波段不變。
- Formation / Viewing / Twilight Glow 三軌分離不變。
- Missing ≠ Clear ≠ Zero ≠ N/A。
- 不修改任何物理權重、COT、SSA、g、HG phase、降水消光或攝影判斷。

## 驗證狀態

- 專項測試：PASS。
- 完整 regression 與 FULL-CLEAN extracted regression 以正式封包結果為準。
- 真實新 CASE Field Validation：OPEN。
