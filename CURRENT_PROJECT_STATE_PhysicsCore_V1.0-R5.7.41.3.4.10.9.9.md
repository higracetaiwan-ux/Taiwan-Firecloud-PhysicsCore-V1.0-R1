# Taiwan Firecloud PhysicsCore — Current Project State

> 版本：**V1.0-R5.7.41.3.4.10.9.9**  
> Internal：`1.0.0-R5.7.41.3.4.10.9.9`  
> Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`  
> Release state：**REGRESSION PASS / FIELD RETEST CANDIDATE**

## 已完成 Field
- `.10.9.3 = FIELD PASS + TWS111 CROSS-SITE PASS`
- `.10.9.4 = FIELD PASS`
- `.10.9.5 = FIELD PASS`
- `.10.9.6 = FIELD PASS`：TWS106 near-field source underrepresentation confirmed。
- `.10.9.7 = FIELD PASS`：CAMS spectral AOD exact reuse confirmed。
- `.10.9.8`：TWS089 HTTPS connection reuse FIELD PASS；DWD cache-scope contract defect found。

## `.10.9.8` TWS089 runtime
Worker 574.204 s；Core 540.009 s；DWD secondary 46.263 s；CAMS prefetch 228.508 s。DWD 相對 `.10.9.7` 158.752 s 改善約 70.9%，但 raw hits=0；cache path 仍落在 `.firecloud_state`，證明 `.10.9.8` user-level cache contract 未真正生效。

## `.10.9.9`
1. CAMS pressure-level exact-union bundle：O3 + 532-nm aerosol + geopotential 一次 ADS request；成功完整時兩個 legacy roles exact reuse。
2. Bundle incomplete/failure 自動 fallback 原兩個 requests。
3. 新 Integrity `CAMS_PRESSURE_LEVEL_BUNDLE_EXACT_REUSE_PROVENANCE`。
4. 修 app/worker DWD cache-scope：只有真正 user-configured state root 才 state-scoped；app default handoff 改 user-level cache。
5. isolated-job DWD raw cache 一併隔離。
6. DWD provenance dynamic truth，不再固定標 user-level。

## Frozen science
Formation=Sun→CloudBase；Viewing=Cloud→Observer；Twilight Glow獨立第三分支。六波段、Canvas、Dynamic Corridor/REZ、Earth Shadow、Production/Shadow COT、CLWMR/ICMR threshold、Missing≠Clear≠Zero 全部不變。

## 下一步 Field
用 `.10.9.9` 重跑 TWS089 2026-09-14 sunrise。確認：
- CAMS actual provider requests 4→3（若 bundle accepted）；
- O3/Native532 audit = `EXACT_SOURCE_REUSE` from `PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE`；
- `CAMS_PRESSURE_LEVEL_BUNDLE_EXACT_REUSE_PROVENANCE=PASS`；
- DWD `shared_cache_scope/raw_cache_scope` 與實際 cache path一致；
- science artifacts無 regression。
