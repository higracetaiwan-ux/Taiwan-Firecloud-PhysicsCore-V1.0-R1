# GFS Hourly Native Valid-Time Alignment Hotfix — R5.7.41.3.4.10.9.5

## 目的

修正 NOAA GFS 0.25° native `pgrb2` / diagnostic-only `pgrb2b` 的 forecast-hour resolver。舊 resolver 對所有 forecast lead 一律以 3 小時取整，會在 GFS 實際已有逐小時輸出的前 120 小時內，錯選較早或較晚的 native state。

TWS106 2026-09-14 sunset 已實證舊版 `.10.9.4` 在事件 10:00–10:26 UTC 使用 `06Z f003`（valid 09:00 UTC / 17:00 local），而不是可用的 `06Z f004`（valid 10:00 UTC / 18:00 local）。

## 修正契約

- forecast hour `f000–f120`：依逐小時 cadence 選最近有效時次；
- `f123–f384`：依 3 小時 cadence 選最近有效時次；
- cycle availability / 5 h latency / frozen analysis clock 規則不變；
- primary `pgrb2` 與 diagnostic `pgrb2b` 必須使用同一 resolver；
- 不修改 CLWMR/ICMR threshold；
- 不修改 native cloud-column reconstruction；
- 不修改任何 Formation / Viewing / Twilight Glow / COT / Red-Light 科學規則。

## Provenance

GFS native request audit 新增：

- `gfs_target_time_utc`
- `gfs_valid_time_utc`
- `gfs_valid_time_offset_seconds`
- `gfs_forecast_cadence_policy`

`GFS_NATIVE_VALID_TIME_ALIGNMENT` Analysis Integrity gate 驗證：

1. resolved valid time = run + forecast hour；
2. audit offset 與 target/valid time 差一致；
3. f000–f119 最近逐小時時次誤差 ≤ 1800 s；
4. f120+ 跨 cadence 邊界／3-hourly domain 誤差 ≤ 5400 s；
5. cadence policy 明確為 `HOURLY_F000_F120_THEN_3HOURLY_F123_F384`。

## Frozen science

Science baseline 維持 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。本 hotfix 是 provider temporal alignment，不得被解讀成新的雲物理、COT、Formation、Viewing 或 Glow 規則。
