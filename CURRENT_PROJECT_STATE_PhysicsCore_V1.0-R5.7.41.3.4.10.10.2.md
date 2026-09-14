# Taiwan Firecloud PhysicsCore — Current Project State

> 版本：**V1.0-R5.7.41.3.4.10.10.2**  
> Internal：`1.0.0-R5.7.41.3.4.10.10.2`  
> 名稱：**UI Information Architecture Cleanup**  
> Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`  
> Release state：**REGRESSION PASS / FIELD RETEST CANDIDATE**

## 本版定位

本版只整理 Streamlit 主畫面的資訊架構，不修改 Frozen Science。主畫面改為優先顯示現行版本、Frozen Science baseline、Formation / Viewing / Twilight Glow 三軌、資料來源、Ice Optics 狀態與背景分析階段；完整版本歷史移入折疊區與既有 release 文件。

## UI 整理

- 頁首移除數十版串接式 changelog，改為版本 / Science Baseline / 現行里程碑。
- 新增「本版更新與版本歷史」折疊區。
- 資料來源改為 Open-Meteo / NOAA GFS / DWD ICON / CAMS / 六波段的結構化說明。
- 模型輸出層改為 Formation、Viewing、Twilight Glow 三欄獨立說明。
- Cloud Optical Physics、Ice Cloud Spectral Optics、Frozen Science、最近版本、歷史科學、Runtime/Provider Hotfix 分開折疊。
- 背景分析預設顯示人類可讀階段；Job ID / attempt / PID 移至「Runtime 詳細資訊」。

## Ice Optics / WINDY 架構

`.10.10.1` 的 decoupled architecture 完整保留：PhysicsCore 負責 Ice Engine/LUT authoring/calibration/validation/release；WINDY 匯入 `FIRECLOUD_ICE_OPTICS_PORTABLE_V1` 後本地執行，不依賴 PhysicsCore runtime。

## Frozen Science audit

相對 `.10.10.1`，16 個核心 science files 全部 byte-identical。Formation / Viewing / Twilight Glow / gas / aerosol / cloud optics / Dynamic Corridor / REZ / Earth Shadow / COT / Missing semantics 均未修改。

## Regression

- UI targeted tests：4/4 PASS
- full working-tree regression：752/752 PASS
- final FULL-CLEAN fresh-extract regression：752/752 PASS
- Python compile：PASS
- Streamlit browser smoke：本執行環境未安裝 `streamlit` CLI，因此未在此容器啟動 UI server；不影響 pytest / source validation 結果。
- existing warning：1 個 pandas FutureWarning（既有）

## 下一步

1. 用本版跑一次正式 PhysicsCore CASE，確認 Analysis Integrity / CASE Integrity 與 Ice portable artifacts。
2. UI 整理 Field PASS 後，回到 authoritative Ice LUT science build，不再擴大 UI/效能修改線。
