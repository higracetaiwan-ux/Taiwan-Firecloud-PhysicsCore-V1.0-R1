# Test Report — PhysicsCore V1.0-R5.7.41.3.4.10.30.12

## 結果
- Step3Q targeted lineage：**39/39 PASS**
- Full test collection：**966 tests**
- Full regression：**966/966 PASS**
- Failures：**0**
- Warnings：**1**（既有 pandas `FutureWarning`，非本版新增）

## 新增測試
`tests/test_r574134103012_official_aer_download_endpoint_and_footprint.py`

驗證：
1. AER 官方 binary endpoint、歷史 FTP path、secondary extracted footprint 均被明確 pin；
2. 新 evidence 只能提升 lineage，不得提升 original archive bytes/hash、pre-averaging generator、exact weighting 或 Production Ice Optics；
3. archive verifier 能對本地 tar.gz 計算 SHA256/MD5、tar manifest 與 footprint，但不會自行宣告 authoritative archive hash / byte identity。

## Science regression boundary
Frozen science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`。
沒有修改 Formation / Viewing / Twilight Glow / 六波段 / Canvas / Corridor / REZ / Earth Shadow / Production/Shadow COT。
