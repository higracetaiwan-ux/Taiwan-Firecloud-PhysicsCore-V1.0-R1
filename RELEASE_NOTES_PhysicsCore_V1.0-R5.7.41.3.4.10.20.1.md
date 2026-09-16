# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.20.1

**狀態：QA PASS / FIELD validation pending**  
**最新正式 FIELD baseline：V1.0-R5.7.41.3.4.10.19 FIELD PASS**  
**Frozen Science Baseline：R5.7.41.2_SHADOW_COT_AB_FROZEN**

## 本版目的

完成 Ice Optics Phase 2 Step 3G 的主要數值恢復與 diagnostic mass-closure preflight，同時保持所有 production promotion fail-close。

## 主要修正

1. **修正 Eq.(5) provenance 混淆**
   - single-author Wyser (1998) Eq.(5) 不再標示為 `D=2.5 L^0.6`。
   - Primary Eq.(5) 恢復為 hexagonal solid-column 的分段 `L/D` 關係：
     - `L/D = 1`，`L < 30 µm`
     - `L/D = 1 + 0.003(L - 30)`，`L >= 30 µm`
   - `D=2.5 L^0.6` 保留為 **Wyser & Yang (1998) separate geometry lineage**，禁止拿來替代 single-author Wyser Eq.(5)。

2. **Primary Eq.(6) numeric recovery**
   - 由 Wyser (1998) primary indexed text 恢復：
     - `m_g(L_um) = 2.311e-2 * (L_um / 1e4)^2.7625`
   - `m` 單位為 g，`L` 單位為 µm。
   - g/µm expanded form 與 SI form 已完成 machine reproduction，unit-consistency PASS。

3. **Diagnostic primary Eq.(6) PSD mass closure**
   - 使用 recovered Eq.(6) + pinned Wyser mixed PSD + Eq.(7)/(8) IWC normalization。
   - 測試 3 temperatures × 3 IWC × 2 resolutions = **18 cases**。
   - 最大 mass-closure relative error：約 `3.55e-16`。
   - 最大 20 µm branch-continuity relative error：約 `1.25e-15`。
   - 最大 normalization convergence relative error：約 `8.20e-7`。
   - 此結果明確標示為 **NUMERICAL PREFLIGHT / diagnostic-only**，不建立 operational validity domain。

4. **Contract schema 升級**
   - `FIRECLOUD_ICE_WYSER_PRIMARY_NUMERIC_RECOVERY_V3`
   - 新增 diagnostic primary Eq.(6) mass-closure 與 convergence gates。
   - CASE Analysis Integrity 同步驗證：numeric preflight 可以 PASS，但 scientific/production promotion 必須仍為 false。

## 仍然阻擋

- `INDEPENDENT_EQ6_EXTERNAL_NUMERIC_CORROBORATION_PASS=false`
- `SCIENTIFIC_MASS_CLOSURE_EXECUTED=false`
- `ABSOLUTE_PSD_RECONSTRUCTION_EXECUTABLE=false`
- `PSD_MASS_CLOSURE_VALIDATION_PASS=false`
- `WYSER_L_TO_YANG_DMAX_COORDINATE_VALIDATED=false`
- `BULK_YANG_BI_PSD_INTEGRATION_ELIGIBLE=false`
- `GFSV16_DMAX_MAPPING_ELIGIBLE=false`
- `PRODUCTION_ICE_OPTICS_READY=false`
- `physics_promotion_allowed=false`

因此 WINDY 仍不得由 IWP / T / RH / rei / cloud fraction 猜 Dmax、habit、roughness 或 Ice τ。

## Regression

- Full regression：**846 / 846 PASS**
- 既有 pandas `FutureWarning`：1，非測試失敗。
- Frozen Formation / Viewing / Twilight Glow / 六波段 / Canvas / Corridor / REZ / Missing semantics 未改。

## 下一步

優先尋找第二份真正獨立、可追溯的 **Wyser Eq.(6) numeric corroboration**。在該 gate 通過前，diagnostic mass closure 不得升級為 scientific mass-closure validation。之後才進入 Wyser `L → Yang/Bi maximum_dimension_um` geometry bridge、solid-column habit compatibility、roughness uncertainty 與 six-band bulk integration。
