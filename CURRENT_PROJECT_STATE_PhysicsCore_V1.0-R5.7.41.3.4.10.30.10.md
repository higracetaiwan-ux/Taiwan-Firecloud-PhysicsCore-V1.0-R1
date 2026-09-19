# Taiwan Firecloud PhysicsCore — Current Project State

版本：`1.0.0-R5.7.41.3.4.10.30.10`  
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`  
目前 Step：**3Q.10**  
上一個正式 FIELD baseline：**R5.7.41.3.4.10.30.9 FIELD PASS**（TWS001，2026-09-19 sunset）

## 本版主題
**Official AER v2.5 Archive Publication-Chain Qualification**。

本版只補強 Fu96/RRTM_SW v2.5 的歷史 provenance，不修改 Formation、Viewing、Twilight Glow、六波段、Canvas / Corridor / REZ、Earth Shadow、Production/Shadow COT、Missing≠Clear≠Zero 或 Production Ice Optics 科學規則。

## 已新增並正式固定的證據
- AER 官方 RRTM_SW Code and Examples 頁面明列 v2.5 source package：`aer_rrtm_sw_v2.5.tar.gz`。
- AER 官方 repo 的 `README.cvs_checkin_notes`（pinned blob SHA `9304d7bbd17766b48a58fb2c500e8f5f951b557f`）記錄 2004 public-release procedure：更新 release files 後，以 `script_build_rrtm_sw.pl` 建立網站用 source-code / example tar files，並要求 build script 使用正確 version number。
- 因此可以把「官方 archive filename ↔ 官方 website tar-build release process」提升為 **publication lineage qualified**。

## 仍然不能宣稱
- 尚未取得並驗證 original `aer_rrtm_sw_v2.5.tar.gz` bytes。
- 尚未取得 provenance-qualified original tarball cryptographic hash。
- 第三方 external mirror **不得**宣稱與 original AER tarball byte-identical。
- Q. Fu high-resolution pre-averaging tables / historical band averaging generator / exact solar grid & discrete weights 仍未恢復。
- Band 24 / 25 exact reproduction 仍未完成。

正式 state：
`PASS_FAIL_CLOSED_V25_OFFICIAL_ARCHIVE_PUBLICATION_CHAIN_QUALIFIED_ORIGINAL_TARBALL_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED`

## Production gates
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`
- `TAU_ICE_PRODUCTION_ALLOWED=False`
- `PRODUCTION_ICE_OPTICS_READY=False`
- `physics_promotion_allowed=False`
- Step 3R：**blocked**

## 下一個 blocker
優先順序：
1. 取得 original `aer_rrtm_sw_v2.5.tar.gz` bytes 或可信 archival copy；
2. 建立 original archive hash / authenticity chain；
3. 與 external mirror 做完整 file-tree / content comparison；
4. 繼續尋找 `/storm/rc1/cvsroot/rc/rrtm_sw/` CVS attic / preprocess code；
5. 尋找 Q. Fu high-resolution cloud-optics tables與 historical band-averaging generator；
6. 僅在能 deterministic reproduce archived Band 24/25 tables 時，才評估進入 Step 3R。
