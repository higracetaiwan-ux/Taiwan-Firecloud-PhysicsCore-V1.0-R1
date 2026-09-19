# Taiwan Firecloud PhysicsCore — Current Project State

版本：`1.0.0-R5.7.41.3.4.10.30.14`  
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`  
目前 Step：**3Q.14**  
上一個正式 FIELD baseline：**R5.7.41.3.4.10.30.13 FIELD PASS**（TWS106 高美濕地，2026-09-19 sunset）

## 本版主題
**Pre-2020 Cross-Repository Critical Fu96 Raw-Blob Replication Qualification**。

## 已確認
1. AER 官方 2004 release-side source history與 `.10.30.13` scientific-source semantic equivalence qualification保持不變。
2. `tomflannaghan/pyrrtm` 在 2014-07-14 commit `31d77636…` 已加入 shortwave code，時間早於 2020 nickedkins v2.5 import。
3. 2014 pyrrtm tree 與 2020 nickedkins import 對固定 26-file scientific-source set 做 Git blob SHA comparison：22/26 raw-byte identical。
4. 4 個 nonmatch files：`RDI1MACH.f`、`disort.f`、`rrtatm.f`、`rrtm.f`；本版不將這些差異隱藏或自動視為相同。
5. 與 Fu96 cloud-table / runtime solar context / Band 24 / Band 25 最直接相關的 4 個 critical files全部 raw-byte replicated：`cldprop.f`、`taumoldis.f`、`k_gB24.f`、`k_gB25.f`。
6. 新增 deterministic Git-tree manifest verifier，可重跑 26-file raw-blob comparison，但明確禁止把 cross-repository replication 解讀成 original AER tarball identity。

## 正式 state
`PASS_FAIL_CLOSED_V25_PRE2020_CROSS_REPOSITORY_CRITICAL_FU96_RAW_BLOB_REPLICATION_QUALIFIED_ORIGINAL_TARBALL_BYTES_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED`

## Production gates
- `PYRRTM_SW_2014_PRE2020_HISTORY_PINNED=True`
- `RRTM_SW_V25_CROSS_REPOSITORY_RAW_BLOB_MATCH_22_OF_26_QUALIFIED=True`
- `RRTM_SW_V25_CRITICAL_FU96_BAND24_25_RAW_BLOB_REPLICATION_QUALIFIED=True`
- `RRTM_SW_V25_CROSS_REPOSITORY_RAW_BLOB_REPLICATION_IS_ORIGINAL_AER_TARBALL_IDENTITY=False`
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
1. 真正取得官方 `aer_rrtm_sw_v2.5.tar.gz` bytes，固定 SHA256/MD5 + tar manifest；
2. 以 `.10.30.12` archive verifier、`.10.30.13` semantic verifier、`.10.30.14` raw-blob manifest verifier 三重交叉驗證；
3. 持續搜尋 historical Fu96 high-resolution pre-averaging source tables / generator；
4. 恢復 exact historical solar spectrum / discrete weighting realization；
5. 只有可 deterministic reproduce archived Band 24 / 25 tables，才評估 Step 3R。
