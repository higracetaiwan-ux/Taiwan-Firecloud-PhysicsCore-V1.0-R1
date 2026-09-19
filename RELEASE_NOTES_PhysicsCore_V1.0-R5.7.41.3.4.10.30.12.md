# Taiwan Firecloud PhysicsCore V1.0 — Release Notes

版本：`1.0.0-R5.7.41.3.4.10.30.12`
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## Step 3Q.12
**Official AER Download Endpoint + Independent Extracted-Distribution Footprint Qualification**

本版只強化 Fu96 / RRTM_SW v2.5 歷史 provenance 與 archive acquisition tooling，不修改 Formation、Viewing、Twilight Glow、六波段、Canvas / Corridor / REZ、Earth Shadow、Production/Shadow COT 或任何 frozen science rule。

## 新增證據
- AER 官方 RRTM_SW Code and Examples 頁面的 v2.5 source package 直接連到：
  `https://files.aer.com/rtweb/aer_rrtm_sw/aer_rrtm_sw_v2.5.tar.gz`
- v2.5 update notice 保留歷史 anonymous FTP 發布路徑：
  `ftp://ftp.aer.com/pub/downloads/aer_rrtm_sw/aer_rrtm_sw_v2.5.tar.gz`
- 獨立 RRTM_SW v2.5 安裝紀錄顯示，從 AER 取得並解壓後可見 `src/`、`makefiles/`、`rrtm_sw_instructions`、`update_rrtm_sw_v2.5.txt`，並在 makefile 中看到 `VERSION = v2.5`。
- 新增 `tools/verify_aer_rrtm_sw_v25_archive.py`：對實際取得的 archive 計算 SHA256/MD5、列出 tar manifest、檢查 expected footprint；工具本身不會自動提升 archive authenticity。

## 正式 qualification state
`PASS_FAIL_CLOSED_V25_OFFICIAL_DOWNLOAD_ENDPOINT_AND_EXTRACTED_FOOTPRINT_QUALIFIED_ORIGINAL_TARBALL_BYTES_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED`

## 仍然 fail-close
- original `aer_rrtm_sw_v2.5.tar.gz` bytes：本 release evidence set 尚未實際取得
- original archive provenance-qualified SHA256/MD5：未建立
- external mirror 與 original tarball byte identity：未證明
- Q. Fu high-resolution pre-averaging tables：未恢復
- historical band-averaging generator：未恢復
- exact historical solar grid / discrete weights：未恢復
- Band 24 / 25 deterministic reproduction：未完成
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`
- `TAU_ICE_PRODUCTION_ALLOWED=False`
- `PRODUCTION_ICE_OPTICS_READY=False`
- Step 3R：blocked

## Regression
- Step3Q lineage：39/39 PASS
- Full regression：966/966 PASS
- Failures：0
- Existing pandas FutureWarning：1
