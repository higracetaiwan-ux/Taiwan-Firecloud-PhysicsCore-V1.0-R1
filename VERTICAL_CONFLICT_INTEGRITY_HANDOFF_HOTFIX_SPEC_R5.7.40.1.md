# R5.7.40.1 Vertical Conflict Integrity Handoff Hotfix 規格

## 問題
R5.7.40 已生成 `v1_canvas_vertical_conflict_qualification`，但 `model.py` 的 `_pre_integrity_result` 漏傳 `v1_target_canvas_optical_evidence`。因此 `build_analysis_integrity_audit()` 無法建立 expected conflict canvas set，錯誤輸出 `ALLOWED_EMPTY`。

## 修正
將已生成的 `v1_target_canvas_optical_evidence` 明確傳入 pre-export Integrity audit。

## 不得改變
- 不改 target COT readiness。
- 不改 Formation / Viewing / Twilight Glow / Photography。
- 不允許 RH 或 cloud fraction 生成 condensate/COT。
- 不改 R5.7.40 vertical-conflict classification。

## 驗證契約
1. Production handoff 必須恰好包含一次 `v1_target_canvas_optical_evidence`。
2. 有 `DIRECT_EVIDENCE_CONFLICT` target 且 qualification 已存在時不得輸出 `ALLOWED_EMPTY`。
3. R5.7.40 真實 CASE replay：432 qualification rows；45 expected / 45 observed unique canvases；Integrity = PASS。
4. Full regression 必須全綠。
