# Test Report — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.27

## Focused verification
- Step 3N RED：module 尚未存在時 3/3 預期失敗（ModuleNotFoundError）。
- Step 3N core GREEN：3/3 PASS。
- Step 3N handoff RED→GREEN：最終 core + handoff 6/6 PASS。
- Release identity RED：舊 `.10.26` 版本字串如預期失敗。
- Step 3M + Step 3N + UI/version focused regression：**19/19 PASS**。

## Step 3N artifacts
- Evidence：11 rows。
- Gate：1 row。
- Contract：deterministic JSON。
- Reference availability：SSA=true；asymmetry=true。
- Broad-band mapping semantics：PASS。
- Independent SSA numerical validation：false。
- Independent asymmetry numerical validation：false。
- Exact six-band like-for-like optical validation：false。
- `tau_ice` production / Production Ice Optics / physics promotion：false。

## Working-tree full regression
- Collected：910 tests。
- 4 shards：218 / 243 / 214 / 235。
- Result：**910/910 PASS**。
- Warning：1 個既有 pandas `FutureWarning`。

## Candidate FULL-CLEAN verification
- ZIP members：1179。
- cache / pyc / pyo artifacts：0。
- fresh-extract version：`1.0.0-R5.7.41.3.4.10.27`。
- fresh-extract regression：**910/910 PASS**（4 shards：218 / 243 / 214 / 235）。
- 唯一 warning：既有 pandas `FutureWarning`。
- Step 3N evidence：11 rows，byte-exact regeneration PASS，SHA256 `3d3e923d080e6193e44a51f89a53f81fe0dffd158fb5a71834aa946c70ab2d25`。
- Step 3N gate：1 row，byte-exact regeneration PASS，SHA256 `7cf58cde7ff6edef022332fd6898e7ad86ef5f728ab3f74ad48e2c9857cd1766`。
- Step 3N contract：1878 bytes，byte-exact regeneration PASS，SHA256 `d0ad18ccf49ca2ca92a47d1a772c7f137db99e7bbdb2d69ca9f5580c4a511cc6`。

## Final immutable package
本報告更新後重建正式 FULL-CLEAN ZIP；重建後必須執行最後 read-only 910-test、cache hygiene、Step 3N byte-exact regeneration 與 SHA256 封口。
