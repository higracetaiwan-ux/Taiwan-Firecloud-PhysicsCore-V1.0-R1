# Ice Optics Phase 2 Step 3E — Wyser PSD Normalization + Geometry / L→Dmax Qualification

## 版本
`V1.0-R5.7.41.3.4.10.18`

## 核心結論
Step 3E 將「normalization rule 已知」和「absolute PSD 可以數值執行」嚴格分開。

Wyser (1998) primary text 明確定義所有粒徑分布為 `n(L)=A_x n_x(L)`，並由 IWC mass integral 反解自由振幅。因此本版正式 pin：

`A = IWC / ∫ m(L) phi(L) dL`

這代表 IWC→PSD amplitude 的**規則**有 primary-source provenance；但因 Wyser Eq.(6) 的 exact numeric mass-size/density contract 與 Eq.(5) exact column geometry 尚未以可獨立重現的 primary-quality 形式 pin，PhysicsCore 仍不得直接數值重建 absolute `n(L)`。

## 已 pin
- Wyser PSD amplitude normalization rule。
- Mixed PSD shape：`L<=20 µm` Gamma、`L>20 µm` power law。
- `nu=3`、`lambda=0.3 µm^-1`。
- 20 µm continuity factor：`alpha=20^(nu-B) exp(-lambda*20)`（由 continuity 解析推導）。
- GFS v16 public-source B(T,IWC) equivalent。
- nominal integration domain `L=10–1000 µm`。

## 尚未 pin / 明確封鎖
- exact numeric Wyser Eq.(6) mass-size/density coefficients/units。
- exact primary-quality Wyser Eq.(5) width/length law。
- absolute PSD numerical reconstruction。
- Wyser L → Yang/Bi `maximum_dimension_um` coordinate bridge。
- PSD mass-closure validation。
- Yang/Bi exact habit bridge與 roughness policy。
- independent bulk-optics validation與 production promotion。

## 二手幾何關係的處置
後續文獻可見 `D=0.7L`（小尺寸）與 `D=6.96√L`（較大尺寸）等 column width law，但本版只列為 lineage/reference candidate。除非證明它就是 Wyser Eq.(5) 的 exact lineage，不得代替 primary Wyser geometry。

## Gate
`WYSER_NORMALIZATION_RULE_PINNED_EXECUTION_GEOMETRY_BLOCKED`

- `WYSER_IWC_AMPLITUDE_NORMALIZATION_RULE_PINNED=true`
- `ABSOLUTE_PSD_RECONSTRUCTION_EXECUTABLE=false`
- `WYSER_EXACT_COLUMN_WIDTH_LAW_PINNED=false`
- `WYSER_L_TO_YANG_DMAX_COORDINATE_VALIDATED=false`
- `PSD_MASS_CLOSURE_VALIDATION_PASS=false`
- `BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE=false`
- `PRODUCTION_ICE_OPTICS_READY=false`
- `physics_promotion_allowed=false`
