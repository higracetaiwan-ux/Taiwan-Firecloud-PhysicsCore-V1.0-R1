# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.9

## Red-Light Reference Availability Runtime Hotspot Decomposition

本版延續 R5.7.41.3.4.8，凍結科學基線仍為 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。

### R5.7.41.3.4.8 Field 結論
2026-09-13 Sunset / TWS056 淡水漁人碼頭同一 deployment 連續兩跑：
- persistent provider cache 跨 analysis job 正常命中；第二跑 DWD network requests = 0，CAMS 5/5 為 prior-run persistent cache；
- Total Analysis Core 約 927.6 s → 551.1 s；
- Viewing Geometry 第二跑約 1.973 s，Phase 1 Field PASS；
- warm run 最大可分解 stage 改為 `RED_LIGHT_REFERENCE_AVAILABILITY`，約 153.926 s。

### 本版改動
只新增 Red-Light 八段 component profiler：receiver selection、spectral RT、cloud path、virtual canvas、precipitation path、merge、six-band availability、path-state assembly。

### 科學不變
不改 reference receivers、不減六波段、不改 ray sampling、不改 blocker / precipitation / Missing semantics，也不改 Formation / Viewing / Glow / Photography / Earth Shadow / COT。

### 驗證
- Red-Light profiler-on / profiler-off deterministic science output：`check_exact=True`。
- Targeted runtime/profiler regression：18/18 PASS。
- Working-tree full regression：641/641 PASS。
- 1 個既有 pandas FutureWarning，非失敗。

### Field 狀態
此版為 **Field-Test Candidate**。下一步以 TWS056 / 2026-09-13 Sunset warm-cache CASE 實跑，依八段 profiler 排名後才選擇 Phase 1 optimization target。
