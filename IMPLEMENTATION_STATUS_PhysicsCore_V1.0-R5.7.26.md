# PhysicsCore V1.0-R5.7.26 Implementation Status

## 已完成

### Red-Light Availability

- [DONE] Reference Receiver sampling：Primary 0–40 km / Extended 40–100 km。
- [DONE] 4 / 5 / 8 / 12 km reference receiving heights。
- [DONE] −5° / 0° / +5° directions。
- [DONE] 550 / 575 / 600 / 650 / 700 / 750 nm 六波段保留。
- [DONE] finite-solar-disk DirectSolarFraction。
- [DONE] Gas / O₃ path。
- [DONE] CAMS aerosol path。
- [DONE] upstream CloudScene blocker evidence。
- [DONE] forecast-native 3-D precipitation/hydrometeor evidence。
- [DONE] Reference receiver 永不成為 Canvas。

### No-Canvas 語義

- [DONE] `SPECTRAL_AEROSOL_PATH = NOT_APPLICABLE`。
- [DONE] `SPECTRAL_CLOUD_PATH = NOT_APPLICABLE`。
- [DONE] `FULL_SPECTRAL_RT = NOT_APPLICABLE`。
- [DONE] `CLEAR_RED_PATH_NO_CANVAS` 與其他 no-Canvas context states。
- [DONE] Canvas geometry completeness guard：資料不足時保持 `CANVAS_AVAILABILITY_UNKNOWN`。
- [DONE] legacy physics score 在 no-Canvas 情境下明確失去 operational applicability。
- [DONE] summary/headline propagation。
- [DONE] CASE export 新增 reference evidence 與 summary。
- [DONE] Analysis Integrity 新增 no-Canvas semantic checks。

## 尚未完成／不屬於本版

- [PENDING FIELD VALIDATION] 真實 R5.7.26 CASE 驗證 Red-Light reference branch。
- [PENDING] `Unused Red-Light Potential` 的 Ground Truth calibration；目前不得稱 High/Medium/Low 機率。
- [PENDING] Glow / Twilight Glow 完整第三分支。
- [PENDING] Viewing Full Six-Band RT。
- [PENDING] Target Canvas optical truth 中 Bounded branch 真實 CASE 驗證。
- [PENDING] Genuine calibrated Tier-2 directional LUT（需外部 libRadtran/MYSTIC）。

## 目前分析主線

R5.7.26 完成後，分析功能應繼續往：

1. 真實 CASE 驗證 Red-Light Availability / no-Canvas headline；
2. Target Canvas Optical Truth / Response closure；
3. Tier-1 / genuine Tier-2 directional radiance；
4. Formation Brightness / Redness / Effective Area 時序；
5. Viewing Full RT；
6. Glow branch；
7. Photography Decision 與 Ground Truth calibration。

完整 Taiwan Firecloud System（GPS、地圖量測、衛星雲圖量測、Firecloud 3D、Event lifecycle 等）依使用者指定，待分析功能完善後再統一整理。

## Regression

- Working tree：**456 passed / 0 failed**。
- FULL-CLEAN ZIP 解壓後：**456 passed / 0 failed**。
