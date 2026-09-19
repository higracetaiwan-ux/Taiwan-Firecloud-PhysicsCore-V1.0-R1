# Taiwan Firecloud PhysicsCore V1.0 — Current Project State

## 現行 QA 版本
`1.0.0-R5.7.41.3.4.10.30.20`

## Science baseline
`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## 最新 FIELD baseline
`R5.7.41.3.4.10.30.18.2 FIELD PASS`

`.10.30.20` 尚未執行 FIELD CASE；本版屬 Step 3Q provenance / diagnostic tooling，不改 Frozen Formation / Viewing / Twilight Glow science，也不啟用 Production Ice Optics。

## Step 3Q
**Step 3Q.20 — Band25 Forward-Reproduction Harness + Contract Consistency Closure**

正式 QA 狀態：
`PASS_FAIL_CLOSED_FU96_PRIMARY_BAND_FORWARD_RECONSTRUCTION_INPUTS_QUALIFIED_RRTMG_FINE_GRID_AND_EXACT_BAND24_25_REALIZATION_UNRECOVERED`

### 本版完成
- 新增 `firecloud/fu96_rrtmg_band25_reproduction.py`。
- 對 pinned archived RRTMG Band25 的 **46 個 Dge nodes（5–140 µm，每 3 µm）**建立可重現 negative-control harness。
- 直接使用 recovered Fu96 primary band 1 Eq.3.9 broadband coefficients 逐節點重算並產生 residual table。
- 固定 Band25 geometry：`16000–22650 cm⁻¹` = 約 `0.441501–0.625000 µm`。
- 新增 `tools/verify_fu96_rrtmg_band25_reproduction_harness.py`。
- 生成正式 evidence：
  - `ICE_MICROPHYSICS_FU96_RRTMG_BAND25_DIRECT_CONTROL_RESIDUALS_R5.7.41.3.4.10.30.20.csv`
  - `ICE_MICROPHYSICS_FU96_RRTMG_BAND25_REPRODUCTION_DIAGNOSTIC_R5.7.41.3.4.10.30.20.json`
- 修正 `.10.30.19` contract payload 遺留的舊 co-albedo equation 字串：serialized `alpha_linear` / `alpha_log` 現與 Step 3Q.17 一致，保留 `beta_lambda` extinction weighting。
- CASE integrity gate 已要求新的 Band25 harness / residual-topology capability，同時維持所有 production guards 為 False。

### Band25 negative-control 結果
- reference nodes：46
- extinction RMSE / mean(reference)：`0.0047811239553869666`
- SSA RMSE / mean(reference)：`3.790091528184389e-06`
- asymmetry RMSE / mean(reference)：`0.0010955150422100914`
- extinction residual：隨 Dge 單調不增加，且只在 `107–110 µm` 間跨零一次
- SSA residual：46/46 為負
- asymmetry residual：46/46 為負

上述結果只證明「direct primary broad-band copy 不是 archived Band25 exact generator」，不得 inverse-fit historical generator。

### 仍未恢復
- exact fine spectral grid nodes
- exact fine-grid interpolation realization
- provenance-linked pre-averaging source-wavelength optical samples
- exact historical solar spectrum identity
- exact within-band discrete solar weights

因此：
- `RRTMG_BAND25_EXACT_REPRODUCTION_PASS=False`
- `RRTMG_BAND24_EXACT_REPRODUCTION_PASS=False`
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`
- `TAU_ICE_PRODUCTION_ALLOWED=False`
- `PRODUCTION_ICE_OPTICS_READY=False`
- `physics_promotion_allowed=False`
- Step 3R：`BLOCKED`

## 下一步
優先搜尋／恢復 Band25 的 historical intra-band realization：fine grid、interpolation、source-wavelength Fu optical inputs、solar spectrum / discrete weights。只有 authoritative provenance 或等價 deterministic reproduction 足以關閉 exact gate；禁止用 runtime g-point weights、假定 fine grid 或 final-table inverse fit 代替。
