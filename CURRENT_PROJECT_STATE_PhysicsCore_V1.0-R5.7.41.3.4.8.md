# Taiwan Firecloud PhysicsCore — Current Project State

## 現行版本
**V1.0-R5.7.41.3.4.8 — Viewing Path Geometry Runtime Optimization Phase 1**

Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`

## R5.7.41.3.4.7.1 Field CASE 結論
事件：2026-09-12 Sunset｜TWS106 高美濕地。

Integrity：
- Analysis：72/72 PASS
- CASE：32/32 PASS
- 10 份核心 science CSV 與 R5.7.41.3.4.6 warm baseline byte-for-byte exact-equivalent。

Viewing/Photography profiler：
- total 130.925 s
- Path Geometry 56.920 s（43.5%，最大戶）
- Spectral Extinction 40.711 s（31.1%）
- Precipitation Evidence 15.091 s
- Target Optics Reconciliation 9.206 s
- Prepare Spectral Runtime Context 8.544 s
- 其餘 summary/status/decision < 0.5 s 合計。

## R5.7.41.3.4.8 已完成
- Geometry immutable plan + numeric array fast path。
- 17-point LOS double-sampling removal（sample reuse）。
- TWS106 1131-target exact-equivalence 0 differences。
- 本機 geometry 13.210 s → 1.657 s（約 7.97×；僅工程 benchmark，非 Field 結論）。
- working-tree full regression 638/638 PASS。

## 另一個獨立營運發現
`.3.4.7.1` run mode 雖標 `WARM_PRODUCTION`，但部署後 provider cache 實際為 cold/current-run：
- CAMS prefetch 311.126 s；五角色均為 CURRENT_RUN_CACHE newly written。
- DWD：176 network requests、約 223 MB、raw cache hits = 0。
因此 `WARM_PRODUCTION` 目前描述的是 requested run mode，不等同 actual provider cache warmness。此議題與 geometry science 無關，後續需新增 actual cache-state telemetry / deployment cache persistence strategy。

## 下一步
1. 部署 R5.7.41.3.4.8。
2. 以 TWS106 同一 CASE 再跑一次；最好同一 deployment 連續跑兩次，以分離 cold-provider 與 warm-provider runtime。
3. 確認 Field `VIEWING_COMPONENT_PATH_GEOMETRY` 實際下降幅度與 science exact-equivalence。
4. 再決定下一個 runtime target：Viewing Spectral Extinction、Red-Light Reference Availability 或 provider-cache persistence。
5. Shadow COT positive cohort 持續隨天氣收集，不阻塞工程開發。
