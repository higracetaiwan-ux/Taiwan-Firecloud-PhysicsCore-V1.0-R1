# R5.7.41.3.4.10.9.9 — DWD State-Dir Explicitness + Legacy Exact-Cache Bridge Hotfix

## 問題

`.10.9.8` 預期在使用者沒有明確設定 `FIRECLOUD_STATE_DIR` 時，DWD exact cache 使用穩定 user-home root：`~/.cache/taiwan_firecloud/dwd_icon/`。但 Streamlit app 啟動 worker 時永遠傳入 `FIRECLOUD_STATE_DIR`，即使只是 app 預設 `.firecloud_state`，因此 provider 把它誤認成 deployment explicit override。

## 修正

### 1. Explicitness marker

`app.py` 新增 `_STATE_DIR_EXPLICIT_CONTRACT`，worker env 新增 `FIRECLOUD_STATE_DIR_EXPLICIT=0|1`。

- marker=0：app-default state-dir，不視為 deployment contract；
- marker=1：尊重 explicit state-root contract；
- standalone caller 沒有 marker：若有 `FIRECLOUD_STATE_DIR`，維持歷史行為視為 explicit。

### 2. Dynamic cache-scope provenance

`shared_cache_scope` 改為動態輸出：
- `USER_HOME_CROSS_RELEASE_EXACT_IDENTITY`
- `EXPLICIT_STATE_DIR_EXACT_IDENTITY`
- `EXPLICIT_DWD_SHARED_CACHE_DIR_EXACT_IDENTITY`

另輸出 `state_dir_explicit_contract`。

### 3. Validated legacy-state raw-cache bridge

若 marker=0、user-home shared cache miss，但舊 `.firecloud_state/provider_cache_shared/dwd_icon_raw` 仍存在，僅對同一 exact identity 執行：identity JSON、byte size、SHA256、QC stamp 全部驗證。PASS 才可匯入新 shared root。禁止相似 run/lead/level 替代。

### 4. Decoded-optics legacy bridge

相同 run/lead、route-state signature、model-level set 的 decoded optics cache可由舊 state root精確橋接至新 shared root。

### 5. COLD_ISOLATED_TEST 防漏

isolated job namespace 額外明確設定 `FIRECLOUD_DWD_ICON_SHARED_CACHE_DIR` 與 `FIRECLOUD_DWD_ICON_RAW_CACHE_DIR` 到 job-local provider root，避免 cold test 命中 warm production cache。

### 6. Analysis Integrity

新增 `DWD_EXACT_CACHE_SCOPE_PROVENANCE`，檢查 scope label、state-dir explicitness、thread-local HTTPS reuse、legacy bridge source provenance。

## 不變項

不修改 DWD URL、run/lead、QC/QI/T/P bytes、model levels 55–108、grid locator、vertical geometry、COT、provider precedence、Missing semantics、Formation、Viewing、Twilight Glow、六波段或任何 Frozen Science。
