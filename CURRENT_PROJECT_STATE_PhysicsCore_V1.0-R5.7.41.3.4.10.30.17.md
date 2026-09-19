# Taiwan Firecloud PhysicsCore — Current Project State

- Current QA release: `R5.7.41.3.4.10.30.17`
- Latest FIELD baseline before this QA release: `R5.7.41.3.4.10.30.16 FIELD PASS`
- Frozen science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`
- Step 3R: **BLOCKED**
- Step3Q contract: `FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_17`
- Qualification: `PASS_FAIL_CLOSED_FU96_LINEAGE_BROADBAND_WEIGHTING_EQUATION_TRANSCRIPTION_CORRECTED_EXACT_RRTM_BAND24_25_REALIZATION_UNRECOVERED`

## 新增進展
Fu96-lineage broadband averaging equation transcription 已修正：co-albedo 的 linear/log averaging 均保留 extinction coefficient `beta_lambda` 與 TOA solar irradiance weighting；asymmetry factor 使用 scattering weighting。

## 未解決 blocker
1. original AER v2.5 tarball bytes/hash；
2. Fu96 high-resolution ice-cloud spectral samples / pre-averaging generator；
3. exact historical solar spectrum/grid/discrete weights；
4. archived Band 24/25 deterministic reproduction。
