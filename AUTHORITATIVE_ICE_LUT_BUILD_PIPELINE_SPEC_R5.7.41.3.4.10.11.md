# Authoritative Ice LUT Build Pipeline — R5.7.41.3.4.10.11

## 目的

本版建立 **Yang/Bi V2 authoritative source → Firecloud 六波段 Ice Optics LUT → WINDY portable package** 的正式建置與 QA gate。

本版 **不將 Ice Optics 推入 Formation / Viewing / Twilight Glow production physics**；Frozen Science baseline 仍為：

`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## Authoritative source contract

來源：Yang/Bi ice-particle single-scattering database Version 2（Zenodo record 5348402）。

短波 archive：`Data_0.2_15.25.tar.gz`

Published MD5：`2fb9bbab2c2c735a869c863a680e2f70`

README MD5：`50ae2be17e08bdccda9a5f5f3b194936`

來源結構 frozen：

- 9 habits：`single_column`, `plate`, `HC`, `droxtal`, `HBR`, `SBR`, `8_columns`, `5_plates`, `10_plates`
- 3 roughness：`Rough000`, `Rough003`, `Rough050`
- 27 個 `isca.dat`
- 每個 `isca.dat`：396 wavelengths × 189 sizes = 74844 rows
- source wavelength range：0.2–15.25 µm
- source size range：2–10000 µm

## Firecloud target bands

固定：

`550 / 575 / 600 / 650 / 700 / 750 nm`

每個 target wavelength：

1. source grid 有 exact wavelength → `EXACT_SOURCE_WAVELENGTH`
2. exact 不存在，但 target 位於兩個 published source wavelengths 之間 → `LINEAR_INTERPOLATION_WITHIN_SOURCE_GRID`
3. 超出 source grid → FAIL

禁止 wavelength extrapolation。

## Mass extinction

單粒子 source optical property 轉換：

`k_ext = Qext × A_proj / (rho_ice × V)`

其中 `rho_ice = 917 kg/m³`。

來源 `A_proj` 為 µm²，`V` 為 µm³；程式進行 SI unit conversion，輸出：

`mass_extinction_coefficient_m2_kg [m²/kg]`

## Size coordinate

保留：

`D_eff = 1.5 × V / A_proj`

`r_eff_coordinate = D_eff / 2`

這是由 database geometry 推導出的 LUT size coordinate，**不得未標示地等同 forecast-native microphysical ice effective radius**。

## Strict release gate

要產出正式 calibrated LUT / WINDY portable package，以下必須全部 PASS：

1. published shortwave archive MD5 已驗證；
2. 27/27 `isca.dat` 全部存在；
3. 每檔 row/wavelength/size counts 符合 source contract；
4. wavelength / Dmax source range 正確；
5. Qext、SSA、g、V、A 均 finite/physical；
6. 同一粒子尺寸的 V/A 在 wavelength 維度保持幾何一致；
7. 六個 Firecloud wavelengths 均位於 published source domain；
8. 每個 habit × roughness × size 產生完整六波段；
9. `k_ext` / SSA / g 全 finite 且 physical；
10. runtime `effective_radius` coordinate 無模糊重複映射。

任一失敗：

- `release_ready = false`
- 不輸出正式 calibrated LUT（除非 explicit diagnostic `--emit-failed-lut`）
- 不輸出 WINDY portable ZIP
- Missing 保持 Missing，不補造係數。

## 新增工具

### `tools/build_authoritative_ice_optics_lut.py`

範例：

```bash
python tools/build_authoritative_ice_optics_lut.py \
  --archive /path/Data_0.2_15.25.tar.gz \
  --source-root /path/extracted \
  --output-dir ./ice_lut_build \
  --portable-zip ./Firecloud-Ice-Optics-Portable-V1.zip
```

輸出：

- `ice_optics_source_inventory_v1.csv`
- `ice_optics_spectral_grid_audit_v1.csv`
- `ice_optics_authoritative_build_qa_v1.json`
- `ice_optics_authoritative_source_manifest_v1.json`
- `manifest.json`
- QA PASS 時：`ice_optics_lut_v1.csv`
- QA PASS 且指定 `--portable-zip` 時：standalone WINDY portable package

## 本版 source readiness 狀態

Release 本身不內嵌 27.4 GB published archive，也不內嵌任何未驗證 coefficient。

因此目前狀態為：

`AUTHORITATIVE_SOURCE_SELECTED / LOCAL_SOURCE_ARCHIVE_NOT_BUNDLED`

這是刻意的 fail-close 設計，不代表 pipeline 未完成。
