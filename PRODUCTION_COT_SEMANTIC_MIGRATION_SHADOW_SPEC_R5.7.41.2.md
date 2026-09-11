# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.2
## Production COT Semantic Migration Contract / Shadow Mode

### 目的
R5.7.41.1 已證明 legacy `direct_native_cot` 與 R5.7.41 target-envelope in-cloud COT 的差異是可解釋的物理語義差，而非未知數值漂移。本版建立正式 migration contract，但**不切換 Production Target COT**。

### 目前兩套語義
- `LEGACY_CF_SCALED_GRID_CELL_MEAN`：既有 Production COT。primary pgrb2、Cloud Fraction 縮放 extinction、legacy half-cell edge support。
- `IN_CLOUD_EXACT_ENVELOPE_ASSUMED_REFF`：R5.7.41 target Cloud Base–Top exact envelope、pgrb2+pgrb2b、Cloud Fraction 不縮放 COT、明確 assumed effective radius。

Cloud Fraction / Canvas Coverage 與 in-cloud COT 永久分離。Cloud Fraction 不得生成或修改 candidate COT。

### Shadow eligibility gates
只有同時滿足以下條件，才標記 `ELIGIBLE_SHADOW_CANDIDATE`：
1. Target Cloud Base–Top envelope 有效。
2. Vertical native evidence sufficient，至少兩個 target-envelope native samples，且 vertical bracketing complete。
3. 無 `DIRECT_EVIDENCE_CONFLICT`。
4. Target envelope 內 condensate evidence 完整，Missing 不得當 Zero。
5. Candidate COT 未使用 Cloud Fraction。
6. 未使用 RH 推導 condensate。
7. `r_eff` provenance 明確；本版為 `ASSUMED_DEFAULTS_EXPLICIT`。
8. Vertical integration contract PASS，COT 狀態為 `COT_ESTIMATE_ASSUMED_REFF`。

### Shadow-only 硬規則
即使 eligibility PASS：
- `production_target_cot_source = LEGACY_CF_SCALED_GRID_CELL_MEAN`
- `shadow_candidate_cot_source = IN_CLOUD_EXACT_ENVELOPE_ASSUMED_REFF`
- `production_switch_performed = False`
- `production_target_cot_replaced = False`
- `cot_promotion_allowed = False`
- `formation_promotion_allowed = False`

因此 R5.7.41.2 不修改 Formation、Viewing、Glow、Photography 或任何物理門檻。

### CASE 輸出
- `v1_canvas_cot_semantic_migration.csv`
- `v1_canvas_cot_semantic_migration_summary.csv`

每筆永久保留：
- `legacy_grid_cell_mean_cot`
- `in_cloud_target_cot`
- `cloud_fraction`
- `canvas_coverage_semantics`
- `cot_migration_delta`
- `cot_migration_ratio`
- 所有 eligibility gate 與 ineligibility reasons
- Production 與 shadow source provenance

### Integrity
新增：
- `CANVAS_COT_SEMANTIC_MIGRATION_SHADOW`
- `CANVAS_COT_SEMANTIC_MIGRATION_SHADOW_SUMMARY`

Integrity 必須確認：
- 一個 vertical-overlap target 對應一個 shadow migration row；
- eligible row 的所有 gates 均 PASS；
- ineligible row 必須有明確原因；
- candidate COT 不使用 CF/RH；
- Production source 仍為 legacy；
- 0 production switch / 0 COT promotion / 0 Formation promotion。

### 離線回放
`tools/replay_r57412_cot_semantic_migration.py` 可直接讀 R5.7.41 CASE ZIP／目錄，不呼叫任何網路 provider。

2026-09-11 sunset Field CASE 離線 shadow replay：
- target rows：767
- eligible shadow candidates：108
- ineligible：659
- 659 筆皆因 `DIRECT_EVIDENCE_CONFLICT` 且 vertical COT integration fail-close
- production switch：0
- COT promotion：0
- Formation promotion：0

### 後續
Shadow Mode 累積多 CASE 後，才可討論 Production switch。由於 candidate COT 目前仍使用 assumed `r_eff`，正式語義必須維持 `IN_CLOUD_COT_ESTIMATE_ASSUMED_REFF`，不得稱為 `EXACT_NATIVE_COT`。
