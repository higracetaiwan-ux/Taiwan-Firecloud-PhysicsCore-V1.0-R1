# Taiwan Firecloud PhysicsCore — Release Closure Verification

## Release
`V1.0-R5.7.41.3.4.10.30.8`

名稱：**Step 3Q.8 — External RRTM_SW v2.5 Distribution Lineage Qualification**

Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## Qualification state
`PASS_FAIL_CLOSED_V25_EXTERNAL_DISTRIBUTION_LINEAGE_QUALIFIED_PREAVERAGING_GENERATOR_UNRECOVERED`

## Evidence added
- pinned external RRTM_SW v2.5 distribution mirror at commit `a2d974ecefe6f369661bf5a3dfc648f07986ad89`
- v2.5 update note blob `00ac405ca9805ee9fc4fbaad0f0ce3733a72b67b`
- v2.5 makefile blob `0baee98667f89d05e46ed6138cde0057c6e07393`
- v2.5 cldprop blob `d7a2efce33cdf5c1f02a66e598c685ef53b7b8c8`
- v2.5 taumoldis blob `339d64ecb0a4f8fa49938ac4a18ce731e27e34f0`

External v2.5 `cldprop.f` and pinned AER `cldprop.f` are both 2080 lines; the observed five differing lines are CVS keyword expansion/stripping only. This qualifies science/runtime lineage equivalence without claiming original AER tarball byte identity.

## Production guards
All remain fail-closed:
- exact Fu96 weighting unavailable
- pre-averaging generator unrecovered
- exact band 24/25 reproduction false
- independent SSA/g validation false
- tau_ice production disallowed
- Production Ice Optics not ready
- physics promotion disallowed

## Regression
- Step 3Q targeted: **26/26 PASS**
- Full regression: **954/954 PASS**
- Existing pandas FutureWarning: 1
- Failures: 0
- Fresh-extract targeted: **26/26 PASS**

## Artifact byte-exact closure
- evidence SHA256: `5bb874e1b4ef1ca7e3a389978886021b9e7fe65749e624eb969531c9f2d5cecc` — PASS
- gate SHA256: `6db1d034e36840a5615d80b4ce622c60d047fe4036f112ecfab2925c523f41d9` — PASS
- contract SHA256: `71365fee9cc7967aca79ff3731a0ff609a1800c1363afb2228aea5b4ede12463` — PASS

## Decision
**QA PASS / FIELD CASE pending**

Step 3R remains blocked until an authoritative or provenance-linked Q. Fu high-resolution pre-averaging table/generator is recovered and band 24/25 exact reproduction succeeds.
