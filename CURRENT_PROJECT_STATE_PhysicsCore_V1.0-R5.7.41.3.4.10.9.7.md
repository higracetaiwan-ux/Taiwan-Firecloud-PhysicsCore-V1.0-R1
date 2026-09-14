# Taiwan Firecloud PhysicsCore — Current Project State

Current release candidate: **V1.0-R5.7.41.3.4.10.9.7 — Runtime Exact-Source Reuse + GFS Merge Defragmentation**

Internal version: `1.0.0-R5.7.41.3.4.10.9.7`

Science baseline remains frozen at **`R5.7.41.2_SHADOW_COT_AB_FROZEN`**.

## 已完成 Field baseline

- `.10.9 = FIELD PASS`
- `.10.9.3 = FIELD PASS + TWS111 CROSS-SITE PASS`
- `.10.9.4 = FIELD PASS`
- `.10.9.5 = FIELD PASS`
- `.10.9.6 TWS106 = FIELD PASS`

## `.10.9.6 TWS106` 根因結論

- GFS 06Z f004，valid-time offset −21.746 s，alignment PASS。
- 0–100 km source-level 1080 rows：990 exact zero、90 Missing、0 below-threshold positive、0 at/above-threshold positive。
- 0–100 km native voxel 21060 rows：CLWMR/ICMR/cloud fraction positive 全 0。
- 因此 local Ground Truth low cloud mismatch = **GFS native source underrepresentation**；不是 threshold/interpolation/cloud-column reconstruction 刪掉正值。
- 「沒有可用 Native CLWMR/ICMR 光譜 RT 輸入」為正確 fail-close。

## `.10.9.7` Runtime scope

1. CAMS scattering-column request 的 exact 550/645/670/800 AOD 完整時，直接供 spectral AOD 使用；跳過重複 ADS request。
2. 不完整時仍執行原 dedicated spectral request。
3. 新增 exact-reuse provenance Integrity。
4. GFS canonical merge 改 batch concat，消除 highly-fragmented PerformanceWarning。
5. 不修改 DWD 時間態資料重用策略；不同 lead 不跨時次冒充 exact data。

## TWS106 performance proxy

`.10.9.6`：
- worker elapsed 632.94 s
- CAMS prefetch 254.16 s
- dedicated `SPECTRAL_COLUMN_AOD` 47.275 s
- scattering role 已同時要求 550/645/670/800 nm AOD
- 2691/2691 exported CAMS route rows四個 AOD source columns 完整

因此 `.10.9.7` 可在同型完整 scattering response 下少一次 ADS request；實際 Field wall-clock 待正式 CASE。

## Regression

- targeted exact-reuse/defragmentation tests：4 PASS
- adjacent tests：31 PASS
- full working-tree：**722/722 PASS**
- final fresh-extract：**722/722 PASS**
- FULL-CLEAN entries：**842**
- cache/pyc contamination：**0**
- warning：1 existing pandas `FutureWarning`
- status：**REGRESSION PASS / FIELD RETEST CANDIDATE**

## 下一步

先跑 TWS106 `.10.9.7` Field CASE：確認 `CAMS_SPECTRAL_COLUMN_AOD=EXACT_SOURCE_REUSE`、request count 5→4、Integrity PASS、science outputs 無 regression，再比較 CAMS_PREFETCH_TOTAL / worker elapsed。
