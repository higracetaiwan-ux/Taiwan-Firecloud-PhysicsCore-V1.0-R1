# Taiwan Firecloud PhysicsCore V1.0 — Release Notes

## R5.7.41.3.4.10.30.19

**Step 3Q.19 — Fu Primary-Band Forward-Reconstruction Input Qualification**

本版不修改 `R5.7.41.2_SHADOW_COT_AB_FROZEN` 科學基線。

### 本版新增證據
- 固定 Fu radiation source 中明確標註為 Fu (1996) Eq. 3.9a–d 的六個 solar primary-band `ap/bps/cp/dps` 係數，共 **90 個數值**。
- 同一組 solar coefficients 在第二個 repository 中 **90/90 數值一致**；僅作 cross-repository numeric replication，不宣稱獨立歷史 archive。
- 新增 diagnostic-only `firecloud/fu96_primary_band_forward_model.py`，可直接計算六個 Fu primary solar bands 的 extinction / SSA / asymmetry / forward-delta。
- 固定 GCRT/RRTMG 文件所述 forward process：Fu Eq. 3.8/3.9 + Tables 3a–3d → source wavelengths → fine spectral grid interpolation → RRTMG band average → `extice3/ssaice3/asyice3/fdlice3`。
- Band25 46-node forward diagnostic 證明：直接使用 Fu 第一 primary-band broad coefficients **不能 exact reproduce** archived RRTMG Band25；extinction relative RMSE 約 0.478%，asymmetry relative RMSE 約 0.110%。
- 明確分離 Fu radiation transport label `0.7–1.3 µm` 與 Fu96-lineage optical-property averaging interval `0.7–1.41 µm`。

### Fail-close
- `RRTMG_FINE_SPECTRAL_GRID_REALIZATION_RECOVERED=False`
- `PREAVERAGING_SPECTRAL_SAMPLES_RECOVERED=False`
- `RRTMG_BAND24_EXACT_REPRODUCTION_PASS=False`
- `RRTMG_BAND25_EXACT_REPRODUCTION_PASS=False`
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`
- `PRODUCTION_ICE_OPTICS_READY=False`
- `physics_promotion_allowed=False`

Qualification: `PASS_FAIL_CLOSED_FU96_PRIMARY_BAND_FORWARD_RECONSTRUCTION_INPUTS_QUALIFIED_RRTMG_FINE_GRID_AND_EXACT_BAND24_25_REALIZATION_UNRECOVERED`
