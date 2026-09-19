# Test Report — PhysicsCore V1.0-R5.7.41.3.4.10.30.13

## 結果
- Step3Q targeted lineage：**42/42 PASS**
- Full test collection：**969 tests**
- Full regression：**969/969 PASS**
- Failures：**0**
- Warnings：**1**（既有 pandas `FutureWarning`，非本版新增）

## 新增測試
`tests/test_r574134103013_official_aer_scientific_source_semantic_equivalence.py`

驗證：
1. 26-file official scientific-source set、24/26 normalized full-file matches、2 files / 4 lines operational deltas均被明確 pin；
2. scientific-source semantic equivalence 只能提升 provenance lineage，不得提升 raw-byte identity、original archive bytes/hash、pre-averaging generator、exact weighting 或 Production Ice Optics；
3. semantic verifier 對 synthetic 26-file trees 能 deterministic 接受 generic CVS expansion + 兩種 documented operational deltas，其他 delta 則 fail-close。

## Science regression boundary
Frozen science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`。  
沒有修改 Formation / Viewing / Twilight Glow / 六波段 / Canvas / Corridor / REZ / Earth Shadow / Production/Shadow COT。
