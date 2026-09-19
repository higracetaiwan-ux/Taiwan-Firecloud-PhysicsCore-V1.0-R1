# Release Closure Verification — PhysicsCore V1.0-R5.7.41.3.4.10.30.11

## Release identity
`V1.0-R5.7.41.3.4.10.30.11`

## Step
**Step 3Q.11 — Official AER Historical Source-Tree CVS-Normalized Equivalence Qualification**

Formal state:
`PASS_FAIL_CLOSED_V25_OFFICIAL_SOURCE_TREE_CVS_NORMALIZED_EQUIVALENCE_QUALIFIED_ORIGINAL_TARBALL_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED`

## Regression closure
- Step 3Q targeted lineage: **36/36 PASS**
- Full regression: **963/963 PASS**
- Fresh-extract targeted: **36/36 PASS**
- Fresh-extract collection: **963 tests collected**
- Existing pandas FutureWarning: **1**
- Failures: **0**

## Artifact byte-exact closure
- evidence: `625e582660536f40a944f48e2a1888a14df5fc82157402dc1bb9f9a6836faf6b`
- gate: `470a7a84af79d84a4b17f4c64a1928949714dba1904a403e5124a19f4cf09bb9`
- contract V1_11: `1d2bf6bdd5653ba8801902f15aac0491f3ecf46d5fcaa1a5048791f2252fc068`

Fresh regeneration of all three Step 3Q artifacts is byte-exact.

## New provenance boundary qualified
- AER official historical `src/cldprop.f` commit `356609ea083f9684dc83a56e3f5c96515cb25b19`, date `2004-04-15T18:42:10Z`, blob `8632f7d1940285665b62fdbb30c69861924251da` is pinned.
- AER official historical `src/taumoldis.f` commit `a43212334fd726dec8d69203be0c7d50fd9ce1b0`, date `2004-04-15T18:50:57Z`, blob `b2b1080fe51b7c3d512de26b4507314fee17ff58` is pinned.
- Official `cldprop.f` and the external v2.5 mirror import are 2080-line full-file equivalents after canonical CVS keyword normalization.
- Official `taumoldis.f` and the external v2.5 mirror import are 2054-line full-file equivalents after canonical CVS keyword normalization; the mirror preserves revision 2.5 / 2004-04-15 18:50:57.
- This qualifies the pinned critical historical source-tree equivalence only.

## Still fail-closed
- Original `aer_rrtm_sw_v2.5.tar.gz` bytes are not recovered in the qualified evidence set.
- Original archive provenance-qualified cryptographic hash is not recovered.
- CVS-normalized critical source equivalence is not treated as original tarball byte identity.
- Entire external repository/archive byte identity with the original AER tarball is not proven.
- Historical Q. Fu pre-averaging tables/generator and exact solar discrete weights remain unrecovered.
- Band 24/25 exact reproduction remains blocked.

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

Latest formal FIELD baseline before this release remains `R5.7.41.3.4.10.30.10 FIELD PASS`. `.10.30.11` requires its own real forecast FIELD CASE before promotion to FIELD PASS.
