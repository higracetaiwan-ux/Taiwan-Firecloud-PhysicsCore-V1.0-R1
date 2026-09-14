# Taiwan Firecloud PhysicsCore — Current Project State

> 版本：**V1.0-R5.7.41.3.4.10.9.8**
> Internal：`1.0.0-R5.7.41.3.4.10.9.9`
> Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`
> Release state：**REGRESSION PASS / FIELD RETEST CANDIDATE**

## 凍結科學

Formation = Sun→CloudBase；Viewing = Cloud→Observer；Twilight Glow 為獨立第三分支。六波段 550/575/600/650/700/750 nm、Canvas 0–40/40–100 km、Dynamic Corridor/REZ、Earth Shadow、Missing≠Clear≠Zero、Production/Shadow COT 語意均不變。

## 已完成 Field

- `.10.9.3 = FIELD PASS + TWS111 CROSS-SITE PASS`
- `.10.9.4 = FIELD PASS`
- `.10.9.5 = FIELD PASS`
- `.10.9.6 = FIELD PASS`；TWS106 source-attribution 確認 near-field GFS source underrepresentation。
- `.10.9.7 = FIELD PASS`；TWS089 CAMS `SPECTRAL_COLUMN_AOD=EXACT_SOURCE_REUSE`、Integrity PASS。

## `.10.9.7` TWS089 新 hotspot

- Worker：639.155 s
- Core：602.000 s
- CAMS prefetch：173.194 s
- DWD secondary prefetch：158.752 s
- DWD network attempts：356
- DWD network bytes：約 436.7 MB
- DWD raw persistent hits：0

## `.10.9.8` 改動

1. DWD durable exact cache 預設移至 user-level stable root，跨 full-replacement release 可 reuse exact identities。
2. 明確 `FIRECLOUD_STATE_DIR` 仍維持舊 state-root contract。
3. DWD HTTP transport 改 thread-local `requests.Session` keep-alive。
4. Audit 顯示 exact cache scope 與 connection-reuse mode。
5. 不減 levels、不跨 lead、不改任何科學計算。

## 測試

Working tree：**726/726 PASS**；FULL-CLEAN fresh-extract：**726/726 PASS**。1 個既有 pandas FutureWarning。Frozen core source audit：16/16 byte-identical。

## 下一步

用 `.10.9.8` 正式重跑 TWS089 2026-09-14 sunrise。第一個 `.10.9.8` cold run 可能仍需下載新的 DWD objects；之後同 exact run/lead/file 在 `.10.9.8` rerun 或後續 full-replacement release 應能由 stable user cache 命中。Field 需檢查 DWD audit 的 `shared_cache_scope` / `http_connection_reuse`、network requests/bytes、raw/decoded cache hits、science output與 Integrity。
