# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.12.1

## 名稱
Ice Optics Phase 2 — Evidence Integrity Gate Hotfix

## 變更原因
`.10.12` 的 TWS106 2026-09-16 sunset FIELD CASE 已證明三個 Phase 2 證據檔會被實際封存，且各自 SHA256 與 `case_archive_manifest.csv` 一致；但 `case_integrity_audit.csv` 尚未把這三個新檔列為 required evidence member。這代表未來若 Phase 2 證據檔意外缺失，舊 CASE Integrity 仍可能顯示 PASS。

## 本版修正
- `ice_microphysics_native_input_capability_audit.csv` 加入 CASE Archive required evidence gate。
- `ice_microphysics_phase2_mapping_eligibility.csv` 加入 CASE Archive required evidence gate。
- `ice_microphysics_phase2_contract.json` 加入 CASE Archive required evidence gate。
- Analysis Integrity 新增：
  - `ICE_MICROPHYSICS_PHASE2_EVIDENCE_PRESENT`
  - `ICE_MICROPHYSICS_PHASE2_CONTRACT_FREEZE`
  - `ICE_MICROPHYSICS_PHASE2_MAPPING_FAIL_CLOSED`
- `model.py` 明確設定 `ice_microphysics_phase2_required=True`。
- 新增 regression test `test_r57413410121_phase2_evidence_integrity_gate.py`。

## 科學基線
- Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`，**完全不變**。
- Formation / Viewing / Twilight Glow：不變。
- 550/575/600/650/700/750 nm 六波段：不變。
- Canvas / Corridor / REZ / Earth Shadow / Production-Shadow COT：不變。
- 不新增 `r_eff→Dmax`、IWP→Dmax、T/RH/TCDC→Dmax、habit default、roughness default 或 assumed PSD。
- `physics_promotion_allowed=false` 保持不變。

## 測試
- Targeted Phase 2 / Ice Optics regression：29/29 PASS。
- Full regression：776/776 PASS，0 failed。
- 1 個既有 pandas FutureWarning，非本版失敗。

## FIELD 狀態
- `.10.12` TWS106 CASE：Phase 2 runtime/audit 行為正確，但發現 CASE Integrity required-member 漏接，因此 **不升格 `.10.12 FIELD PASS`**。
- `.10.12.1`：Implementation / Regression PASS；需新 FIELD CASE 驗證新的 3 項 Analysis Integrity 與 3 個 Archive required-member gate。
