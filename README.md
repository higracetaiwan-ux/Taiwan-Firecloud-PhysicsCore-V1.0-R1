# Taiwan Firecloud PhysicsCore V1.0-R5.7.21.1

## 目前版本重點

本版將核心火燒雲 Formation 分析太陽高度正式擴充為 **0°～−6°、每 0.5° 一個取樣點，共 13 個角度**。

核心角度：

`0, −0.5, −1, −1.5, −2, −2.5, −3, −3.5, −4, −4.5, −5, −5.5, −6°`

## 核心架構

PhysicsCore 持續維持三個獨立問題：

- **Formation**：Sun → CloudBase，判斷火燒雲是否形成。
- **Viewing**：Cloud → Observer，判斷已形成的火燒雲是否看得到。
- **Glow**：獨立的大氣霞光分支，不取代雲底受光 Formation。

Formation 核心輸出仍分離為 Brightness、Redness、Effective Illuminated Area，不合併成單一 Formation Score。

## 六波段

完整保留：

`550 / 575 / 600 / 650 / 700 / 750 nm`

其中 575 nm 持續保留 O₃ Chappuis 吸收的重要角色。

## Tier-2

程式已具備 calibrated scattering LUT ingestion、domain validation 與 4-D solver infrastructure，但 production response 仍需要真實、通過 QC 的 calibrated LUT 才能啟用；沒有 LUT 時不會生成假的 Tier-2 radiance。

## 跨區域時間

延續 R5.7.21：

- 依座標自動解析 IANA timezone。
- 物理時刻另外保存 UTC。
- 同一 UTC 瞬間的太陽幾何不受顯示時區影響。
- 可用日本、沖繩或其他區域作 REAL_CANVAS regression testing。

## 執行與部署

主要 Streamlit 入口：

`app.py`

完整依賴請見：

`requirements.txt`

版本變更請見：

`RELEASE_NOTES_PhysicsCore_V1.0-R5.7.21.1.md`
