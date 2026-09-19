# Taiwan Firecloud PhysicsCore V1.0 — Current Project State

## 現行 Engineering / QA 版本
`1.0.0-R5.7.41.3.4.10.30.21`

## Science baseline
`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## 最新 FIELD baseline
`R5.7.41.3.4.10.30.20 FIELD PASS`

FIELD CASE：`TWS100 合歡山北峰 / 2026-09-20 sunrise / WARM_PRODUCTION`。
`.10.30.20` CASE：201 members、CRC PASS、manifest 199/199 present/hash/size PASS、case integrity 140/140 PASS、analysis integrity 0 FAIL、CAMS spectral/O3 payload validity 均 1.0。

## Step 3Q
**Step 3Q.21 — Band25 Historical Source-Domain / Runtime-Weight Scope Qualification + CAMS Bounded Reattach Observation Window**

正式 QA 狀態：
`PASS_FAIL_CLOSED_FU96_PRIMARY_BAND_FORWARD_RECONSTRUCTION_INPUTS_QUALIFIED_RRTMG_FINE_GRID_AND_EXACT_BAND24_25_REALIZATION_UNRECOVERED`

### 本版完成
- 新增 `firecloud/fu96_rrtmg_band25_historical_scope.py`。
- Fu96 lineage source-domain constraint：single-scattering 計算具有 **200 wavelength samples**、六個 solar primary bands；但 exact 200 wavelength coordinates 尚未恢復。
- pin 現行 AER RRTMG_SW runtime scope：
  - commit `286e84ed14f61e2279ba819f4ce512a30b48f0b3`
  - `rrtmg_sw_cldprop.f90` blob `71a1d4c86a19fe2de1af7e5682562688da25cde0`
  - `rrtmg_sw_init.f90` blob `1236caef0b669f96cb0b2405c723dc2664703595`
- 正式區分：3 µm Dge linear interpolation 是 **post-table runtime lookup**，不是 wavelength-domain historical spectral pre-averaging realization。
- 正式區分：current RRTMG `rwgt` / `sfluxref` g-point reduction 不得替代 unrecovered Fu96 cloud-table historical solar/discrete weights。
- 新增 `tools/verify_fu96_rrtmg_band25_historical_scope.py`。
- CASE integrity 已要求 Step 3Q.21 新增的 true/false scope guards。

### CAMS runtime hardening
`.10.30.20 FIELD` 首次實際觸發 adaptive same-request-ID reattach，但兩個 native 3-D aerosol roles 都在 initial timeout 後又耗用完整 reattach deadline 並再次 timeout，造成 core runtime 約 1086.8 s。

`.10.30.21` 將 reattach 改為 bounded observation window：
- initial production deadline 210 s → default reattach observation 73.5 s
- initial deadline 90 s → default reattach observation 31.5 s
- 短 deadline 不會被放大
- 可由 `FIRECLOUD_CAMS_DEFERRED_REATTACH_DEADLINE_SECONDS` 明確覆寫，但不得超過 initial deadline
- reattach-only、same request-ID、no fresh submit、Missing/fail-close 全部不變

新 contract：
`R5.7.41.3.4.10.30.21_BOUNDED_SAME_REQUEST_ID_REATTACH_OBSERVATION_WINDOW_V1`

### Fail-close 維持
- `FU96_LINEAGE_EXACT_200_WAVELENGTH_NODE_GRID_RECOVERED=False`
- `RRTMG_FINE_SPECTRAL_GRID_REALIZATION_RECOVERED=False`
- `RRTMG_BAND25_HISTORICAL_INTRABAND_INPUT_BUNDLE_COMPLETE=False`
- `RRTMG_BAND25_EXACT_REPRODUCTION_PASS=False`
- `RRTMG_BAND24_EXACT_REPRODUCTION_PASS=False`
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`
- `TAU_ICE_PRODUCTION_ALLOWED=False`
- `PRODUCTION_ICE_OPTICS_READY=False`
- `physics_promotion_allowed=False`
- Step 3R：`BLOCKED`

## QA
- CAMS / Step3Q targeted：`12/12 PASS`
- Step3Q lineage：`76/76 PASS`
- Full regression collection：`1003 tests`
- Full regression：`1003/1003 PASS`（12 批完整覆蓋；1 existing pandas FutureWarning）

## 下一步
Step 3Q.22 優先找回 Band25 exact 200-node wavelength coordinates、pre-averaging source optical samples、historical solar spectrum / discrete weights、fine-grid interpolation realization。若沒有 authoritative provenance 或 deterministic exact reproduction，不得升 `RRTMG_BAND25_EXACT_REPRODUCTION_PASS`。
