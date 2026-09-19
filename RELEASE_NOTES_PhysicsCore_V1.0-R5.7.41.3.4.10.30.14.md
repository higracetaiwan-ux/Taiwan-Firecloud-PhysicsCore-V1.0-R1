# Taiwan Firecloud PhysicsCore V1.0 — Release Notes

版本：`1.0.0-R5.7.41.3.4.10.30.14`  
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## Step 3Q.14
**Pre-2020 Cross-Repository Critical Fu96 Raw-Blob Replication Qualification**

本版只強化 Fu96 / RRTM_SW v2.5 歷史 provenance；不修改 Formation、Viewing、Twilight Glow、六波段、Canvas / Corridor / REZ、Earth Shadow、Production/Shadow COT 或任何 frozen science rule。

## 新增證據
- Pin `tomflannaghan/pyrrtm` 首次加入 shortwave code 的歷史 commit：`31d776362503c20e84d2a6d78be4a96517f89e49`，時間 `2014-07-14T13:11:02Z`，tree `e4a56fd0b150b6536e9653c9b4446aa5a0a03d31`。
- 該 2014 repository history 早於既有 nickedkins v2.5 import（`040d18018f553faeeae625fd4ef73d50ba0436fb`，2020-03-17）。
- 針對固定的 26-file Fortran scientific-source set，以 Git blob SHA 做 raw-byte comparison：**22/26 exact raw-blob match**。
- 4 個未 raw-match files 明確保留為：`RDI1MACH.f`、`disort.f`、`rrtatm.f`、`rrtm.f`；本版不把它們自動 normalize 成相同。
- 4 個 provenance-critical files 在 2014 與 2020 histories 之間全部 raw-byte identical：
  - `cldprop.f` → `d7a2efce33cdf5c1f02a66e598c685ef53b7b8c8`
  - `taumoldis.f` → `5111a3bb7d981ea8facb4733c2ebb8d7f1308486`
  - `k_gB24.f` → `7847f1d19a9008137d60db422c623505ebf8835e`
  - `k_gB25.f` → `e3cc504280805b0b2de725d5645334095a92b07e`
- 新增 `tools/verify_rrtm_sw_v25_cross_repository_raw_blobs.py`，可對兩份已匯出的 Git tree manifests deterministic 計算 26-file raw blob match、nonmatch 與 critical-file replication。

## 正式 qualification state
`PASS_FAIL_CLOSED_V25_PRE2020_CROSS_REPOSITORY_CRITICAL_FU96_RAW_BLOB_REPLICATION_QUALIFIED_ORIGINAL_TARBALL_BYTES_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED`

## Scope guard
本版 qualified 的是 **separate repository-history raw-blob replication**，不是：
- original `aer_rrtm_sw_v2.5.tar.gz` byte identity
- authoritative original archive hash
- whole 26-file set raw-byte equality
- whole-repository equality
- historical Fu96 pre-averaging generator recovery

不同 repository histories 仍可能同源於同一份歷史 AER distribution；因此 cross-repository replication 只提高 lineage confidence，不可升格成 original archive authenticity proof。

## 仍然 fail-close
- Original AER v2.5 tarball bytes/hash：未恢復
- Q. Fu high-resolution pre-averaging tables：未恢復
- Historical band-averaging generator：未恢復
- Exact historical solar grid / discrete weights：未恢復
- Band 24 / 25 deterministic reproduction：未完成
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`
- `TAU_ICE_PRODUCTION_ALLOWED=False`
- `PRODUCTION_ICE_OPTICS_READY=False`
- Step 3R：blocked

## Regression
- Step3Q lineage：45/45 PASS
- Full regression：972/972 PASS
- Failures：0
- Existing pandas FutureWarning：1
