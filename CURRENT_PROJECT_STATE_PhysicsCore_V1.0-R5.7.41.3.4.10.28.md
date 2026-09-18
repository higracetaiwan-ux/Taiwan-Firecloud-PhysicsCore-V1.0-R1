# Taiwan Firecloud PhysicsCore — CURRENT PROJECT STATE

## 現行版本

- Development release: `1.0.0-R5.7.41.3.4.10.28`
- Milestone: **Step 3O — Fu96/RRTMG SSA + Asymmetry Numeric Cross-Check**
- Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`
- Latest formal FIELD baseline: `R5.7.41.3.4.10.27 FIELD PASS`
- Current status: **QA CANDIDATE / FIELD VALIDATION PENDING**（working-tree 917/917 PASS；candidate fresh-extract 917/917 PASS；Step 3O byte-exact PASS；final immutable closure pending）

## 本版新增

1. 固定 RRTMG Fu96 visible band 24/25 reference table：46 個 `Dge=5,8,...,140 µm` 節點 × 2 bands = 92 records。
2. 以 Wyser PSD × Yang/Bi `single_column` × `Rough000/Rough003/Rough050` 重建 population bulk SSA/g。
3. 使用 volume/projected-area 定義建立 diagnostic bridge：`Dge = 4/(3√3) × De_bulk`。
4. 執行 27 population states × 2 RRTMG bands = **54 comparison rows**。
5. 數值 cross-check 可完整執行，但不新增 science tolerance，不把 broad-band reference 誤稱成六波段 monochromatic validation。

## 本版 regression characterization

- `Dge` range：約 `42.421785–106.739973 µm`，全部位於 RRTMG 5–140 µm valid domain。
- SSA sample-mean vs RRTMG broad-band：max absolute difference 約 `1.23243e-05`，mean 約 `7.88446e-06`。
- asymmetry `g` sample-mean vs RRTMG broad-band：max absolute difference 約 `0.0215156`，mean 約 `0.00870808`。
- 上述差值僅是 regression characterization，不是 production tolerance。

## 仍維持 fail-close

- `FULL_BAND_SPECTRAL_WEIGHTING_AVAILABLE = false`
- `INDEPENDENT_SSA_VALIDATION_PASS = false`
- `INDEPENDENT_ASYMMETRY_VALIDATION_PASS = false`
- `FULL_SIX_BAND_LIKE_FOR_LIKE_OPTICAL_VALIDATION_PASS = false`
- `TAU_ICE_PRODUCTION_ALLOWED = false`
- `PRODUCTION_ICE_OPTICS_READY = false`
- `physics_promotion_allowed = false`
- Runtime habit / roughness inference 仍禁止。
- Formation / Viewing / Twilight Glow 不變。

## 下一個真正 blocker

要把 SSA/g 從 numeric cross-check 提升為真正 validation，需要完整 Yang/Bi source spectrum 與 RRTMG band spectral weighting / aggregation contract，不能以目前六個 monochromatic samples 代替 broad-band integration。
