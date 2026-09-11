# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.2

## Production COT Semantic Migration Contract / Shadow Mode

R5.7.41.2 將 legacy Production COT 與 R5.7.41 in-cloud exact-envelope assumed-r_eff COT 並列為兩套明確語義，新增 future-production eligibility gates，但本版不執行 Production switch。

新增：
- `firecloud/canvas_cot_semantic_migration.py`
- `v1_canvas_cot_semantic_migration.csv`
- `v1_canvas_cot_semantic_migration_summary.csv`
- `tools/replay_r57412_cot_semantic_migration.py`
- Analysis Integrity：`CANVAS_COT_SEMANTIC_MIGRATION_SHADOW`
- Analysis Integrity：`CANVAS_COT_SEMANTIC_MIGRATION_SHADOW_SUMMARY`

硬規則：Cloud Fraction = Canvas horizontal occupancy，與 in-cloud COT 分離；CF/RH 不得生成 candidate COT；direct conflict fail-close；assumed `r_eff` 必須明示。本版 Production COT source 仍固定 `LEGACY_CF_SCALED_GRID_CELL_MEAN`，任何 eligible candidate 都只在 Shadow Mode 中觀察，0 Production switch / 0 COT promotion / 0 Formation promotion。

2026-09-11 R5.7.41 Field CASE 離線 replay：767 targets，108 eligible shadow candidates，659 ineligible；Production switch=0。

Working-tree regression：580/580 PASS。Extracted full regression：580/580 PASS。FULL-CLEAN release gate：CLOSED。
