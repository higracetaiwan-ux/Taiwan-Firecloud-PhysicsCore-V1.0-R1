# R5.7.41.3.4.10.8 — Viewing→Glow Molecular Context Handoff

## 目的

移除 Twilight Glow 在 Main Viewing 已建立 gas runtime context 後，仍再次對完整 `gas_profile_route_snapshots` 做 pandas copy/groupby/numeric conversion 的重複成本。

## Exact handoff

Glow 從 shared Viewing `gas_contexts` 取得 exact route 的 prepared z/T/P arrays，並從同一 `gas_groups` 只重建 Glow molecular boundary 所需的：

- `actual_lo`
- `anchor_lo`
- `pressure_lo`

其餘 Rayleigh、local molecular state、near-surface boundary diagnostics 仍使用原 `.10.2` prepared helper。

## Fail-close

只有當每一條 Viewing gas route 都存在 `valid=True` 且結構完整的 prepared gas context 時才使用 handoff。任何 route invalid / missing / malformed 時，整體退回 `.10.2` `_prepare_glow_molecular_numeric_routes(gas_profiles)`。

因此 Rayleigh/T/P readiness 不會被 HITRAN O2/H2O/O3 species readiness 綁定。

## 不變的科學契約

- 六波段 550/575/600/650/700/750 nm 不變。
- HITRAN / O3 XSC / gas LUT 不變。
- Rayleigh cross section 不變。
- Cloud→Observer geometry 不變。
- near-surface tolerance / quantization 不變。
- Missing ≠ Clear ≠ Zero 不變。
- Formation / Viewing / Twilight Glow 三分架構不變。

## Actual-case benchmark

2026-09-14 TWS091 sunrise `.10.7` CASE：53,404 gas-profile rows，39 exact routes，2691 distance profiles。

- legacy molecular prep median：3.537930 s
- shared handoff median：0.115728 s
- speedup：約 30.57×
- distances / z / T / P / actual_lo / anchor_lo / pressure_lo：**0 differences**

這是 local same-input benchmark，不預先視為 Field speedup。
