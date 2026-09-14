# R5.7.41.3.4.10.9.6 — GFS Native Near-field Source Attribution + Timeline Valid-Time Provenance

## 目的

本版只新增／修正診斷證據鏈，不改任何 Frozen PhysicsCore 科學規則。

TWS106 `.10.9.5` 正式 CASE 已證明 GFS hourly valid-time hotfix 生效：事件 0° 10:00:21 UTC 使用 06Z f004（10:00 UTC），offset −21.746 s，Integrity PASS。但 0–100 km native condensate / native TCDC 仍全部為 0，而現場 Ground Truth 有大量低雲。

因此本版需要回答：

1. 0–100 km 的零值是在 GFS 解碼後 pressure-level source 就已經為零，還是進入 voxel interpolation / `1e-7 kg/kg` envelope threshold 後才消失？
2. `.10.9.4/.10.9.5` Observer Timeline 把同一個 GFS provider state 在 13 個太陽角度重用後，以 angle analysis time 當作多個 native snapshot time；這是 provenance 語意錯誤，必須改成 provider `gfs_valid_time_utc`。
3. 因台灣秋季短生命期積雲可能在日落前約 2 小時發展、日落前後減弱，Observer Timeline 診斷窗擴展至 T−180→T+60，但仍不得成為 forecast physics input。

## 新增 source-attribution artifacts

- `v1_gfs_native_nearfield_source_levels.csv`
- `v1_gfs_native_nearfield_source_summary.csv`

資料直接來自已下載／已解碼的 GFS pressure-level route fields，位於 native voxel interpolation **之前**。

逐 pressure level 保留：
- CLWMR / ICMR / total condensate
- TCDC
- RH / temperature
- geopotential-derived AGL altitude
- run / forecast hour / target time / provider valid time / valid-time offset
- nearest 0.25° route-grid sampling provenance

condensate 狀態必須分離：
- `SOURCE_CONDENSATE_EXACT_ZERO`
- `SOURCE_CONDENSATE_POSITIVE_BELOW_ENVELOPE_THRESHOLD`
- `SOURCE_CONDENSATE_AT_OR_ABOVE_ENVELOPE_THRESHOLD`
- `SOURCE_CONDENSATE_MISSING`

因此 `Missing != Zero != below-threshold positive`。

## Timeline native-time provenance 修正

Native timeline matching 優先使用 `gfs_valid_time_utc`，不得使用 angle-local `time` 偽裝成 provider snapshot time。

新增欄位：
- `native_provider_valid_time`
- `native_time_basis`

正式 GFS 路徑必須標：
`PROVIDER_GFS_VALID_TIME_UTC`

Legacy/unit-test 資料才可 fallback：
`ANGLE_ANALYSIS_TIME_LEGACY_FALLBACK`

## Timeline window

- T−180 → T+60
- 5-minute cadence
- 0–100 km
- coarse route interpolation 沿用既有 Open-Meteo route contract
- 不新增 provider request
- native temporal interpolation = 禁止
- provider-valid native evidence只有在 ±180 s 內才可 handoff
- −6°之後仍為 `POST_MINUS6_DIAGNOSTIC_ONLY`

## Integrity

新增／強化：
- `GFS_NATIVE_NEARFIELD_SOURCE_ATTRIBUTION`
- `GFS_NATIVE_NEARFIELD_SOURCE_ZERO_VS_THRESHOLD_VISIBLE`
- `GFS_NATIVE_NEARFIELD_SOURCE_SUMMARY`
- `OBSERVER_ENVIRONMENT_TIMELINE_NATIVE_VALID_TIME_PROVENANCE`
- timeline window contract 改為至少 T−180→T+60

## Frozen guards

以下全部不變：
- Formation = Sun→CloudBase
- Viewing = Cloud→Observer
- Twilight Glow 獨立第三分支
- 550/575/600/650/700/750 nm
- Canvas 0–40 / 40–100 km
- Dynamic Corridor / REZ
- Production COT / Shadow COT 語意
- `Missing != Clear != Zero`
- 不得由 RH/CF 造 condensate / τ / COT
- source diagnostic 不得 promotion Formation / Viewing / Glow
