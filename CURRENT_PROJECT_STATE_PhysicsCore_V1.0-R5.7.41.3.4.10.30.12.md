# Taiwan Firecloud PhysicsCore — Current Project State

版本：`1.0.0-R5.7.41.3.4.10.30.12`  
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`  
目前 Step：**3Q.12**  
上一個正式 FIELD baseline：**R5.7.41.3.4.10.30.11 FIELD PASS**（TWS106 高美濕地，2026-09-19 sunset）

## 本版主題
**Official AER Download Endpoint + Independent Extracted-Distribution Footprint Qualification**。

## 已確認
1. AER 官方 `RRTM_SW Code and Examples` 現行頁面把 `aer_rrtm_sw_v2.5.tar.gz` 直接連至：
   `https://files.aer.com/rtweb/aer_rrtm_sw/aer_rrtm_sw_v2.5.tar.gz`
2. 歷史 v2.5 update notice 記錄 anonymous FTP 路徑：
   `ftp.aer.com/pub/downloads/aer_rrtm_sw/aer_rrtm_sw_v2.5.tar.gz`
3. 獨立安裝紀錄提供 extracted distribution footprint：`src/`、`makefiles/`、`rrtm_sw_instructions`、`update_rrtm_sw_v2.5.txt`，並顯示 makefile `VERSION = v2.5`。
4. `.10.30.11` 的 official AER 2004 `cldprop.f` / `taumoldis.f` CVS-normalized critical-source equivalence 繼續成立。
5. 新增本地 archive acquisition verifier，供真正取得 tarball 後立即固化 hashes + manifest。

## 正式 state
`PASS_FAIL_CLOSED_V25_OFFICIAL_DOWNLOAD_ENDPOINT_AND_EXTRACTED_FOOTPRINT_QUALIFIED_ORIGINAL_TARBALL_BYTES_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED`

## Production gates
- `AER_OFFICIAL_RRTM_SW_V25_BINARY_DOWNLOAD_ENDPOINT_PINNED=True`
- `AER_RRTM_SW_V25_HISTORICAL_FTP_DISTRIBUTION_PATH_PINNED=True`
- `RRTM_SW_V25_INDEPENDENT_EXTRACTED_DISTRIBUTION_FOOTPRINT_QUALIFIED=True`
- `AER_RRTM_SW_V25_ARCHIVE_ACQUISITION_VERIFIER_READY=True`
- `AER_OFFICIAL_RRTM_SW_V25_ARCHIVE_BYTES_RECOVERED=False`
- `AER_OFFICIAL_RRTM_SW_V25_ARCHIVE_HASH_RECOVERED=False`
- `RRTM_SW_PREAVERAGING_GENERATOR_RECOVERED=False`
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`
- `TAU_ICE_PRODUCTION_ALLOWED=False`
- `PRODUCTION_ICE_OPTICS_READY=False`
- `physics_promotion_allowed=False`
- Step 3R：**blocked**

## 下一個 blocker
優先順序：
1. 在可成功取得 binary 的環境，用 `tools/verify_aer_rrtm_sw_v25_archive.py --download-to aer_rrtm_sw_v2.5.tar.gz --json-out ...` 取得並固定實際 bytes/hash；
2. 將取得的 tarball manifest 與 `.10.30.11` 已 qualified 的 historical source anchors / external distribution 做完整 comparison；
3. 若 archive authenticity chain 足夠，再把 `ARCHIVE_BYTES_RECOVERED/HASH_RECOVERED` 由 False 提升；
4. 繼續尋找 historical pre-averaging generator / Q. Fu high-resolution source tables；
5. 只有可 deterministic reproduce archived Band 24 / 25 tables，才評估 Step 3R。
