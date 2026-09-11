# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.1
## COT Diagnostic Reconciliation Spec

### 目的
R5.7.41 Field CASE 顯示，同一批 108 個 non-conflict Canvas：
- production `direct_native_cot / target_cot_nominal` 約 `0.00736229`
- R5.7.41 overlap `cot_estimate_assumed_reff` 約 `0.01335034`

R5.7.41.1 不改 Production COT，而是把兩者的物理語義拆開並要求可完全重建。

### 已確認的兩種語義
1. **Legacy / Production direct COT**
   - primary GFS pgrb2 pressure levels only
   - condensate + assumed r_eff
   - sample Cloud Fraction 會縮放 extinction
   - multi-level CloudLayer 會在上下端各加半個 native level spacing 的 edge support
   - 因此較接近 grid-cell-mean / CF-scaled optical depth 語義

2. **R5.7.41 overlap diagnostic COT**
   - primary pgrb2 + pgrb2b intermediate pressure levels
   - 只積分 target Cloud Base–Top envelope
   - Cloud Fraction 固定不參與 COT
   - 代表 target in-cloud microphysics diagnostic
   - 仍使用 assumed effective radius，因此不是 exact/native COT

### Reconciliation 分解
對可比較 Target 輸出：
- `legacy_primary_exact_envelope_cf_scaled_cot`
- `primary_exact_envelope_incloud_cot`
- `legacy_half_cell_edge_support_delta_cot`
- `cloud_fraction_semantics_delta_cot`
- `pgrb2b_vertical_resolution_delta_cot`
- `observed_new_minus_legacy_delta_cot`
- `explained_new_minus_legacy_delta_cot`
- `reconciliation_residual_cot`

必須滿足：

`new - legacy = CF semantic delta + pgrb2b resolution delta - legacy half-cell edge delta + residual`

其中 residual 應僅為浮點誤差。

### 2026-09-11 Field CASE 離線重播
108/108 comparable targets：
- `SEMANTIC_DIFFERENCE_EXPLAINED`
- legacy reconstruction match：108/108
- overlap / legacy COT ratio：約 `1.8133405`
- mean legacy half-cell edge delta：約 `0.00368114545`
- mean CF semantic delta：約 `0.00518793206`
- mean pgrb2b resolution delta：約 `0.00448126273`
- max abs residual：約 `9.63e-17`

### 硬性安全契約
- `production_target_cot_replaced = False`
- `cot_promotion_allowed = False`
- `formation_promotion_allowed = False`
- `cloud_fraction_used_for_new_cot = False`
- `rh_used_to_infer_condensate = False`

本版只完成診斷 reconciliation，不決定哪一套 COT 可以進入 Production Formation。
