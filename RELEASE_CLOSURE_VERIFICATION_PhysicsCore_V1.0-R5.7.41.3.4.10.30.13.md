# Release Closure Verification — PhysicsCore V1.0-R5.7.41.3.4.10.30.13

## Release identity
`V1.0-R5.7.41.3.4.10.30.13`

## Step
**Step 3Q.13 — Official AER 2004 Scientific-Source Semantic Equivalence Qualification**

Formal state:
`PASS_FAIL_CLOSED_V25_OFFICIAL_SCIENTIFIC_SOURCE_SEMANTIC_EQUIVALENCE_QUALIFIED_ORIGINAL_TARBALL_BYTES_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED`

## Regression closure
- Step 3Q targeted lineage: **42/42 PASS**
- Full regression: **969/969 PASS**
- Fresh-extract targeted: **42/42 PASS**
- Fresh-extract collection: **969 tests collected**
- Existing pandas FutureWarning: **1**
- Failures: **0**

## Artifact byte-exact closure
- evidence: `433433b722cf7b5c21e9cbb0ae2c4cf8f67bd2bddcccda3ff446fa940e895952`
- gate: `4158523730c332c4f8ffb90e3b5d643e99a2b22eee8c3ceebf9a996575763a88`
- contract V1_13: `338072a43b34b6ee0a3b3669ead104084aad2bf124696596dfba7a1da4eecfd0`

Fresh regeneration of all three Step 3Q artifacts is byte-exact.

## New provenance boundary qualified
- AER official 2004 release-side commit/tree is pinned at `a43212334fd726dec8d69203be0c7d50fd9ce1b0` / `24beb15d868c131b81e354ea34b2b409c4a4062e`.
- External v2.5 import commit/tree is pinned at `040d18018f553faeeae625fd4ef73d50ba0436fb` / `51b90dfdb83f33f55dc3f23b680af6e327fe1fd8`.
- The official scientific-source set contains 26 Fortran files.
- 24/26 files are complete-file identical after generic CVS-keyword normalization.
- `rrtatm.f` has only three documented operational date/time-output comment deltas.
- `rrtm.f` has only one documented operational input-filename literal delta.
- No scientific source delta was identified in RT equations, cloud/gas optics tables, spectral coefficient tables, or band definitions within the pinned 26-file comparison.
- `tools/verify_rrtm_sw_v25_scientific_source_semantics.py` deterministically enforces this boundary.

## Still fail-closed
- Scientific-source semantic equivalence is not whole-repository equality or raw-byte identity.
- Original `aer_rrtm_sw_v2.5.tar.gz` bytes remain unrecovered in the qualified evidence set.
- No provenance-qualified original archive SHA256/MD5 is claimed.
- Historical Q. Fu high-resolution pre-averaging tables/generator and exact solar discrete weights remain unrecovered.
- Band 24/25 deterministic reproduction remains blocked.

## Science/production guard
Frozen science baseline remains `R5.7.41.2_SHADOW_COT_AB_FROZEN`.
No Formation / Viewing / Twilight Glow / six-band / Canvas / Corridor / REZ / Earth Shadow / COT science rule changed.

`EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`  
`TAU_ICE_PRODUCTION_ALLOWED=False`  
`PRODUCTION_ICE_OPTICS_READY=False`  
`physics_promotion_allowed=False`

Step 3R remains blocked.

## Decision
**QA PASS**

Latest formal FIELD baseline before this release is `R5.7.41.3.4.10.30.12 FIELD PASS`. `.10.30.13` requires its own real forecast FIELD CASE before FIELD promotion.
