# Taiwan Firecloud PhysicsCore V1.0 — Test Report

## R5.7.41.3.4.10.30.20

- New Step3Q.20 tests: **4/4 PASS**
- Step3Q lineage: **70/70 PASS**
- Full regression collection: **997 tests**
- Full regression execution: **997/997 PASS**
  - Segment 1: 237/237 PASS
  - Segment 2: 345/345 PASS（1 existing warning）
  - Segment 3: 232/232 PASS
  - Segment 4: 183/183 PASS
- Failures: `0`
- Frozen science unchanged.
- New Band25 verifier: PASS

## Release artifact SHA256
- evidence: `00f5b65bdc64c2c44f93752a45df3f36970e42e8a1d82ed6939ce32e73d38969`
- gate: `13bc95aceac92239e7f89682e572f776d5a0cbe2a35e15683074f472887e3636`
- contract: `cbfdf092aa67f453b1385f6af91d29f328881082ccf087d7074c05bc19763199`

## 備註
單一 `pytest -q` 命令在執行環境的 command timeout 前約跑到 50%，未出現 assertion failure。為取得完整 closure，依排序後的 268 個 test files 分成四段執行；四段覆蓋完整 997-test collection，總計 997/997 PASS。
