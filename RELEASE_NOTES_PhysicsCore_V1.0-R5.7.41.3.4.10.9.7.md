# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.9.7 Release Notes

## Runtime Exact-Source Reuse + GFS Merge Defragmentation

`.10.9.6` TWS106 正式 CASE 已證明 near-field low-cloud mismatch 來自 GFS native source underrepresentation，而該次總 runtime 約 633 s；主要耗時之一為 CAMS prefetch。

本版只做 exact-reuse / runtime hygiene，不修改 Frozen Physics。

### 1. CAMS Spectral AOD exact reuse

CAMS `AEROSOL_SCATTERING_COLUMN_PROPERTIES` 本身已包含 provider-native 550/645/670/800 nm AOD。當四波段在整條 route 完整時，直接 handoff 給 spectral AOD consumer，跳過重複 `SPECTRAL_COLUMN_AOD` ADS request。

若不完整則 fail back 到原 dedicated request，沒有資料合成。

TWS106 `.10.9.6` Field proxy：dedicated spectral request 曾耗時 **47.275 s**；scattering request 與 spectral request 使用相同 date/time/lead/area 且都要求 550/645/670/800 nm。正式 route snapshot 2691/2691 rows 四個 source AOD 欄位完整。因此下一次同型 cold run 可少一個 ADS request；實際 wall-clock 改善仍以 Field CASE 為準。

### 2. GFS merge defragmentation

將 `gfs_native.merge_native_into_snapshot()` 的 canonical 欄位建立改成 batch concat，移除正式 CASE 中大量 pandas highly-fragmented PerformanceWarning。數值 precedence 與 Missing semantics 不變。

### 3. Integrity

新增 `CAMS_SPECTRAL_AOD_EXACT_REUSE_PROVENANCE`。只有 audit 明確標記 exact reuse 且 source role 為 `AEROSOL_SCATTERING_COLUMN_PROPERTIES`、provider elapsed=0 才 PASS。

### Science baseline

仍為 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。
