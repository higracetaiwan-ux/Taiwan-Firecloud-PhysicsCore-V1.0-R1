# Release Notes — V1.0-R5.7.41.3.4.10.7

## Viewing↔Glow Shared Hydrometeor Context

本版是 runtime-only exact-reuse release。Main Viewing 對每個 exact `(time, solar_altitude_deg)` route snapshot 建立一次 native hydrometeor context，Twilight Glow 直接重用相同 RWMR/SNMR/GRLE cells 與 horizontal-support groups，不再第二次從 DataFrame 重新建構。

### 不變的科學契約

- 17-point Cloud→Observer LOS 不變。
- pressure levels / RWMR / SNMR / GRLE 不變。
- Qext、粒徑、密度與六波段 grey precipitation semantics 不變。
- Missing / partial / resolved-zero fail-close semantics 不變。
- Formation、Viewing、Glow、Photography、COT、Earth Shadow 均未重新設計。

### 驗證

- Prepared vs direct precipitation evidence exact-equivalent。
- Glow supplied-context reuse gate PASS。
- Targeted + adjacent tests：33/33 PASS。
- Full working-tree regression：683/683 PASS（396 + 287 分組），1 個既有 pandas FutureWarning。

### Field baseline

2026-09-14 sunrise TWS091 `.10.6`：
- Analysis Integrity: 70 PASS + 1 NOT_APPLICABLE（71 checks）
- CASE Integrity: 32/32 PASS
- Glow Observer Precipitation: 8.250749 s
- Glow Observer Spectral Extinction: 2.740815 s
- Glow total: 29.901809 s

`.10.7` release status：FIELD TEST CANDIDATE。
