# Direct Conflict Eligibility Handoff Hotfix Spec — R5.7.41.3.2

## 目的

修正 R5.7.41.3.1 已能在 vertical conflict qualification 辨識 `CONDENSATE_CLOUD_CF_LOW`，但 Vertical Microphysics Overlap 與 Shadow COT Migration eligibility 尚未同步 fail-close 的跨層 handoff gap。

## Field trigger

2026-09-12 sunrise / TWS059 野柳岬 CASE：
- Target Optical Truth：每個角度 3 個 `CONDENSATE_CLOUD_CF_LOW_CONFLICT`，13 個角度共 39 rows。
- Vertical Conflict Qualification：39/39 正確標為 `PRIMARY_NATIVE_CONDENSATE_WITH_LOW_CF_CONFLICT`。
- 舊 Vertical Overlap：`direct_target_evidence_conflict=False`。
- 舊 Shadow Migration：錯誤產生 585/585 `ELIGIBLE_SHADOW_CANDIDATE`。

## 修正契約

1. Vertical Microphysics Overlap 的 direct conflict taxonomy 必須同時包含：
   - `CF_CLOUD_CONDENSATE_ZERO`
   - `CONDENSATE_CLOUD_CF_LOW`
2. direct conflict 時：
   - `direct_target_evidence_conflict=True`
   - `cot_diagnostic_state=BLOCKED_DIRECT_EVIDENCE_CONFLICT`
   - `cot_estimate_assumed_reff=Missing`
3. Shadow Migration 不得只信任 overlap-derived conflict flag，必須獨立交叉檢查：
   - `target_optical_truth_state= DIRECT_EVIDENCE_CONFLICT`
   - 或 direct-conflict resolver state。
4. 任何 direct conflict candidate 必須：
   - `migration_eligibility_state=INELIGIBLE_SHADOW_CANDIDATE`
   - reasons 包含 `DIRECT_EVIDENCE_CONFLICT`
   - vertical integration contract fail-close
   - public Shadow candidate COT 保持 Missing。
5. Analysis Integrity 必須獨立驗證：Target Optical Truth direct-conflict key 與 eligible Shadow candidate key 不得交集。

## 不改動

- Production COT source
- Formation science
- Viewing science
- Twilight Glow
- Photography Decision
- Cloud Fraction 不得生成／縮放 Shadow in-cloud COT
- RH 不得生成 condensate 或 COT
- Production switch / COT promotion / Formation promotion 仍全部禁止
