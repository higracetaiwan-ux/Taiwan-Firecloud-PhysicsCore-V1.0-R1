# R5.7.22.1 Route Invariance 規格

## 目的

將三種不同問題永久分離：

1. **Provider Spatial Sampling Grid**：GFS / CAMS / Forecast 從哪裡取樣。
2. **Per-Angle Sun→Cloud Geometry**：每個太陽高度的入射光路。
3. **Cloud→Observer Directional Scattering Geometry**：θ₀ / θᵥ / Δφ 與 scattering angle diagnostic。

分析角度的增加或刪減，不得自動重畫 Provider Spatial Sampling Grid。

## 固定 Reference Route

正式 reference angle：

`−2.0°`

Reference route bearing：

`bearing = solar_azimuth_at_minus_2_deg + direction_offset`

目前 direction offsets：

`−5° / 0° / +5°`

## 固定 Spatial Sampling Domain

Spatial route domain 依完整 PhysicsCore 0°～−6° 路徑需求推導，但不依 runtime subset 改變。

因此：

- runtime = 0°～−4° → route grid 不縮短
- runtime = 0°～−6° → 同一 route grid
- runtime 缺少 −2° → 仍獨立求 −2° reference crossing

## Per-Angle Geometry

每個 runtime angle 仍獨立計算：

`time(angle)`

`solar_azimuth(angle)`

`Sun→CloudBase geometry(angle)`

`DirectSolarFraction(angle)`

`six-band RT(angle)`

`Tier-2 θ₀ / θᵥ / Δφ(angle)`

Reference Route 不取代 per-angle physics；它只固定 provider evidence lattice。

## CASE 證據

`route_reference_contract.csv` 必須保存：

- contract ID
- reference solar altitude
- reference time local / UTC
- reference azimuth
- route domain max
- route point count
- runtime angle count / min / max
- route invariance boolean
- per-angle geometry independent boolean

## Regression 原則

同一事件在只改變 runtime angle range 時，舊角度的 provider route 應保持：

- point_id 相同
- distance 相同
- direction offset 相同
- bearing 相同
- lat/lon 相同（容許浮點誤差）

新增角度只允許增加 per-angle 計算量，不允許改變既有 provider spatial evidence。
