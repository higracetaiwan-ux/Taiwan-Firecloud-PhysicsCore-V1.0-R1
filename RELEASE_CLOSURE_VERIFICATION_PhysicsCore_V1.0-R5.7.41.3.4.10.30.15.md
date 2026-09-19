# Release Closure Verification — R5.7.41.3.4.10.30.16

**Decision: QA PASS / FIELD pending**

## Identity
- Version: `1.0.0-R5.7.41.3.4.10.30.16`
- Step: `Step 3Q.15 — Official AER RRTM_SW→RRTMG_SW Fu96 Final-Table Continuity Qualification`
- Frozen science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`
- Qualification state: `PASS_FAIL_CLOSED_AER_HISTORICAL_RRTM_BAND_GENERATION_PIPELINE_SCOPE_QUALIFIED_ORIGINAL_TARBALL_BYTES_HASH_UNRECOVERED_FU96_CLOUD_PREAVERAGING_GENERATOR_UNRECOVERED`

## New provenance closure
- AER official 2004 RRTM_SW v2.5 source: `src/cldprop.f`
- AER official 2007 RRTMG_SW source: `src/rrtmg_sw_cldprop.f90`
- Compared table families: `EXTICE3`, `SSAICE3`, `ASYICE3`, `FDLICE3`
- Bands: 16–29
- Arrays: **56/56 exact numeric match**
- Values: **2576/2576 exact numeric match**

This qualifies authoritative AER cross-generation final-table continuity only. It does not recover the high-resolution pre-averaging spectral samples, historical generator, exact historical solar weighting realization, or original AER v2.5 tarball bytes/hash.

## Regression
- Step3Q lineage: **48/48 PASS**
- Full regression: **975/975 PASS**
- Failures: **0**
- Existing warnings: **1 pandas FutureWarning**

## Fresh-extract pre-closure
- Step3Q: **48/48 PASS**
- Collection: **975 tests**
- Evidence regeneration: **BYTE-EXACT PASS**
- Gate regeneration: **BYTE-EXACT PASS**
- Contract regeneration: **BYTE-EXACT PASS**

## Artifact SHA256
- evidence: `1bbaa8a9b6b781c652aed507fc84de503c8efc899d08bbf81ff33f600c94533d`
- gate: `43a165ad4bfcb5117eec536e3b29b5e55007cbd0f9dbc3c944ae6d1f9a1e3cf5`
- contract V1_15: `8f17d72fd8fc3ea251f38eb7252b05332300028532d7032d35f26011b8fbb8b8`

## Guard state
- `AER_OFFICIAL_RRTM_SW_V25_ARCHIVE_BYTES_RECOVERED=False`
- `AER_OFFICIAL_RRTM_SW_V25_ARCHIVE_HASH_RECOVERED=False`
- `RRTM_SW_PREAVERAGING_GENERATOR_RECOVERED=False`
- `EXACT_HISTORICAL_SOLAR_SPECTRUM_AND_WEIGHTS_RECOVERED=False`
- `RRTMG_BAND24_EXACT_REPRODUCTION_PASS=False`
- `RRTMG_BAND25_EXACT_REPRODUCTION_PASS=False`
- `EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`
- `TAU_ICE_PRODUCTION_ALLOWED=False`
- `PRODUCTION_ICE_OPTICS_READY=False`
- `physics_promotion_allowed=False`

Step 3R remains blocked.
