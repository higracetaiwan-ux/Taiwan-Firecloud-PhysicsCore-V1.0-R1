# Taiwan Firecloud PhysicsCore V1.0 — Test Report

## R5.7.41.3.4.10.30.21

- Step3Q.21 / CAMS targeted: **12/12 PASS**
- Step3Q lineage: **76/76 PASS**
- Full regression collection: **1003 tests**
- Full regression execution: **1003/1003 PASS**
  - batch 0: 69/69 PASS
  - batch 1: 95/95 PASS
  - batch 2: 68/68 PASS
  - batch 3: 84/84 PASS
  - batch 4: 81/81 PASS
  - batch 5: 100/100 PASS
  - batch 6: 84/84 PASS（1 existing pandas FutureWarning）
  - batch 7: 89/89 PASS
  - batch 8: 77/77 PASS
  - batch 9: 83/83 PASS
  - batch 10: 83/83 PASS
  - batch 11: 90/90 PASS
- Failures: `0`
- Step3Q.21 verifier: PASS
- Frozen science unchanged.

## Release artifact SHA256
- evidence: `f43ba4fa7dcf869fcc18eccadec105f3f52eb9239f62d236fa38ec6767d426ad`
- gate: `7a873a8877ce00b3764632fe863cbbd093cb20fb99ab677b8e44f64ba2fceeda`
- contract: `bc0f646466c5c97ae693b84dbccc43e54564fa7b0a1ea99796993b60dfe5de18`

## 備註
單一 `pytest -q` 在執行環境 command timeout 前跑到約 50%，未出現 assertion failure。為避免把 timeout 誤當 PASS，本版依 269 個 test files 分成 12 個獨立批次重新覆蓋完整 1003-test collection，合計 1003/1003 PASS。
