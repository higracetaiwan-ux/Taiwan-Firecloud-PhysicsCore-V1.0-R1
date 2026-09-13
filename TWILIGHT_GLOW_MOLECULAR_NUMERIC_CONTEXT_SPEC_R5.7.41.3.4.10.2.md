# Twilight Glow Molecular Numeric Route Context — R5.7.41.3.4.10.2

## 目的
降低 `TWILIGHT_GLOW_COMPONENT_VOLUME_ASSEMBLY` 中同一 time/angle/direction molecular route 被 1092 個 Glow volumes 重複轉換與掃描的成本。

## Runtime-only 變更
- 新增 `_prepare_glow_molecular_numeric_routes()`。
- 每 route/distance 一次保存排序後的 native T/P vertical arrays。
- 一次保存 lower-boundary metadata：actual lowest level、ML137/surface READY anchor、pressure-level-only lowest anchor。
- Rayleigh observer path、local molecular state、lower-boundary diagnostics 改讀 numeric route context。
- HITRAN species path仍使用既有 prepared gas context；Rayleigh/local T/P readiness 不與 O2/H2O/O3 species readiness綁定。

## 凍結不變
- Rayleigh cross section 與六波段 550/575/600/650/700/750 nm。
- curved-Earth Scatter→Observer geometry。
- `GLOW_OBSERVER_MOLECULAR_BOUNDARY_TOLERANCE_KM = 0.01 km`。
- 1 m boundary quantization contract。
- near-surface ML137 + surface bridge semantics。
- HITRAN O2/H2O/O3 physics。
- Missing ≠ Clear ≠ Zero。
- Formation / Viewing / Glow independence、Photography、Shadow/Production COT。

## Actual CASE exact-equivalence
TWS134 2026-09-13 sunset：1092 Glow volumes。
- legacy vs prepared Rayleigh：1092/1092 exact。
- legacy vs prepared local molecular state：1092/1092 exact。
- legacy vs prepared boundary diagnostics：1092/1092 exact（NaN-aware）。
- 三 helper runtime：4.0718 s → 0.2971 s，約 13.7×；此為離線 helper benchmark，不作 Field speedup 宣稱。

## Field gate
下一個 `.3.4.10.2` CASE 應主要檢查：
1. `TWILIGHT_GLOW_COMPONENT_VOLUME_ASSEMBLY` 是否明顯低於 `.3.4.10.1` TWS134 的 25.414 s；
2. `TWILIGHT_GLOW_COMPONENT_LOOKUP_CONTEXT_PREP` 不應因 context preparation 反向大幅增加；
3. Analysis / CASE Integrity 必須維持 PASS；
4. science outputs 不得因 runtime context 改變。
