# Runtime / I-O Hardening Spec — R5.7.41.3.4.6

## 1. Scope

R5.7.41.3.4.6 是純工程版本，科學基線固定：

`R5.7.41.2_SHADOW_COT_AB_FROZEN`

本版一次收斂四個互相獨立、可做 exact-equivalence 驗證的 runtime / I-O 項目：

1. DWD ICON secondary persistent raw cache；
2. DWD API efficiency audit correction；
3. CASE export bounded buffered ZIP streaming；
4. Aggregation 細分 profiling telemetry。

不得修改 Production / Shadow COT、Shadow eligibility、Earth Shadow、DirectSolarFraction、Formation、Viewing、Twilight Glow、Photography、六波段或 Missing 語義。

## 2. DWD persistent raw cache

### 2.1 Warm / Cold namespace

正常 `WARM_PRODUCTION` 的 DWD raw cache 固定放在 `FIRECLOUD_STATE_DIR/provider_cache_shared/dwd_icon_raw`，讓不同 analysis worker / 後續分析可重用。

`COLD_ISOLATED_TEST` 仍使用該 job 自己的 provider cache namespace；只共用 DWD 靜態 remap 資源。

### 2.2 Exact identity key

每個 raw field 的 identity 必須完整包含：

- provider / model；
- product；
- grid；
- run UTC；
- forecast lead；
- model level；
- variable；
- source URL；
- raw-cache schema version。

不允許「相近 cycle / lead / level / variable」替代。

### 2.3 Integrity guard

persistent raw cache hit 必須同時通過：

- raw file 存在且非空；
- exact identity JSON 完全一致；
- provenance stamp 存在；
- cache schema 一致；
- QC state = `CACHE_READY`；
- byte size 一致；
- SHA256 一致。

任一條件失敗即 fail closed，重新向 DWD 下載；不得把壞 cache 當有效 field。

下載仍採 temporary file → `os.replace()` atomic commit。Identity / provenance 只在完整 decompressed GRIB 已原子落盤後寫入；若程序在中間中斷，下一次會把未完整 commit 的 raw 檔視為不可信並重新下載。

## 3. DWD API efficiency audit

修正舊版 `OK_DOWNLOADED` 已覆寫原始 transfer status，導致 `api_efficiency_audit.csv` 將真實 176 次 network request 誤報為 0 的問題。

R5.7.41.3.4.6 直接使用 provider 明確 transfer flags，新增/保留：

- `network_requests`（相容欄位）；
- `network_attempts`；
- `network_successes`；
- `network_failures`；
- `network_bytes`；
- `raw_cache_hits`；
- `decoded_cache_hits`；
- `decoded_field_cache_hits`；
- `negative_availability_cache_hits`；
- `failure_rows`。

這些欄位只做工程 telemetry，不進入任何 physics gate。

## 4. CASE export buffered streaming

保留 R2.1 DataFrame→CSV→ZipExtFile streaming 架構，新增固定上限 4 MiB 的 UTF-8 write coalescing buffer。

必須 exact 保持：

- uncompressed CSV bytes；
- SHA256；
- byte size；
- row count；
- ZIP compression method / level；
- `case_archive_manifest.csv` schema；
- CASE Integrity contract。

新增 CASE export profiling：

- `CASE_PRE_EXPORT_PREPARATION`；
- `CASE_EXPORT_CSV_MEMBERS`；
- `CASE_EXPORT_JSON_MEMBERS`；
- 原有 `CASE_EXPORT_SERIALIZATION` / `TOTAL_TO_CASE_ARCHIVE`。

## 5. Aggregation profiling

本版只細分 telemetry，不重構 aggregation science / algorithm。

新增：

- `AGGREGATION_TIMELINE_AND_GEOMETRY`；
- `AGGREGATION_CLOUD_MATRIX_DRAIN`；
- `AGGREGATION_SPECTRAL_ATMOS_MATRIX_DRAIN`；
- `AGGREGATION_FORMATION_EVIDENCE`；
- `AGGREGATION_VIEWING_AND_PHOTOGRAPHY`；
- `AGGREGATION_TIER2_AND_CORE_SUMMARY`；
- `AGGREGATION_COMPLETENESS_AND_DECISION`；
- `AGGREGATION_SPECTRAL_COVERAGE_DIAGNOSTICS`。

所有新 profiler row 標記 `R5741346_DIAGNOSTIC_PROFILE_ONLY`；不得被任何結果選擇、Formation、Viewing、Glow 或 Integrity science gate 使用。

## 6. Verification contract

### 6.1 Provider cold→warm exact-equivalence

同一 exact DWD raw identity：

- 第一次：network download；
- 清空 process-local decoded cache 模擬新 worker；
- 第二次：persistent raw cache hit；
- decoded DataFrame 必須 `check_exact=True` 完全一致；
- 第二次 network request = 0。

### 6.2 Cache corruption fail-close

raw cache byte 被修改後，下一次必須因 byte-size / SHA256 mismatch 重新下載，不得繼續使用。

### 6.3 CASE export exact-equivalence

CSV payload/hash/size 必須 exact-equivalent。

### 6.4 Full regression / fresh extract

正式 release 必須完成 working-tree regression、FULL-CLEAN、SHA256、fresh-extract full regression。
