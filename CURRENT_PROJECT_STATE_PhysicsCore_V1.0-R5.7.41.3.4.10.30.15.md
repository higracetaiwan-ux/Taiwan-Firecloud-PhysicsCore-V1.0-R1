# Taiwan Firecloud PhysicsCore — Current Project State

- Version: `1.0.0-R5.7.41.3.4.10.30.16`
- Engineering step: **Step 3Q.15**
- QA state: **QA PASS / FIELD pending**
- Latest FIELD baseline before this release: `R5.7.41.3.4.10.30.14 FIELD PASS`
- Frozen science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`
- Qualification state: `PASS_FAIL_CLOSED_AER_HISTORICAL_RRTM_BAND_GENERATION_PIPELINE_SCOPE_QUALIFIED_ORIGINAL_TARBALL_BYTES_HASH_UNRECOVERED_FU96_CLOUD_PREAVERAGING_GENERATOR_UNRECOVERED`

## New evidence
AER official 2004 RRTM_SW v2.5 and AER official 2007 RRTMG_SW preserve identical Fu96 final cloud tables for `EXTICE3`, `SSAICE3`, `ASYICE3`, `FDLICE3`: **56/56 arrays, 2576/2576 values identical**.

## Still blocked
- original AER v2.5 tarball bytes/hash
- Fu96 high-resolution pre-averaging samples
- historical band-averaging generator
- exact historical solar spectrum/discrete weights
- deterministic Band 24/25 reproduction
- Production Ice Optics
- Step 3R
