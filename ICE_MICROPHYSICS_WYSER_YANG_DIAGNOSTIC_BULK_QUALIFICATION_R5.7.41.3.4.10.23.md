# Ice Microphysics Step 3J — Diagnostic PSD × Yang/Bi Cext Bulk Integration Qualification

版本：`R5.7.41.3.4.10.23`  
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## 目的

在 Step 3I 已確認的 shared `maximum_dimension_um` diagnostic bridge 上，首次執行六波段 bulk extinction 數值積分，但嚴格停留在 diagnostic preflight：

```text
n(D) = A · phi(D)
A = IWC / ∫ m_Wyser(D) phi(D) dD
β_ext(λ) = ∫ n(D) C_ext,Yang(D,λ) dD
k_ext(λ) = β_ext(λ) / IWC_kg_m3
```

其中：

- PSD / number population normalization 使用 Wyser Eq.(6) mass semantic。
- optical kernel 使用 Yang/Bi V2 `single_column/Rough000` diagnostic reference `C_ext(Dmax,λ)`。
- 兩種 mass semantics 不可互換。
- `single_column/Rough000` 不是 runtime habit/roughness default。

## Numerical method

- Dmax domain：10–1000 µm。
- wavelengths：550 / 575 / 600 / 650 / 700 / 750 nm。
- interpolation：log(D)–log(Cext) piecewise linear，並強制 source knots 進 integration grid；禁止 extrapolation。
- diagnostic grids：1025、4097 points。
- reference grid：16385 points。
- temperature matrix：233.16 / 253.16 / 273.16 K。
- IWC matrix：0.001 / 0.1 / 10.0 g m⁻³。
- total cases：18。

## 結果

18/18 cases：

- bulk `β_ext/k_ext` finite positive：PASS。
- PSD numeric mass closure：PASS。
- grid convergence：PASS。
- max mass-closure relative error：`3.552713678800501e-16`。
- max bulk-grid convergence relative error：`2.8615945138814625e-06`，低於 `5e-4` tolerance。

253.16 K / IWC 0.1 g m⁻³ / 4097-grid sample：

| λ (nm) | β_ext (m⁻¹) | k_ext (m²/kg) |
|---:|---:|---:|
| 550 | 0.00353398938809 | 35.3398938809 |
| 575 | 0.00353560999814 | 35.3560999814 |
| 600 | 0.00354978120075 | 35.4978120075 |
| 650 | 0.00357360786905 | 35.7360786905 |
| 700 | 0.00355681253440 | 35.5681253440 |
| 750 | 0.00354106457313 | 35.4106457313 |

## Qualification

```text
DIAGNOSTIC_SIX_BAND_BULK_EXTINCTION_PASS = true
DIAGNOSTIC_BULK_GRID_CONVERGENCE_PASS = true
DIAGNOSTIC_PSD_MASS_CLOSURE_PASS = true

SCIENTIFIC_BULK_VALIDATION_PASS = false
YANG_BI_HABIT_BRIDGE_VALIDATED = false
YANG_BI_ROUGHNESS_BRIDGE_VALIDATED = false
BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE = false
TAU_ICE_PRODUCTION_ALLOWED = false
PRODUCTION_ICE_OPTICS_READY = false
physics_promotion_allowed = false
```

Qualification state：

`DIAGNOSTIC_BETA_KEXT_NUMERIC_READY_SCIENTIFIC_AND_TAU_PROMOTION_BLOCKED`

## 仍然禁止

- 不得將 `single_column/Rough000` 當 runtime habit/roughness default。
- 不得把 Step 3J diagnostic `k_ext` 寫入 production ice runtime。
- 不得由本版 `k_ext` 直接合成 `tau_ice = IWP × k_ext`。
- 不得把 numerical convergence 當 independent scientific validation。
- 不得用 Yang geometric mass 取代 Wyser Eq.(6) 做 PSD normalization。

## Frozen Science

Formation / Viewing / Twilight Glow、六波段 baseline、Canvas/Corridor/REZ、Earth Shadow、Production/Shadow COT、Missing ≠ Clear ≠ Zero 與 WINDY portable decoupling 全部不變。
