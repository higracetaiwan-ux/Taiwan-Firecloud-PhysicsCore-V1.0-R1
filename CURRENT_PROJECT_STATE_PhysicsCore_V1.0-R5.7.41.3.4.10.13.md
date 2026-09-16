# Taiwan Firecloud PhysicsCore — Current Project State

版本：`V1.0-R5.7.41.3.4.10.13`  
狀態：**IMPLEMENTATION / REGRESSION PASS — FIELD VALIDATION PENDING**

## Science baseline

唯一凍結基線仍為：`R5.7.41.2_SHADOW_COT_AB_FROZEN`

Formation / Viewing / Twilight Glow、六波段、Canvas/Corridor/REZ、Earth Shadow、Production/Shadow COT、CLWMR/ICMR threshold、Missing≠Clear≠Zero、WINDY portable decoupling均未更動。

## Phase 2 目前進度

- `.10.12`：Native Microphysics Capability Audit + Dmax/PSD Mapping Eligibility Contract
- `.10.12.1`：Phase 2 Evidence Integrity Gate Hotfix — **FIELD PASS**
- `.10.13`：Authoritative Size/PSD Source Capability Registry + Eligibility Gate — implementation/regression complete

## `.10.13` 結論

目前調查的台灣可用全球來源沒有 direct Dmax 或 production-ready PSD：

- GFS：mass-only
- ICON Global：mass-only
- ECMWF Open Data：公開 subset 無 direct ice-size/number/PSD
- GEOS-FP：forecast state mass-only
- ECMWF effective-size：reference-only，effective size ≠ Yang/Bi Dmax
- RAP：mass + ice number concentration，但 North America reference-only，且仍需 scheme-specific PSD contract

因此：

- `DMAX_SOURCE_SELECTION_ELIGIBLE=false`
- `PSD_SOURCE_SELECTION_ELIGIBLE=false`
- `PRODUCTION_ICE_OPTICS_READY=false`
- `physics_promotion_allowed=false`

## 測試

- targeted: 35/35 PASS
- full: 782/782 PASS
- fresh-extract full: 782/782 PASS
- 0 failures
- 1 existing pandas FutureWarning

## 下一個 FIELD gate

使用 `.10.13 FULL-CLEAN` 跑一個正式 CASE，需確認：

1. CASE ZIP 有三個 source-registry evidence artifacts。
2. Analysis Integrity 新增三個 source-registry checks 全 PASS。
3. CASE Integrity 新增三個 `ARCHIVE_MEMBER::ice_microphysics_source_*` checks 全 PASS。
4. source gate仍為 `NO_AUTHORITATIVE_TAIWAN_SIZE_OR_PSD_SOURCE`。
5. positive-IWP rows仍不得因 source registry 自動取得 Dmax/PSD/τ/promotion。

FIELD PASS 前不開始 production mapping。
