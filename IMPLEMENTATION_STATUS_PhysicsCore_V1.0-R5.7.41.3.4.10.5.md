# Implementation Status — V1.0-R5.7.41.3.4.10.5

## 狀態

- `.10.4 Gas Spectroscopy State Memo`：**FIELD PASS**。
- `.10.5 Viewing / Glow Route Group Direct Reuse`：**IMPLEMENTED / REGRESSION PASS / FIELD TEST CANDIDATE**。
- Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`，未改。

## `.10.5` 實作

- 移除 Viewing/Glow spectral builder 每 target 的 aerosol/gas route boolean slicing。
- 保留 exact route-group key：time + angle + direction。
- target-distance bound 仍在原 integrators 內完成。
- 沒有更動 aerosol / gas / cloud / precipitation 公式。

## 驗證

- Actual TWS134 Glow 1092 targets：exact A/B PASS。
- Actual TWS134 Main Viewing 585 targets：exact A/B PASS。
- Targeted：23/23 PASS。
- Working-tree full regression：670/670 PASS。
- Final FULL-CLEAN fresh-extract：**670/670 PASS**。
