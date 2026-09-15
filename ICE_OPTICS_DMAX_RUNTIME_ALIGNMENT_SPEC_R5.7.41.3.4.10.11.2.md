# Ice Optics Dmax Runtime Contract Alignment Spec — R5.7.41.3.4.10.11.2

## 目的

本版承接 `.10.11.1` 已通過的 Yang/Bi V2 authoritative source gate 與 Portable V1.1 驗證，
只修正 PhysicsCore 內部「診斷 runtime」仍殘留的舊 `r_eff` lookup 路徑，並把已驗證的 Portable
科學 artifact 與 lineage 資訊納入完整 release。Frozen Formation / Viewing / Twilight Glow science 完全不變。

## 問題來源

`.10.11.1` 已正式把 authoritative Ice LUT primary size coordinate 改為：

`habit + roughness + maximum_dimension_um + wavelength_nm`

Portable V1.1 evaluator 也已使用 Dmax lookup/interpolation。

但 `firecloud/ice_cloud_spectral_optics.py` 的 Phase-1 diagnostic runtime 仍存在：

- `_lookup_six_band_by_reff(...)`
- `ICE_EFFECTIVE_RADIUS_MISSING`
- `LINEAR_REFF_INTERPOLATION_WITHIN_LUT`

這會造成「authoritative/Portable 已 Dmax-first，但 PhysicsCore diagnostic runtime 仍 r_eff-first」的 contract split。

## `.10.11.2` 修正

### 1. Diagnostic runtime Dmax-first

改為：

`_lookup_six_band_by_dmax(...)`

允許：

- exact Dmax row
- 同一 habit + roughness 內 Dmax linear interpolation

禁止：

- Dmax extrapolation
- habit interpolation
- roughness interpolation
- `r_eff -> Dmax` 暗中轉換

### 2. Positive-IWP fail-close

Positive IWP 若無 calibrated/native Dmax：

`ICE_MAXIMUM_DIMENSION_MISSING`

`missing_reason = NO_NATIVE_OR_CALIBRATED_ICE_DMAX`

即使有 `ice_effective_radius_um` 也不得代替 Dmax。

### 3. r_eff 定位

`ice_effective_radius_um` 繼續保留為 diagnostic/mapping metadata，
但不參與六波段 authoritative group selection。

### 4. Integrity contract

CASE / Analysis Integrity 的 Ice Optics schema 現在要求：

- `ice_maximum_dimension_um`
- `primary_size_coordinate = maximum_dimension_um`

並持續要求：

- `physics_role = DIAGNOSTIC_ONLY_UNASSIGNED`
- `tau_synthesis_allowed = false`
- `formation_promotion_allowed = false`

### 5. Certified Portable artifact bundle

Release 內附已驗證 Portable V1.1 artifact 與：
- source manifest
- portable manifest
- contract
- reference vectors
- validation certification
- portable LUT serialization
- portable package SHA256

Portable ZIP SHA256：

`802d82b49cef4e20a4458bc50f063133a58b19fcfcb4e49941cc8ca16f7afd05`

注意：Portable LUT CSV 是 portable builder 的 canonical serialization；authoritative build manifest
保存的 source-build LUT SHA256 為 `d6a9b1be541044b2fc95c1794d3568e4a7183c35f66a9c37b8d265ebcd9743c5`。
兩者 byte hash 不要求相同，科學 records 已做 CSV↔JSON / Python↔JS parity 驗證。

## Frozen boundary

本版仍然：

- `physics_promotion_allowed = false`
- 不進 Production Formation
- 不進 Production Viewing
- 不改 Twilight Glow
- 不做 PSD/habit mixture/roughness climatology
- 不製造 `r_eff -> Dmax` mapping

下一階段才進 Phase 2 microphysics mapping。
