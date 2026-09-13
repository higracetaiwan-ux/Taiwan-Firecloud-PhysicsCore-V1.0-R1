# R5.7.41.3.4.10 — Twilight Glow Runtime Hotspot Decomposition Spec

## 目的
`.3.4.9.2` 第二跑顯示 Twilight Glow Independent Branch 約 90.98 s，為目前最穩定、最大的非-provider CPU stage。R5.7.41.3.4.10 只做 profiler decomposition，不改 Glow physics。

## 新增 component stages
1. `TWILIGHT_GLOW_COMPONENT_GEOMETRY`
2. `TWILIGHT_GLOW_COMPONENT_TARGETS`
3. `TWILIGHT_GLOW_COMPONENT_OBSERVER_PRECIPITATION`
4. `TWILIGHT_GLOW_COMPONENT_OBSERVER_SPECTRAL_EXTINCTION`
5. `TWILIGHT_GLOW_COMPONENT_LOOKUP_CONTEXT_PREP`
6. `TWILIGHT_GLOW_COMPONENT_VOLUME_ASSEMBLY`
7. `TWILIGHT_GLOW_COMPONENT_SUMMARY`
8. `TWILIGHT_GLOW_COMPONENT_PHASE1_EXPORTS`
9. `TWILIGHT_GLOW_COMPONENT_AEROSOL_SCATTERING`
10. `TWILIGHT_GLOW_COMPONENT_AEROSOL_SUMMARY_ATTACH`

所有 component row 使用 `cache_status=R57413410_COMPONENT_PROFILE_ONLY`。

## Science freeze
不改：
- Sun→scatter→observer geometry
- 550/575/600/650/700/750 nm 六波段
- Rayleigh / HITRAN gas / O3 / aerosol / cloud / precipitation extinction
- aerosol SSA / asymmetry / HG phase-function evidence
- Missing semantics
- Glow 與 Formation / Viewing 的 branch independence
- multiple-scattering / calibrated-radiance 未解狀態

## Field gate
用 TWS056 / 2026-09-13 sunset 跑 `.3.4.10` CASE，確認 10 component elapsed 合計能合理解釋 `TWILIGHT_GLOW_INDEPENDENT_BRANCH`，再只針對最大 component 做 exact-equivalent optimization。
