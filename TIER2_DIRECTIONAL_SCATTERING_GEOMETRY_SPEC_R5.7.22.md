# R5.7.22 Tier-2 Full Directional Cloud Scattering Geometry 規格

## 目的

多重散射雲輻射不能只用單一 `scattering_angle` 唯一決定。

R5.7.22 將 production 雲散射方向幾何正式定義為：

`Rλ = f(τ, r_eff, θ₀, θᵥ, Δφ, λ)`

## 方向角定義

### θ₀：Solar Zenith

`solar_zenith_deg`

Cloud → Sun 與雲底當地向上天頂的夾角。

- 0°：太陽在雲底正上方
- 90°：當地幾何水平
- >90°：太陽方向位於當地水平面以下

Firecloud 的地球曲率／高雲／雲底受光幾何可能需要 >90° 的方向，因此資料結構允許 0–180°。

### θᵥ：View Zenith

`view_zenith_deg`

Cloud → Observer 與雲底當地向上天頂的夾角。

地面觀測者位於雲下時通常會有 `θᵥ > 90°`。

### Δφ：Relative Azimuth

`relative_azimuth_deg`

Cloud→Sun 與 Cloud→Observer 在 target-local 水平面的最小方位差。

範圍：0–180°。

若其中一個方向近乎垂直而方位角退化，程式會：

- 將 `Δφ` canonicalize 為 0°
- 同時保存 `azimuth_degeneracy_state`

## Scattering Angle

`scattering_angle_deg`

定義為：

Sun→Cloud incoming photon 與 Cloud→Observer outgoing photon 的夾角。

- 0°：forward scattering
- 180°：backward scattering

R5.7.22 起它只作 **derived diagnostic**，不再是 production LUT interpolation axis。

## 座標轉換

事件太陽角度最初由觀測點取得。

R5.7.22 使用：

1. Observer local ENU 太陽方向
2. 轉成 ECEF unit vector
3. 因太陽近似無限遠，方向在 Canvas 範圍視為平行
4. 投影到每個 target cloud 的 local ENU
5. 取得 target-local `θ₀ / solar azimuth`
6. Cloud→Observer ECEF 向量再轉 target-local ENU
7. 取得 `θᵥ / view azimuth / Δφ`

## Production LUT interpolation axes

固定：

- `cot`
- `effective_radius_um`
- `solar_zenith_deg`
- `view_zenith_deg`
- `relative_azimuth_deg`

六波段：

- 550 nm
- 575 nm
- 600 nm
- 650 nm
- 700 nm
- 750 nm

## cloud thickness

`cloud_thickness_km` 仍保留在：

- Canvas target geometry
- cloud body evidence
- CASE
- 未來 sensitivity study

但 R5.7.22 不把它當成純雲散射 LUT 的必要 interpolation axis。

## Production calibration 要求

必須聲明：

- full directional geometry
- 0–180° hemisphere support
- multiple scattering enabled
- solver family/version
- cloud optics source
- phase-function source
- response definition / units
- QC PASS
- validation reference
- CSV SHA256

舊 scattering-angle-only LUT 不得自動升級。
