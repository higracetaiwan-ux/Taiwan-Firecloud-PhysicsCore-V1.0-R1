# Release Closure Verification — PhysicsCore V1.0-R5.7.41.3.4.10.30.10

## Release identity
`V1.0-R5.7.41.3.4.10.30.10`

## Step
**Step 3Q.10 — Official AER v2.5 Archive Publication-Chain Qualification**

Formal state:
`PASS_FAIL_CLOSED_V25_OFFICIAL_ARCHIVE_PUBLICATION_CHAIN_QUALIFIED_ORIGINAL_TARBALL_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED`

## Regression closure
- Step 3Q targeted lineage: **33/33 PASS**
- Full regression: **960/960 PASS**
- Fresh-extract targeted: **33/33 PASS**
- Fresh-extract collection: **960 tests collected**
- Existing pandas FutureWarning: **1**
- Failures: **0**

## Artifact byte-exact closure
- evidence: `5b059e87ff1ff9995a08f0ceee2921412db3af2612636b7cf5443d5a1aff6d7b`
- gate: `edbf59d61846af685cc954ae441859dfd285959ccb83239197d7021a837b5bcb`
- contract V1_10: `3d038fafee25d8b958ad70c948b36f57daf608dd6c38e1793e513bf7fd9673bc`

Fresh regeneration of all three Step 3Q artifacts is byte-exact.

## New provenance boundary qualified
- Official AER source archive filename pinned: `aer_rrtm_sw_v2.5.tar.gz`.
- Official AER 2004 public-release procedure pinned: `script_build_rrtm_sw.pl` builds source/example tar files for the web-site with the proper version number.
- This qualifies the official publication lineage only.

## Still fail-closed
- Original `aer_rrtm_sw_v2.5.tar.gz` bytes not recovered in the qualified evidence set.
- Original archive provenance-qualified cryptographic hash not recovered.
- External mirror byte identity with original AER tarball is not proven.
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

Latest formal FIELD baseline before this release remains `R5.7.41.3.4.10.30.9 FIELD PASS`. `.10.30.10` requires its own real forecast FIELD CASE before promotion to FIELD PASS.
