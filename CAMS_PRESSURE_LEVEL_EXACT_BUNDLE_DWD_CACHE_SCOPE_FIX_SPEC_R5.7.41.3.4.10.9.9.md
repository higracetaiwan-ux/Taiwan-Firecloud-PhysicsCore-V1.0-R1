# R5.7.41.3.4.10.9.9 — CAMS Pressure-Level Exact Bundle + DWD Cache-Scope Contract Fix

## 目的
在不改任何 Frozen PhysicsCore 科學規則的前提下，降低 CAMS cold-run serial ADS latency，並修正 `.10.9.8` 在 app→worker state-dir handoff 下的 DWD cache-scope 語意錯置。

## CAMS exact-union pressure-level bundle
既有兩個 logical roles：
- `O3_PRESSURE_LEVEL`: ozone + geopotential，18 pressure levels。
- `NATIVE_AEROSOL_532NM_PRESSURE_LEVEL`: aerosol_extinction_coefficient_532nm + geopotential，同一組 18 pressure levels。

兩者 dataset/run/lead/type/area/pressure levels 完全相同。`.10.9.9` 新增 `PRESSURE_LEVEL_CHEMISTRY_OPTICS_BUNDLE`，variables 為兩者 exact union：`ozone + aerosol_extinction_coefficient_532nm + geopotential`。

只有當：
1. 所有 requested point_id 均存在；
2. O3 18 層欄位完整；
3. Aerosol 532 18 層欄位完整；
才允許兩個 legacy roles 以 `EXACT_SOURCE_REUSE` handoff。handoff elapsed=0，source role 必須為 bundle。任一條件不足即回原獨立 request。禁止時間替代、Ångström、RH/CF、垂直 proxy 或 Missing→Zero。

新增 Integrity：`CAMS_PRESSURE_LEVEL_BUNDLE_EXACT_REUSE_PROVENANCE`。

## DWD cache-scope contract 修正
`.10.9.8` 的 provider 邏輯把任何存在的 `FIRECLOUD_STATE_DIR` 視為 operator explicit override；但 app 本身永遠會把預設 `.firecloud_state` 寫入 detached worker env。因此 Field CASE 實際仍使用 `.firecloud_state/provider_cache_shared/...`，卻 audit 成 user-level cross-release。

`.10.9.9`：
- app 在建立 worker 前記錄 state dir 是否原本由使用者/部署明確設定；
- child env 新增 `FIRECLOUD_STATE_DIR_EXPLICIT_USER_OVERRIDE=0/1`；
- marker=0 時，DWD shared raw/decoded cache 使用 `~/.cache/taiwan_firecloud/dwd_icon/`；
- marker=1 時維持 explicit state-root contract；
- isolated-job namespace 明確設定 `FIRECLOUD_DWD_ICON_RAW_CACHE_DIR`，確保 raw bytes 也隔離；
- provenance `shared_cache_scope/raw_cache_scope` 依實際 contract 動態輸出。

## 不變項
不改 NOAA GFS、DWD URL/run/lead/model levels、CAMS valid time、Formation、Viewing、Twilight Glow、六波段、Earth Shadow、Dynamic Corridor/REZ、Canvas、COT、CLWMR/ICMR threshold、Missing semantics、Photography Decision。
