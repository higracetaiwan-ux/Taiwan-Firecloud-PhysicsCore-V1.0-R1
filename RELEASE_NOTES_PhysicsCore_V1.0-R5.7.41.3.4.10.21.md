# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.21

**狀態：QA PASS / FIELD validation pending**  
**最新正式 FIELD baseline：V1.0-R5.7.41.3.4.10.20.1 FIELD PASS**  
**Frozen Science Baseline：R5.7.41.2_SHADOW_COT_AB_FROZEN**

## 本版目的

完成 Ice Optics Phase 2 Step 3H：把「Wyser 的 `L` 與 Yang/Bi 的 `maximum_dimension_um` 是否是同一種 size coordinate」與「兩者 solid-column shape 是否等價」正式拆開判定。

## 主要成果

1. **L → Dmax coordinate gate 解鎖**
   - Wyser (1998) 將 nonspherical ice particle size distribution 定義在 maximum dimension / length `L`。
   - Yang/Bi authoritative database 使用 particle maximum dimension 作為 size axis。
   - 因此 `Wyser L_um == Yang/Bi maximum_dimension_um` 可作為 **coordinate identity**。

2. **Yang/Bi V2 exact single-column geometry 由 source rows 重新釘定**
   - bundled LUT 的 `effective_diameter_um` 由 authoritative source `V/A` rowwise 產生，未依賴 Step 3H aspect-ratio 公式。
   - 以 regular hexagonal-column geometry 重現 189 個 `single_column / Rough000 / 600 nm` Dmax rows：
     - `a=0.35L`，`L<100 µm`
     - `a=3.48*sqrt(L)`，`L>=100 µm`
   - `3.48` 最大相對 `De` 誤差約 `5.84e-7`。
   - `0.348` alternative 最大相對誤差約 `0.8973`，不符合 authoritative source geometry。
   - 因此 runtime/release evidence 不使用有疑義的文字轉錄代替 source-row geometry。

3. **Coordinate identity ≠ shape identity**
   - Wyser Eq.(5) width law 與 source-validated Yang/Bi V2 single-column law仍不同。
   - 診斷點 `10 / 30 / 100 / 1000 µm` 的最大相對 width difference 為 `0.3`。
   - Shape / projected-area / volume-mass compatibility 全部維持 false。

4. **CASE evidence handoff**
   - 新增 Step 3H evidence CSV / gate CSV / contract JSON。
   - Analysis Integrity 新增 evidence-present / contract-freeze / fail-closed checks。
   - CASE required members 與 archive content gates 同步納入 Step 3H。

## 仍然阻擋

- `WYSER_TO_YANG_SOLID_COLUMN_SHAPE_COMPATIBILITY_PASS=false`
- `WYSER_TO_YANG_PROJECTED_AREA_COMPATIBILITY_PASS=false`
- `WYSER_TO_YANG_VOLUME_MASS_COMPATIBILITY_PASS=false`
- `INDEPENDENT_EQ6_EXTERNAL_NUMERIC_CORROBORATION_PASS=false`
- `SCIENTIFIC_MASS_CLOSURE_EXECUTED=false`
- `YANG_BI_HABIT_BRIDGE_VALIDATED=false`
- `YANG_BI_ROUGHNESS_BRIDGE_VALIDATED=false`
- `BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE=false`
- `GFSV16_DMAX_MAPPING_ELIGIBLE=false`
- `PRODUCTION_ICE_OPTICS_READY=false`
- `physics_promotion_allowed=false`

因此 WINDY `twfc.validated-ice-dmax-mapping.v1_1` 仍必須 fail-close。

## Frozen Science

Formation / Viewing / Twilight Glow、六波段 550/575/600/650/700/750 nm、Canvas/Corridor/REZ、Earth Shadow、Production/Shadow COT、Missing ≠ Clear ≠ Zero 全部未修改。
