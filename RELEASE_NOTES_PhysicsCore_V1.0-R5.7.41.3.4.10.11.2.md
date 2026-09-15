# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.11.2

## 名稱

**Dmax Runtime Contract Alignment + Certified Portable Bundle**

## 修正摘要

`.10.11.1` 的 authoritative Yang/Bi V2 builder 與 WINDY Portable V1.1 已經是 Dmax-first，
但 PhysicsCore Phase-1 diagnostic runtime 還保留舊 r_eff-first lookup。
本版完成三者一致化。

### 主要改動

- diagnostic runtime lookup：`r_eff` → `maximum_dimension_um`
- exact / linear Dmax interpolation 僅限同 habit + roughness
- 禁止 Dmax extrapolation
- 禁止 r_eff → Dmax substitution
- positive IWP 缺 Dmax → `ICE_MAXIMUM_DIMENSION_MISSING`
- CASE Integrity 要求 Dmax-first contract
- bundled certified Portable V1.1 provenance/artifact
- Frozen production science 無任何門檻或權重變更

## Authoritative / Portable validation baseline

- Yang/Bi archive MD5 PASS
- 27/27 source PASS
- 162/162 spectral targets PASS
- 30,618 LUT rows
- 5,103 six-band Dmax groups
- Portable V1.1 ZIP SHA256: `802d82b49cef4e20a4458bc50f063133a58b19fcfcb4e49941cc8ca16f7afd05`
- Production promotion: **NO**

## 後續

下一版開始 Phase 2 microphysics mapping；在 mapping 被科學驗證前，
不得以 forecast r_eff、climatology、RH、CF 或固定 habit 製造 Dmax/τ。
