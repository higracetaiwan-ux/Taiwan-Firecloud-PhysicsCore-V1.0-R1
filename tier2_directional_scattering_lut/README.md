# R5.7.22 Full Directional Tier-2 LUT 格式

本目錄提供 **格式模板**，不是 calibrated LUT，也不得直接當作 production physics 使用。

CSV 必要欄位：

- `phase`
- `wavelength_nm`
- `cot`
- `effective_radius_um`
- `solar_zenith_deg`
- `view_zenith_deg`
- `relative_azimuth_deg`
- `response_factor`
- `calibration_state`
- `lut_version`

六波段固定為：`550 / 575 / 600 / 650 / 700 / 750 nm`。

Production manifest 必須聲明 full-hemisphere directional support、multiple scattering、RT solver provenance、QC、SHA256 與 validation reference。
