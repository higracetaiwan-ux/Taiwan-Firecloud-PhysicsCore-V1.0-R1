# Test Report — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.26

## Working tree
- Step 3M core / handoff / release identity：PASS。
- Adjacent Step 3J / 3K / 3L + UI focused regression：PASS。
- Full regression：**903/903 PASS**，1 個既有 pandas `FutureWarning`。

## Step 3M numerical verification
- single-particle rows：1,962。
- minimum size parameter：58.643062867。
- matched-geometry bulk cases / rows：18 / 324。
- max matched bulk relative difference：0.028779758046。
- mean matched bulk relative difference：0.005933343552。
- max grid-convergence relative error：2.8615945e-06。

## Fail-close verification
- independent SSA/g validation：false。
- full optical validation：false。
- scientific bulk validation：false。
- `tau_ice` production：false。
- Production Ice Optics：false。
- physics promotion：false。

## Candidate FULL-CLEAN verification
- ZIP members：1164。
- cache / pyc / pyo artifacts：0。
- fresh-extract version：`1.0.0-R5.7.41.3.4.10.26`。
- fresh-extract regression：**903/903 PASS**（4 shards：210 / 257 / 198 / 238）。
- 唯一 warning：既有 pandas `FutureWarning`。
- Step 3M evidence：12 rows，byte-exact regeneration PASS。
- Step 3M gate：1 row，byte-exact regeneration PASS。
- Step 3M contract：2499 bytes，byte-exact regeneration PASS。
- Artifact SHA256：
  - evidence `05c9fb344947b5c0b5b515023d8bdeb4793c935f0662152a87b347877f69577b`
  - gate `6ac19754b310e7c4c606517b23be977d2eefefbb4b755a1ef36461cf87b01a9c`
  - contract `671e861e353f49e2c219a5a7658e3a985b6bd30dbd861569e593445138c5e5ea`

## Final immutable package
本報告更新後重建正式 FULL-CLEAN ZIP；重建後必須執行最後 read-only 903-test、cache hygiene、Step 3M byte-exact regeneration 與 SHA256 封口。
