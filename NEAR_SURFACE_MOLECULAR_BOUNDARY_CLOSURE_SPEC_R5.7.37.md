# R5.7.37：近地層分子邊界閉環規格

## 目的

R5.7.37 處理 Twilight Glow `Scatter→Observer` 分子消光路徑在最低原生 pressure-level 以下、但仍高於地表的短距離垂直缺口。2026-09-10 台灣 R5.7.36 CASE 在 `−6° / 100 km / scatter altitude 3.75 km` 出現 3 個 rows，LOS 第一段 midpoint 約 74.6 m AGL，而最低原生 pressure-level 約 96 m AGL，形成約 21 m 缺口。

## 凍結規則

既有最低端點 tolerance **固定維持 0.01 km（10 m）**。R5.7.37 不把 tolerance 改成 20、25、50 m，也不以更粗的垂直量化掩蓋缺口。

## 新增證據鏈

只有以下證據同時存在時，才建立近地分子 anchor：

- Open-Meteo `surface_pressure`
- Open-Meteo `temperature_2m`
- Open-Meteo `relative_humidity_2m`
- CAMS native `ozone`，model level 137

ML137 壓力以 ECMWF 最低 hybrid layer 的 full-level 比例 `0.998815 × surface_pressure` 推導；高度以 surface pressure 與 2 m temperature 的 hypsometric relation 求得，正常約 10 m AGL。H₂O 由 2 m T/RH 與 ML137 pressure 推導；O₂ 維持既有乾空氣組成；O₃ 僅使用 CAMS native ML137 kg/kg 轉換為 mole fraction / number density。

## 嚴格 Missing 規則

任何必要證據缺失時：

- 不建立 near-surface anchor；
- 不把 1000 hPa O₃ 向地面外插；
- 不使用固定 O₃ 或標準 O₃ profile；
- 不用 RH、cloud cover 或其他代理值製造 O₃；
- Rayleigh / gas species 依既有規則保持 `PARTIAL/MISSING`。

## RT 行為

若 LOS sample 位於 `ML137 anchor ≤ z < lowest pressure-level`，則由兩個真實 anchor 做 bracket interpolation。這不是 endpoint extrapolation，因此不消耗或放寬 10 m tolerance。

如果 sample 仍低於所有真實 anchor，才回到原有最低 endpoint snap，而且仍要求量化後 gap `≤0.01 km`。

## CASE provenance

Observer extinction export 新增：

- `glow_observer_pressure_level_only_raw_max_gap_km`
- `glow_observer_near_surface_boundary_anchor_segment_count`
- `glow_observer_near_surface_boundary_bridge_segment_count`
- `glow_observer_near_surface_boundary_anchor_min_km`
- `glow_observer_near_surface_boundary_contract`

即使 bridge 成功，CASE 仍保留「若只有 pressure-level 時原本 gap 多大」的證據，不會把原問題洗掉。

## Integrity

新增：

- `NEAR_SURFACE_MOLECULAR_BOUNDARY_ANCHOR_PROVENANCE`
- `NEAR_SURFACE_MOLECULAR_BOUNDARY_FROZEN_10M_TOLERANCE`
- `NEAR_SURFACE_MOLECULAR_BOUNDARY_BRIDGE_PROVENANCE`

其中第二項會硬性確認 tolerance 仍為 `0.01 km`。

## 驗證狀態

程式與 synthetic regression 可驗證 21 m pressure-level-only gap 在存在 ML137 真實 bracket 時被解析，但舊 R5.7.36 CASE 本身沒有 ML137 O₃ 與新增的 2 m T/RH request，因此不能宣稱 R5.7.37 FIELD PASS。必須以 R5.7.37 重新產生新 CASE。
