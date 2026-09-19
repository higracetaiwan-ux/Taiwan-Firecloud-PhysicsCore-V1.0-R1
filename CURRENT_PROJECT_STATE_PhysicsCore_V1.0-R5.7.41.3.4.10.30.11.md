# Taiwan Firecloud PhysicsCore — Current Project State

版本：`1.0.0-R5.7.41.3.4.10.30.11`  
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`  
目前 Step：**3Q.11**  
上一個正式 FIELD baseline：**R5.7.41.3.4.10.30.10 FIELD PASS**（TWS106 高美濕地，2026-09-19 sunset）

## 本版主題
**Official AER Historical Source-Tree CVS-Normalized Equivalence Qualification**。

本版只補強 Fu96/RRTM_SW v2.5 歷史 provenance，不修改 Formation、Viewing、Twilight Glow、六波段、Canvas / Corridor / REZ、Earth Shadow、Production/Shadow COT、Missing≠Clear≠Zero 或 Production Ice Optics 科學規則。

## 已新增並正式固定的證據
- AER 官方 historical repo 直接保留 `cldprop.f` 2004-04-15 18:42:10 UTC history，官方 blob SHA `8632f7d1940285665b62fdbb30c69861924251da`。
- AER 官方 historical repo 直接保留 `taumoldis.f` 2004-04-15 18:50:57 UTC history，官方 blob SHA `b2b1080fe51b7c3d512de26b4507314fee17ff58`。
- external mirror import 中 `cldprop.f` 保留 revision 2.7 / 2004-04-15 18:42:10；與官方檔案皆為 2080 lines，CVS keyword normalization 後 full-file identical。
- external mirror import 中 `taumoldis.f` 保留 revision 2.5 / 2004-04-15 18:50:57；與官方檔案皆為 2054 lines，CVS keyword normalization 後 full-file identical。
- 因此可以把這兩個本專案目前最關鍵的 v2.5 source anchors 提升為 **official historical critical-source-tree equivalence qualified**。

## 仍然不能宣稱
- critical source files 等價 ≠ entire external repository tree 等價。
- CVS-normalized source equivalence ≠ original `aer_rrtm_sw_v2.5.tar.gz` byte identity。
- 尚未取得 original tarball bytes 或 provenance-qualified cryptographic hash。
- 尚未恢復 Q. Fu high-resolution pre-averaging tables / historical band averaging generator / exact solar grid & discrete weights。
- Band 24 / 25 exact reproduction 仍未完成。

正式 state：
`PASS_FAIL_CLOSED_V25_OFFICIAL_SOURCE_TREE_CVS_NORMALIZED_EQUIVALENCE_QUALIFIED_ORIGINAL_TARBALL_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED`

## Production gates
- `RRTM_SW_V25_OFFICIAL_SOURCE_TREE_CVS_NORMALIZED_EQUIVALENCE_QUALIFIED=True`
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
1. 嘗試取得 original `aer_rrtm_sw_v2.5.tar.gz` bytes 或可信 archival copy；
2. 建立 original archive hash / authenticity chain；
3. 若可取得 original archive，做完整 tarball ↔ source-tree / external mirror manifest comparison；
4. 繼續尋找 `/storm/rc1/cvsroot/rc/rrtm_sw/` CVS attic / release preprocess code；
5. 尋找 Q. Fu high-resolution cloud-optics tables與 historical band-averaging generator；
6. 僅在能 deterministic reproduce archived Band 24/25 tables 時，才評估進入 Step 3R。
