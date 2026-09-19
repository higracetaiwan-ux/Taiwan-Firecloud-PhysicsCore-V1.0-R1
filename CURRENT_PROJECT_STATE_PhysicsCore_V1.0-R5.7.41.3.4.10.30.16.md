# Taiwan Firecloud PhysicsCore — Current Project State

## Current engineering release
`R5.7.41.3.4.10.30.16`

## Frozen science baseline
`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## Step 3Q.16 conclusion
AER historical `RRTM_BAND_GEN` molecular/k-distribution/Planck pipeline is provenance-qualified from the public AER-RC `rrtmgp-band-generation` repository and imported SVN history. This **does not** recover the Fu96 ice-cloud high-resolution pre-averaging generator.

Current key state:
- Historical AER molecular band-generation pipeline recovered: **True**
- Fu96 cloud pre-averaging generator recovered: **False**
- Original AER v2.5 tarball bytes/hash recovered: **False**
- Exact historical solar/discrete weighting recovered: **False**
- Band 24 exact reproduction: **False**
- Band 25 exact reproduction: **False**
- Production Ice Optics ready: **False**
- Step 3R: **Blocked**

## Preserved prior qualifications
- Official AER v2.5 archive publication chain and download endpoint pinned.
- Official AER 2004 source tree ↔ external mirror CVS-normalized equivalence qualified.
- 26-file scientific-source semantic equivalence qualified with documented operational deltas.
- 2014 pyrrtm ↔ 2020 mirror: 22/26 raw Git-blob replication; critical `cldprop/taumoldis/k_gB24/k_gB25` raw-byte replicated.
- AER official 2004 RRTM_SW → 2007 RRTMG_SW Fu96 final-table continuity: 56/56 arrays, 2576/2576 values.

## Next provenance blockers
1. Recover original `aer_rrtm_sw_v2.5.tar.gz` bytes/hash or authoritative equivalent.
2. Recover provenance-linked Fu96 high-resolution ice-cloud spectral sample set.
3. Recover the Fu96 cloud table band-averaging generator and exact solar/discrete weights.
4. Deterministically reproduce archived Band 24 and Band 25 tables.
5. Only then consider Step 3R.
