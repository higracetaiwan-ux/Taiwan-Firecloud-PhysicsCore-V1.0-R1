# Taiwan Firecloud PhysicsCore V1.0-R5.7.37 發行說明

## 本版主題

**Near-Surface Molecular Boundary Closure（近地層分子邊界閉環）**。

R5.7.37 不改變 Formation、Viewing、Twilight Glow 三軌架構，也不改六波段與 13 個太陽角度。主要修正 Twilight Glow `Scatter→Observer` 路徑在最低原生 pressure-level 以下出現 10–數十公尺真實資料缺口時，無法完成 Rayleigh / gas-species integration 的問題。

## 主要改動

1. 新增 CAMS 獨立 role：`O3_NEAR_SURFACE_MODEL_LEVEL_137`。
2. CAMS 每個有效時次由 4 條角色增為 5 條角色：pressure-level O₃、ML137 O₃、Spectral AOD、Native 3D aerosol、Aerosol SSA/g。
3. Open-Meteo surface-only request 新增 `temperature_2m`、`relative_humidity_2m`，既有 `surface_pressure` 保留。
4. `build_gas_profile()` 在證據完整時新增 ML137 近地分子 anchor。
5. Rayleigh 與 HITRAN gas-species observer path 可在 ML137 與最低 pressure-level 之間做真實 bracket interpolation。
6. CASE 新增 near-surface bridge provenance 與三個 Integrity guards。

## 沒有改動的硬規則

- molecular endpoint tolerance 仍為 **10 m / 0.01 km**。
- Missing 不等於 Clear/Zero。
- 不向下外插 pressure-level O₃。
- 不使用固定 O₃ profile。
- Formation 判斷不因 Glow 修正而被改寫。

## Regression

- R5.7.37 專項：9/9 PASS。
- 完整 working-tree regression：**533/533 PASS**。
- FULL-CLEAN 解壓後 regression：**533/533 PASS**。
- FULL-CLEAN：**506 個檔案成員，0 cache/pyc 污染**。

## Field Validation

**OPEN**。舊 R5.7.36 CASE 沒有 R5.7.37 新增的 ML137 O₃ / 2 m thermodynamic evidence，不能用離線補值冒充真實 FIELD PASS。請以 R5.7.37 跑新的 sunset/sunrise CASE。
