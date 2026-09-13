# Twilight Glow Observer Precipitation Horizontal-Support Ray Reuse — R5.7.41.3.4.10.3

## 目的
消除 Cloud→Observer native hydrometeor precipitation integration 的重複 LOS 幾何計算。

## 問題
舊版對同一 target、同一 horizontal support 上的每個 pressure-level hydrometeor cell，都重算一次完全相同的 17-point curved-Earth observer LOS。

## 新方法
以 `(direction, support_start_km, support_end_km)` 將垂直 hydrometeor cells 分組：

- 每個 horizontal support 只計算一次原本相同的 17-point observer LOS。
- 仍逐 pressure level 判定垂直交會。
- 仍逐 pressure level 累積 extinction 與 path length。
- 原 cell order、Missing/partial semantics、六波段 grey Tier-1 precipitation optics 完全保留。

## 不變的 science
- RWMR / SNMR / GRLE native hydrometeor fields
- Qext=2 Tier-1 large-particle model
- rain/snow/graupel assumed radii/densities
- 17-point Cloud→Observer LOS sampling
- all pressure levels
- `Missing != Clear != Zero`
- surface precipitation rate never becomes tau
- Formation / Viewing separation
- six wavelengths 550/575/600/650/700/750 nm

## Verification
- Grouped integrator vs legacy exact equality
- Missing-intersection semantics exact
- Resolved-zero no-intersection semantics exact
- ray sampler call count reduced from per vertical cell to per horizontal support
- synthetic multi-level benchmark ≈2.46× in isolated integrator
