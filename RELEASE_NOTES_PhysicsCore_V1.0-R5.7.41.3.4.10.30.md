# Release Notes — PhysicsCore V1.0-R5.7.41.3.4.10.30

## Step 3Q：Fu96/RRTMG Exact Band-Weighting Provenance Qualification

本版新增 `firecloud/ice_microphysics_fu96_rrtmg_band_weighting_provenance.py`，建立 reproducible fail-closed provenance gate。

### 新增
- Fu96 primary source provenance pin。
- RRTMG Fu96 Dge lineage pin。
- band 24/25 final Fu96 table provenance pin。
- exact weighting prerequisites audit。
- 明確禁止未驗證的 weighting substitute。
- model / CASE archive / case-integrity handoff。
- stable canonical JSON contract serialization。

### 科學結果
目前公開、已 pin 的證據足以確認 lineage 與 final broad-band tables，但不足以重建 Fu96 high-resolution → RRTM_SW band 24/25 的 exact weighting transformation。因此本版不宣告 exact weighting PASS。

### Frozen science
Formation / Viewing / Twilight Glow、六波段、Canvas、Dynamic Corridor/REZ、Earth Shadow、Production/Shadow COT、Missing≠Clear≠Zero 全部不變。

### Regression
933/933 PASS；1 個既有 pandas FutureWarning，非失敗。
