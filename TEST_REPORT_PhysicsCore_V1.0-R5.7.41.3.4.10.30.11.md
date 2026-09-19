# Test Report — 1.0.0-R5.7.41.3.4.10.30.11

## Pre-package regression
- Step 3Q targeted lineage: **36/36 PASS**
- Full regression: **963/963 PASS**
- Failures: **0**
- Warnings: **1**（既有 pandas FutureWarning；非 failure）

完整 regression 採 mutually-exclusive test-file batches：
- Batch 1：218/218 PASS
- Batch 2：268/268 PASS
- Batch 3：223/223 PASS，1 warning
- Batch 4：254/254 PASS
- 合計：**963/963 PASS**

## Step 3Q.11 新增 regression
1. AER 官方 2004 `cldprop.f` / `taumoldis.f` history + pinned commit/blob metadata。
2. official ↔ external mirror critical files 的 CVS-normalized full-file equivalence qualification。
3. source-tree equivalence 只提升 provenance lineage，不得提升 original tarball bytes/hash、pre-averaging generator、exact weighting 或 Production Ice Optics。
4. contract V1_11 / Step 3Q.11 / fail-closed state identity。

## Frozen science guard
`R5.7.41.2_SHADOW_COT_AB_FROZEN` 未修改；Formation / Viewing / Twilight Glow / six-band / Canvas / Corridor / REZ / Earth Shadow / COT science 不變。
