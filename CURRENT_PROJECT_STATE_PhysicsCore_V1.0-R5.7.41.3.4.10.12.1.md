# Taiwan Firecloud PhysicsCore — Current Project State

## 現行版本
**V1.0-R5.7.41.3.4.10.12.1 — Ice Optics Phase 2 Evidence Integrity Gate Hotfix**

## 現行狀態
**IMPLEMENTATION / REGRESSION PASS — FIELD VALIDATION PENDING**

## 唯一科學基線
`R5.7.41.2_SHADOW_COT_AB_FROZEN`

Frozen Formation / Viewing / Twilight Glow、六波段、Canvas、Dynamic Corridor/REZ、Earth Shadow、Production/Shadow COT、CLWMR/ICMR threshold、Missing≠Clear≠Zero、WINDY portable decoupling 全部不變。

## `.10.12` TWS106 FIELD CASE 實證
- 站點：TWS106 高美濕地
- 事件：2026-09-16 sunset
- GFS：2026-09-16 00Z / f010 / valid 10Z
- Phase 2 capability audit：19 rows
- mapping eligibility：1 row，`INSUFFICIENT_MICROPHYSICS`
- positive IWP rows：2353
- runtime Dmax non-null：0
- runtime r_eff non-null：0
- resolved habit：0
- resolved roughness：0
- `MICROPHYSICS_MAPPING_READY=false`
- `SINGLE_PARTICLE_LUT_LOOKUP_ELIGIBLE=false`
- `BULK_PSD_SYNTHESIS_ELIGIBLE=false`
- `PRODUCTION_ICE_OPTICS_READY=false`
- `physics_promotion_allowed=false`
- 正 IWP 列六波段 tau 未被合成。

### 發現的 release-gate 缺口
三個 Phase 2 artifacts 均已寫入 CASE 且 manifest SHA256 正確，但 `.10.12` 的 `case_integrity_audit.csv` 沒有把它們列成 required evidence，因此 `.10.12` 不升格 FIELD PASS。

## `.10.12.1` 修正
1. Analysis Integrity 強制檢查 Phase 2 evidence presence。
2. 強制驗證 Frozen Science / Dmax-first / forbidden implicit mappings contract。
3. 強制驗證 mapping fail-closed 狀態。
4. CASE Archive Integrity 強制要求三個 Phase 2 artifacts。

## Regression
- Targeted：29/29 PASS
- Full：776/776 PASS
- 0 failed
- 1 existing pandas FutureWarning

## 下一步
使用本 `.10.12.1 FULL-CLEAN` 再跑一個 FIELD CASE。Acceptance：
- Analysis Integrity 應新增 3 個 Phase 2 PASS（預期總數約 95 PASS，視其他可選檢查而定）。
- CASE Integrity 應明確出現三個 `ARCHIVE_MEMBER::ice_microphysics_*` PASS（預期總數約 47 PASS）。
- 三個 Phase 2 artifacts 必須在 manifest 中且 SHA256 一致。
- 正 IWP、無合法 Dmax/PSD 時仍不得生成 tau、不得 promotion。
