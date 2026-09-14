# Field Validation — R5.7.41.3.4.10.7 — 2026-09-14 Sunrise / TWS091 日月潭朝霧碼頭

## 結論

**`.10.7 Viewing↔Glow Shared Hydrometeor Context = FIELD PASS`**。

## Integrity

- Analysis Integrity：70 PASS + 1 NOT_APPLICABLE（71 checks）
- CASE Integrity：32/32 PASS
- `NEAR_SURFACE_MOLECULAR_BOUNDARY_BRIDGE_PROVENANCE = NOT_APPLICABLE`：本次 `bridged_rows=0`，屬正常狀態。

## Runtime A/B

同事件 `.10.6 → .10.7`：

- Glow Observer Precipitation：8.250749 s → **2.407172 s**（**−70.825% / 3.428×**）
- Glow total：29.901809 s → **22.970400 s**（**−23.181%**）
- Glow Lookup Context Prep：7.456110 s → 6.647128 s
- Glow Volume Assembly：8.073043 s → 7.226424 s
- Glow Observer Spectral：2.740815 s → 3.087648 s

Runtime detail 明確記錄：`hydrometeor_context_reused=True; hydrometeor_context_count=13`。

## Science / provider 判讀

`.10.6` 與 `.10.7`：

- GFS native run：同為 2026-09-13 12Z / lead 9h；native GRIB inventory、pressure-profile 3-D、native cloud 3-D 均一致。
- DWD ICON secondary：同為 2026-09-13 12Z / lead 10h。
- CAMS：同為 2026-09-13 00Z / lead 21h。
- `v1_viewing_precipitation_evidence.csv`：**byte-identical**。這是 `.10.7` 直接受影響的 Viewing/Glow hydrometeor path 證據，證明 shared context 未改 precipitation science。

67 個 `v1_*.csv` 中有 12 個不同，但差異主要由 Open-Meteo surface forecast 重新網路抓取造成：request keys 相同，但抓取時間不同，`forecast_raw.csv` 的 surface cloud/visibility/precipitation/T/RH 內容更新，連帶影響 Red-Light 與部分 Glow evidence。這不是 `.10.7` shared hydrometeor context 的 science drift。

## Verdict

`.10.7` Field gate 關閉：**FIELD PASS**。
