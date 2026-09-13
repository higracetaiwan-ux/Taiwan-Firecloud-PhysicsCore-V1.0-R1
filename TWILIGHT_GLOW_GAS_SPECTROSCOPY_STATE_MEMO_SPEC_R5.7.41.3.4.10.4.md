# R5.7.41.3.4.10.4 — Viewing / Glow Gas Spectroscopy State Memo Spec

## 目的

降低 `build_viewing_spectral_extinction()` 中重複 `_sigma_fast()` spectroscopy lookup 的 runtime，完全不改 Gas RT 科學結果。

## Field 依據

R5.7.41.3.4.10.3 TWS134：

- Glow Observer Spectral Extinction：8.533 s，為 Glow 第一大戶。
- cProfile：`_integrate_view_gas()` 約 2.77 s；`_sigma_fast()` 約 157,248 calls。
- 1092 Glow targets / 8736 gas segments 中，exact `(temperature_k, pressure_hpa)` 僅 264 組跨 route 重複。

## 實作

只修改 `firecloud/viewing_spectral.py` runtime orchestration：

1. 對 prepared spectroscopy LUT 建 deterministic content signature。
2. 建 process-local `gas_sigma_cache`。
3. cache key：
   `LUT-content-signature + gas + wavelength_nm + exact temperature_k + exact pressure_hpa`
4. cache miss：仍呼叫原 `_sigma_fast()`。
5. cache hit：直接使用先前完全相同的 sigma。
6. `sigma × density × path` 仍在每一 segment 內、依 O2→H2O→O3 原順序執行並累加。

## 明確不改

- `gas_rt.py`
- HITRAN / O3 XSC / Runtime LUT
- nearest real T/P state selection
- O2 / H2O / O3 number density
- curved-Earth observer LOS
- gas profile interpolation
- 六波段 550/575/600/650/700/750 nm
- Missing / partial / resolved semantics
- Formation / Viewing / Glow science
- Shadow / Production COT

## Exact-equivalence gates

- LUT content 相同 → signature 相同；sigma payload 改變 → signature 不同。
- `_integrate_view_gas()` cache off vs cache on exact tuple equality。
- 同 state 重複 segment 的 `_sigma_fast()` call count 必須下降。
- TWS134 actual gas evidence 1092 targets：**1092/1092 exact**。
- TWS134 isolated full observer spectral A/B：CSV SHA256 exact。
