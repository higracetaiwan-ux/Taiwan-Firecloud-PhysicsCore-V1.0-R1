# Taiwan Firecloud PhysicsCore V1.0
## R5.7.41.3.4.10.12 — Ice Optics Phase 2
### Native Microphysics Capability Audit + Dmax/PSD Mapping Eligibility Contract

**狀態：PHASE 2 READINESS / DIAGNOSTIC CONTRACT ONLY**  
**唯一現行基線：V1.0-R5.7.41.3.4.10.11.2 FIELD PASS**  
**凍結 Science Baseline：R5.7.41.2_SHADOW_COT_AB_FROZEN**  
**Production promotion：禁止；`physics_promotion_allowed=false`**

---

## 1. 本版第一步的邊界

本文件只做兩件事：

1. 盤點目前 PhysicsCore `main` 真正會從 GFS 取得、解碼、衍生與輸出到 CASE / Ice runtime 的 microphysics inputs。
2. 定義 **Dmax / PSD Mapping Eligibility** 的證據門檻與 fail-close 狀態。

本步驟**不建立任何**下列科學規則：

- `r_eff -> Dmax`
- `CER -> Dmax`
- `IWP -> Dmax`
- `temperature -> Dmax`
- `cloud thickness -> Dmax`
- temperature / RH / cloud regime -> habit
- 任意固定 habit
- 任意固定 roughness
- 任意假設性 PSD `N(D)`

這些項目只有在後續取得可追溯、經校準且完成 QA 的 science mapping 後，才可另開 gate。

---

## 2. Audit 的證據分類

### 2.1 `GFS_NATIVE_GRIB`
目前 GFS provider 直接從 GRIB2 要求並解碼的欄位。

現行 `firecloud/providers/gfs_native.py` 的 native short names：

- `CLWMR` — cloud liquid water mixing ratio
- `ICMR` — cloud ice water mixing ratio
- `RWMR` — rain water mixing ratio
- `SNMR` — snow water mixing ratio
- `GRLE` — graupel mixing ratio
- `TCDC` — cloud fraction
- `TMP` — temperature
- `RH` — relative humidity
- `HGT` — geopotential height

並保存 GRIB `typeOfLevel / level / units` inventory。

### 2.2 `GFS_NATIVE_GRIB_DIAGNOSTIC`
`gfs_canvas_optical_probe.py` 另外從 `pgrb2b.0p25` 在 0–100 km Canvas 取得中間壓力層：

- `CLWMR`
- `ICMR`
- `TMP`
- `HGT`

此 probe 目前是 diagnostic-only，不改 frozen Formation。

### 2.3 `PHYSICSCORE_DERIVED_FROM_NATIVE`
由 native 量經明確、非假設性的物理／幾何轉換得到：

- `air_density_kgm3 = p / (R_d T)`
- `ice_water_content_gm3 = max(ICMR,0) × air_density × 1000`
- `ice_water_path_proxy_gm3_km = Σ(IWC × voxel_step_km)`
- Ice runtime 把上述 IWP proxy 以數值等價關係讀為 `native_iwp_kg_m2`
- `native_vertical_completeness`

**這些不是 GFS native particle-size fields。**

### 2.4 `ICE_RUNTIME_INPUT_SLOT`
Ice optics runtime 可以讀取，但現行 GFS → `native_cloud_columns` 鏈沒有建立來源的欄位：

- `ice_maximum_dimension_um`
- `maximum_dimension_um`
- `ice_effective_radius_um`
- `ice_habit`
- `surface_roughness`

「runtime 有欄位」不得等同「forecast 有 native field」。

---

## 3. 現行能力結論

### 3.1 已確認有的 native / deterministic inputs

目前可確定：

- native cloud ice mass：`ICMR`
- native liquid/mixed-phase context：`CLWMR`
- native frozen hydrometeor context：`SNMR`, `GRLE`
- precipitation context：`RWMR`
- cloud occupancy/context：`TCDC`
- thermodynamics：`TMP`, `RH`
- vertical geometry：`HGT`, pressure-level metadata
- derived mass fields：`IWC`, `IWP`
- vertical data quality：`native_vertical_completeness`
- run / valid-time / GRIB metadata provenance

### 3.2 尚未證明存在的 native particle-size information

目前 GFS ingestion contract 中**沒有證明存在**：

- native `Dmax`
- native cloud-ice `r_eff` / CER
- native PSD bins
- native number concentration
- native PSD moments sufficient to reconstruct `N(D)`
- native ice habit
- native surface roughness

因此目前的資料能力是：

> **mass/phase/thermodynamic/vertical structure available; particle-size distribution state unresolved.**

### 3.3 CASE 證據界線

基線 `.10.11.2` 已記錄 TWS175：

- Ice runtime rows = 2691
- positive-IWP rows = 213
- exact-zero IWP rows = 2478
- native vertical completeness = 1.0
- ready six-band Ice optics rows = 0
- `MICROPHYSICS_MAPPING_READY=false`
- `PRODUCTION_ICE_OPTICS_READY=false`

但本次工作階段沒有重新取得 TWS175 raw CASE ZIP/CSV，因此本 Audit 對 CASE 的標示分成：

- **baseline CASE evidence confirmed**
- **direct raw CASE seen this session = NO**

這避免把摘要證據誤寫成「本輪已重新逐列讀 raw CASE」。

---

# 4. Dmax Mapping Eligibility Contract

## 4.1 狀態機

每個 positive-ice-mass voxel / column 只能進入下列三種狀態之一：

### `NATIVE_DMAX_AVAILABLE`

只有全部條件成立才可使用：

1. Dmax 來自 raw provider field 或 CASE 中可回溯到 raw provider 的欄位。
2. Provider semantics 明確定義該量為與 Yang/Bi `maximum_dimension_um` 可比較的 **maximum particle dimension**；不能只因欄位叫 diameter/radius 就視為 Dmax。
3. Units 可直接、無假設地轉為 µm。
4. run / cycle / valid time / level / provider provenance 完整。
5. 值 finite 且 > 0。
6. 適用於該 cloud-ice population，而非 precipitation particle 或不相干 hydrometeor。
7. 進 LUT 時仍遵守：
   - exact Dmax node：可用；
   - 同 habit + roughness 之 LUT range 內 linear Dmax interpolation：可用；
   - Dmax extrapolation：禁止。

**目前狀態：NOT ESTABLISHED。**

### `CALIBRATED_DMAX_MAPPING_AVAILABLE`

只有全部條件成立才可使用：

1. Mapping 有明確 source / literature / model provenance。
2. Mapping versioned。
3. Inputs 全部是目前 CASE 真正存在且 semantic 已驗證的欄位。
4. Mapping domain（T/P/IWC/IWP/其他需要量的範圍）明確。
5. 超出 domain 必須 fail-close，不能 extrapolate。
6. 具 uncertainty 定義。
7. 有 synthetic QA 與 independent validation。
8. 不包含 hidden default / climatological silent fill。
9. Promotion 前另經 science gate。

**目前狀態：NOT ESTABLISHED。**

### `INSUFFICIENT_MICROPHYSICS`

若前兩者皆不成立，positive-IWP/positive-IWC state 必須：

- 不做 Yang/Bi Dmax lookup；
- 不做 `r_eff -> Dmax`；
- 不以 IWP、T、RH、CF、cloud thickness 猜 Dmax；
- fail-close。

**目前 positive-IWP rows 的預設 eligibility：`INSUFFICIENT_MICROPHYSICS`。**

---

# 5. PSD Mapping Eligibility Contract

本 Contract 只定義「可不可以進 PSD mapping」，不選任何 PSD 公式。

## 5.1 `NATIVE_PSD_AVAILABLE`

只有當 provider / CASE 真正提供：

- size bins；或
- number concentration + 足夠的 distribution moments/parameters；或
- provider 明確定義且足以重建 `N(D)` 的 microphysics state

並且 units、population、vertical level、valid time、provenance 全部完整時才成立。

**目前狀態：NOT ESTABLISHED。**

## 5.2 `CALIBRATED_PSD_MAPPING_AVAILABLE`

只有當：

1. 有外部 source-cited parameterization；
2. 所需 inputs 全部是現行 GFS/CASE 真正存在；
3. provider semantics 相容；
4. domain / uncertainty / fail-close 行為明確；
5. 有 validation；
6. 不使用 hidden defaults；

才可成立。

**目前狀態：NOT ESTABLISHED。**

## 5.3 `INSUFFICIENT_PSD_INPUTS`

現行下列資料本身都**不足以**構成 PSD：

- `ICMR`
- `IWP`
- `TMP`
- `RH`
- `TCDC`
- cloud thickness
- vertical completeness

因此現行 PSD eligibility：

`INSUFFICIENT_PSD_INPUTS`

---

# 6. Habit / Roughness 的 Phase-2 Gate

目前不建立 habit 或 roughness 規則。

### Habit

現行狀態：

`ICE_HABIT_UNRESOLVED`

不得：

- 固定 `plate`
- 固定任一 Yang/Bi habit
- 用溫度單獨決定 habit
- 未經校準就做 probabilistic mixture

### Roughness

現行狀態：

`ICE_ROUGHNESS_UNRESOLVED`

不得：

- 自動選 `Rough000`
- 自動選 `Rough003`
- 自動選 `Rough050`

若未來只能做 sensitivity ensemble，仍須與 production truth 分開。

---

# 7. LUT / bulk optics 雙重 Eligibility

## 7.1 Single-particle LUT lookup eligibility

需同時：

- legal Dmax
- resolved habit
- resolved roughness
- calibrated LUT configured
- Dmax inside LUT domain

目前：

`SINGLE_PARTICLE_LUT_LOOKUP_ELIGIBLE=false`

## 7.2 Bulk PSD synthesis eligibility

需同時：

- legal PSD representation
- ice mass/path support
- complete vertical support
- resolved habit strategy
- resolved roughness strategy
- calibrated LUT configured
- six-band completeness

目前：

`BULK_PSD_SYNTHESIS_ELIGIBLE=false`

---

# 8. Missing / fail-close reason contract

本版沿用／正式化以下 readiness blockers：

- `ICE_DMAX_NATIVE_FIELD_UNAVAILABLE`
- `ICE_DMAX_MAPPING_UNAVAILABLE`
- `ICE_PSD_INPUT_INCOMPLETE`
- `ICE_HABIT_UNRESOLVED`
- `ICE_ROUGHNESS_UNRESOLVED`

Runtime 既有較底層 state（例如 `ICE_MAXIMUM_DIMENSION_MISSING`, `ICE_HABIT_MISSING`, `ICE_ROUGHNESS_MISSING`）可以保留；`.10.12` 的 capability audit 應額外輸出上述 readiness blocker，兩層不要互相覆蓋。

多個 blocker 可同時存在，不要用單一 reason 隱藏其他缺口。

---

# 9. Zero-IWP 特例

既有 `.10.11.2` 行為保留：

- 若 native vertical support 完整且 IWP 為 exact zero，runtime 可判定 `NO_ICE_CONDENSATE_AT_NATIVE_STATE`；
- 六波段 `tau_ice=0`, transmission=1 是「該 state 無 ice mass」的 deterministic 結果；
- **這不代表 Dmax/PSD mapping ready**；
- 不得把大量 zero-IWP row 當作 microphysics mapping validation PASS。

---

# 10. `.10.12` 起始狀態

```text
SCIENCE_BASELINE = R5.7.41.2_SHADOW_COT_AB_FROZEN
ICE_PHASE2_MODE = DIAGNOSTIC_READINESS_ONLY

NATIVE_ICE_MASS_INPUT_READY = true
NATIVE_THERMODYNAMIC_CONTEXT_READY = true
NATIVE_VERTICAL_PROFILE_SUPPORT = true
NATIVE_DMAX_AVAILABLE = false
CALIBRATED_DMAX_MAPPING_AVAILABLE = false
NATIVE_PSD_AVAILABLE = false
CALIBRATED_PSD_MAPPING_AVAILABLE = false
ICE_HABIT_RESOLUTION_READY = false
ICE_ROUGHNESS_RESOLUTION_READY = false

MICROPHYSICS_MAPPING_READY = false
SINGLE_PARTICLE_LUT_LOOKUP_ELIGIBLE = false
BULK_PSD_SYNTHESIS_ELIGIBLE = false
PRODUCTION_ICE_OPTICS_READY = false
physics_promotion_allowed = false
```

---

# 11. `.10.12` 應新增的 CASE audit 輸出欄位

下一個程式實作步驟應讓 CASE 自己證明每次 run 的 capability，而不是靠開發者猜測。

建議每個 native field / mapping candidate 輸出：

- `provider`
- `provider_schema_version`
- `gfs_run_utc`
- `gfs_forecast_hour`
- `gfs_valid_time_utc`
- `field_short_name`
- `canonical_semantic`
- `type_of_level`
- `level`
- `units`
- `native_message_present`
- `decoded_route_value_count`
- `nonnull_count`
- `positive_count`
- `native_vs_derived`
- `source_artifact`
- `source_provenance`
- `dmax_mapping_role`
- `psd_mapping_role`
- `eligibility_state`
- `eligibility_blockers`

並產出：

`ICE_MICROPHYSICS_NATIVE_INPUT_CAPABILITY_AUDIT_R5.7.41.3.4.10.12.csv`

---

# 12. Acceptance Gate（本階段）

`.10.12` 第一階段只有在以下條件成立才可標記 `NATIVE MICROPHYSICS CAPABILITY AUDIT PASS`：

1. Audit 能明確區分 raw native / deterministic derived / runtime slot / missing。
2. `IWP` 不再被標成 GFS native。
3. Dmax / r_eff / habit / roughness 不因 runtime 欄位存在而被標成 provider native。
4. PSD/number concentration/moments 沒有 evidence 時保持 unavailable。
5. positive IWP + no legal Dmax => fail-close。
6. habit / roughness unresolved 不被 default 補值。
7. frozen Formation / Viewing / Twilight Glow / Production COT 不變。
8. `physics_promotion_allowed=false`。
9. 新 Audit 被收進 CASE archive。
10. 有 targeted tests 驗證「不會因 ICMR/IWP/T/RH/CF 自動生出 Dmax」。

---

# 13. 本輪證據來源

Repo `main`：

- `firecloud/providers/gfs_native.py`
- `firecloud/providers/gfs_canvas_optical_probe.py`
- `firecloud/native_cloud.py`
- `firecloud/ice_cloud_spectral_optics.py`
- `firecloud/model.py`

Baseline memory / FIELD evidence：

- `V1.0-R5.7.41.3.4.10.11.2 FIELD PASS`
- TWS175 2026-09-17 sunrise
- TWS106 native source attribution

本輪尚未直接重新開啟 TWS175 raw CASE ZIP/CSV，因此 raw CASE row-level re-audit 應列為下一個 evidence-closure 工作，不得假稱已完成。
