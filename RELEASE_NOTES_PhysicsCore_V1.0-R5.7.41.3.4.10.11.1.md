# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.11.1

## 名稱

**TAMU V2 Source Contract Correction + Dmax-First Ice LUT**

## 修正

- 修正 canonical habit `HC` 對 Yang/Bi V2 實際 source directory `hollow_column` 的 resolver。
- 移除錯誤的「同一 Dmax 之 Volume 必須跨 wavelength invariant」hard failure。
- HBR/SBR wavelength-dependent source-row geometry 改為合法 authoritative metadata，並保留 spread diagnostic。
- Authoritative LUT key 改為 `habit + roughness + Dmax + wavelength`。
- `effective_radius_um` 降為 source-row-derived diagnostic/mapping coordinate，不再作 cross-band release key。
- Portable WINDY contract 升為 `FIRECLOUD_ICE_OPTICS_PORTABLE_V1_1`。
- Portable evaluator 改用 Dmax exact/linear interpolation；禁止 Dmax extrapolation 與未驗證的 r_eff→Dmax substitute。
- 新增 positive-IWP 無 Dmax fail-close：`ICE_MAXIMUM_DIMENSION_MISSING`。
- 新增 `ice_optics_portable_sdk_v1_1/`。

## 真實 source 驗證

- HBR sample：74844 rows / 396 wavelengths / 189 Dmax；source QA PASS；六目標波段 6/6 PASS。
- SBR sample：74844 rows / 396 wavelengths / 189 Dmax；source QA PASS；六目標波段 6/6 PASS。
- HBR single-habit six-band LUT：1134 rows = 189×6；Node portable parity PASS 6 vectors。

## 明確未做

- 未把 r_eff 自動轉成 Dmax。
- 未提前做 PSD / habit mixture / climatological size prior。
- 未推進 Ice Optics 到 Production Formation / Viewing / Twilight Glow。
- 未修改 frozen science baseline。

## Science baseline

`R5.7.41.2_SHADOW_COT_AB_FROZEN`
