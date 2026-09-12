# Test Report — PhysicsCore V1.0-R5.7.41.3.4.8

## Field profiler source
2026-09-12 Sunset｜TWS106 高美濕地｜V1.0-R5.7.41.3.4.7.1 CASE.

## Integrity of profiler CASE
- Analysis Integrity: 72/72 PASS
- CASE Integrity: 32/32 PASS
- `.3.4.6 ↔ .3.4.7.1` core science CSV exact comparison: 10/10 byte-for-byte identical.

## Viewing Path Geometry A/B
Input workload:
- cloud layers: 4940 rows
- Canvas targets: 1131 rows
- time/angle/direction transects: 39

Reference R5.7.41.3.4.7.1 implementation:
- 13.210126 s local benchmark

R5.7.41.3.4.8 implementation:
- 1.657015 s local benchmark
- speedup: ~7.97x
- output: 1131 rows x 25 columns
- exact comparison: 0 differences, treating NaN-to-NaN as equal

## Tests
- Viewing/runtime targeted suite: 19/19 PASS
- Working-tree full regression: 638/638 PASS
- Final FULL-CLEAN fresh-extract full regression: 638/638 PASS
- Existing pandas FutureWarning: 1; non-failure and pre-existing

## Archive hygiene
- `__pycache__`: 0
- `.pytest_cache`: 0
- `.pyc`: 0
- `.firecloud_state`: 0
- runtime provider cache payloads: 0

## Science contract
No threshold, wavelength, Formation gate, Earth Shadow rule, COT semantic, Viewing obstruction semantic, Twilight Glow branch, or Photography decision rule changed.
