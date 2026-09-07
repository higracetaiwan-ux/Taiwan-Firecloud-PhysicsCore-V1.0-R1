# Taiwan Firecloud PhysicsCore V1.0-R5.7.22.1

## 目前版本重點

## R5.7.22.1 Route Invariance Hotfix

本版在 R5.7.22 Full Directional Cloud Scattering Geometry Contract 上修正 provider sampling route 與 runtime 太陽角度集合耦合的問題。

正式凍結：

- GFS / CAMS / Forecast 的 Reference Route 固定以太陽高度 **−2.0°** 的太陽方位建立。
- Provider spatial sampling distance lattice 固定依完整 **0°～−6°** PhysicsCore 路徑需求建立。
- 改變 runtime angle subset、或從 9-angle 擴充到 13-angle，不得旋轉或縮短既有 sampling corridor。
- 每個太陽高度仍使用自己的事件時間、太陽高度與太陽方位計算 Sun→Cloud 與 Tier-2 directional geometry。
- CASE 新增 `route_reference_contract.csv`，保存 reference angle、reference time、reference azimuth、route domain 與 invariance provenance。

此修正關閉 R5.7.21.1 / 未修正 R5.7.22 中因核心角度中點由 −2° 變成 −3°，導致 route bearing 約偏移 0.672° 的回歸。


R5.7.22 正式把 Tier-2 雲散射方向幾何由原本只依賴 `scattering_angle`，升級為完整的 target-local directional contract：

- `θ₀ = solar_zenith_deg`
- `θᵥ = view_zenith_deg`
- `Δφ = relative_azimuth_deg`
- `scattering_angle_deg` 僅保留為衍生診斷，不再是 production interpolation axis

核心火燒雲太陽高度維持：

`0, −0.5, −1, −1.5, −2, −2.5, −3, −3.5, −4, −4.5, −5, −5.5, −6°`

共 13 個角度。

## 核心架構

PhysicsCore 持續維持三個獨立問題：

- **Formation**：Sun → CloudBase，判斷火燒雲是否形成。
- **Viewing**：Cloud → Observer，判斷已形成的火燒雲是否看得到。
- **Glow**：獨立的大氣霞光分支，不取代雲底受光 Formation。

Formation 核心輸出仍分離為 Brightness、Redness、Effective Illuminated Area，不合併成單一 Formation Score。

## Tier-2 Full Directional Scattering

R5.7.22 production LUT 的核心插值維度為：

`COT × r_eff × θ₀ × θᵥ × Δφ`

六波段各自完整保留：

`550 / 575 / 600 / 650 / 700 / 750 nm`

### 方向幾何定義

- `θ₀`：Cloud → Sun 相對雲底當地天頂的夾角，範圍 0–180°。
- `θᵥ`：Cloud → Observer 相對雲底當地天頂的夾角，範圍 0–180°。
- `Δφ`：Cloud→Sun 與 Cloud→Observer 在雲底當地水平面的最小方位差，範圍 0–180°。
- `scattering_angle_deg`：Sun→Cloud incoming photon 與 Cloud→Observer outgoing photon 的夾角，只作診斷。

太陽方向會先由觀測點 local ENU 轉為 ECEF，再投影到每個 target cloud 的 local ENU；不再把觀測點太陽角度直接當成每個雲底的 local angles。

### cloud thickness 的角色

`cloud_thickness_km` 仍保留於 target / CASE 幾何與雲體證據，但 R5.7.22 不再把它當成純雲散射 LUT 的 production interpolation axis。

## Production LUT 安全閘門

R5.7.22 不接受舊版 scattering-angle-only LUT 直接升級成 production LUT。

Production LUT 必須提供：

- full directional `θ₀ / θᵥ / Δφ` 網格
- 六波段完整覆蓋
- multiple-scattering 校準來源
- full-hemisphere 0–180° 支援聲明
- RT solver provenance
- QC PASS
- validation reference
- CSV SHA256

舊 R5.7.19/R5.7.20 LUT 只保留歷史 regression 用途，不能啟動 R5.7.22 production solver。

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

本版文件：

- `RELEASE_NOTES_PhysicsCore_V1.0-R5.7.22.md`
- `IMPLEMENTATION_STATUS_PhysicsCore_V1.0-R5.7.22.md`
- `TIER2_DIRECTIONAL_SCATTERING_GEOMETRY_SPEC_R5.7.22.md`
