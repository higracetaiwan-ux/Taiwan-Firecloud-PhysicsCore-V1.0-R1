# Ice Microphysics Step 3K — Fu96 Independent Bulk Validation Qualification

版本：`R5.7.41.3.4.10.24`  
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`  
狀態：**QA PASS / FIELD VALIDATION PENDING**

## 目的

Step 3J 已用 Wyser Eq.(6) 正規化 PSD × Yang/Bi V2 `C_ext(Dmax,λ)` 算出六波段 diagnostic `β_ext` / `k_ext`。Step 3K 建立一條不使用 Yang/Bi `C_ext` 的獨立 optical-kernel cross-check：保留相同 Wyser number population，改用 Wyser Eq.(5) hex-column projected area 與 Fu (1996) geometric-optics `β_ext≈2A_c`。

## Provenance

- Fu (1996), *An Accurate Parameterization of the Solar Radiative Properties of Cirrus Clouds for Climate Models*, DOI `10.1175/1520-0442(1996)009<2058:AAPOTS>2.0.CO;2`.
- NOAA/NCEP technical note reproduces Fu Eq.(3.3): extinction coefficient based on IWC / generalized effective size and geometric-optics `β=2A_c`.
- Robinson (2007) reproduces Fu random-orientation solid-hex projected-area and volume definitions.

## Reference chain

```text
Wyser Eq.(6) mass normalization -> n(L)
Wyser Eq.(5) width D(L)
Pbar(L)=3/4 * [D L + sqrt(3)/4 D^2]
A_c = integral[Pbar(L) n(L) dL]
Fu geometric optics: beta_ext ~= 2 A_c
k_ext = beta_ext / IWC
```

此 reference chain **不使用 Yang/Bi C_ext**。Yang/Bi Step 3J 只作被比較對象。

## 18-case 結果

- cases：`18`
- Fu projected-area chain numeric pass：`True`
- projected-area numeric pass：`True`
- max Fu unit-chain relative error：`1.22441956002415e-05`
- Step 3J vs Fu relative difference range：`0.2621271071414941` ～ `0.3121662072653651`

### 253.16 K / IWC=0.1 g m^-3 範例

- Fu reference `k_ext`：`48.83268509507885 m²/kg`
- mass-area-equivalent `Dge`：`51.5726471165019 µm`
- solid-hex geometry `Dge`：`113.0846813692464 µm`
- 兩種 Dge **不得互換**。前者沿 Wyser Eq.(6) population mass + projected-area relation；後者是純 solid-hex volume/projected-area geometry。

## 科學判定

這次 cross-check 顯示 Step 3J 的 Yang/Bi-weighted diagnostic `k_ext` 與 Fu projected-area chain 同量級，但存在約 **26.2%–31.2%** 的 material difference。這足以證明 Step 3J 不只是自我數值閉合，也同時說明 Wyser↔Yang/Bi shape / projected-area / habit semantics 仍不能視為等價。

因此：

```text
FU96_INDEPENDENT_OPTICAL_CROSSCHECK_EXECUTED = true
FU96_PROJECTED_AREA_CHAIN_NUMERIC_PASS = true
FU96_DGE_DUAL_SEMANTICS_SEPARATED_PASS = true
FU96_BULK_DIFFERENCE_CHARACTERIZED = true

SCIENTIFIC_BULK_VALIDATION_PASS = false
BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE = false
TAU_ICE_PRODUCTION_ALLOWED = false
PRODUCTION_ICE_OPTICS_READY = false
physics_promotion_allowed = false
```

## 不可做的 shortcut

- 不得把 Fu mass-area-equivalent `Dge` 當作 solid-hex geometry `Dge`。
- 不得把 26–31% 同量級一致性描述成 shape equivalence 或 production validation。
- 不得把 Step 3J/3K diagnostic `k_ext` 寫入 runtime Ice Optics。
- 不得計算 production `τ_ice = IWP × k_ext`。
- 不得由 Step 3K 自動選 habit / roughness。
