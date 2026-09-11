# Direct Conflict Qualification Coverage Hotfix Spec — R5.7.41.3.1

Target Optical Truth 的 `DIRECT_EVIDENCE_CONFLICT` 包含至少：
- `CF_CLOUD_CONDENSATE_ZERO`
- `CONDENSATE_CLOUD_CF_LOW`

Vertical conflict qualification 必須覆蓋所有 direct-conflict canvases，但不得抹平 conflict subtype。

`CONDENSATE_CLOUD_CF_LOW` 對應：`PRIMARY_NATIVE_CONDENSATE_WITH_LOW_CF_CONFLICT`。

所有 qualification 仍 diagnostic-only：
- `cot_promotion_allowed=False`
- `formation_promotion_allowed=False`
- `supplement_cloud_fraction_used=False`
- `rh_used_to_infer_condensate=False`
