# Taiwan Firecloud PhysicsCore V1.0-R5.7.22.1 發行說明

## 版本主題

**Route Invariance Hotfix / Fixed Reference Route + Per-Angle Physics Geometry**

本版是 R5.7.22 的正式 hotfix。目標是讓 GFS、CAMS 與 Forecast 的空間取樣網格，不再因核心太陽角度集合改變而旋轉或縮短。

## 問題來源

R5.7.21 的核心角度為 0°～−4°，程式使用角度集合中點 −2° 的太陽方位建立共用 Route。R5.7.21.1 擴充到 0°～−6° 後，中點變成 −3°，因此同一事件的 reference route 被旋轉約 0.672°。

在 2026-09-08 日本 REAL_CANVAS CASE 中，此差異會讓 100 km、440 km、長距離 CAMS route 的取樣位置產生公里級偏移，並改變部分 native cloud evidence 與 Tier-2 readiness。

## 正式修正

### 1. 固定 Reference Route

新增固定契約：

`REFERENCE_ROUTE_SOLAR_ALTITUDE_DEG = -2.0`

GFS / CAMS / Forecast route 一律使用 −2° 事件時刻的太陽方位建立，不再使用 runtime angle list 的中點。

### 2. 固定 Provider Spatial Sampling Domain

Provider sampling distance lattice 固定依完整 0°～−6° PhysicsCore 路徑需求建立。即使只分析 0°～−4° 或其他 subset，也不會縮短 route domain。

目前正式 route domain 仍為 1180 km。

### 3. Per-Angle Physics 保持獨立

每個太陽高度仍各自保存並使用：

- event time
- solar altitude
- solar azimuth
- Sun→Cloud geometry
- Earth shadow / DirectSolarFraction
- six-band RT
- Formation / Viewing
- Tier-2 θ₀ / θᵥ / Δφ

因此新增 −4.5°～−6° 只增加 per-angle ray / RT / Formation evidence，不會重畫 provider sampling corridor。

### 4. CASE 新增 Route Contract 證據

新增：

`route_reference_contract.csv`

內容包含：

- reference solar altitude
- reference local/UTC time
- reference azimuth
- route domain max
- route point count
- runtime angle count / range
- route invariance state
- per-angle solar geometry independent state

Analysis Integrity 新增 route reference bearing / domain consistency 檢查；CASE Integrity 也要求新版本封存 `route_reference_contract.csv`。

## 實際 Regression 驗證

使用 2026-09-08、33.376 / 130.31、日本 sunset 的既有 R5.7.21 CASE 作 A/B：

- route points：207 vs 207
- max distance：1180 km vs 1180 km
- point_id：完全一致
- distance：最大差 0
- direction offset：最大差 0
- bearing：最大差 0
- latitude：最大差約 7.1×10⁻¹⁵°
- longitude：最大差約 2.8×10⁻¹⁴°

因此先前約 0.672° 的 route drift 已關閉。

## 不變項目

本版沒有改動：

- R5.7.22 Full Directional Scattering LUT V2 axes
- COT × r_eff × θ₀ × θᵥ × Δφ
- scattering angle diagnostic 定位
- Formation / Viewing 分離
- Glow 獨立分支
- 六波段 550/575/600/650/700/750 nm
- Target Optical Truth
- Tier-1
- calibrated LUT production gate
- 科學權重與決策門檻

## 測試

完整 regression：

**386 passed / 0 failed**
