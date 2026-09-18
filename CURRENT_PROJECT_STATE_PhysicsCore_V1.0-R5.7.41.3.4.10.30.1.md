# Taiwan Firecloud PhysicsCore — Current Project State

版本：`1.0.0-R5.7.41.3.4.10.30.1`  
階段：Ice Optics Phase 2 Step 3Q.1 — Fu96/RRTMG Band-Weighting Semantic Narrowing  
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## 本版結論

Step 3Q.1 在 `.10.30` 的 fail-closed provenance gate 上新增可驗證的 weighting semantic narrowing。

已確認：
- Fu-lineage solar band average 採 **solar irradiance weighting** 的物理語義；
- peer-reviewed RRTMG band-integration 公式使用 SW solar spectrum `S(λ)`；
- SSA 以 band-integrated scattering / extinction 建立；
- asymmetry factor `g` 採 scattering-weighted band integration；
- RRTMG SW band 24 / 25 光譜邊界可 pin。

但仍未取得足以重建 archived default Fu96 RRTMG tables 的：
- version-pinned historical pre-averaging spectral samples；
- 當時實際採用的 solar spectrum 版本與離散 weight vector；
- band 24 / 25 exact reproduction。

因此正式 gate：

`PASS_FAIL_CLOSED_WEIGHTING_SEMANTIC_CLASS_QUALIFIED_EXACT_HISTORY_UNRESOLVED`

並維持：
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE = false`
- `BAND_INTEGRATED_OPTICAL_VALIDATION_READY = false`
- `INDEPENDENT_SSA_VALIDATION_PASS = false`
- `INDEPENDENT_ASYMMETRY_VALIDATION_PASS = false`
- `FULL_SIX_BAND_LIKE_FOR_LIKE_OPTICAL_VALIDATION_PASS = false`
- `TAU_ICE_PRODUCTION_ALLOWED = false`
- `PRODUCTION_ICE_OPTICS_READY = false`
- `physics_promotion_allowed = false`

本版不以 equal weighting、未 pin 的 solar spectrum、g-point weighting 或 ad-hoc extinction/scattering weighting 取代 exact historical provenance。
