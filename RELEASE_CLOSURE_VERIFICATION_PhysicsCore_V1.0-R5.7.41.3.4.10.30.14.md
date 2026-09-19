# Release Closure Verification — PhysicsCore V1.0-R5.7.41.3.4.10.30.14

## Release identity
`V1.0-R5.7.41.3.4.10.30.14`

## Step
**Step 3Q.14 — Pre-2020 Cross-Repository Critical Fu96 Raw-Blob Replication Qualification**

Formal state:
`PASS_FAIL_CLOSED_V25_PRE2020_CROSS_REPOSITORY_CRITICAL_FU96_RAW_BLOB_REPLICATION_QUALIFIED_ORIGINAL_TARBALL_BYTES_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED`

## Regression closure
- Step 3Q targeted lineage: **45/45 PASS**
- Full regression: **972/972 PASS**
- PRE-CLOSURE fresh-extract targeted: **45/45 PASS**
- PRE-CLOSURE fresh-extract collection: **972 tests collected**
- Final FULL-CLEAN fresh-extract targeted: **45/45 PASS**
- Final FULL-CLEAN fresh-extract collection: **972 tests collected**
- Existing pandas FutureWarning: **1**
- Failures: **0**

## Artifact byte-exact closure
- evidence: `f1d57c11da592ac89c734b9211956580ce47d85b252434ec2a45c46ed14dd8f9`
- gate: `eb969f1720e756b1950075d43c92056231087fcf29fc010365c3aaa0059a8a67`
- contract V1_14: `906d0031a5ec26ad657a38b95f671f50fcdfa8f43b0204e70165d55d238270bc`

Fresh regeneration of all three Step 3Q artifacts from both the PRE-CLOSURE and final FULL-CLEAN fresh-extract trees is byte-exact.

## New provenance boundary qualified
- Pre-2020 comparison history is pinned to `tomflannaghan/pyrrtm` commit `31d776362503c20e84d2a6d78be4a96517f89e49`, dated `2014-07-14T13:11:02Z`, tree `e4a56fd0b150b6536e9653c9b4446aa5a0a03d31`.
- External v2.5 mirror import remains pinned to `nickedkins/RRTM-LWandSW-Python-wrapper` commit `040d18018f553faeeae625fd4ef73d50ba0436fb`, dated `2020-03-17T22:23:17Z`, tree `51b90dfdb83f33f55dc3f23b680af6e327fe1fd8`.
- Fixed scientific-source comparison set: **26 files**.
- Cross-repository raw Git-blob equality: **22/26 files**.
- Four critical Fu96 / weighting-context files are raw-byte replicated across the pinned 2014 and 2020 histories:
  - `cldprop.f` → `d7a2efce33cdf5c1f02a66e598c685ef53b7b8c8`
  - `taumoldis.f` → `5111a3bb7d981ea8facb4733c2ebb8d7f1308486`
  - `k_gB24.f` → `7847f1d19a9008137d60db422c623505ebf8835e`
  - `k_gB25.f` → `e3cc504280805b0b2de725d5645334095a92b07e`
- `tools/verify_rrtm_sw_v25_cross_repository_raw_blobs.py` deterministically enforces the pinned-manifest comparison boundary.

## Still fail-closed
- Cross-repository replication is **not** proof of two independent original distributions; both repository histories may descend from the same historical AER distribution lineage.
- Cross-repository raw-blob equality is **not** original `aer_rrtm_sw_v2.5.tar.gz` byte identity.
- Original AER v2.5 tarball bytes remain unrecovered in the qualified evidence set.
- No provenance-qualified original archive SHA256/MD5 is claimed.
- Historical Q. Fu high-resolution pre-averaging samples/generator and exact solar discrete weighting realization remain unrecovered.
- Band 24/25 deterministic reproduction remains blocked.

## Science/production guard
Frozen science baseline remains `R5.7.41.2_SHADOW_COT_AB_FROZEN`.
No Formation / Viewing / Twilight Glow / six-band / Canvas / Corridor / REZ / Earth Shadow / COT science rule changed.

`AER_OFFICIAL_RRTM_SW_V25_ARCHIVE_BYTES_RECOVERED=False`  
`AER_OFFICIAL_RRTM_SW_V25_ARCHIVE_HASH_RECOVERED=False`  
`RRTM_SW_PREAVERAGING_GENERATOR_RECOVERED=False`  
`EXACT_FU96_BAND_WEIGHTING_AVAILABLE=False`  
`TAU_ICE_PRODUCTION_ALLOWED=False`  
`PRODUCTION_ICE_OPTICS_READY=False`  
`physics_promotion_allowed=False`

Step 3R remains blocked.

## Decision
**QA PASS / FIELD pending**

Latest formal FIELD baseline before this release is `R5.7.41.3.4.10.30.13 FIELD PASS`. `.10.30.14` requires its own real forecast FIELD CASE before FIELD promotion.
