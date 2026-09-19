# Taiwan Firecloud PhysicsCore V1.0 — Release Notes

版本：`1.0.0-R5.7.41.3.4.10.30.13`  
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## Step 3Q.13
**Official AER 2004 Scientific-Source Semantic Equivalence Qualification**

本版只強化 Fu96 / RRTM_SW v2.5 歷史 provenance；不修改 Formation、Viewing、Twilight Glow、六波段、Canvas / Corridor / REZ、Earth Shadow、Production/Shadow COT 或任何 frozen science rule。

## 新增證據
- Pin AER 官方 2004 release-side source tree：commit `a43212334fd726dec8d69203be0c7d50fd9ce1b0`、tree `24beb15d868c131b81e354ea34b2b409c4a4062e`。
- Pin external v2.5 import tree：commit `040d18018f553faeeae625fd4ef73d50ba0436fb`、tree `51b90dfdb83f33f55dc3f23b680af6e327fe1fd8`。
- 官方 2004 tree 的 Fortran scientific-source set 共 **26 files**。
- 其中 **24/26** 在 generic CVS keyword collapse/expansion normalization 後為 complete-file identical。
- `src/rrtatm.f` 僅有 **3 行** operational delta：mirror 將 `LBLDAT` / `FTIME` / date-time header output calls 註解掉；沒有修改 RT equation / coefficient table / cloud optics table。
- `src/rrtm.f` 僅有 **1 行** operational delta：輸入檔名 literal 由 `INPUT_RRTM` 改為 `input_rrtm_MLS`；計算路徑未改。
- 新增 `tools/verify_rrtm_sw_v25_scientific_source_semantics.py`，可 deterministic 比較兩個本地 source trees，generic-normalize CVS keywords，只允許上述兩種明確 operational delta。

## 正式 qualification state
`PASS_FAIL_CLOSED_V25_OFFICIAL_SCIENTIFIC_SOURCE_SEMANTIC_EQUIVALENCE_QUALIFIED_ORIGINAL_TARBALL_BYTES_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED`

## Scope guard
本版 qualified 的是 **scientific-source semantic equivalence**，不是：
- whole-repository equality
- raw-byte identity
- original `aer_rrtm_sw_v2.5.tar.gz` byte identity
- original archive authoritative hash
- historical Fu96 pre-averaging generator recovery

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
- Step3Q lineage：42/42 PASS
- Full regression：969/969 PASS
- Failures：0
- Existing pandas FutureWarning：1
