# Test Report — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.24.1

## TDD
- New Step 3K stable serialization tests：RED 2/2 → GREEN 2/2。
- Focused Step 3K + handoff + UI：14/14 PASS。

## Working-tree regression
- Full test coverage via 10 independent pytest shards: **884/884 PASS**。
- Every shard returned exit code 0。
- 1 existing pandas FutureWarning；非失敗。
- Shard pass counts：87 + 86 + 78 + 101 + 87 + 98 + 77 + 92 + 69 + 109 = 884。

## Static artifact reproducibility
- Step 3K evidence：byte-exact regeneration PASS（5540 bytes）。
- Step 3K gate：byte-exact regeneration PASS（1085 bytes）。
- Step 3K contract：byte-exact regeneration PASS（1845 bytes）。

## Candidate FULL-CLEAN fresh-extract verification
- ZIP members：1128。
- Cache / pyc / pyo artifacts：0。
- Version identity：`1.0.0-R5.7.41.3.4.10.24.1`。
- Full test coverage via 10 shards：**884/884 PASS**；all shard exit codes 0。
- 1 existing pandas FutureWarning。
- Step 3K evidence / gate / contract regeneration：all byte-exact PASS。

## Final immutable package verification
- Rebuilt FULL-CLEAN after including this TEST REPORT.
- Fresh-extract full test coverage via 10 independent pytest shards: **884/884 PASS**；all shard exit codes 0。
- 1 existing pandas FutureWarning；非失敗。
- Step 3K evidence：byte-exact regeneration PASS（5540 bytes）。
- Step 3K gate：byte-exact regeneration PASS（1085 bytes）。
- Step 3K contract：byte-exact regeneration PASS（1845 bytes）。
- Cache / pyc / pyo artifacts：0。
