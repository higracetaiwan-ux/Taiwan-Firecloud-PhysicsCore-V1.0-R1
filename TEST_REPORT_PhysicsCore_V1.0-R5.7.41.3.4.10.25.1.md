# Test Report — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.25.1

## Working tree
- Step 3L stable-contract FIELD-variant regression：PASS。
- Step 3L core / handoff / UI focused regression：PASS。
- Full regression：**894/894 PASS**，1 個既有 pandas `FutureWarning`。

## Root-cause validation
- `.10.25` CASE/release evidence：byte-exact。
- `.10.25` CASE/release gate：byte-exact。
- `.10.25` contract：兩個 diagnostic sample fields 出現跨平台尾數差異，已由新增 regression test 穩定重現。

## Hotfix scope
- Evidence/source-row stable precision：11 significant digits，未更動。
- Contract sample stable precision：8 significant digits，只作用於四個 `sample_roughness_bulk_ensemble` diagnostic fields。
- Scientific calculations：full double precision，未更動。
- Frozen Science / production gates：未更動。

## Candidate FULL-CLEAN verification
- ZIP members：1151。
- cache / pyc / pyo artifacts：0。
- fresh-extract version：`1.0.0-R5.7.41.3.4.10.25.1`。
- fresh-extract regression：**894/894 PASS**（4 independent shards：215 / 248 / 209 / 222）。
- 唯一 warning：既有 pandas `FutureWarning`。
- Step 3L evidence：12 rows，byte-exact regeneration PASS。
- Step 3L gate：1 row，byte-exact regeneration PASS。
- Step 3L contract：byte-exact regeneration PASS。
- Candidate contract sample canonical values：`0.29651019` / `2.1492854e-06` / `0.016970706` / `5.2712977e-07`。

## Final immutable package
本報告更新後重建正式 FULL-CLEAN ZIP；重建後必須執行最後 read-only 894-test、cache hygiene、Step 3L byte-exact regeneration 與 SHA256 封口。
