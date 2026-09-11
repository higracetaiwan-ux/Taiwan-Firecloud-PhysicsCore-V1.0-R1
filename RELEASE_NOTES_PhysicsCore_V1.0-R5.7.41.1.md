# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.1

## COT Diagnostic Reconciliation

R5.7.41 Field CASE 發現 production `direct_native_cot` 與新 vertical-overlap assumed-r_eff COT 約有 1.81 倍差異。R5.7.41.1 已確認這不是未知數值漂移，而是兩套不同的 COT 語義與垂直積分契約。

新增：
- `firecloud/canvas_cot_reconciliation.py`
- `v1_canvas_cot_reconciliation.csv`
- `v1_canvas_cot_reconciliation_summary.csv`
- `tools/replay_r57411_cot_reconciliation.py`
- Analysis Integrity：`CANVAS_COT_DIAGNOSTIC_RECONCILIATION`
- Analysis Integrity：`CANVAS_COT_DIAGNOSTIC_RECONCILIATION_SUMMARY`

2026-09-11 R5.7.41 Field CASE 離線 replay：108/108 semantic difference explained；max residual 約 `9.63e-17`。

本版不修改 Production target COT、Formation、Viewing、Glow、Photography 或物理門檻。`cot_promotion_allowed=False`、`formation_promotion_allowed=False`。

Working-tree regression：574/574 PASS。
Extracted full regression：574/574 PASS。
FULL-CLEAN release gate：CLOSED。
