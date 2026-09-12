# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.6

## Runtime / I-O Hardening

本版延續 R5.7.41.3.4.5，將目前可安全一起處理的工程項目一次收斂：**DWD persistent raw cache + API audit 修正 + CASE export buffered streaming + aggregation profiling**。Science baseline 仍為 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。

### 1. DWD ICON persistent raw cache

- `WARM_PRODUCTION` 的 DWD raw model-level fields 改放 `FIRECLOUD_STATE_DIR/provider_cache_shared/dwd_icon_raw`，可跨 analysis worker / 後續分析重用。
- `COLD_ISOLATED_TEST` 仍隔離 event/weather raw cache；只共享 DWD 靜態 remap 資源。
- cache key 鎖死 model / product / grid / run / lead / variable / level / URL / schema。
- cache hit 前必須通過 exact identity、QC stamp、byte size、SHA256 全部驗證。
- cache 損壞、identity mismatch、stamp missing 一律重新下載，Missing / error 不會被改寫成 Clear / Zero。
- raw GRIB 仍 temporary file → atomic replace；未完整 commit 的檔案不會被下一次分析信任。

### 2. DWD API efficiency audit correction

修正 `.3.4.4/.3.4.5` Field CASE 中 `dwd_icon_request_audit.csv` 明明有 176 筆 network request，但 `api_efficiency_audit.csv` 誤報 0 的 telemetry bug。

新增明確欄位：`network_attempts`、`network_successes`、`network_failures`、`network_bytes`、`raw_cache_hits`、`decoded_field_cache_hits`、`negative_availability_cache_hits`，並保留 `network_requests` / `decoded_cache_hits` 相容欄位。

### 3. CASE Export Buffered ZIP Streaming

- DataFrame 仍直接串流寫入 ZIP；不 materialize 整份 CSV。
- pandas 小型 UTF-8 writes 先在最多 4 MiB buffer 合併後再送入 ZipExtFile / zlib。
- CSV payload、SHA256、byte size、row count 與 archive integrity semantics exact-equivalent。
- H004 三個大型代表性 CSV benchmark：6.766 s → 6.268 s，約 7.36% serialization reduction；三檔 uncompressed SHA256、byte size 與 compressed member size完全一致。
- 新增 `CASE_PRE_EXPORT_PREPARATION`、`CASE_EXPORT_CSV_MEMBERS`、`CASE_EXPORT_JSON_MEMBERS` telemetry。

### 4. Aggregation profiling

新增細分 runtime telemetry，不改 aggregation 演算法：timeline/geometry、cloud matrix drain、spectral/atmos matrix drain、Formation evidence、Viewing/Photography、Tier-2/core summary、completeness/decision、spectral diagnostics。

新 row 全部標記 `R5741346_DIAGNOSTIC_PROFILE_ONLY`，只用來決定 R5.7.41.3.4.7 真正該最佳化哪個 hotspot。

## Equivalence / Safety

- DWD synthetic cold→warm test：清空 process-local decoded cache後，第二次 exact identity 只讀 persistent raw cache，network 1 → 0，decoded DataFrame `check_exact=True`。
- raw cache corruption test：byte-size/SHA mismatch 必須 fail-close 並重新下載。
- DWD API audit synthetic test：`OK_DOWNLOADED` 正確計入 network attempt/success/bytes，HTTP 404 正確計入 network failure。
- 所有 physics modules / gates 維持既有規則；本版新增的 model.py 變更只有 provider audit summary 與 profiling timers。

## 科學契約不變

- Production / Shadow COT 不變；
- Shadow eligibility 不變；
- Earth Shadow / DirectSolarFraction 不變；
- Formation / Viewing / Twilight Glow 不變；
- 六波段 550/575/600/650/700/750 nm 不變；
- `Missing ≠ Clear ≠ Zero`；
- `DIRECT_EVIDENCE_CONFLICT` fail-close 不變；
- Production switch / COT promotion / Formation promotion 仍為 False。

## Verification

- Targeted Runtime/I-O tests：12/12 PASS。
- Working-tree full regression：628/628 PASS（1 個既有 pandas FutureWarning，非失敗）。
- Trial fresh-extract full regression：628/628 PASS。
- Final-candidate fresh-extract full regression：628/628 PASS。
- Final FULL-CLEAN exact-archive fresh-extract full regression：628/628 PASS。
- Release Gate：**CLOSED**。
