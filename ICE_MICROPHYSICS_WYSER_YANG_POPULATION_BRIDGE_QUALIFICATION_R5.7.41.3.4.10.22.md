# Ice Microphysics Step 3I — Wyser ↔ Yang/Bi Population Bridge Qualification

Version: `V1.0-R5.7.41.3.4.10.22`  
Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`  
Mode: `WYSER_POPULATION_YANG_OPTICAL_KERNEL_BRIDGE_DIAGNOSTIC_ONLY_FAIL_CLOSED`

## 結論

Step 3I 通過的是 **diagnostic numeric bridge executability**，不是 Production Ice Optics promotion。

已確認：

- Step 3H 的 `Wyser L_um == Yang/Bi maximum_dimension_um` coordinate qualification 可沿用。
- Yang/Bi V2 `single_column/Rough000` reference kernel 可在 Wyser 10–1000 µm overlap domain 重建單粒子 `C_ext`。
- 共同 domain 有 **109 個 Dmax × 6 波段 = 654 rows**。
- 六波段為 `[550, 575, 600, 650, 700, 750]` nm。
- reconstructed `Q_ext` range = `1.93436908448–2.24638583681`。
- reconstructed `C_ext` range = `1.32725999166e-10–3.63984790837e-07 m²`。
- source-derived `De=1.5V/A` reproduction 最大相對誤差 = `5.83727823577e-07`。

## 雙 mass semantic 必須分離

```text
Wyser Eq.(6) particle mass
    → PSD / IWC population normalization

Yang/Bi rho_ice * V geometric mass
    → only invert k_ext to single-particle C_ext

兩者不可互換。
```

禁止：

- 用 Yang geometric mass 取代 Wyser Eq.(6) 去 normalize PSD。
- 用 Wyser Eq.(6) mass 去反解 Yang/Bi mass-extinction coefficient。
- 用 area/volume/mass ratio 做 hidden correction。
- 把 `single_column/Rough000` 當成 GFS runtime habit/roughness default。

## 為何 direct equivalence 仍不通過

在完整 overlap domain 的診斷比較中：

- max projected-area relative difference = `0.363455590643`
- max volume relative difference = `0.51`
- max Yang geometric mass vs Wyser Eq.(6) relative difference = `3.20480598334`
- max Wyser Eq.(5) geometric solid mass vs Eq.(6) relative difference = `5.54600124857`

所以 shared Dmax coordinate **不能**被解讀成 shape、projected-area、volume 或 mass identity。

## Gate 狀態

### PASS

- `WYSER_L_TO_YANG_DMAX_COORDINATE_VALIDATED=true`
- `YANG_BI_SINGLE_COLUMN_KERNEL_CEXT_RECONSTRUCTION_PASS=true`
- `WYSER_YANG_DUAL_MASS_SEMANTICS_SEPARATED_PASS=true`
- `WYSER_YANG_HYBRID_POPULATION_BRIDGE_NUMERIC_EXECUTABLE=true`

### BLOCKED / false

- direct shape compatibility
- projected-area equivalence
- volume/mass equivalence
- independent Eq.(6) external numeric corroboration
- scientific mass closure
- Yang/Bi habit bridge
- Yang/Bi roughness bridge
- bulk Yang/Bi PSD integration
- GFSv16 Dmax mapping
- Production Ice Optics
- `physics_promotion_allowed`

## Frozen Science

Formation / Viewing / Twilight Glow、六波段、Canvas / Corridor / REZ、Earth Shadow、Production/Shadow COT 與 Missing≠Clear≠Zero 全部維持原 science baseline，不由 Step 3I 改寫。
