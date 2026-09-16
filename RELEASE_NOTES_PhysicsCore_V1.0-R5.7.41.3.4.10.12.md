# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.12

## 名稱

**Ice Optics Phase 2 — Native Microphysics Capability Audit + Dmax/PSD Mapping Eligibility Contract**

## 定位

本版是 Ice Optics Phase 2 的第一個實作版，工作範圍只有「能力盤點、來源證據、映射資格判定」。

- Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`
- Phase 2 mode：`DIAGNOSTIC_READINESS_ONLY`
- Production promotion：**NO**
- Formation / Viewing / Twilight Glow / Production COT：**完全不變**

## 新增功能

### 1. Native Microphysics Capability Audit

新增：

`firecloud/ice_microphysics_capability.py`

每次分析會根據當次 CASE 真正存在的資料建立：

- GFS GRIB native field inventory
- native field completeness
- native cloud voxel / column derived evidence
- Ice Optics runtime slots

並清楚區分：

1. `NATIVE_GFS`
2. `DETERMINISTIC_DERIVED`
3. `RUNTIME_SLOT`
4. `MISSING_CAPABILITY`

因此 `ICMR`、`IWC`、`IWP`、`Dmax`、`r_eff`、habit、roughness、PSD 不會再被混成同一類 microphysics 證據。

### 2. Dmax / PSD Mapping Eligibility Contract

正式凍結目前 Phase 2 第一階段禁止事項：

- 禁止 `r_eff -> Dmax`
- 禁止 `CER -> Dmax`
- 禁止 `IWP -> Dmax`
- 禁止 `temperature -> Dmax`
- 禁止 `cloud thickness -> Dmax`
- 禁止 `RH / TCDC -> Dmax`
- 禁止 temperature / cloud regime 自動指定 habit
- 禁止 fixed habit default
- 禁止 fixed roughness default
- 禁止無來源 contract 的假設 PSD

目前正式 blockers：

- `ICE_DMAX_NATIVE_FIELD_UNAVAILABLE`
- `ICE_DMAX_MAPPING_UNAVAILABLE`
- `ICE_PSD_INPUT_INCOMPLETE`
- `ICE_HABIT_UNRESOLVED`
- `ICE_ROUGHNESS_UNRESOLVED`

只要其中必要條件未完成，Positive IWP 仍必須 fail-close。

### 3. CASE 新增證據檔

每次新版 CASE ZIP 會新增：

- `ice_microphysics_native_input_capability_audit.csv`
- `ice_microphysics_phase2_mapping_eligibility.csv`
- `ice_microphysics_phase2_contract.json`

三者均會進入既有 CASE archive manifest / SHA256 流程。

### 4. GFS provenance 補強

`gfs_grib_message_inventory.csv` 與 `gfs_native_field_completeness.csv` 現在在 model aggregate 階段保留：

- `gfs_run_utc`
- `gfs_forecast_hour`
- `gfs_valid_time_utc`

供 Phase 2 capability audit 使用；不改變 GFS native 下載、decode 或物理計算。

## 真實 CASE replay

使用既有 FIELD PASS CASE：

`Taiwan-Firecloud-PhysicsCore-V1.0-R5.7.41.3.4.10.11.2_2026-09-17_sunrise_TWS175_CASE.zip`

重放結果：

- GFS GRIB inventory rows：408
- 真正存在的 native shortName：`CLWMR / ICMR / RWMR / SNMR / GRLE / TCDC / TMP / RH / HGT`
- native voxel rows：96,876
- native cloud column rows：2,691
- Ice runtime rows：2,691
- Positive IWP rows：213
- Runtime Dmax non-null：0
- Runtime r_eff non-null：0
- Resolved habit：0
- Resolved roughness：0
- `NATIVE_ICE_MASS_INPUT_READY=true`
- `NATIVE_THERMODYNAMIC_CONTEXT_READY=true`
- `NATIVE_VERTICAL_PROFILE_SUPPORT=true`
- `NATIVE_DMAX_AVAILABLE=false`
- `NATIVE_PSD_AVAILABLE=false`
- `MICROPHYSICS_MAPPING_READY=false`
- `PRODUCTION_ICE_OPTICS_READY=false`
- `physics_promotion_allowed=false`
- final eligibility：`INSUFFICIENT_MICROPHYSICS`

這表示目前 GFS/CASE 有足夠的冰水質量與垂直結構證據，但**沒有粒徑分布證據可以合法推出 Yang/Bi Dmax / PSD**。

## 測試

完整 regression：

- **772 passed**
- **0 failed**
- **1 existing pandas FutureWarning**

Phase 2 targeted gate 另外明確驗證：

- Positive IWP + ICMR + T + RH + cloud fraction，仍不得自動產生 Dmax。
- 即使 runtime 有 `ice_effective_radius_um`，沒有 Dmax 時仍為 `ICE_MAXIMUM_DIMENSION_MISSING`。
- audit 必須將 IWP 標為 deterministic derived，而非 GFS native。
- habit / roughness 不可 default-fill。
- CASE archive 必須包含三個新 Phase 2 evidence artifacts。

## 下一步

`.10.12` 完成後下一個合理工作不是直接發明 Dmax 公式，而是：

1. 盤點是否有其他 **authoritative forecast/native source** 能提供 cloud-ice particle size / number concentration / PSD moments。
2. 若採外部 calibrated mapping，先建立來源、適用域、輸入欄位、uncertainty 與 fail-close contract。
3. 在上述證據存在前，不建立 r_eff→Dmax、habit 或 roughness 經驗規則。
4. 完成新版本 FIELD CASE 後，才可將 `.10.12` 從 implementation/regression pass 升為 FIELD PASS。
