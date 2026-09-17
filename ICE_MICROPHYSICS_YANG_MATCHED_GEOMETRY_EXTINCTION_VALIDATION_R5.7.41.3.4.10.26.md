# Ice Microphysics — Yang/Bi Matched-Geometry Extinction Validation — R5.7.41.3.4.10.26

## 定位
本文件記錄 Ice Optics Phase 2 **Step 3M**。本步驟只建立與 Yang/Bi `single_column` 相同幾何的獨立 extinction reference；不是 full optical validation，也不是 production promotion。

## 比對方法
- 測試鏈：Yang/Bi V2 `single_column` source geometry 與 `C_ext`。
- 獨立 reference：Fu96 geometric-optics extinction law `Cext_reference ≈ 2 × projected area`。
- matched geometry：reference 與測試鏈使用相同 Dmax 與 Yang/Bi mean projected area；reference **不使用 Yang/Bi Cext/Qext**。
- population：沿用 Wyser population/PSD，避免改變既有 Step 3J population definition。
- 波段：550 / 575 / 600 / 650 / 700 / 750 nm。
- roughness diagnostic ensemble：Rough000 / Rough003 / Rough050。

## 數值結果
- single-particle comparisons：1,962 rows（109 Dmax × 6 bands × 3 roughness）。
- Dmax domain：10–1000 µm。
- minimum size parameter：58.643062867，通過 Step 3M 採用的 geometric-optics domain floor (>15)。
- single-particle max relative difference vs 2A：0.1231929184。
- single-particle mean relative difference：0.0079473979167。
- matched-geometry bulk matrix：18 cases / 324 comparison rows。
- matched-geometry bulk max relative difference：0.028779758046（約 2.878%）。
- matched-geometry bulk mean relative difference：0.005933343552（約 0.593%）。
- max grid-convergence relative error：2.8615945e-06。

Step 3K 的 cross-geometry comparison 曾落在約 26–31%；Step 3M 在相同 Yang/Bi 幾何下明顯收斂，支持「幾何差異是 Step 3K discrepancy 的主要來源之一」。這是 diagnostic characterization，**不把 3% 設成 universal production tolerance**。

## Gate
- matched-geometry extinction reference：READY。
- geometric-optics domain：PASS。
- matched-geometry bulk difference：CHARACTERIZED。
- independent SSA validation：BLOCKED / NOT EXECUTED。
- independent asymmetry validation：BLOCKED / NOT EXECUTED。
- full like-for-like optical validation：BLOCKED。
- scientific bulk validation：BLOCKED。
- runtime habit / roughness truth：UNAVAILABLE。
- `tau_ice` production：BLOCKED。
- Production Ice Optics：BLOCKED。
- physics promotion：BLOCKED。

## Frozen Science
Science baseline 維持 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。Formation / Viewing / Twilight Glow、六波段、Canvas / Corridor / REZ、Earth Shadow、Production / Shadow COT 與 Missing≠Clear≠Zero 均不變。
