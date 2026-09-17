# CURRENT PROJECT STATE — Taiwan Firecloud PhysicsCore V1.0

## Current Version

`V1.0-R5.7.41.3.4.10.22`

Status: **QA PASS — FIELD VALIDATION PENDING**

Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`

Latest formal FIELD baseline: `V1.0-R5.7.41.3.4.10.21 FIELD PASS`（TWS091 + TWS100，2026-09-17 sunrise）

## Current Milestone

Ice Optics Phase 2 Step 3I — **Wyser Population + Yang/Bi Optical-Kernel Bridge（Diagnostic / Fail-Closed）**

## Current Gate

`WYSER_YANG_HYBRID_POPULATION_BRIDGE_NUMERIC_READY_SCIENTIFIC_PROMOTION_BLOCKED`

### Newly passed

- Step 3H `L → maximum_dimension_um` coordinate qualification：PASS
- Yang/Bi V2 `single_column/Rough000` six-band reference kernel reconstruction：PASS
- 10–1000 µm domain：109 Dmax × 6 bands = 654 rows
- Yang source `De=1.5V/A` reproduction：PASS，max relative error `5.83727823577e-07`
- Wyser population mass vs Yang optical-kernel mass semantic separation：PASS
- Hybrid population bridge numeric executability：PASS

### Still blocked

- direct solid-column shape equivalence
- projected-area equivalence
- volume/mass equivalence
- independent exact numeric corroboration for Wyser Eq.(6)
- scientific mass closure promotion
- Yang/Bi habit bridge
- Yang/Bi roughness bridge
- six-band bulk PSD integration
- GFSv16 Dmax mapping
- Production Ice Optics
- `physics_promotion_allowed=false`

## Important semantic contract

```text
Wyser Eq.(6) mass = population / PSD normalization mass
Yang/Bi rho*V mass = optical-kernel inversion mass

They are not interchangeable.
```

The diagnostic `single_column/Rough000` kernel is not a runtime habit/roughness choice.

## Numerical diagnostics

- `Q_ext` range: `1.93436908448–2.24638583681`
- `C_ext` range: `1.32725999166e-10–3.63984790837e-07 m²`
- max projected-area relative difference: `0.363455590643`
- max volume relative difference: `0.51`
- max Yang mass vs Wyser Eq.(6) relative difference: `3.20480598334`

## WINDY Handoff Readiness

`twfc.validated-ice-dmax-mapping.v1_1` 仍必須 fail-close。Step 3I 只證明 diagnostic hybrid bridge 的數值 ingredients 已可執行，尚未取得 habit、roughness、scientific mass closure 或 independent bulk-optics validation。

## Next Step

FIELD 驗證 `.10.22` 的 Step 3I evidence/gate/contract handoff。FIELD PASS 後，下一階段應做 **Step 3J diagnostic PSD × Yang C_ext bulk integration**，但仍只能是 diagnostic：在 Eq.(6) independent corroboration、habit/roughness 與 independent bulk validation 通過前，不得產生 production `tau_ice` 或 Formation promotion。
