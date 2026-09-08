# Taiwan Firecloud PhysicsCore V1.0-R5.7.23 發行說明

## 版本主旨

**Runtime Hardening + Genuine Liquid-Cloud Full Directional Calibration Pipeline V3**

本版從 **R5.7.22.1 ACCEPTED BASELINE** 延伸，不更改既有科學權重或 Formation / Viewing / Glow 分離。

## 1. Runtime Hardening

針對長時間 TEST 曾停留於 CAMS AOD、`−3° 重建 0.5 km 垂直雲柱`、`−5.5° 建立氣體狀態`，但重新 TEST 後可能因前輪 persistent cache 而成功的情況，本版新增：

- Cold / Warm / Resume 三種執行契約
- per-job Cold Test cache isolation
- provider cache provenance
- atomic cache commit
- CAMS production global ADS single-flight
- worker independent heartbeat
- true stage trace
- RSS / peak RSS resource telemetry
- CASE runtime execution / cache / stage / resource 四份證據

因此之後可以區分「本輪新算」與「沿用前次資料」，也能判斷 UI 最後顯示字樣是否真的是耗時 stage。

## 2. Genuine liquid-cloud directional calibration

Production response 固定：

`Rλ = f(COT, r_eff, θ₀, θᵥ, Δφ, λ)`

六波段：550 / 575 / 600 / 650 / 700 / 750 nm。

新增：

- CASE → REAL liquid target evidence → calibration domain
- libRadtran/MYSTIC geometry adapter
- unit incident irradiance normalization
- liquid cloud profile generator
- cloud-only spherical MYSTIC input renderer
- batch runner（含 render-only 安全模式）
- external result collector
- V3 calibrated sample QC 與 provenance contract
- V3 production package / runtime validation

## 3. V3 calibration gate

每個 sample 必須保存：

- `response_factor`
- `response_factor_std`
- `photon_count`
- `sample_qc_state`
- `solver_run_id`

Manifest 另外強制：

- solver adapter contract
- incident irradiance reference
- atmospheric coupling
- surface boundary
- reference cloud base/top
- vertical sensitivity validation reference
- geometry mapping validation reference
- minimum photon count
- maximum MC relative / absolute error
- calibration scope
- domain-spec SHA256

普通 CSV 即使寫上 `CALIBRATED` 也不能越過 production gate。

## 4. Double-counting 防護

Calibration LUT 只描述：

`Unit incident beam → Liquid Cloud → Directional Radiance`

不包含：

- O₃ / gas absorption
- Rayleigh
- aerosol
- Earth Shadow

這些仍由 Formation 的 `Eλ,base = F☉ × Tλ,path` 負責。

因此 runtime 才做：

`Lλ,observer = Eλ,base × Rλ,cloud`

## 5. Genuine LUT 狀態

本建置環境沒有 `uvspec`，因此**沒有生成或安裝 genuine calibrated production LUT**。

Production 必須保持 blocked；本版沒有 synthetic LUT。

## 6. 相容性

保持：

- R5.7.22.1 Reference Route / 1180 km route contract
- 13-angle：0°→−6° / 0.5°
- 六波段完整保留
- `cloud_thickness_km` 不是 production scattering interpolation axis
- Legacy scattering-angle-only LUT 不可 production 使用
