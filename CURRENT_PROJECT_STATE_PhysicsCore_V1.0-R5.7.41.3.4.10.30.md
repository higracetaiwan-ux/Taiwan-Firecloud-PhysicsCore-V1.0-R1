# Taiwan Firecloud PhysicsCore — Current Project State

版本：`1.0.0-R5.7.41.3.4.10.30`  
階段：Ice Optics Phase 2 Step 3Q — Fu96/RRTMG Exact Band-Weighting Provenance Qualification  
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## 本版結論

Step 3Q 已把 Fu96 → RRTM/RRTMG shortwave broad-band ice-optics 的 provenance blocker 正式資格化。

已確認並 pin：
- Fu (1996) primary solar ice-cloud parameterization；
- RRTM/RRTMG `ICEFLAG=3` 的 Fu96 `Dge` lineage；
- RRTMG band 24 / 25 最終 `extice3 / ssaice3 / asyice3` reference tables；
- Fu96 明確指出 absorption-band spectral intervals 中 SSA averaging technique 具有物理重要性。

仍未取得足以重建最終 RRTMG tables 的：
- authoritative pre-averaging spectral sample set；
- exact per-sample weights 或 exactly-equivalent algorithm；
- 無歧義 weighting semantics；
- band 24 / 25 exact reproduction。

因此正式 gate：

`PASS_FAIL_CLOSED_EXACT_WEIGHTING_PROVENANCE_UNRESOLVED`

並維持：
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE = false`
- `BAND_INTEGRATED_OPTICAL_VALIDATION_READY = false`
- `INDEPENDENT_SSA_VALIDATION_PASS = false`
- `INDEPENDENT_ASYMMETRY_VALIDATION_PASS = false`
- `FULL_SIX_BAND_LIKE_FOR_LIKE_OPTICAL_VALIDATION_PASS = false`
- `TAU_ICE_PRODUCTION_ALLOWED = false`
- `PRODUCTION_ICE_OPTICS_READY = false`
- `physics_promotion_allowed = false`

禁止以 equal weighting、假設 solar-flux weighting、假設 g-point weighting、或 extinction/scattering weighting 取代缺失的 authoritative provenance。
