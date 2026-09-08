# PhysicsCore V1.0-R5.7.23｜Liquid Cloud Full Directional Calibration Pipeline 規格

## 1. 版本目的

R5.7.23 以 **R5.7.22.1 ACCEPTED BASELINE** 為唯一基準，補齊 Tier-2 genuine calibrated liquid-cloud Full Directional LUT 的「生產與驗證鏈」，不改動既有 Formation、Viewing、Glow、Route Invariance 與六波段科學契約。

Production response 固定為：

\[
R_\lambda=f(\tau,r_e,\theta_0,\theta_v,\Delta\phi,\lambda)
\]

其中：

- `τ`：target cloud optical thickness / COT
- `r_e`：effective radius
- `θ₀`：target-local solar zenith
- `θᵥ`：target-local Cloud→Observer view zenith
- `Δφ`：target-local relative azimuth
- `λ`：550 / 575 / 600 / 650 / 700 / 750 nm

`scattering_angle_deg` 僅為衍生診斷，不是 production interpolation axis。

## 2. 不可破壞的硬規則

1. **Missing ≠ Clear ≠ Zero**。
2. 不得以 RH、Cloud Fraction、幾何或缺失 condensate 製造 COT。
3. 第一版 genuine production calibration 僅做 `LIQUID` cloud。
4. `cloud_thickness_km` 保留為幾何與 target optical evidence；在沒有 sensitivity study 前，不升格為 LUT interpolation axis。
5. 不得使用 scattering-angle-only legacy LUT 冒充 Full Directional LUT。
6. 不得使用 synthetic / dummy / regression-only response 冒充 genuine production calibration。
7. 外部 RT 結果未通過 QC 前，不得生成 production LUT package。

## 3. Calibration target 選取

正式入口為：

`select_liquid_calibration_targets()`

只接受同時滿足：

- `tier2_input_contract_state = INPUTS_READY_AWAITING_LUT_SOLVER`
- `directional_geometry_state = FULL_DIRECTIONAL_GEOMETRY_READY`
- `phase = LIQUID`（`WATER` 正規化為 `LIQUID`）
- COT 為 `EXACT_VALUE`，或 `BOUNDED_NATIVE_BRACKET + BOUNDED_INTERVAL`
- `COT / r_eff / θ₀ / θᵥ / Δφ` 均有有限數值

不符合者不會被推估或補值後加入 calibration domain。

## 4. REAL_CANVAS → Calibration Domain

`plan_liquid_directional_calibration_domain()` 由真實 Tier-2-ready targets 建立 domain：

- COT：使用 physics design knots 對真實 observed COT range 做 bracket，並保留 guard knot。
- `r_eff`：至少 bracket 真實 observed range；目前 design knots 為 4–30 µm。
- `θ₀ / θᵥ / Δφ`：由 observed range 加 margin 後建立可重現角度 grid。
- 六波段固定全部保留。

COT / `r_eff` design knots 是**校準網格設計點**，不是火燒雲經驗分數或 Suitable 門檻。

## 5. libRadtran / MYSTIC 外部 genuine RT 契約

R5.7.23 預設正式 solver family：

`LIBRADTRAN_UVSPEC_MYSTIC`

校準 recipe 明確要求：

- `rte_solver mystic`
- spherical 1D：`mc_spherical 1D`
- multiple scattering
- `mc_vroom` variance reduction
- 明確 photon count
- liquid-water Mie optics
- 完整 solver version / atmosphere / cloud-optics / phase-function provenance

目前 template 故意保留以下外部必填項：

- libRadtran data path
- validated atmosphere profile
- solar spectrum
- liquid cloud profile / optical setup
- calibration sensor altitude
- response normalization

這些項目在未經正式校準協定確認前，不由 PhysicsCore 自動猜測。

### θᵥ → uvspec `umu`

PhysicsCore 的 `θᵥ` 定義為 target-local **Cloud→Observer propagation vector** 相對上方天頂的角度。

R5.7.23 外部 job table 轉換為：

`uvspec_umu = -cos(θᵥ)`

並保存原始 `view_zenith_deg`；此轉換只負責 geometry adapter，不改寫 PhysicsCore 幾何定義。

## 6. Calibration Job Bundle

正式 bundle 包含：

- `tier2_liquid_directional_calibration_jobs.csv`
- `tier2_liquid_directional_domain_spec.json`
- `tier2_libradtran_mystic_solver_recipe.json`
- `uvspec_mystic_spherical_template.inp`
- `tier2_external_results_required_schema.csv`
- `tier2_liquid_directional_calibration_bundle_manifest.json`

Manifest 必須顯示：

`production_lut_state = NOT_YET_GENERATED_EXTERNAL_RT_REQUIRED`

直到 genuine external RT 結果回填並通過 QC。

## 7. External RT Result QC

每個 `job_id` 必須一對一回傳：

- `response_factor`
- `mc_relative_sigma`
- `solver_exit_code`
- `solver_family`
- `solver_version`
- `result_contract`

硬性檢查：

- 完整 job set，不得缺列／多列／重複
- response 非負且有限
- Monte-Carlo relative sigma 不超過指定門檻（預設 0.02）
- solver exit code = 0
- result contract 一致
- solver family 必須為 production approved full-hemisphere solver
- solver version 不得空白或混用

## 8. Production LUT Build

只有 `validate_external_rt_results()` 通過後，才允許：

`build_production_lut_from_external_results()`

它會交給 R5.7.22 既有 production package builder，重新驗證：

- full 5D tensor completeness
- 六波段完整性
- calibrated metadata
- full-hemisphere provenance
- response schema / units / geometry convention
- SHA256

正式輸出仍採 runtime 既有檔名：

- `tier2_directional_scattering_lut.csv`
- `tier2_directional_scattering_lut_manifest.json`

## 9. CLI

### 建立外部校準工作包

```bash
python build_tier2_liquid_directional_calibration_jobs.py \
  --foundation-csv <foundation.csv> \
  --readiness-csv <readiness.csv> \
  --output-dir <calibration_bundle_dir> \
  --libradtran-version <version>
```

### 以 genuine external RT 結果建立 production LUT package

```bash
python build_tier2_liquid_directional_lut_from_results.py \
  --jobs-csv <jobs.csv> \
  --results-csv <external_results.csv> \
  --metadata-json <calibration_metadata.json> \
  --output-dir <production_lut_package_dir>
```

第二個指令只建立通過 runtime validation 的 package；是否安裝到 production runtime 應再走既有 installer / deployment 流程，不會隱式覆寫已安裝 LUT。

## 10. R5.7.23 完成與未完成邊界

### 已完成

- REAL Tier-2-ready liquid target selector
- REAL domain planner
- full-directional external job generator
- MYSTIC spherical solver recipe / template
- uvspec geometry adapter
- external result schema 與 QC gate
- genuine result → calibrated package builder
- runtime package validation
- 回歸測試

### 尚未宣稱完成

- genuine libRadtran/MYSTIC response 大規模實際運算
- genuine calibrated production LUT 安裝
- liquid cloud optical calibration protocol 的最終 atmosphere / effective variance / normalization 定案
- ice-cloud production LUT
- `cloud_thickness_km` sensitivity study

在這些項目完成前，production solver 應繼續正確顯示 LUT 尚未安裝／尚未校準，而不是產生假 Tier-2 radiance。
