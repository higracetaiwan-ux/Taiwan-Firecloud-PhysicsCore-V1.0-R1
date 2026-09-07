# PhysicsCore V1.0-R5.7.21.1 實作狀態

## 本版目標

將 Taiwan Firecloud 核心火燒雲太陽高度分析範圍從 `0°～−4°` 正式擴充到 `0°～−6°`，並保持 0.5° 解析度。

## 已完成

- `FIRECLOUD_CORE_ANGLES_DEG` 擴充為 13 個角度。
- `CORE_FIRECLOUD_ANGLES_DEG` immutable contract 同步更新。
- `ModelConfig.solar_angles_deg` 預設 runtime grid 同步更新。
- Operational/Core eligibility 自動涵蓋新增的 −4.5°、−5°、−5.5°、−6°。
- UI 核心時間軸標題與角度說明同步更新。
- 無正式 selected angle 時的診斷顯示角度搜尋範圍擴充為 −6°～0°。
- CASE 既有 per-angle 表格會自然增加新增四個角度的資料列；不另造平行 schema。
- Late Glow 分類仍可在 −4°～−6° 與 Core Formation 同時存在，兩個物理分支不互相取代。
- 新增專屬回歸測試，驗證 13-angle、−6° 下界與 Late Glow overlap。

## 未變更

- Formation / Viewing / Photography Decision 分層。
- 六波段與 O₃ Chappuis 575 nm 契約。
- Shared Geometry、Earth Shadow、折射架構。
- Target Optical Truth、Tier-1 response、Tier-2 LUT/solver production gate。
- CAMS/GFS provider 與 payload integrity 規則。

## 驗收重點

新 CASE 應確認：

1. `summary.csv` 出現 13 個核心太陽高度。
2. `event_time_contract.csv` 對應 13 個事件時間點。
3. Formation / Viewing / Tier-2 readiness 等 per-angle summary 均涵蓋到 −6°。
4. −4.5°～−6° 若因 Earth Shadow 而沒有 direct solar ray，應保留為物理 N/A/blocked evidence，不得視為資料缺失。
5. CASE Integrity 與 Analysis Integrity 仍需正常 PASS。

## 測試結果

完整 regression：**372 passed / 0 failed（18.51 秒）**。
