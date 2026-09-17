# CURRENT PROJECT STATE — Taiwan Firecloud PhysicsCore V1.0

## Current Version

`V1.0-R5.7.41.3.4.10.23`

Status: **QA PASS — FIELD VALIDATION PENDING**

Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`

Latest formal FIELD baseline: `V1.0-R5.7.41.3.4.10.22 FIELD PASS`（TWS091 + TWS100，2026-09-17 sunrise）

## Current Milestone

Ice Optics Phase 2 Step 3J — **Diagnostic Wyser PSD × Yang/Bi Cext Bulk Integration（β_ext / k_ext，Fail-Closed）**

## Current Gate

`DIAGNOSTIC_BETA_KEXT_NUMERIC_READY_SCIENTIFIC_AND_TAU_PROMOTION_BLOCKED`

### Newly passed

- Step 3I hybrid population/kernel numeric bridge inheritance：PASS
- six-band `β_ext(λ)` diagnostic integration：PASS
- six-band `k_ext(λ)=β_ext/IWC_kg_m3` diagnostic calculation：PASS
- Wyser PSD numeric mass closure：PASS
- 1025 / 4097 vs 16385 reference-grid convergence：PASS
- 18-case diagnostic preflight：PASS
- max mass-closure relative error：`3.552713678800501e-16`
- max bulk convergence relative error：`2.8615945138814625e-06`

### Still blocked

- independent exact numeric corroboration for Wyser Eq.(6)
- scientific bulk-optics validation
- Yang/Bi habit bridge
- Yang/Bi roughness bridge
- bulk Yang/Bi PSD integration production eligibility
- `tau_ice` production synthesis
- GFSv16 Dmax runtime mapping
- Production Ice Optics
- `physics_promotion_allowed=false`

## Diagnostic sample

253.16 K / IWC 0.1 g m⁻³：

```text
550 nm  k_ext = 35.3398938809 m²/kg
575 nm  k_ext = 35.3560999814 m²/kg
600 nm  k_ext = 35.4978120075 m²/kg
650 nm  k_ext = 35.7360786905 m²/kg
700 nm  k_ext = 35.5681253440 m²/kg
750 nm  k_ext = 35.4106457313 m²/kg
```

這些值只屬 diagnostic reference `single_column/Rough000` kernel，不得直接寫入 production ice runtime。

## WINDY Handoff Readiness

`twfc.validated-ice-dmax-mapping.v1_1` 仍必須 fail-close。Step 3J 只證明 diagnostic bulk integrator 的數值鏈已可執行；尚未取得 habit、roughness、independent Eq.(6) corroboration 與 independent bulk-optics validation，因此不可輸出 production `tau_ice`。

## Next Step

先用 `.10.23` 跑 TWS091 + TWS100 FIELD CASE，驗證 Step 3J evidence/gate/contract CASE handoff 與 Frozen Science fail-close。FIELD PASS 後再進下一階段：scientific bulk-validation / habit-roughness qualification，仍不得跳過 promotion gates。
