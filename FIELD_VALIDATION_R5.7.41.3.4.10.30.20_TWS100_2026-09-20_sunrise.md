# FIELD VALIDATION — Taiwan Firecloud PhysicsCore V1.0

## 版本
- Program version: `1.0.0-R5.7.41.3.4.10.30.20`
- Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`
- CASE: `2026-09-20 sunrise`
- Site: `TWS100 合歡山北峰`
- Runtime mode: `WARM_PRODUCTION`
- FIELD 結論: **PASS**

## CASE Archive Integrity
- ZIP members: 201
- `case_archive_manifest.csv`: 199 artifacts
- 另外 2 個 archive 自身成員：
  - `case_archive_manifest.csv`
  - `case_integrity_audit.csv`
- ZIP CRC: PASS
- Manifest present: 199/199
- SHA256: 199/199 PASS
- Byte size: 199/199 PASS
- `case_integrity_audit.csv`: **140/140 PASS**

CASE ZIP SHA256:

`9d726930a146698b159d3999f0a8922cb99aabf56f6609313e48f29e317cd2f9`

## Analysis Integrity
`analysis_integrity_audit.csv`:
- PASS: 128
- WARN: 6
- ALLOWED_EMPTY: 4
- NOT_APPLICABLE: 3
- FAIL: **0**

WARN / ALLOWED_EMPTY 主要來自：
- 本次 Formation 沒有 eligible Canvas，因此 Viewing target 為空。
- CAMS native 3-D aerosol long-range coverage 未 ready，Missing 保持 Missing。
- pgrb2b diagnostic probe 為空，但不改寫 Formation / target COT。
- target-dependent spectral table 因 no-canvas 合法為空。

這些狀態均未構成 CASE corruption 或 science promotion。

## Formation 結果
13 個 solar-angle rows（-6° → 0°）全部：
- `primary_canvas_state = ABSENT`
- `extended_canvas_state = ABSENT`
- `core_score_eligible = False`
- `physics_score = NaN`
- `data_completeness = 0.0`

這是「NO CANVAS」物理結果，不是資料毀損。

主要 red-light path：
- -6° ~ -5°：`NO_DIRECT_RED_ACCESS`
- -4.5° ~ -2.5°：多為 `RED_LIGHT_PATH_PARTIAL`
- -2°：`RED_LIGHT_PATH_CONFLICT`
- -1.5° ~ -1°：`RED_LIGHT_PATH_PARTIAL`
- -0.5° ~ 0°：`RED_LIGHT_PATH_ATTENUATED`

因沒有 Canvas，不能把 red-light availability 誤升格成 Firecloud Formation。

## CAMS / O3
### O3
- `CAMS_O3_ROUTE_HANDOFF`: PASS
- O3 route rows: 53,495
- `CAMS_O3_ROUTE_PAYLOAD_VALIDITY = 1.0`
- `CAMS_O3_QUALITY_MISSING_FRACTION = 0.0`

### Spectral aerosol
- `CAMS_AEROSOL_SPECTRAL_PAYLOAD_VALIDITY = 1.0`
- temporal provenance:
  - exact = 1.0
  - bounded fallback = 0.0
  - missing = 0.0
- `SPECTRAL_COLUMN_AOD` 使用 `AEROSOL_SCATTERING_COLUMN_PROPERTIES` exact-source reuse。
- provider elapsed for exact reuse = 0。

## `.10.30.18.2` Adaptive Same-Request-ID Reattach FIELD Exercise

本次 CASE 第一次實際 FIELD 走到 `.10.30.18.2` adaptive reattach branch。

### PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE
- initial ADS request ID:
  `9e945105-d226-4439-aa29-02bf12a42935`
- initial state:
  `CAMS_ADS_RUNNING_GRACE_EXCEEDED`
- `TIMEOUT_DEFERRED`
- `deferred_reattach_attempted = True`
- `deferred_reattach_count = 1`
- reattach request ID 與 original request ID 相同
- reattach 後仍為 `TIMEOUT_DEFERRED`

### NATIVE_AEROSOL_532NM_PRESSURE_LEVEL
- initial ADS request ID:
  `f839f0a3-d3f4-49fd-9ac0-46221d948f00`
- initial state:
  `CAMS_ADS_RUNNING_GRACE_EXCEEDED`
- `TIMEOUT_DEFERRED`
- `deferred_reattach_attempted = True`
- `deferred_reattach_count = 1`
- reattach request ID 與 original request ID 相同
- reattach 後仍為 `TIMEOUT_DEFERRED`

### FIELD 判定
已 FIELD 驗證：
- timeout 後進入 adaptive reattach branch
- 保存 original ADS request ID
- same-request-ID reattach
- 沒有 fresh resubmit
- 第二次仍 timeout 時維持 Missing / fail-close
- 不製造 synthetic native 3-D aerosol

尚未 FIELD 驗證：
- initial timeout → same-request-ID reattach → provider 成功 → harvest

因此：
- `ADAPTIVE_REATTACH_BRANCH_FIELD_EXERCISED = True`
- `ADAPTIVE_REATTACH_FAIL_CLOSE_FIELD_PASS = True`
- `ADAPTIVE_REATTACH_SUCCESSFUL_HARVEST_FIELD_PASS = False / NOT_YET_EXERCISED`

## Step 3Q.20 / Band25 FIELD Evidence
CASE 內正式 contract：
`FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_20`

確認：
- `FU96_PRIMARY_BAND_EQ39_COEFFICIENT_INPUT_SET_RECOVERED = True`
- `FU96_PRIMARY_BAND_FORWARD_MODEL_EXECUTABLE = True`
- `FU96_SOLAR_COEFFICIENT_REPLICATION_90_OF_90_QUALIFIED = True`
- `RRTMG_BAND25_PINNED_REFERENCE_GRID_46_NODES = True`
- `RRTMG_BAND25_FORWARD_REPRODUCTION_HARNESS_READY = True`
- `RRTMG_BAND25_DIRECT_PRIMARY_CONTROL_RESIDUAL_TOPOLOGY_QUALIFIED = True`

Fail-close 正確保留：
- `RRTMG_BAND25_HISTORICAL_INTRABAND_INPUT_BUNDLE_COMPLETE = False`
- `RRTMG_FINE_SPECTRAL_GRID_REALIZATION_RECOVERED = False`
- `RRTMG_BAND24_EXACT_REPRODUCTION_PASS = False`
- `RRTMG_BAND25_EXACT_REPRODUCTION_PASS = False`
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE = False`
- `TAU_ICE_PRODUCTION_ALLOWED = False`
- `PRODUCTION_ICE_OPTICS_READY = False`
- `physics_promotion_allowed = False`

`.10.30.20` contract 中 Step 3Q.17 修正過的 co-albedo weighting 也保持：
- linear: `sum(alpha_lambda*beta_lambda*S_lambda*dLambda) / sum(beta_lambda*S_lambda*dLambda)`
- log: `exp(sum(ln(alpha_lambda)*beta_lambda*S_lambda*dLambda) / sum(beta_lambda*S_lambda*dLambda))`

沒有退回 solar-only weighting。

## Runtime
- `TOTAL_ANALYSIS_CORE`: **1086.807 s**
- runtime trace 到 worker COMPLETED: **1157.714 s**
- 約 19.3 分鐘完成整體 worker execution
- peak RSS: 約 **843 MB**

相較 `.10.30.18.2` TWS100 FIELD 的約 327.7 s core，本次明顯較慢。

主要原因不是 `.10.30.20` Band25 diagnostic 本身，而是 CAMS：
- PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE initial timeout + reattach timeout
- NATIVE_AEROSOL_532NM_PRESSURE_LEVEL initial timeout + reattach timeout
- AEROSOL_SCATTERING_COLUMN_PROPERTIES 約 108.8 s

因此下一版若要優化效能，應優先處理 CAMS deferred/reattach waiting policy，而不是改 Frozen Science 或 Band25 science。

## 正式 FIELD 結論

**R5.7.41.3.4.10.30.20 FIELD PASS**

理由：
1. CASE archive / hash / CRC 全部完整。
2. `case_integrity_audit` 140/140 PASS。
3. `analysis_integrity_audit` 0 FAIL。
4. CAMS spectral AOD 與 O3 payload validity 均為 1.0。
5. Step 3Q.20 / Band25 contract 正確進入 CASE。
6. 所有 production ice-optics promotion gate 繼續 fail-close。
7. Frozen Science 未改動。
8. No-Canvas 結果保持物理語意，沒有用 red-light path 或 Missing 資料造出 Formation。

## 下一步
建議從 `.10.30.20 FIELD PASS` 進 `.10.30.21`。

優先級：
1. 繼續 Band25 historical fine-grid / interpolation / within-band solar weights provenance recovery。
2. 同時把 CAMS reattach 的 runtime cost 納入 `.10.30.21` runtime diagnostics / optimization：
   - 不改 fail-close contract
   - 不允許 fresh duplicate submit
   - 但避免兩個 native 3-D roles 各自重複消耗完整 running grace + reattach grace 而拖長整次分析。
3. 等未來真正出現 `TIMEOUT_DEFERRED → REATTACH → SUCCESS → HARVEST`，再正式關閉 adaptive successful-harvest FIELD branch。
