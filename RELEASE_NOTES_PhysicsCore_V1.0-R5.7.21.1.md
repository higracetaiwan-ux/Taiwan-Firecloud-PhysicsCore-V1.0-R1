# Taiwan Firecloud PhysicsCore V1.0-R5.7.21.1 發行說明

## 版本主題

**太陽高度核心分析範圍擴充：0° → −6°，0.5° 取樣**

## 主要變更

- 核心 Formation 太陽高度由原本 `0°～−4°` 擴充為 `0°～−6°`。
- 固定取樣角度改為 13 點：
  - `0.0°`
  - `−0.5°`
  - `−1.0°`
  - `−1.5°`
  - `−2.0°`
  - `−2.5°`
  - `−3.0°`
  - `−3.5°`
  - `−4.0°`
  - `−4.5°`
  - `−5.0°`
  - `−5.5°`
  - `−6.0°`
- Formation、Viewing、Tier-2 readiness、Tier-2 foundation、LUT domain 與 CASE 證據全部使用同一套 13-angle runtime grid。
- UI 核心形成時間軸與診斷選角範圍同步擴充到 −6°。
- −4°～−6° 的 Late Glow 診斷分類仍保留，但不再是「未執行的外部角度」；它現在可與 Core Formation 在同一物理時間點並存，Formation 與 Glow 的語意仍保持分離。
- 航海曙暮光 −7° 以下仍不納入核心 Firecloud runtime。

## 相容性與科學邊界

- 不修改 Formation / Viewing 分離架構。
- 不修改六波段 `550/575/600/650/700/750 nm`。
- 不修改 Target Optical Truth、Tier-1、Tier-2 solver 數學、calibrated LUT production gate。
- Missing、Clear、Zero、Not Applicable 的既有語意不變。
- 不使用任何假 LUT 或假光學厚度。

## 效能影響

角度數由 9 增加到 13，因此每事件的 per-angle 幾何、RT、Canvas 與 Tier-2 readiness 工作量會增加。GFS/CAMS 仍維持事件級預取與快取，不會因角度數增加而重新下載 13 次。

## 驗證

- 新增 R5.7.21.1 太陽高度範圍契約測試。
- 既有 timeline/runtime angle tests 已更新為 13-angle contract。
- 完整回歸測試結果請見 `IMPLEMENTATION_STATUS_PhysicsCore_V1.0-R5.7.21.1.md`。
