# Test Report — V1.0-R5.7.41.3.4.10.6

## Targeted regression

- `.10.6` cloud numeric context + adjacent Viewing/Glow chain：**41/41 PASS**
- Covers resolved occupancy, Missing COT, Missing CF, direct conflict, path clear, headerless empty evidence, runtime-context reuse.

## Actual TWS134 exactness

- Main Viewing：585 rows × 74 columns, `check_dtype=True, check_exact=True`
- Glow observer spectral：1092 rows × 74 columns, `check_dtype=True, check_exact=True`
- Main CSV SHA256 exact：`450f38d12db5d4eb2d27f0ce1c7f7495ac5105b644afbf40e3e09a182a23cdd7`
- Glow CSV SHA256 exact：`1eecc0585f520e4d3f5162fbf121600afbbf7633bfd57ca610242b22f8005870`

## Full regression

- Working tree：**678/678 PASS**
- Existing pandas FutureWarning：1（非 failure）
- First FULL-CLEAN fresh-extract gate：**678/678 PASS**
- Existing pandas FutureWarning：1（同既有 warning，非 failure）
- Final re-packed FULL-CLEAN fresh-extract gate：**678/678 PASS**
