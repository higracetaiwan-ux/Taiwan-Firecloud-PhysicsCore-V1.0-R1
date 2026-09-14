# R5.7.41.3.4.10.9 — Viewing→Glow Gas Spectroscopy Cache Handoff

## 目的

移除 Twilight Glow Volume Assembly 對 Main Viewing 已經計算過的 HITRAN/O3 LUT spectroscopy state 再次呼叫 `_sigma_fast()` 的重複成本。

## Shared cache source

Main Viewing `viewing_spectral.py` 自 `.10.4` 建立：

- `gas_sigma_cache`
- `gas_lut_signatures`

`.10.9` 只將這兩個既有 runtime objects handoff 到 Twilight Glow；不另建不同的 spectroscopy 規則。

## Exact key

`(lut_content_signature, gas_name, wavelength_nm, exact_temperature_k, exact_pressure_hpa)`

只有完整 exact key 命中才重用 sigma。

## Glow gas path 保持不變

- Cloud/Scatter→Observer gas segments 不變。
- T/P interpolation 不變。
- O2/H2O/O3 mole fraction 與 number density 不變。
- 六波段 550/575/600/650/700/750 nm 不變。
- 每段 `sigma × density × path` 浮點運算順序不變。
- O2→H2O→O3 與 wavelength loop 順序不變。
- Missing / unresolved semantics 不變。

## Fail-close

只要 shared cache 或 exact route LUT signature 不存在，即呼叫原本 `_sigma_fast()`；不跨 LUT signature 共用，不用近似 T/P key，不從其他 route 猜測。

## Runtime telemetry

Glow runtime stats 新增：

- `shared_gas_sigma_cache_available`
- `shared_gas_sigma_cache_entry_count_before_volume`
- `shared_gas_sigma_cache_entry_count_after_volume`
- `shared_gas_sigma_cache_reused`
- contract：`R574134109_VIEWING_GLOW_GAS_SPECTROSCOPY_CACHE_HANDOFF`

## Actual-case exact benchmark

2026-09-14 TWS091 sunrise `.10.8` CASE：1092 Glow volumes。

- legacy gas-species paths：約 2.844 s
- shared spectroscopy cache：約 1.073 s
- speedup：約 2.65×
- 1092/1092 Python exact equality
- Main Viewing cache 約 450 entries；Glow 完成約 11,394 entries

這是 local same-input benchmark，不預先宣稱 Field speedup。
