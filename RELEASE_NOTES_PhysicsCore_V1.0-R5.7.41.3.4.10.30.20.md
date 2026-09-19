# Taiwan Firecloud PhysicsCore V1.0 — Release Notes

## R5.7.41.3.4.10.30.20

**Step 3Q.20 — Band25 Forward-Reproduction Harness + Contract Consistency Closure**

本版不修改 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。

### 新增
- `firecloud/fu96_rrtmg_band25_reproduction.py`
  - 載入 pinned RRTMG Band25 46-node reference grid。
  - 以 recovered Fu96 primary band 1 Eq.3.9 建立 deterministic direct-copy negative control。
  - 輸出 extinction / SSA / asymmetry 的逐節點 residual 與 summary。
  - 建立 exact-reproduction prerequisite matrix，缺任一 historical input 都 fail-close。
- `tools/verify_fu96_rrtmg_band25_reproduction_harness.py`
- `tests/test_r574134103020_band25_forward_reproduction_harness.py`
- 兩份正式 Band25 diagnostic evidence（CSV + JSON）。

### Contract consistency 修正
Step 3Q.17 已正式更正 Fu96-lineage co-albedo weighting 為 extinction-weighted：

`alpha_linear = Σ(alpha_lambda beta_lambda S_lambda dLambda) / Σ(beta_lambda S_lambda dLambda)`

`ln(alpha_log) = Σ(ln(alpha_lambda) beta_lambda S_lambda dLambda) / Σ(beta_lambda S_lambda dLambda)`

`.10.30.19` evidence row 已正確，但 contract payload 的 human-readable equation string 仍殘留舊的 solar-only 表達式。本版修正 payload，使 evidence / gate / contract 三者一致。這是 provenance serialization 修正，不改 Frozen Science。

### Band25 結果
- 46 nodes，Dge `5–140 µm`，step `3 µm`
- Band25：`16000–22650 cm⁻¹` ≈ `0.441501–0.625000 µm`
- direct-primary control：
  - extinction relative RMSE over mean = `0.0047811239553869666`
  - SSA relative RMSE over mean = `3.790091528184389e-06`
  - asymmetry relative RMSE over mean = `0.0010955150422100914`
- extinction residual 僅在 Dge `107–110 µm` 間跨零一次；SSA / asymmetry residual 皆全節點同為負值。

此 residual topology 只作 negative-control qualification；禁止以 residual 反解或擬合 historical generator。

### Fail-close 維持
- `RRTMG_BAND25_HISTORICAL_INTRABAND_INPUT_BUNDLE_COMPLETE=False`
- `RRTMG_FINE_SPECTRAL_GRID_REALIZATION_RECOVERED=False`
- `PREAVERAGING_SPECTRAL_SAMPLES_RECOVERED=False`
- `EXACT_HISTORICAL_SOLAR_SPECTRUM_AND_WEIGHTS_RECOVERED=False`
- `RRTMG_BAND25_EXACT_REPRODUCTION_PASS=False`
- `RRTMG_BAND24_EXACT_REPRODUCTION_PASS=False`
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`
- `TAU_ICE_PRODUCTION_ALLOWED=False`
- `PRODUCTION_ICE_OPTICS_READY=False`
- `physics_promotion_allowed=False`

Step 3R remains blocked.
