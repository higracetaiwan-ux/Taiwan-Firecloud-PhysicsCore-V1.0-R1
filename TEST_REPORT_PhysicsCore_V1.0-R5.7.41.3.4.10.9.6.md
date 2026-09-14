# Test Report — V1.0-R5.7.41.3.4.10.9.6

## Working-tree regression

- **718/718 PASS**
- 1 existing pandas `FutureWarning`

## 新增／更新測試

- GFS source exact-zero vs below-threshold attribution
- source diagnostic role separation / Integrity
- Timeline T−180→T+60 contract
- provider GFS valid-time based native matching
- native temporal interpolation remains forbidden
- CASE required-member contract updated for two source-attribution artifacts

## Frozen source audit

以下核心 science modules 相對 `.10.9.5` byte-identical：

`formation.py`, `viewing.py`, `viewing_spectral.py`, `twilight_glow.py`, `gas_rt.py`, `cloud_optics.py`, `config.py`, `red_light_availability.py`, `photography_decision.py`, `native_cloud.py`, `formation_gates.py`, `formation_prerequisites.py`, `spectral_rt.py`, `spectral_color.py`, `illumination.py`, `optical_path.py`。

本版變更限於 orchestration / evidence export / integrity / timeline provenance 與新的 diagnostic module。

## Fresh-extract regression

- draft fresh-extract: **718/718 PASS**
- final FULL-CLEAN fresh-extract: **718/718 PASS**
- 1 existing pandas `FutureWarning`
- cache/pyc contamination before packaging: **0**
