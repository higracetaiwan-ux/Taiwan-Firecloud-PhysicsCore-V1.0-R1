# Taiwan Firecloud PhysicsCore — Ice Cloud Spectral Optics Shared Module Phase 1

版本：**V1.0-R5.7.41.3.4.10.10**  
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`  
Contract：`FIRECLOUD_ICE_OPTICS_V1`

## 1. 目的

建立 PhysicsCore 與 WINDY Firecloud Observer 共用的冰雲六波段光學資料契約：

`550 / 575 / 600 / 650 / 700 / 750 nm`

本階段只做 calibrated-LUT 匯入、單位轉換、IWP×k_ext 診斷、CASE/WINDY 輸出與 Integrity。**不得改寫 Frozen Formation / Viewing / Twilight Glow / Red-Light / Photography Decision / Production COT。**

## 2. 權威資料源策略

首選來源為 Yang/Bi ice-particle single-scattering database V2（Yang et al. 2013；Bi & Yang 2017）。來源 `isca.dat` 保留：wavelength、maximum dimension、particle volume、projected area、extinction efficiency Qext、SSA、asymmetry factor g。程式不隨版本包附帶未驗證的係數；必須由權威 source 轉出 normalized LUT。

## 3. k_ext 定義

單粒子 extinction cross section：

`C_ext = Qext × A_proj`

冰粒質量：

`m = rho_ice × V`

因此：

`k_ext [m²/kg] = Qext × A_proj / (rho_ice × V)`

本版固定與既有 PhysicsCore 一致的 bulk ice density：`rho_ice = 917 kg/m³`。

## 4. Effective size

資料源提供 maximum dimension、volume、projected area。Phase 1 同時保存：

- `maximum_dimension_um`
- `effective_diameter_um = 1.5 × V / A`
- `effective_radius_um = effective_diameter / 2`

這是 geometry-derived size coordinate。**不得默認等同 forecast model 的 native microphysical r_eff。** 未來若 provider 有明確 native r_eff，需另行 provenance 對接。

## 5. 六波段 LUT schema

必要欄位：

- `wavelength_nm`
- `maximum_dimension_um`
- `effective_diameter_um`
- `effective_radius_um`
- `ice_habit`
- `surface_roughness`
- `mass_extinction_coefficient_m2_kg`
- `single_scattering_albedo`
- `asymmetry_parameter`
- `source_dataset`
- `source_version`
- `source_record_provenance`

每個 habit × roughness × size group 必須完整具備六波段；否則 LUT validation FAIL。

## 6. 光學深度

只有以下資料全部完整時才允許計算：

1. native IWP 有值且 vertical support 完整；
2. calibrated effective radius 有值；
3. ice habit 有值；
4. surface roughness 有值；
5. 六波段 LUT 完整。

公式：

`tau_ice(lambda) = IWP [kg/m²] × k_ext(lambda) [m²/kg]`

`T_ice(lambda) = exp(-tau_ice(lambda))`

`native_cloud.py` 的 `ice_water_path_proxy_gm3_km` 在 vertical support 完整時數值上等於 `kg/m²`，因為 `1 g/m³ × 1 km = 1 kg/m²`。

## 7. Missing / Zero 規則

- `Missing != Clear != Zero`
- IWP Missing → tau Missing
- vertical completeness < 1 → tau Missing
- positive IWP + LUT/r_eff/habit/roughness 不完整 → tau Missing
- **只有完整 vertical support 下的 exact IWP=0 才可輸出 tau=0、T=1**
- 禁止 RH、Cloud Fraction、季節經驗、固定 habit、未標示 fixed r_eff 補造 tau

## 8. Phase 1 role separation

所有 runtime rows 固定：

- `ice_optics_phase = PHASE1_DIAGNOSTIC_ONLY_NO_PHYSICS_PROMOTION`
- `physics_role = DIAGNOSTIC_ONLY_UNASSIGNED`
- `tau_synthesis_allowed = False`
- `formation_promotion_allowed = False`

注意：`tau_synthesis_allowed=False` 表示不得用 proxy 補造 tau；當全部 calibrated inputs 真實完整時，Phase 1 診斷仍可依公式計算 spectral tau，但結果目前不回灌 frozen science。

## 9. WINDY Shared Export

新增 compact outputs：

- `v1_windy_ice_optics_summary.csv`
- `windy_firecloud_ice_optics_summary_v1.json`

Contract metadata：

- `ice_optics_contract_version = FIRECLOUD_ICE_OPTICS_V1`
- `physicscore_version`
- `science_baseline`
- `wavelengths_nm`
- `physics_promotion_allowed = false`
- LUT readiness/provenance

距離帶：0–40 / 40–100 / 100–300 / 300–350 / 350–440 km。

## 10. Source normalizer tool

`tools/build_ice_optics_lut_from_tamu.py`

輸入一個 TAMU `isca.dat`、habit、roughness；輸出 Firecloud normalized six-band CSV。波長若非 source exact point，只允許在同一 calibrated source spectral grid 內做線性 interpolation，且 provenance 必須標成 `LINEAR_WAVELENGTH_INTERPOLATION_WITHIN_SOURCE_GRID`。

## 11. Phase 2 / Phase 3

Phase 2：完成 calibrated habit/roughness/PSD strategy，評估 bulk mixture、SSA、g、phase-function/Legendre moments。  
Phase 3：經 A/B + Ground Truth validation 後，才考慮把 spectral ice optics 接到 Formation upstream blocker / illuminated Canvas scattering / Viewing 路徑。任何 production switch 必須另立 release gate。
