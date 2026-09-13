# Taiwan Firecloud PhysicsCore — Current Project State

## 現行版本
**V1.0-R5.7.41.3.4.9 — Red-Light Reference Availability Runtime Hotspot Decomposition**

Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## 已關閉里程碑：R5.7.41.3.4.8
2026-09-13 Sunset / TWS056 淡水漁人碼頭 Field 驗證：
- Viewing Path Geometry：Field PASS；第二跑約 1.973 s。
- Persistent Provider Cache：Field PASS；CAMS 5/5 prior-run persistent hit，DWD network requests 168 → 0。
- warm Total Analysis Core：約 551.075 s。
- 第一跑/第二跑 science outputs 保持一致；差異集中 runtime/provider/manifest metadata。
- Analysis Integrity 第二跑僅 CAMS post-success recovery telemetry WARN；因無 fresh CAMS download，屬 warm-cache 預期現象。

## 現行最大 runtime target
TWS056 warm run：`RED_LIGHT_REFERENCE_AVAILABILITY` 約 153.926 s。

R5.7.41.3.4.9 先拆解為：
1. BUILD_RECEIVERS
2. SPECTRAL_RT
3. CLOUD_PATH
4. VIRTUAL_CANVAS
5. PRECIPITATION_PATH
6. MERGE
7. SIX_BAND_AVAILABILITY
8. PATH_STATE

## 本版狀態
- profiler implementation：完成。
- deterministic exact-equivalence：PASS。
- working-tree regression：641/641 PASS。
- Field profiler：待測。

## 下一步
1. 部署 `.3.4.9`。
2. 優先重跑 **2026-09-13 Sunset / TWS056 淡水漁人碼頭**；同 deployment provider cache 已可 warm reuse 時最具比較價值。
3. 上傳 CASE ZIP。
4. 依八段 profiler 的 Field elapsed_seconds 排名。
5. 只對實測最大 component 做 exact-equivalent optimization。
6. Shadow COT positive cohort 持續隨天氣收集，不阻塞 runtime engineering。
