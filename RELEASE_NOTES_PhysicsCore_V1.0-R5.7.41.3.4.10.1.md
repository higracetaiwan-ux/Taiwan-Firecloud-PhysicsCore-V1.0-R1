# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.1

## 名稱
Twilight Glow Observer Aerosol Numeric Route Context

## 來源
直接延續 `V1.0-R5.7.41.3.4.10 FULL-CLEAN`。Science baseline 維持 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。

## Field evidence
`.3.4.10` TWS106 CASE：Twilight Glow 60.523 s；Observer Spectral Extinction 21.376 s 為 10-component profiler 第一名。Actual-CASE cProfile 進一步定位 `_integrate_view_aerosol()` 的重複 pandas row filtering / pressure-profile materialization 為主要成本。

## 變更
- `firecloud/viewing_spectral.py` 新增 `_prepare_aerosol_numeric_route_context()`。
- 每個 time/angle/direction route 一次建立 numeric CAMS aerosol records。
- 保存 native pressure-level geopotential / ext532 arrays、explicit six-band AOD、temporal provenance。
- 新增 `_integrate_view_aerosol_prepared()`，以相同 segment / interpolation / endpoint / partial semantics 積分。
- Shared Viewing runtime context 同時供 main Viewing 與 Twilight Glow 重用。

## 不變
不改 CAMS 原始值、AOD interpolation contract、532 nm vertical extinction interpolation、Glow 0.05 km lowest-endpoint tolerance、temporal evidence rules、六波段、Cloud/Precipitation/Gas/Rayleigh 物理、Formation、Photography、Shadow/Production COT。

## 驗證
- Targeted Viewing/Glow tests：19/19 PASS。
- Full regression：654/654 PASS（1 existing pandas FutureWarning）。
- TWS106 actual-CASE Glow targets：1092 rows，legacy/optimized `check_exact=True`。
- TWS106 main Viewing targets：585 rows，legacy/optimized `check_exact=True`。
- Field gate：OPEN；等待 `.3.4.10.1` CASE。
