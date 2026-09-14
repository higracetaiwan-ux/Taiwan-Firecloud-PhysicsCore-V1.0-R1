# Field Validation — R5.7.41.3.4.10.9.9 TWS089 2026-09-15 Sunrise

## 結論

`.10.9.9 = FIELD PASS`。

- Job：COMPLETED
- Worker elapsed：510.408 s
- TOTAL_ANALYSIS_CORE：478.618 s
- TOTAL_TO_CASE_ARCHIVE：505.046 s
- Analysis Integrity：85 PASS / 1 NOT_APPLICABLE / 0 FAIL
- CASE Integrity：38/38 PASS

## CAMS Pressure-Level Exact Bundle

正式 Field 成功：

- `PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE`：OK，40.186 s
- `O3_PRESSURE_LEVEL`：`EXACT_SOURCE_REUSE`，0.0 s
- `NATIVE_AEROSOL_532NM_PRESSURE_LEVEL`：`EXACT_SOURCE_REUSE`，0.0 s
- `AEROSOL_SCATTERING_COLUMN_PROPERTIES`：OK，53.246 s
- `SPECTRAL_COLUMN_AOD`：`EXACT_SOURCE_REUSE`，0.0 s
- `O3_NEAR_SURFACE_MODEL_LEVEL_137`：OK，49.203 s

真實 ADS provider jobs = 3。  
`CAMS_PRESSURE_LEVEL_BUNDLE_EXACT_REUSE_PROVENANCE=PASS`。  
`CAMS_SPECTRAL_AOD_EXACT_REUSE_PROVENANCE=PASS`。  
CAMS Prefetch = 147.876 s。

## DWD cache-scope contract

`.10.9.9` 修正成功：

- `shared_cache_scope = USER_LEVEL_CROSS_RELEASE_EXACT_IDENTITY`
- `raw_cache_scope = USER_LEVEL_CROSS_RELEASE_EXACT_IDENTITY`
- `http_connection_reuse = THREAD_LOCAL_REQUESTS_SESSION_POOL`
- cache path 實際位於 `/home/appuser/.cache/taiwan_firecloud/dwd_icon/raw_grib/...`

本次為 2026-09-15 sunrise，DWD exact run/lead 與前一日 CASE 不同，因此 raw cache hits=0 屬正常，不能拿來否定 cross-release exact-cache 設計。

DWD secondary prefetch = 40.822 s；network attempts/success = 335/335；network bytes 約 406 MB。

## Science

本次 Formation 0° 至 −4.5°均有 Primary/Extended Canvas available；不同角度依 Red-Light evidence 在 `FORMATION_EVIDENCE_AVAILABLE` / `UNCERTAIN_OPTICS` 間切換；−5°至−6°為 `NOT_FORMED_EARTH_SHADOW`。本版 Field 驗證重點為 provider orchestration/cache contract；Frozen science 未更動。
