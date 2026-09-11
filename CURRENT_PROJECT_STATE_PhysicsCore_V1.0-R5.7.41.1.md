# Taiwan Firecloud PhysicsCore — Current Project State
## V1.0-R5.7.41.1

### 正式基線
- 前一正式版：V1.0-R5.7.41
- 本工作版：V1.0-R5.7.41.1 COT Diagnostic Reconciliation

### 已完成
R5.7.41 Target Vertical Microphysics Overlap 已 Field PASS / CLOSED：Analysis Integrity 68/68 PASS、CASE Integrity 23/23 PASS。

R5.7.41.1 針對同一 Field CASE 中 `direct_native_cot≈0.00736229` 與 `overlap COT≈0.01335034` 做離線 reconciliation。108/108 comparable targets 全部可由以下三項完整解釋：
1. legacy half-cell edge support
2. Cloud Fraction 是否縮放 extinction 的語義差
3. pgrb2b intermediate pressure-level vertical resolution

最大 residual 僅約 `9.63e-17`。

### 凍結規則
- 不由 RH / CF 生成 condensate 或新 COT
- Missing != Zero != Clear
- R5.7.41.1 不替換 Production target COT
- `cot_promotion_allowed=False`
- `formation_promotion_allowed=False`
- Formation / Viewing / Twilight Glow 保持分離

### Release Gate
- working-tree regression：574/574 PASS
- extracted regression：574/574 PASS
- FULL-CLEAN：CLOSED

### 下一步
1. 決定是否建立 Production COT semantic migration
2. 在 migration 前保持新 overlap COT diagnostic-only
3. Native 127-level provider 仍為後續獨立工作，不與本 reconciliation 混版
