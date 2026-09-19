# Release Closure Verification — PhysicsCore V1.0-R5.7.41.3.4.10.30.12

## Release identity
`V1.0-R5.7.41.3.4.10.30.12`

## Step
**Step 3Q.12 — Official AER Download Endpoint + Independent Extracted-Distribution Footprint Qualification**

Formal state:
`PASS_FAIL_CLOSED_V25_OFFICIAL_DOWNLOAD_ENDPOINT_AND_EXTRACTED_FOOTPRINT_QUALIFIED_ORIGINAL_TARBALL_BYTES_HASH_UNRECOVERED_PREAVERAGING_GENERATOR_UNRECOVERED`

## Regression closure
- Step 3Q targeted lineage: **39/39 PASS**
- Full regression: **966/966 PASS**
- Fresh-extract targeted: **39/39 PASS**
- Fresh-extract collection: **966 tests collected**
- Existing pandas FutureWarning: **1**
- Failures: **0**

## Artifact byte-exact closure
- evidence: `f0d0635aa1de3db2950c118e543d8df927ee302db61bde035c849cff97cf34db`
- gate: `1486efb1e9e9b12e831a7a336ce94917e693d7652489ce599d07f0c4016f5ae2`
- contract V1_12: `80233b50a1af22052b1815e449105b123a5d34924cc64c73e901cdb1624fc82b`

Fresh regeneration of all three Step 3Q artifacts is byte-exact.

## New provenance boundary qualified
- AER official current RRTM_SW page directly links `aer_rrtm_sw_v2.5.tar.gz` to `https://files.aer.com/rtweb/aer_rrtm_sw/aer_rrtm_sw_v2.5.tar.gz`.
- Historical v2.5 update notice pins anonymous FTP distribution under `ftp.aer.com/pub/downloads/aer_rrtm_sw/`.
- Independent installation evidence records an extracted v2.5 footprint containing `src/`, `makefiles/`, `rrtm_sw_instructions`, `update_rrtm_sw_v2.5.txt`, and a makefile with `VERSION = v2.5`.
- `tools/verify_aer_rrtm_sw_v25_archive.py` is included to hash and manifest actual local archive bytes without self-promoting them to authoritative status.
- Step 3Q.11 critical `cldprop.f` / `taumoldis.f` official-vs-mirror CVS-normalized equivalence remains qualified.

## Still fail-closed
- Original `aer_rrtm_sw_v2.5.tar.gz` bytes were not successfully acquired into this release evidence set.
- No provenance-qualified original archive SHA256/MD5 is claimed.
- A live official binary endpoint or secondary extracted footprint is not treated as original-tarball byte identity.
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

Latest formal FIELD baseline before this release is `R5.7.41.3.4.10.30.11 FIELD PASS`. `.10.30.12` requires its own real forecast FIELD CASE before FIELD promotion.
