# Test Report — PhysicsCore V1.0-R5.7.41.3.4.10.30.14

## 結果
- Step3Q targeted lineage：**45/45 PASS**
- Full test collection：**972 tests**
- Full regression：**972/972 PASS**
- Failures：**0**
- Warnings：**1**（既有 pandas `FutureWarning`，非本版新增）

## 新增測試
`tests/test_r574134103014_pre2020_cross_repository_raw_blob_replication.py`

驗證：
1. 2014 pyrrtm pre-2020 history、26-file cross-repository 22/26 raw-blob match 與 4 critical-file raw replication被明確 pin；
2. `cldprop.f`、`taumoldis.f`、`k_gB24.f`、`k_gB25.f` 的 blob SHA 在 2014 / 2020 pinned histories 間完全一致；
3. cross-repository replication 只能提升 provenance lineage，不能提升 original archive bytes/hash、pre-averaging generator、exact weighting 或 Production Ice Optics；
4. manifest verifier 對 synthetic 26-file Git trees deterministic 計算 22 matches / 4 nonmatches，同時保持 original archive identity/hash=False。

## Science regression boundary
Frozen science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`。  
沒有修改 Formation / Viewing / Twilight Glow / 六波段 / Canvas / Corridor / REZ / Earth Shadow / Production/Shadow COT。
