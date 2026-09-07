# Tier-2 Full Directional Scattering Runtime

此目錄只接受 **R5.7.22 Full Directional** production LUT。

需要同時放置：

- `tier2_directional_scattering_lut.csv`
- `tier2_directional_scattering_lut_manifest.json`

正式插值軸固定為：

`COT × r_eff × θ₀ × θᵥ × Δφ`

其中：

- `θ₀ = solar_zenith_deg`
- `θᵥ = view_zenith_deg`
- `Δφ = relative_azimuth_deg`
- `scattering_angle_deg` 僅為衍生診斷，不再是 production interpolation axis。
- `cloud_thickness_km` 仍保留於 target/CASE 幾何證據，但不是本 LUT 的 interpolation axis。

舊 R5.7.19/R5.7.20 的 scattering-angle-only LUT 不會被自動升級，也不能啟動 R5.7.22 production solver。
