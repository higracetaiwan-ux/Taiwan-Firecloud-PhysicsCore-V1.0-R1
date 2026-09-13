# Taiwan Firecloud PhysicsCore — Current Project State

## 現行版本
**V1.0-R5.7.41.3.4.10.3**

Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## 最近 Field 結果
- `.3.4.9.2` Red-Light precipitation ray reuse：FIELD PASS。
- `.3.4.10.1` Glow observer aerosol numeric context：FIELD PASS。
- `.3.4.10.2` Glow molecular numeric context：FIELD PASS。
  - TWS134 Volume Assembly 25.414 s → 6.047 s。
  - Glow total 62.652 s → 42.331 s。
- `.3.4.10.3`：Field-Test Candidate，目標為 Observer Precipitation 14.309 s。

## 下一個 Field gate
在 TWS134 / 2026-09-13 sunset 測 `.3.4.10.3`：
`TWILIGHT_GLOW_COMPONENT_OBSERVER_PRECIPITATION` 應由約 14.31 s 明顯下降；其餘 science state 不得因 runtime scheduling 改變。

## 尚未關閉的主要工作
- Glow runtime：Observer Precipitation、Observer Spectral Extinction、Lookup Context Prep。
- Red-Light：Spectral RT 為目前主要內部 component。
- Shadow COT：繼續收集正案例 Ground Truth；仍不得 promotion。
- genuine Tier-2 directional scattering：需外部 libRadtran/MYSTIC。
- Glow multiple scattering / absolute radiometric calibration：後續。
