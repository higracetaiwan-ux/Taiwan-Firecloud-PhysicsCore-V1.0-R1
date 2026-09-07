# Taiwan Firecloud PhysicsCore V1.0-R5.7.22 發行說明

## 版本主題

**Full Directional Cloud Scattering Geometry Contract**

本版正式把 Tier-2 雲散射方向幾何由單一 `scattering_angle` 升級為：

`θ₀ + θᵥ + Δφ`

其中 `scattering_angle_deg` 保留為衍生診斷，不再是 production 多重散射 LUT 的唯一方向座標。

## 主要變更

### 1. 新增完整 target-local directional geometry

每個 Canvas target 新增：

- `solar_zenith_deg`
- `view_zenith_deg`
- `relative_azimuth_deg`
- `solar_altitude_target_deg`
- `solar_azimuth_target_deg`
- `view_elevation_deg`
- `view_azimuth_target_deg`
- `mu0`
- `mu_view`
- `azimuth_degeneracy_state`
- `directional_geometry_state`
- `scattering_angle_deg`

### 2. 修正太陽方向座標系

舊版直接把觀測點的太陽高度／方位當成 target-local 角度。

R5.7.22 改為：

`Observer local ENU solar direction → ECEF → Target local ENU`

因此 0–100 km Canvas 中每個雲底都會取得自己的 target-local solar/view geometry。

### 3. 新 production LUT V2

正式 interpolation axes：

`COT × r_eff × solar_zenith_deg × view_zenith_deg × relative_azimuth_deg`

`scattering_angle_deg` 不再作 production interpolation axis。

`cloud_thickness_km` 保留 target/CASE 幾何證據，但不是本版純雲散射 LUT 的必要 interpolation axis。

### 4. 舊 LUT 不自動升級

若偵測到 R5.7.19/R5.7.20 scattering-angle-only LUT：

`LEGACY_SCATTERING_ANGLE_LUT_DETECTED_NOT_PRODUCTION_ELIGIBLE`

程式不會自動使用，也不會產生 Tier-2 radiance。

### 5. Production calibration gate 強化

新 V2 LUT 必須具備：

- full directional geometry contract
- full-hemisphere 0–180° 支援
- multiple scattering
- RT solver/version provenance
- cloud optics / phase-function source
- QC PASS
- validation reference
- SHA256

一般 plane-parallel scattering-angle-only LUT 不符合本版 production gate。

### 6. 新工具

新增：

- `tools/generate_tier2_directional_scattering_calibration_jobs.py`
- `tools/build_tier2_directional_scattering_calibration_package.py`
- `tools/install_tier2_directional_scattering_lut.py`

### 7. CASE evidence 擴充

原有 Tier-2 CASE 檔名維持相容，但內容新增完整方向幾何欄位。

## 不變項目

本版沒有改動：

- Formation / Viewing 分離
- Glow 獨立分支
- 六波段定義
- Target Optical Truth
- COT conflict semantics
- Tier-1
- Formation Brightness / Redness / Effective Illuminated Area
- 科學權重與決策門檻

## 測試

完整 regression：

**381 passed / 0 failed**
