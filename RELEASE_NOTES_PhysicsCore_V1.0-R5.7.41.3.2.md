# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.2

## Direct Conflict Eligibility Handoff Hotfix

- 修正 Target Optical Truth → Vertical Microphysics Overlap → Shadow COT Migration 的 direct-conflict handoff。
- `CONDENSATE_CLOUD_CF_LOW` 現在在 overlap 層與 migration eligibility 均 fail-close。
- Shadow migration 新增 independent Target Optical Truth / resolver cross-check；不再只依賴 overlap 的 `direct_target_evidence_conflict`。
- direct conflict 時 public Shadow candidate COT 強制 Missing，不能保留數值看似可用的 assumed-r_eff COT。
- Analysis Integrity 新增 independent handoff guard，禁止 Target Optical Truth direct conflict 與 eligible Shadow candidate 重疊。
- 不修改 Production COT、Formation、Viewing、Twilight Glow、Photography science。

## Field trigger

2026-09-12 sunrise / TWS059 野柳岬 R5.7.41.3.1 CASE：Vertical Conflict Qualification 已正確辨識 39 個 `CONDENSATE_CLOUD_CF_LOW` rows，但 Shadow Migration 因 overlap conflict flag 尚未同步，錯誤顯示 585/585 eligible。R5.7.41.3.2 離線 replay 修正為 546 eligible / 39 ineligible，39 個 conflict candidate COT 全部 Missing。

## Regression
Working-tree：594/594 PASS；FULL-CLEAN fresh-extract：594/594 PASS；1 個既有 pandas FutureWarning，非失敗；Release Gate CLOSED。
