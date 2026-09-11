# Taiwan Firecloud PhysicsCore — Current Project State
## V1.0-R5.7.40.1

目前主線仍為 Canvas Optical Truth。

R5.7.40 真實 CASE 已將 432/432 qualification rows 分類為 `ISOLATED_PRIMARY_CF_SPIKE_HYDROMETEOR_UNSUPPORTED`，45 個 unique conflict canvases 全部有 vertical context，且 COT/Formation promotion 仍禁止。

R5.7.40 同時暴露 Integrity handoff 漏接：`_pre_integrity_result` 未傳 `v1_target_canvas_optical_evidence`，使 audit 錯誤輸出 `ALLOWED_EMPTY`。R5.7.40.1 已補齊 handoff；舊 CASE 離線 replay 現為 PASS，432 rows、45 expected / 45 observed。

科學輸出不變。R5.7.40.1 FULL-CLEAN release gate 已完成；下一步跑新 CASE field validation。首頁版本歷程文字整理另開獨立 UI metadata cleanup，不與本 hotfix 混版。

## Release Gate
- Working regression：564/564 PASS
- FULL-CLEAN：CLOSED
- Extracted regression：564/564 PASS
- Field validation：OPEN
