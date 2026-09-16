# FIELD Validation Review — R5.7.41.3.4.10.12 / TWS106 / 2026-09-16 sunset

## 結論
**Phase 2 runtime behavior PASS；Release gate NOT PASS。** 因 CASE Integrity 沒有把三個新 Phase 2 artifacts 納入 required evidence，所以 `.10.12` 不升格為正式 FIELD PASS。

## 實跑證據
- `ice_microphysics_native_input_capability_audit.csv`：存在，19 rows，manifest SHA256 match。
- `ice_microphysics_phase2_mapping_eligibility.csv`：存在，1 row，manifest SHA256 match。
- `ice_microphysics_phase2_contract.json`：存在，manifest SHA256 match。
- 全 CASE manifest：145 entries，0 missing，0 SHA mismatch。
- Analysis Integrity：92/92 PASS。
- CASE Integrity：44/44 PASS，但其中 0 筆檢查引用 `ice_microphysics`，證明 required-member gate 漏接。

## Microphysics 實跑狀態
- Ice runtime：2691 rows。
- positive IWP：2353 rows。
- Dmax finite/non-null：0。
- r_eff finite/non-null：0。
- habit resolved：0。
- roughness resolved：0。
- `eligibility_state=INSUFFICIENT_MICROPHYSICS`。
- 五個 blockers 全部存在：Dmax native unavailable、Dmax mapping unavailable、PSD incomplete、habit unresolved、roughness unresolved。
- `tau_synthesis_allowed=false`：2691/2691。
- `formation_promotion_allowed=false`：2691/2691。
- 正 IWP rows 的六波段 `tau_ice` 全部未生成。

## Ice runtime state 補充
此 CASE 沒有配置 Ice LUT，因此正 IWP rows 主要停在 `ICE_OPTICS_LUT_UNAVAILABLE`（2327 rows），另 26 rows 為 native vertical support incomplete。這仍然是 fail-closed；Phase 2 eligibility table 另外明確證明 Dmax/PSD/habit/roughness 都未就緒。

## 效能
- `ICE_MICROPHYSICS_PHASE2_CAPABILITY_AUDIT`：0.079 s。
- `ICE_CLOUD_SPECTRAL_OPTICS_SHARED_PHASE1`：1.753 s。
- GFS native download/decode：6.282 s。
- TOTAL_TO_CASE_ARCHIVE：568.797 s。

## 修正
缺口已於 `.10.12.1` 修正：Analysis Integrity + Archive Integrity 同時硬性 gate 三個 Phase 2 evidence artifacts。
