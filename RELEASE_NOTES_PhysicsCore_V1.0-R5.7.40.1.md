# Taiwan Firecloud PhysicsCore V1.0-R5.7.40.1 發行說明

## 修正
- 修正 R5.7.40 Vertical Conflict Qualification 的 pre-export Analysis Integrity handoff。
- `_pre_integrity_result` 現在包含 `v1_target_canvas_optical_evidence`。
- 防止真實 conflict canvas 被誤判為 `ALLOWED_EMPTY / 0 conflict canvases`。

## 真實 CASE replay
R5.7.40 / 2026-09-10 sunset CASE：432 qualification rows，45 expected / 45 observed unique conflict canvases；新 guard = PASS。

## 科學邊界
本 hotfix 不改 COT、Formation、Viewing、Glow、Photography，也不改任何物理門檻。

## Regression
- Focused handoff regression：15/15 PASS。
- Full working-tree regression：564/564 PASS。
- FULL-CLEAN extracted regression：564/564 PASS。
