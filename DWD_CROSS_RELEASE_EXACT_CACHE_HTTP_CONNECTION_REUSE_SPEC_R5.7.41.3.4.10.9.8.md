# R5.7.41.3.4.10.9.8 — DWD Cross-Release Exact Cache + HTTPS Connection Reuse

## 目的

`.10.9.7` TWS089 Field 已證明 CAMS spectral-AOD exact-source reuse 成功；新的主要 operational bottleneck 是 DWD ICON secondary native optics。該 CASE 對 f003/f004 共產生 356 個 network attempts、約 436.7 MB transport，`SECONDARY_FORECAST_NATIVE_OPTICS_PREFETCH` 158.752 s。

本版只做 I/O / cache orchestration，禁止修改任何 Frozen Physics。

## A. 穩定的 cross-release exact cache scope

舊預設把 DWD durable raw / decoded cache 放在相對 `.firecloud_state`。完整替換程式若解壓到新資料夾，會讓相同 run/lead/file identity 再次 cold-start。

新預設：

`~/.cache/taiwan_firecloud/dwd_icon/`

包含：

- `raw_grib/`：exact DWD raw GRIB bytes；
- `decoded_secondary_optics/`：exact run/lead + route-state decoded optics。

優先順序：

1. `FIRECLOUD_DWD_ICON_RAW_CACHE_DIR`（raw-only explicit override）；
2. `FIRECLOUD_DWD_ICON_SHARED_CACHE_DIR`（shared DWD root）；
3. 若明確設定 `FIRECLOUD_STATE_DIR`，維持原 state-root contract；
4. 否則使用 user-level shared cache。

Raw cache identity、SHA256、byte size、QC stamp 驗證不變；identity mismatch / corrupt cache 必須 fail-close 回正常 network path。

## B. Thread-local HTTPS keep-alive

DWD 一個 model-level field 一個 object。舊 transport 使用 `requests.get()`，大量 level fetch 可能反覆建立 HTTPS connections。

`.10.9.8` 每個 ThreadPool worker 使用自己的 `requests.Session`：

- 同一 worker 的後續 request 可 keep-alive reuse；
- Session 不跨 thread 共享，避免 mutable session thread-safety 問題；
- URL / timeout / response bytes / bz2 decode / ecCodes decode 完全不變；
- `max_retries=0`，不新增隱性 request；
- embedders/tests 既有 `requests.get` monkeypatch hook 仍相容。

Audit 增加：

- `shared_cache_scope = USER_LEVEL_CROSS_RELEASE_EXACT_IDENTITY`
- `http_connection_reuse = THREAD_LOCAL_REQUESTS_SESSION_POOL`

## 科學不變條款

禁止改動：

- DWD run/lead resolver；
- model levels 55–108；
- QC/QI/T/P field contract；
- route→native source address mapping；
- hypsometric vertical geometry；
- assumed reff / extinction / derived COT；
- provider precedence；
- Missing / Clear / Zero；
- Formation / Viewing / Twilight Glow / Red-Light / Production COT / Shadow COT。

本版不以減少 vertical levels 換速度，也不跨 forecast lead 重用資料。
