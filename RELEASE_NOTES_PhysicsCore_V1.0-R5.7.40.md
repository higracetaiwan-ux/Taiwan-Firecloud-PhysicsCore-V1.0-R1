# Taiwan Firecloud PhysicsCore V1.0-R5.7.40 發行說明

## 主題
Cloud-Fraction ↔ Native Hydrometeor Vertical Conflict Qualification。

## 完成
- 新增 `firecloud/canvas_optical_vertical_conflict.py`。
- 對 `CF_CLOUD_CONDENSATE_ZERO` Canvas 檢查主衝突 pressure level、上下主 pgrb2 鄰層、兩側最近 pgrb2b 中間 hydrometeor levels。
- pgrb2b probe 收斂為 hydrometeor-only pressure-level evidence；不使用 pgrb2b TCDC 作 geometry/COT。
- 新增兩個 CASE tables 與兩個 Integrity guards。
- 所有 classification 都明確 `cot_promotion_allowed=False`、`formation_promotion_allowed=False`。
- RH/cloud fraction 不得生成 condensate/COT；Missing 保持 Missing。

## 驗證
- Focused：20/20 PASS。
- Working full regression：562/562 PASS。
- Field validation：OPEN，需 R5.7.40 新 CASE。

## Release Gate
- Working regression：562/562 PASS
- FULL-CLEAN：CLOSED
- Extracted regression：562/562 PASS
- cache / pyc：0
- Field validation：OPEN
