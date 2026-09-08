# Taiwan Firecloud PhysicsCore V1.0-R5.7.23 實作狀態

## 正式來源基線

**V1.0-R5.7.22.1 ACCEPTED BASELINE**。

R5.7.23 不改寫既有 Formation / Viewing / Glow、Route Invariance、Earth Shadow、六波段、Target Optical Truth 與 Missing 語義。

## A. Runtime Hardening：已完成

- [x] `WARM_PRODUCTION / COLD_ISOLATED_TEST / RESUME_SAME_JOB`
- [x] per-job isolated provider cache namespace
- [x] provider cache provenance
- [x] GFS / CAMS / Open-Meteo / AQ / DWD dynamic cache atomic commit
- [x] CAMS production default global ADS single-flight
- [x] 5 秒 analysis-worker independent heartbeat
- [x] true stage trace
- [x] RSS / peak RSS / process / DataFrame telemetry
- [x] UI 顯示 stage elapsed + RSS
- [x] CASE：`runtime_execution_contract.csv`
- [x] CASE：`runtime_cache_provenance.csv`
- [x] CASE：`runtime_stage_trace.csv`
- [x] CASE：`runtime_resource_telemetry.csv`

## B. Genuine Liquid-Cloud Full Directional Calibration：已完成工程鏈

- [x] REAL Tier-2-ready liquid target selector
- [x] CASE / foundation+readiness → COT / r_eff / θ₀ / θᵥ / Δφ domain planner
- [x] `tools/derive_tier2_liquid_directional_domain_from_case.py`
- [x] 六波段 full-directional job grid
- [x] `firecloud/tier2_libradtran_mystic_adapter.py`
- [x] target-local geometry → uvspec/MYSTIC adapter
- [x] unit incident irradiance normalization
- [x] liquid `wc_file` reference profile generator
- [x] cloud-only MYSTIC renderer（不重算 Gas / Rayleigh / aerosol / Earth Shadow）
- [x] spherical MYSTIC batch runner CLI
- [x] `mc.rad.spc` / `mc.rad.std.spc` collector
- [x] V3 per-sample QC：response std / photon count / QC state / solver run id
- [x] V3 manifest provenance gate
- [x] domain spec SHA256 gate
- [x] external genuine result → production directional LUT package builder
- [x] runtime V3 LUT validation

## C. Genuine calibrated LUT 的真實狀態

本建置環境目前**沒有 `uvspec` / libRadtran 執行檔**。

因此本版可以產生、渲染、驗證 genuine calibration jobs，但不能在此環境執行真正 MYSTIC Monte-Carlo 全 job grid。

正式狀態仍必須是：

`CALIBRATED DIRECTIONAL LUT NOT INSTALLED`

以及 calibration bundle：

`NOT_YET_GENERATED_EXTERNAL_RT_REQUIRED`

**本版沒有 synthetic response 冒充 genuine LUT。**

## D. Production V3 install 前仍需外部證據

即使 external MYSTIC jobs 全部完成，production install gate 仍要求：

- genuine solver version
- Mie/cloud-optics provenance
- phase-function provenance
- unit incident irradiance contract
- cloud-only atmospheric coupling contract
- black surface boundary
- reference cloud base / top
- cloud vertical-sensitivity validation reference
- geometry-mapping validation reference
- minimum photon count
- maximum MC relative / absolute error
- calibration scope
- exact domain-spec SHA256
- 每 sample solver run id 與 QC PASS

## E. 尚未在本建置環境完成的物理資料產品

- [ ] genuine libRadtran/MYSTIC 大規模 calibration execution
- [ ] genuine calibrated liquid-cloud production LUT
- [ ] production LUT install
- [ ] 同一 REAL_CANVAS CASE 安裝後 Tier-2 deterministic response 驗收

這些不是程式缺漏，而是必須由真正 external RT 執行結果提供；不得由 synthetic fixture 取代。

## F. 後續主線（非本次 release blocker）

- GFS 09Z / 10Z temporal interpolation contract
- ice-cloud genuine directional LUT
- cloud-thickness sensitivity study（除非證明必要，不升格 LUT axis）
