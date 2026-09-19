# Taiwan Firecloud PhysicsCore — Current Project State

版本：`1.0.0-R5.7.41.3.4.10.30.13`  
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`  
目前 Step：**3Q.13**  
上一個正式 FIELD baseline：**R5.7.41.3.4.10.30.12 FIELD PASS**（TWS106 高美濕地，2026-09-19 sunset）

## 本版主題
**Official AER 2004 Scientific-Source Semantic Equivalence Qualification**。

## 已確認
1. AER 官方 2004 release-side commit/tree：`a4321233…` / `24beb15d…`。
2. external v2.5 import commit/tree：`040d1801…` / `51b90dfd…`。
3. 官方 2004 `src/` Fortran scientific-source set 共 26 files。
4. 24/26 files 經 generic CVS keyword normalization 後 complete-file identical。
5. `rrtatm.f` 唯一剩餘差異為 3 行日期/時間輸出 calls 被註解，屬 operational output delta。
6. `rrtm.f` 唯一剩餘差異為 1 行 input filename literal，屬 operational I/O delta。
7. 沒有在此 pinned 26-file comparison 中發現 RT equations、cloud/gas optics tables、spectral coefficient tables 或 band definitions 的 scientific-source delta。
8. 新增 deterministic semantic verifier，未來可對真正取得的 original tarball source tree 以同一規則重驗。

## 正式 state
`PASS_FAIL_CLOSED_V25_OFFICIAL_SCIENTIFIC_SOURCE_SEMANTIC_EQUIVALENCE_QUALIFIED_ORIGINAL_TARBALL_BYTES_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED`

## Production gates
- `RRTM_SW_V25_SCIENTIFIC_SOURCE_SEMANTIC_EQUIVALENCE_QUALIFIED=True`
- `RRTM_SW_V25_SCIENTIFIC_SOURCE_SEMANTIC_EQUIVALENCE_IS_FULL_RAW_BYTE_IDENTITY=False`
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
2. 用 `.10.30.12` archive verifier 與 `.10.30.13` scientific-source semantic verifier 同時驗證 archive；
3. 若 original archive authenticity chain 足夠，才提升 archive bytes/hash gates；
4. 持續找 historical pre-averaging generator / Q. Fu high-resolution spectral source tables；
5. 只有可 deterministic reproduce archived Band 24 / 25 tables，才評估 Step 3R。
