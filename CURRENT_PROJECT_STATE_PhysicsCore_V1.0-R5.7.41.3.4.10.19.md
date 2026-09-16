# CURRENT PROJECT STATE — Taiwan Firecloud PhysicsCore V1.0

## Current Version
`V1.0-R5.7.41.3.4.10.19`

Status: **IMPLEMENTATION / REGRESSION PASS — FIELD VALIDATION PENDING**

Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`

Latest formal FIELD baseline: **`V1.0-R5.7.41.3.4.10.18 FIELD PASS`**

## Current Milestone
Ice Optics Phase 2 Step 3F — **Exact Wyser Eq.(5)/(6) Geometry + Mass-Size / PSD Mass-Closure Qualification**

## Current gate
`WYSER_GEOMETRY_LINEAGE_CORROBORATED_PRIMARY_MASS_SIZE_CLOSURE_BLOCKED`

### 已提升證據強度
- Primary prose：Eq.(5) 為 continuous solid-column `L↔D` relation。
- Primary prose：Eq.(6) 為 `m=rho*V`，rho/V 均為 L 的函數；m[g]、L[µm]；cold solid columns、L/D>2。
- Secondary lineage：`D=2.5L^0.6` 被後續文獻明確歸因 Wyser/Wyser–Yang。

### 仍未完成
- primary-quality machine-verifiable Eq.(5) numeric formula；
- primary-quality Eq.(6) exact coefficients / exponents / units；
- executable `m(L)`；
- absolute PSD reconstruction；
- `∫m(L)n(L)dL = IWC` mass-closure grid；
- Wyser L → Yang/Bi Dmax coordinate validation；
- habit / roughness bridge；
- independent bulk-optics validation。

### Production state
- `ABSOLUTE_PSD_RECONSTRUCTION_EXECUTABLE=false`
- `PSD_MASS_CLOSURE_VALIDATION_PASS=false`
- `BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE=false`
- `GFSV16_DMAX_MAPPING_ELIGIBLE=false`
- `PRODUCTION_ICE_OPTICS_READY=false`
- `physics_promotion_allowed=false`

## WINDY handoff
WINDY consumer interface / portable contract 可繼續開發；正式 Ice Optics bundle 仍不可開啟。

下一個真正需要取得的是 primary-quality Eq.(5)/(6) numeric representation；在此之前不應用二手式子進 production physics。
