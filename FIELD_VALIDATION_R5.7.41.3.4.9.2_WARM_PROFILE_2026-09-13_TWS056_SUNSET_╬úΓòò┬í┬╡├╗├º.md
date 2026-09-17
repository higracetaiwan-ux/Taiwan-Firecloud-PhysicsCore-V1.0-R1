# R5.7.41.3.4.9.2 第二跑 Field Validation — TWS056 / 2026-09-13 Sunset

## 結論
`.3.4.9.2` 的 precipitation Phase 2 Field PASS 維持成立；第二跑再次看到 Red-Light precipitation path 約 7.63 s，遠低於 `.3.4.9.1` 的 109.515 s。

本次**不是全 provider warm repeat**。CAMS / GFS 已命中 persistent cache，但 DWD ICON 在兩次執行間由 00Z 更新為 06Z cycle，Open-Meteo canonical JSON cache 也因預設 TTL=1800 s 已過期，因此兩次 science CSV 不應要求 byte-for-byte 相同。

## Runtime
- 第一跑 `TOTAL_ANALYSIS_CORE`: 819.767 s
- 第二跑 `TOTAL_ANALYSIS_CORE`: 475.024 s（-42.1%）
- 第一跑 `TOTAL_TO_CASE_ARCHIVE`: 860.598 s
- 第二跑 `TOTAL_TO_CASE_ARCHIVE`: 515.906 s（-40.1%）
- CAMS prefetch: 330.425 → 4.242 s（5/5 prior-run persistent hits）
- GFS native: 第二跑 0 network request，raw/decoded cache hit
- DWD secondary: 第二跑仍 158 network requests / 171,912,762 bytes
- Open-Meteo: 第二跑 7/7 MISS；canonical request keys 與第一跑相同，但預設 1800 s TTL 已過期

## DWD cycle drift
- 第一跑：ICON run `2026-09-13 00:00Z`, lead 10 h
- 第二跑：ICON run `2026-09-13 06:00Z`, lead 4 h

因此第二跑取得更新的 secondary forecast evidence；這是 provider evidence 更新，不是 `.3.4.9.2` science regression。

## Stable decision semantics
雖然部分 spectral numeric evidence 因 provider 更新而變動，下列 categorical decision/state 保持一致：
- Formation state / Formation gates
- Viewing state / Viewing spectral state
- Photography decision role
- Red-Light path states / Canvas states
- Twilight Glow states
- `summary.csv` operational decision

`v1_formation.csv` 本身兩跑完全一致；Viewing / Red-Light / Glow 的部分數值因 DWD/Open-Meteo evidence 更新而合理改變。

## `.3.4.9.2` Phase 2 stability
- `RED_LIGHT_COMPONENT_PRECIPITATION_PATH`: 6.777 → 7.631 s（執行抖動範圍；仍較 `.3.4.9.1` 約 109.5 s 快約 14× 以上）
- `RED_LIGHT_REFERENCE_AVAILABILITY`: 45.305 → 45.943 s
- Analysis Integrity: 71/71 PASS
- CASE Integrity: 32/32 PASS

## 第二跑非-provider CPU 排名
1. Twilight Glow Independent Branch: 90.977 s
2. Gas + Spectral RT: 48.284 s
3. Red-Light Reference Availability: 45.943 s
4. Cloud 3D Optical Blocking: 41.585 s
5. CASE Export Serialization: 40.882 s
6. Viewing + Photography: 35.547 s

下一個 profiler 應優先拆 Twilight Glow，而不是再次碰 precipitation。
