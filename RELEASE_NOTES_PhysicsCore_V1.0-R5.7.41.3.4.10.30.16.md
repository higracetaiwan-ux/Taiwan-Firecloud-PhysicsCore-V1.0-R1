# Taiwan Firecloud PhysicsCore V1.0 — R5.7.41.3.4.10.30.16 Release Notes

## 版本名稱
Step 3Q.16 — Historical AER RRTM Band-Generation Pipeline Scope Qualification

## 本版目的
本版只處理 Fu96 / RRTM_SW / RRTMG_SW provenance，不改動 frozen science。新增 AER-RC `rrtmgp-band-generation` 歷史工作樹的來源與範圍資格判定，明確區分「歷史 RRTM molecular/k-distribution/Planck band-generation pipeline」與「尚未恢復的 Fu96 ice-cloud high-resolution pre-averaging generator」。

## 新增證據
- AER-RC `rrtmgp-band-generation` GitHub repository 於 2025-01-14 公開建立，但保存 176 個帶 `git-svn-id` 的 AER `RRTM_BAND_GEN` 歷史 commits，時間可追至 2014-03-03。
- 2014-04-02 commit `5ce72bd363c993189767f09f1c9fe9bc84b72c56` 明示：`Adding initial band generation codes from Karen and original RRTM work. No modifications yet.`，並固定 SVN revision 24171。
- 該初始檔案集合包含 `script.gen_2band`、`kdis_2sort_*`、`write_data_*`、`write_tape5*`、Planck/continuum/minor-gas 工具。
- `script.gen_2band` 直接以 LBLRTM optical-depth 輸出建立 molecular absorption k-distributions、continuum/minor-gas coefficients、g-band 與 Planck products。
- 在這個 qualified initial file set 中，沒有找到 provenance-linked Q. Fu high-resolution ice-cloud spectral sample set，也沒有 Fu96 cloud-optics band-averaging generator。

## Gate 結果
- `AER_HISTORICAL_RRTM_MOLECULAR_BAND_GENERATION_PIPELINE_RECOVERED=True`
- `AER_HISTORICAL_RRTM_BAND_GENERATION_PIPELINE_IS_FU96_CLOUD_PREAVERAGING_GENERATOR=False`
- `FU96_CLOUD_PREAVERAGING_GENERATOR_RECOVERED=False`
- `RRTM_SW_PREAVERAGING_GENERATOR_RECOVERED=False`
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`
- `TAU_ICE_PRODUCTION_ALLOWED=False`
- `PRODUCTION_ICE_OPTICS_READY=False`
- `physics_promotion_allowed=False`

## 不變項目
Science baseline 維持 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。Formation / Viewing / Twilight Glow、六波段、Canvas、Dynamic Corridor/REZ、Earth Shadow、Production/Shadow COT、Missing≠Clear≠Zero 等 frozen science 全部不變。Step 3R 仍 blocked。

## 測試
- Step3Q lineage：51/51 PASS
- Full regression：978/978 PASS
- Failures：0
- 既有 pandas FutureWarning：1
