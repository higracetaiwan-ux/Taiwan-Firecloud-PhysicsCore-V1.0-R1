# Taiwan Firecloud PhysicsCore V1.0 — Release Notes

版本：`1.0.0-R5.7.41.3.4.10.30.8`
名稱：**Ice Optics Phase 2 Step 3Q.8 — External RRTM_SW v2.5 Distribution Lineage Qualification**
日期：2026-09-19
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## 本版目的

本版不解鎖 Production Ice Optics，也不進 Step 3R。目的為補強 Fu96 → RRTM/RRTMG historical provenance：正式 pin 一份外部保存的 RRTM_SW v2.5 distribution lineage，並確認其 cloud runtime source 與 AER 公開 RRTM_SW source 的科學內容一致性，同時維持 original AER tarball byte identity 未證明的 fail-close 邊界。

## 新增資格證據

- pin `nickedkins/RRTM-LWandSW-Python-wrapper` commit `a2d974ecefe6f369661bf5a3dfc648f07986ad89` 作為 **external archival lineage evidence**。
- `SW/update_rrtm_sw_v2.5.txt`：April 2004，明確記錄 `RRTM_SW v2.4.1 has been updated to RRTM_SW v2.5`。
- `SW/makefiles/make_rrtm_sw_linux_pgi`：`VERSION = v2.5`，保留 2004-04-16 CVS Id。
- `SW/src/cldprop.f`：保留 CVS provenance：author `jdelamer`、revision `2.7`、date `2004/04/15 18:42:10`。
- 外部 v2.5 `cldprop.f` 與 pinned AER `RRTM_SW/src/cldprop.f` 均為 2080 行；僅 5 行不同，全部是 CVS keyword 展開/移除，實際程式與 table 內容一致。
- `SW/src/taumoldis.f`：明確區分 low-resolution 與 high-resolution Kurucz solar source，並記錄某 band total irradiance discrepancy 需由 `SCALEKUR` 修正。

## 新增 fail-close 規則

- external v2.5 mirror 可作 source-lineage evidence，但在沒有 original AER v2.5 archive hash 前，不得宣稱 original tarball byte-identical。
- runtime low-resolution Kurucz `SFLUXREF` 不得替代未恢復的 high-resolution cloud-table spectral weights。
- v2.5 runtime distribution 仍只證明 post-averaged cloud tables / runtime logic；未找到 Q. Fu high-resolution pre-averaging cloud table source 或 generator。

## 新 qualification state

`PASS_FAIL_CLOSED_V25_EXTERNAL_DISTRIBUTION_LINEAGE_QUALIFIED_PREAVERAGING_GENERATOR_UNRECOVERED`

## Production gate

以下仍全部維持 `False`：

- `RRTM_SW_PREAVERAGING_GENERATOR_RECOVERED`
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE`
- `RRTMG_BAND24_EXACT_REPRODUCTION_PASS`
- `RRTMG_BAND25_EXACT_REPRODUCTION_PASS`
- `BAND_INTEGRATED_OPTICAL_VALIDATION_READY`
- `INDEPENDENT_SSA_VALIDATION_PASS`
- `INDEPENDENT_ASYMMETRY_VALIDATION_PASS`
- `FULL_SIX_BAND_LIKE_FOR_LIKE_OPTICAL_VALIDATION_PASS`
- `TAU_ICE_PRODUCTION_ALLOWED`
- `PRODUCTION_ICE_OPTICS_READY`
- `physics_promotion_allowed`

## Regression

- Step 3Q targeted：26/26 PASS
- Full regression：954/954 PASS
- 既有 pandas FutureWarning：1
- failures：0

## Frozen science

Formation / Viewing / Twilight Glow、六波段、Canvas、Dynamic Corridor / REZ、Earth Shadow、Production/Shadow COT、Missing≠Clear≠Zero 等既有 science baseline 均未更動。
