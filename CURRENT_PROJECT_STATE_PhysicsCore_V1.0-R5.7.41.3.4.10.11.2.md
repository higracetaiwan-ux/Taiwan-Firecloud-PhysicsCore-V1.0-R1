# Taiwan Firecloud PhysicsCore — Current Project State

> Version: **V1.0-R5.7.41.3.4.10.11.2**  
> Internal: `1.0.0-R5.7.41.3.4.10.11.2`  
> Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`

## Current release status

- `.10.10.2 = FIELD PASS`
- `.10.11 = authoritative source intake gate`
- `.10.11.1 = AUTHORITATIVE ICE LUT BUILD PASS / PORTABLE V1.1 VALIDATION PASS`
- `.10.11.2 = DMAX RUNTIME CONTRACT ALIGNMENT + CERTIFIED PORTABLE BUNDLE`

## 已完成的 authoritative Ice LUT

使用者本機 Yang/Bi V2 shortwave archive 已實跑：

- published MD5 PASS：`2fb9bbab2c2c735a869c863a680e2f70`
- source files：27/27 PASS
- spectral targets：162/162 PASS
- LUT rows：30,618
- six-band Dmax groups：5,103
- duplicate keys：0
- non-finite rows：0
- `overall_status = PASS`
- `release_ready = true`
- authoritative primary size coordinate：`maximum_dimension_um`
- `source_geometry_policy = ROWWISE_SOURCE_GEOMETRY_PRESERVED_DMAX_FIRST`

Portable V1.1 也已獨立驗證：

- package structure：PASS
- internal SHA256 / byte size：PASS
- Node reference vectors：12/12 PASS
- Python ↔ JavaScript randomized parity：100/100 PASS
- TypeScript strict compile：PASS
- Portable ZIP SHA256：`802d82b49cef4e20a4458bc50f063133a58b19fcfcb4e49941cc8ca16f7afd05`

## `.10.11.2` 為何必要

檢查 `.10.11.1-TEST` 後發現：
authoritative builder 與 WINDY Portable 已改成 Dmax-first，但
`firecloud/ice_cloud_spectral_optics.py` 的 PhysicsCore Phase-1 diagnostic runtime
仍用舊 `_lookup_six_band_by_reff`。

本版已將 PhysicsCore diagnostic runtime 同步改為 Dmax-first，
避免在 HBR/SBR 等 source-row-derived `r_eff` 隨 wavelength 變化時使用錯誤 cross-band key。

## Runtime semantics

Positive IWP 要有：

1. complete native vertical support
2. calibrated/native `maximum_dimension_um`
3. ice habit
4. surface roughness
5. calibrated six-band LUT

才可在 diagnostic branch 計算：

`tau_ice(lambda) = IWP * k_ext(lambda)`

若只有 `ice_effective_radius_um` 而沒有 Dmax：

`ICE_MAXIMUM_DIMENSION_MISSING`

不得自行把 r_eff 換算成 Dmax。

## Release bundle

完整程式內保留已驗證 Portable science artifact under：

`firecloud/data/ice_optics/`

但 **不會自動啟用成 Production Ice Optics**；runtime LUT 仍需明確設定，
避免在 Phase 2 microphysics mapping 完成前改變既有 production physics。

## Frozen science

完全不變：

- Formation = Sun → CloudBase
- Viewing = Cloud → Observer
- Twilight Glow = independent third branch
- 550/575/600/650/700/750 nm
- Canvas 0–40 / 40–100 km
- Dynamic Corridor / REZ
- Earth Shadow / Penumbra
- Production vs Shadow COT
- Missing != Clear != Zero

## 下一步

進入 **Ice Optics Phase 2 — Forecast Microphysics Mapping Contract**：

1. 定義 forecast/native ice size evidence 可提供什麼（Dmax、PSD、r_eff、IWC/IWP）。
2. 明確禁止未驗證的 `r_eff -> Dmax` 單值轉換。
3. 建立 PSD → Dmax distribution mapping contract。
4. 再處理 habit mixture 與 roughness strategy。
5. 最後才形成 bulk `k_ext / SSA / g` 與 `IWP -> tau_ice` production candidate。

Production promotion gate 仍未開啟。
