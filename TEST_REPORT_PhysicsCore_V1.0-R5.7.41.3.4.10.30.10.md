# Test Report — 1.0.0-R5.7.41.3.4.10.30.10

## Pre-package regression
- Step 3Q targeted lineage: **33/33 PASS**
- Full regression: **960/960 PASS**
- Failures: **0**
- Warnings: **1**（既有 pandas FutureWarning；非 failure）

完整 regression 因單次工具執行上限在約 52% 被截斷，因此依既有 release closure 方法改採 mutually-exclusive test-file batches：
- Batch 1：316/316 PASS，1 warning
- Batch 2：344/344 PASS
- Batch 3：263/263 PASS
- Batch 4：37/37 PASS
- 合計：**960/960 PASS**

## Step 3Q.10 新增 regression
1. official AER v2.5 archive filename + web tar-build procedure pinning
2. publication-chain qualification 不得提升 original tarball bytes/hash、mirror byte identity 或 pre-averaging generator
3. contract V1_10 / Step 3Q.10 / fail-closed state identity

## Frozen science guard
`R5.7.41.2_SHADOW_COT_AB_FROZEN` 未修改；Formation / Viewing / Twilight Glow / six-band / Canvas / Corridor / REZ / Earth Shadow / COT science 不變。
