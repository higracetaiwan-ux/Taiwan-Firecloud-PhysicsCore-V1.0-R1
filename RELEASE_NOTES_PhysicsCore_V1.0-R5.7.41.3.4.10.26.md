# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.26

## 版本定位
`R5.7.41.3.4.10.26` 是 Ice Optics Phase 2 **Step 3M — Yang/Bi Matched-Geometry Extinction Validation**。

本版回答 Step 3K 留下的 `LIKE_FOR_LIKE_OPTICAL_VALIDATION_PENDING` 中「extinction geometry 是否可被公平比較」這一部分；只推進 extinction reference，不宣稱 full optical validation。

## 為何需要 Step 3M
Step 3K 的 Fu96 cross-check 使用 Wyser Eq.(5) geometry，而 Step 3J 的 Yang/Bi kernel 使用 Yang/Bi `single_column` source geometry。26–31% bulk discrepancy 因此同時包含 optical-law 與 particle-geometry 差異。

Step 3M 固定相同 Yang/Bi Dmax / projected-area geometry，獨立 reference 使用 `Cext≈2A`，且不取用 Yang/Bi Cext/Qext。

## 數值資格結果
- 1,962 single-particle rows。
- 10–1000 µm × 6 bands × 3 roughness。
- minimum size parameter = 58.643062867 (>15)。
- max single-particle relative difference vs 2A = 12.3193%。
- matched-geometry bulk = 18 cases / 324 rows。
- max bulk relative difference = 2.87798%。
- mean bulk relative difference = 0.59333%。
- max grid convergence relative error = 2.8616e-06。

這是 characterization，不建立新的 `<3%` universal production tolerance。

## Fail-close 不變
- independent SSA validation：false。
- independent asymmetry validation：false。
- full like-for-like optical validation：false。
- scientific bulk validation：false。
- runtime habit/roughness truth：unavailable。
- `tau_ice_production_allowed=false`。
- `production_ice_optics_ready=false`。
- `physics_promotion_allowed=false`。

## QA / FIELD
- Working-tree regression：**903/903 PASS**。
- FIELD validation：**PENDING**。
- Latest formal FIELD baseline：`.10.25.1 FIELD PASS`。
