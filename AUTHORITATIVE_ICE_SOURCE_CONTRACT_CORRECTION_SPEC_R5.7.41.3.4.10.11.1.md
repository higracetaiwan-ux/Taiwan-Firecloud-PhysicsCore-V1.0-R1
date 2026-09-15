# Authoritative Ice Source Contract Correction Spec — R5.7.41.3.4.10.11.1

## 目的

本版只修正 `.10.11` 對 Yang/Bi V2 authoritative source 的兩個錯誤假設，並把 Ice LUT 的 authoritative size key 明確改為 Dmax-first；不修改已凍結的 Formation / Viewing / Twilight Glow / Red-Light / COT science。

## 實測觸發證據

使用者下載並驗證 `Data_0.2_15.25.tar.gz`：

- published MD5：`2fb9bbab2c2c735a869c863a680e2f70` PASS
- 解壓後 `isca.dat`：27/27
- 真實 source habit folders：`single_column / plate / hollow_column / droxtal / HBR / SBR / 8_columns / 5_plates / 10_plates`

`.10.11` 首次 strict gate 結果：18 PASS source / 9 FAIL，原因為：

1. `HC` resolver 尋找 `HC/`，但下載 archive 實際資料夾是 `hollow_column/`。
2. HBR/SBR 的同一 Dmax 可出現 wavelength-dependent `volume_um3`；`.10.11` 誤把「V 必須跨 wavelength invariant」當 hard gate。

## 修正後 source contract

### Habit resolver

Firecloud canonical habit 仍保留 `HC`，source directory resolver 接受：

`HC -> hollow_column`（primary published/extracted directory）

並保留 `HC` 作為相容 alias。

### Authoritative key

正式 authoritative row key：

`ice_habit + surface_roughness + maximum_dimension_um + wavelength_nm`

也就是 Dmax-first。

### Source-row geometry

每個 source row 保留自己的：

- `volume_um3`
- `projected_area_um2`
- `Qext`
- `SSA`
- `g`

不再要求 V/A 跨 wavelength 完全不變。

`geometry_consistent` 僅保留為 diagnostic；wavelength-dependent geometry 不再造成 source FAIL，但仍記錄最大 relative spread。

### k_ext

每一個 wavelength row 獨立使用 source-row geometry：

`k_ext = Qext * A_proj / (rho_ice * V)`

其中 `rho_ice = 917 kg/m3`。

### 六波段

固定：550 / 575 / 600 / 650 / 700 / 750 nm。

- 550/600/650/700/750 nm：exact source wavelength
- 575 nm：只允許 source grid 0.57–0.58 µm 內 linear interpolation
- 禁止 spectral extrapolation

## effective radius 定位

`effective_radius_um = (1.5 * V/A) / 2` 仍保留，但改定義為：

`SOURCE_ROW_DERIVED_DIAGNOSTIC_MAPPING_COORDINATE`

它不是 authoritative cross-band key，也不得自行視為 forecast-native microphysical r_eff。

## WINDY portable V1.1

Portable contract 升級：

`FIRECLOUD_ICE_OPTICS_PORTABLE_V1_1`

runtime lookup 軸：`maximum_dimension_um`。

允許：同 habit + roughness 內 Dmax linear interpolation。

禁止：

- Dmax extrapolation
- habit interpolation
- roughness interpolation
- 未驗證的 r_eff -> Dmax conversion

如果 WINDY 沒有 native/calibrated Dmax 或另行驗證的 microphysics mapping，positive IWP 必須 fail-close：

`ICE_MAXIMUM_DIMENSION_MISSING`

## Promotion boundary

本版即使 authoritative LUT build PASS，也只代表 source -> six-band Dmax-first LUT / portable package 構建通過。

仍然：

- `physics_promotion_allowed = false`
- 不進 Production Formation
- 不進 Production Viewing
- 不改 Twilight Glow
- 不提前做 PSD / habit mixture / climatological r_eff replacement
