# Test Report — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.25

## Working tree
- Step 3L core / handoff / UI focused regression：PASS。
- Historical archive fixture regression：PASS after adding the three required Step 3L CASE members。
- Full regression：**892/892 PASS**，1 個既有 pandas `FutureWarning`，pytest exit code 0。

## Step 3L deterministic artifacts
- Evidence：12 rows，byte-exact regeneration PASS。
- Gate：1 row，byte-exact regeneration PASS。
- Contract：byte-exact regeneration PASS。

## Candidate FULL-CLEAN
- ZIP members：1141。
- cache / pyc / pyo artifacts：0。
- fresh-extract version：`1.0.0-R5.7.41.3.4.10.25`。
- fresh-extract regression：**892/892 PASS**（10 independent shards；每個 shard exit code 0）。
- Step 3L evidence / gate / contract：fresh-extract byte-exact regeneration PASS。

## Final package verification
- ZIP members：1141。
- cache artifacts：0。
- fresh-extract version：`1.0.0-R5.7.41.3.4.10.25`。
- fresh-extract regression：**892/892 PASS**（10 independent shards；每個 shard exit code 0）。
- 唯一 warning：既有 pandas `FutureWarning`。
- Step 3L evidence / gate / contract：三者 byte-exact regeneration PASS。

> 本報告更新後會重建正式 ZIP；重建後的 immutable package 必須再次完成相同 892-test / artifact-regeneration read-only verification，才能作為交付檔。
