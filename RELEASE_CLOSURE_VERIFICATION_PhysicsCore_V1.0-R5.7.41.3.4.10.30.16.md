# Release Closure Verification — PhysicsCore V1.0 R5.7.41.3.4.10.30.16

## Release identity
- Version: `1.0.0-R5.7.41.3.4.10.30.16`
- Step: `R5.7.41.3.4.10.30.16`
- Contract: `FIRECLOUD_ICE_FU96_RRTMG_BAND_WEIGHTING_PROVENANCE_V1_16`
- Science baseline: `R5.7.41.2_SHADOW_COT_AB_FROZEN`

## Qualification state
`PASS_FAIL_CLOSED_AER_HISTORICAL_RRTM_BAND_GENERATION_PIPELINE_SCOPE_QUALIFIED_ORIGINAL_TARBALL_BYTES_HASH_UNRECOVERED_FU96_CLOUD_PREAVERAGING_GENERATOR_UNRECOVERED`

## New provenance closure
- AER-RC `rrtmgp-band-generation` public repository is pinned as an imported AER `RRTM_BAND_GEN` SVN history.
- Imported git-svn history count: 176 commits; earliest imported commit timestamp: 2014-03-03.
- 2014-04-02 AER commit `5ce72bd363c993189767f09f1c9fe9bc84b72c56` states that initial band-generation codes from Karen and original RRTM work were added with no modifications yet.
- Pinned code scope: LBLRTM optical-depth driven molecular k-distribution, continuum/minor-gas, g-band and Planck-related generation.
- No provenance-linked Fu96 high-resolution ice-cloud sample set or Fu96 cloud-optics band-averaging generator is promoted from this evidence.

## Fail-close state
- Historical AER molecular band-generation pipeline recovered: True
- Historical AER pipeline is Fu96 cloud pre-averaging generator: False
- Fu96 cloud pre-averaging generator recovered: False
- Original AER v2.5 tarball bytes/hash recovered: False
- Exact Fu96 band weighting available: False
- Band 24 exact reproduction: False
- Band 25 exact reproduction: False
- Production Ice Optics ready: False
- Physics promotion allowed: False

## Regression
- Step3Q lineage: **51/51 PASS**
- Full regression: **978/978 PASS**
- Failures: **0**
- Warning: one pre-existing pandas `FutureWarning`

## PRE-CLOSURE fresh-extract
- ZIP members: 1262
- CRC: PASS
- cache/pyc: 0
- directory entries: 29
- Step3Q fresh-extract: 51/51 PASS
- pytest collection: 978 tests
- provenance evidence regeneration: BYTE-EXACT PASS
- provenance gate regeneration: BYTE-EXACT PASS
- provenance contract regeneration: BYTE-EXACT PASS

## Provenance artifact SHA256
- evidence: `0281c0720f993c28e5179216d3759d9c1e38e3e828b187d9e1cacfa8d358d144`
- gate: `3006762946f481e29fd4d296449a66b67c3c8d0c930d54a146f12e2fb546cead`
- contract: `d4b2eaf80d4cc6b36a57e2368eb79d101871ab1f1edcf76c1324858301216979`

Final FULL-CLEAN ZIP is subject to one final ZIP CRC + fresh-extract Step3Q/collection/artifact-byte-exact verification after this file is included.

## Final FULL-CLEAN verification
- Final package members before closure-report sync: 1263
- Final package CRC: PASS
- Final fresh-extract Step3Q: 51/51 PASS
- Final fresh-extract pytest collection: 978 tests
- Final evidence regeneration: BYTE-EXACT PASS
- Final gate regeneration: BYTE-EXACT PASS
- Final contract regeneration: BYTE-EXACT PASS

The package is re-packed once after recording this verification, followed by a final CRC/fresh-extract verification. No program code, science rule, provenance artifact, or test content is changed in that last re-pack.
