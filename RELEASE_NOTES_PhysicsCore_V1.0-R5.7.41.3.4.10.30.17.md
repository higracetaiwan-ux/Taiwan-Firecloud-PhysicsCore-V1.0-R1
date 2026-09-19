# Taiwan Firecloud PhysicsCore V1.0 — Release Notes

## R5.7.41.3.4.10.30.17

**Step 3Q.17 — Fu96-lineage Broadband Weighting Equation Transcription Correction**

本版只修正 Step3Q provenance/diagnostic contract 的歷史 broadband-weighting 公式轉錄，不修改 frozen Formation / Viewing / Twilight Glow science。

### 修正
- Fu96-lineage linear single-scattering co-albedo band mean：保留 `beta_lambda * S_lambda * dLambda` 權重。
- Fu96-lineage logarithmic co-albedo band mean：同樣保留 extinction `beta_lambda` 權重。
- band-mean asymmetry factor：以 `omega_lambda * beta_lambda * S_lambda * dLambda` scattering weighting。
- 明確禁止把 Fu96-lineage co-albedo 簡化成只有 solar-irradiance weighting。

### Fail-close
- Exact RRTM_SW/RRTMG Band 24/25 historical realization 仍未恢復。
- Fu96 high-resolution pre-averaging samples/generator 仍未恢復。
- Production Ice Optics 不解鎖；Step 3R 仍 blocked。

Qualification: `PASS_FAIL_CLOSED_FU96_LINEAGE_BROADBAND_WEIGHTING_EQUATION_TRANSCRIPTION_CORRECTED_EXACT_RRTM_BAND24_25_REALIZATION_UNRECOVERED`
Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`
