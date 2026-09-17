# Taiwan Firecloud PhysicsCore — CURRENT PROJECT STATE

## 現行版本
- Development release：`1.0.0-R5.7.41.3.4.10.26`
- 狀態：**QA PASS / FIELD VALIDATION PENDING**
- Latest formal FIELD baseline：`V1.0-R5.7.41.3.4.10.25.1 FIELD PASS`
- Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## 本版內容
`.10.26` 是 Ice Optics Phase 2 **Step 3M — Yang/Bi Matched-Geometry Extinction Validation**。

Step 3K 的 Fu96 independent bulk cross-check 同時混合了「獨立 extinction law」與「Wyser Eq.(5) vs Yang/Bi single-column 幾何差異」，因此 26–31% discrepancy 不能直接解讀成 Yang/Bi extinction 本身的誤差。Step 3M 將 reference 改為與 Yang/Bi `single_column` 使用完全相同的 Dmax / projected-area geometry，只保留 optical-law independence：`Cext_reference≈2A_yang`，且 reference chain 不使用 Yang/Bi Cext/Qext。

## Step 3M 結果
- source-row comparison：1,962 rows（109 Dmax × 6 bands × 3 roughness）。
- minimum size parameter：58.643062867；geometric-optics domain floor (>15) PASS。
- single-particle max relative difference vs 2A：12.3193%。
- matched-geometry bulk matrix：18 cases / 324 rows。
- matched-geometry bulk max relative difference：**2.87798%**。
- matched-geometry bulk mean relative difference：**0.59333%**。
- max grid convergence relative error：2.8616e-06。

這支持「幾何 mismatch 是 Step 3K 26–31% discrepancy 的主要來源之一」，但本版沒有把 `<3%` 設成新的科學門檻或 production tolerance。

## Step 3M gate
已解鎖：
- `matched_geometry_extinction_reference_ready=true`
- `geometric_optics_domain_pass=true`
- `matched_geometry_bulk_difference_characterized=true`

仍 fail-close：
- independent SSA validation=false
- independent asymmetry validation=false
- full like-for-like optical validation=false
- scientific bulk validation=false
- runtime GFS habit/roughness truth unavailable
- `tau_ice_production_allowed=false`
- `production_ice_optics_ready=false`
- `physics_promotion_allowed=false`

## QA
- Working-tree regression：**903/903 PASS**，1 個既有 pandas FutureWarning。
- Candidate FULL-CLEAN：1164 members／0 cache-pyc artifacts／fresh-extract **903/903 PASS**（210 / 257 / 198 / 238）。
- Candidate Step 3M evidence / gate / contract：**byte-exact regeneration PASS**。
- Final immutable ZIP：本報告更新後重建，再執行最後 read-only verification。

## FIELD 下一步
使用 `.10.26` 重跑 TWS091 sunrise 或等價 positive-IWP CASE，至少確認：
1. Step 3M evidence 12 rows、gate 1 row、contract 完整封存；
2. CASE 與 release Step 3M 三件 artifacts deterministic byte-exact；
3. positive-IWP runtime 仍沒有 hidden habit/roughness default、`tau_ice` synthesis 或 Formation promotion；
4. `.10.26` FIELD closure 前不進下一個 Ice Optics phase。
