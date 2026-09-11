# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.1

## Direct Conflict Qualification Coverage Hotfix

- 修正 `CANVAS_OPTICAL_VERTICAL_CONFLICT_QUALIFICATION` 對 `DIRECT_EVIDENCE_CONFLICT` 的 coverage 契約。
- R5.7.40 qualifier 原先只處理 `CF_CLOUD_CONDENSATE_ZERO`；本版新增 `CONDENSATE_CLOUD_CF_LOW`。
- 新增 qualification state：`PRIMARY_NATIVE_CONDENSATE_WITH_LOW_CF_CONFLICT`。
- `CONDENSATE_CLOUD_CF_LOW` 保留獨立物理語義，不重新命名成 cloud-fraction spike。
- 不允許 COT / Formation promotion；RH/CF 仍不得生成 condensate 或 COT。
- 不修改 Production COT、Formation、Viewing、Twilight Glow、Photography science。

## Field trigger

2026-09-11 sunrise / TWS091 日月潭朝霧碼頭 R5.7.41.3 CASE：Target Optical Truth 有 58 個 direct-conflict canvases，其中 55 個為 `CF_CLOUD_CONDENSATE_ZERO`，另 3 個為 `CONDENSATE_CLOUD_CF_LOW`。舊 qualifier 僅覆蓋 55 個，造成 Analysis Integrity FAIL。
