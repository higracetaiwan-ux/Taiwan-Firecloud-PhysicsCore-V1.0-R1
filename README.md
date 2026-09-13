> Current release: **V1.0-R5.7.41.3.4.10** — Twilight Glow runtime hotspot decomposition; science baseline remains frozen.

# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.5

## R5.7.41.3.4.5 Viewing→Glow Observer-Cloud Provenance Handoff + Shared Runtime Context

- Viewing 在既有 Cloud→Observer blocker 幾何 pass 內直接保留 Glow 所需的 cloud conflict provenance，不再由 Twilight Glow 為每個 atmospheric volume 重追同一條 observer-cloud path。
- Viewing 與 Glow 可共用 process-local runtime context：route groups、prepared HITRAN gas contexts、exact COT lookup、target optical-truth lookup、projected-support cache。
- 共用 context 僅在來源 DataFrame 為同一個 in-memory object 時重用；來源物件不同就重建，避免 stale cache / cross-run contamination。
- Glow 優先讀取 Viewing handoff；舊/外部資料沒有 handoff 欄位時仍保留 R5.7.41.3.4.4 legacy retrace fallback。
- H004 / TWS021 單角度 84-volume 離線等價 benchmark：R5.7.41.3.4.4 3.961 s → R5.7.41.3.4.5 2.035 s，約 1.95×；detail/summary exact DataFrame equality。
- 此版只做 runtime engineering，不改 Shadow eligibility、Production/Shadow COT、Earth Shadow、Formation、Viewing/Glow physics、六波段或 Missing 語義。

## R5.7.41.3.4.4 Twilight Glow Observer-Cloud Provenance Cache Hardening

- Twilight Glow cloud layer 依 time / solar-angle / direction 預分組。
- exact COT / target optical truth map 單次建立，projected-support geometry 依 transect 共用。
- 新增 `AGGREGATION_EXCLUDING_TWILIGHT_GLOW` 計時，避免把 Glow inclusive time 重複當成 aggregation 瓶頸。
- H004/TWS021 單角度 84-volume benchmark：7.743 s → 3.491 s，約 2.22×，detail/summary exact match。

## R5.7.41.3.4.3 DWD Secondary Runtime Cache Hardening

- DWD ICON secondary QC/QI/T/P decoded fields 可安全跨角度重用。
- 若完整 QC/QI probe 在同一 frozen run/lead 全為 404，後續角度保留 Missing 並停止重送完全相同的 requests。
- 不把 mixed failure / timeout / 5xx / partial ready 寫成 negative availability cache。

## R5.7.41.3.4 Historical GFS AWS Indexed-Range Provider Routing

- 修正歷史事件超出 NOMADS GRIB Filter 線上窗口時，GFS 0.25° native pgrb2 / pgrb2b 直接 403 而失去 CLWMR/ICMR 的問題。
- 保持同一個 frozen GFS run/forecast lead；NOMADS 失敗後改讀 NOAA GFS AWS Open Data 的 `.idx` sidecar，再用 HTTP `Range` 只取指定 pressure-level GRIB messages。
- 主 pgrb2 與 0–100 km pgrb2b intermediate-level optical probe 共用同一歷史 transport。
- AWS Range 僅屬 transport fallback，不改 native condensate、Cloud Fraction、COT、Formation、Viewing、Glow 或 Photography semantics。
- 若 archive object / `.idx` / required message 不存在，仍 fail-close 為 Missing；不改用 RH/CF 補造 condensate。
- 若伺服器忽略 Range 回 HTTP 200，下載立即拒絕，避免意外抓取整個全球 GRIB2 大檔。


## R5.7.41.3.3 Historical Replay Empty Cloud-Volume Guard Hotfix

- 修正歷史回測／舊 provider replay 在 cloud-layer table 為 headerless empty DataFrame 或缺必要欄位時，`viewing_spectral._cloud_expected_tau()` 直接讀取 `direction_offset_deg` 而觸發 `KeyError`。
- 缺 cloud-volume evidence 現在 fail-close 為 `VIEW_CLOUD_VOLUME_UNRESOLVED`；Missing 不得被視為 Clear。
- cloud table schema 完整、僅該 time/angle/direction 無 blocker row 時，仍保留 `VIEW_CLOUD_PATH_CLEAR`。
- 同步 harden route grouping，缺 `solar_altitude_deg` / `direction_offset_deg` / `distance_km` 時不再 crash。
- 不修改 Formation、Production/Shadow COT、Viewing 物理公式、Twilight Glow、Photography 或六波段 science contract。


## R5.7.41.3.2 Direct Conflict Eligibility Handoff Hotfix

- 統一 Target Optical Truth → Vertical Microphysics Overlap → Shadow COT Migration 的 direct-conflict 定義。
- `CONDENSATE_CLOUD_CF_LOW` 現在會在 overlap 層標成 `direct_target_evidence_conflict=True`，並阻擋 assumed-r_eff COT diagnostic。
- Shadow migration 會獨立讀取 `target_optical_truth_state` / `resolver_state`；即使舊 overlap artifact 漏標 conflict，也會 fail-close。
- Analysis Integrity 新增跨層 handoff guard：任何 `DIRECT_EVIDENCE_CONFLICT` 都不得同時是 `ELIGIBLE_SHADOW_CANDIDATE`。
- 不改 Production COT、Formation、Viewing、Twilight Glow 或 Photography science。

## R5.7.41.3.1 Direct Conflict Qualification Coverage Hotfix

修正 `DIRECT_EVIDENCE_CONFLICT` qualification coverage；新增 `CONDENSATE_CLOUD_CF_LOW` 專屬 state，不改 Production science。

# Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3


## R5.7.41.3 Shadow Validation Collection Readiness / Shared Scenic Spot Selector

- 共用台灣晨昏攝影景點母資料庫 V2.2：187 個唯一 GPS 景點。
- Streamlit 事件設定新增區域＋可搜尋景點選單，並保留自訂座標。
- 預設景點：`TWS106` 高美濕地；景點 metadata 只做 CASE provenance，物理仍只使用 lat/lon。
- CASE 新增 `shadow_validation_case_manifest.csv`、`shadow_validation_cohort_summary.csv`、`shadow_validation_ground_truth_template.csv`、`shadow_validation_runtime_summary.csv` 與 `analysis_request.json`。
- Shadow cohort 固定 science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`；任何 Production switch / COT promotion / Formation promotion 都會讓 collection guard FAIL。
- CASE 檔名加入 `site_id`，方便同地點多日收集。
- 不改 Production COT、Formation、Viewing、Twilight Glow、Photography 或既有科學門檻。

## R5.7.41.2 Production COT Semantic Migration Contract / Shadow Mode

本版將 legacy `LEGACY_CF_SCALED_GRID_CELL_MEAN` Production COT 與 `IN_CLOUD_EXACT_ENVELOPE_ASSUMED_REFF` shadow candidate 並列，建立 target envelope、vertical evidence、direct conflict、condensate completeness、CF/RH isolation、r_eff provenance 與 vertical integration eligibility gates。即使 candidate eligible，也不切換 Production：`production_switch_performed=False`、`cot_promotion_allowed=False`、`formation_promotion_allowed=False`。

2026-09-11 R5.7.41 Field CASE 離線 replay：767 targets、108 eligible、659 ineligible、0 switch/promotion。新增 `v1_canvas_cot_semantic_migration.csv`、summary 與 `tools/replay_r57412_cot_semantic_migration.py`。

---


## R5.7.41.1 COT Diagnostic Reconciliation

本版釐清 R5.7.41 Field CASE 中 production `direct_native_cot` 與 target-envelope assumed-r_eff COT 的約 1.81 倍差異。108/108 comparable targets 均可由 legacy half-cell edge support、Cloud Fraction extinction scaling 語義、以及 pgrb2b intermediate-level vertical resolution 三項完整重建；最大 residual 約 `9.63e-17`。

新增 `v1_canvas_cot_reconciliation.csv`、`v1_canvas_cot_reconciliation_summary.csv` 與 `tools/replay_r57411_cot_reconciliation.py`。本版不替換 Production COT，`cot_promotion_allowed=False`、`formation_promotion_allowed=False`。

Working-tree regression：574/574 PASS。Extracted regression：574/574 PASS。FULL-CLEAN release gate：CLOSED。

---

# Taiwan Firecloud PhysicsCore V1.0-R5.7.41

## R5.7.41 Canvas Optical Truth Phase 2A / Target Vertical Microphysics Overlap

本版將 GFS 主 `pgrb2` 與 `pgrb2b` 中間 pressure levels 的 direct-native CLWMR/ICMR/HGT/TMP 合併，逐 Target Canvas 檢查 Cloud Base–Top 的 Interior / Boundary / Outside microphysics evidence。Boundary-only positive condensate 不再被模糊解讀成 interior support；缺 pgrb2b 中間層時保持 Missing / `VERTICAL_EVIDENCE_INCOMPLETE`。

新增 assumed-r_eff COT diagnostic scaffold，但任何 `DIRECT_EVIDENCE_CONFLICT` 都會 block 診斷 COT，且 `cot_promotion_allowed=False`、`formation_promotion_allowed=False`。Formation / Viewing / Glow / Photography science 不變。

新增 CASE：`v1_canvas_vertical_microphysics_overlap.csv`、`v1_canvas_vertical_microphysics_samples.csv`、`v1_canvas_vertical_microphysics_overlap_summary.csv`；另附 `tools/replay_r5741_canvas_vertical_overlap.py` 供舊 CASE 無網路快速重播。

Working-tree regression：571/571 PASS。

---

# Taiwan Firecloud PhysicsCore V1.0-R5.7.40.1

## R5.7.40.1 Vertical Conflict Integrity Handoff Hotfix

R5.7.40 真實 CASE 已產生 432 筆 vertical-conflict qualification rows（45 個 unique conflict canvases），但 pre-export Analysis Integrity 漏傳 `v1_target_canvas_optical_evidence`，導致 `CANVAS_OPTICAL_VERTICAL_CONFLICT_QUALIFICATION` 誤走 `ALLOWED_EMPTY / 0 conflict canvases`。

R5.7.40.1 只補齊這個 Integrity handoff：audit 現在會以真實 `DIRECT_EVIDENCE_CONFLICT` / `CF_CLOUD_CONDENSATE_ZERO` target 集合計算 expected coverage。R5.7.40 CASE 離線 replay 得到 `PASS`、432 qualification rows、45 expected / 45 observed unique canvases。科學輸出、COT readiness、Formation、Viewing、Glow、Photography 均不改。

完整 regression：564/564 PASS。Field validation 尚需用 R5.7.40.1 新 CASE 確認新 CASE 內 audit 行為。

---

# Taiwan Firecloud PhysicsCore V1.0-R5.7.40

## R5.7.40 Cloud-Fraction ↔ Native Hydrometeor Vertical Conflict Qualification

本版延續 R5.7.39.1 已 field-pass 的 GFS `pgrb2b.0p25` provider hotfix，新增 Canvas Optical Truth 的垂直衝突資格層。主 `pgrb2` 提供 cloud-fraction geometry 與主 pressure-level CLWMR/ICMR；`pgrb2b` 僅提供中間 pressure-level 的 CLWMR/ICMR/HGT/TMP hydrometeor context。

R5.7.40 會針對 `CF_CLOUD_CONDENSATE_ZERO` 的 Canvas，檢查主衝突層、上下主 pressure-level 鄰層，以及兩側最近的 pgrb2b 中間層，輸出：

- `ISOLATED_PRIMARY_CF_SPIKE_HYDROMETEOR_UNSUPPORTED`
- `INTERMEDIATE_NATIVE_CONDENSATE_SUPPORT_PRESENT`
- `ADJACENT_PRIMARY_NATIVE_CONDENSATE_SUPPORT_PRESENT`
- `PRIMARY_CF_SIGNAL_WITH_ZERO_INTERMEDIATE_HYDROMETEORS`
- `VERTICAL_CONTEXT_INCOMPLETE`

硬規則不變：本版是 evidence/qualification only；不得由 RH 或 cloud fraction 生成 condensate/COT，不得把 pgrb2b cloud fraction 當 pressure-level geometry，不得自動提升 target COT、Formation 或 Photography outcome。

新增 CASE：`v1_canvas_vertical_conflict_qualification.csv` 與 summary。Focused 20/20 PASS；working-tree full regression 562/562 PASS。Field validation 需以 R5.7.40 新 CASE 驗證真實 150 ↔ 125/175 hPa 等垂直 context。

---

# Taiwan Firecloud PhysicsCore V1.0-R5.7.39.1


## R5.7.39.1 pgrb2b Secondary Filter Endpoint Hotfix

R5.7.39 真實 CASE 確認 `pgrb2b.0p25` 誤用主產品 `filter_gfs_0p25.pl` 會回 HTTP 500。R5.7.39.1 改用 Secondary Parameters 的 `filter_gfs_0p25b.pl`。本 hotfix 只修 provider routing，不改 target COT readiness、Formation、Viewing、Glow 或 Photography。Focused 10/10 PASS；full regression 552/552 PASS。

## R5.7.39 Canvas Optical Truth Phase 1 / GFS pgrb2b Native Condensate Probe

R5.7.39 新增 diagnostic-only 的 GFS `pgrb2b.0p25` intermediate pressure-level native condensate probe。它在 0–100 km Formation Canvas 內讀取 125/175/225/.../925 hPa 的 CLWMR/ICMR/TCDC/TMP/HGT，並只保留落入 Canvas fixed vertical envelope 的原生 evidence，用來判斷既有 `CF_CLOUD_CONDENSATE_ZERO` 是否可能來自主 pressure-level 垂直取樣過粗。

本版不把 probe positive 自動升格成 target COT，不改 Formation，也不使用 RH/cloud fraction 生成 condensate/COT。Missing 仍為 Missing。新增 CASE `v1_canvas_optical_native_probe.csv`、summary、request audit 與 `CANVAS_OPTICAL_TRUTH_PGRB2B_PROBE_CONTRACT` Integrity。Focused **9/9 PASS**；working-tree full regression **551/551 PASS**。Field Validation 需新 CASE。


## R5.7.38 CAMS Post-success Download Recovery

R5.7.38 專門處理 ADS remote job 已 `successful`、但檔案下載節點暫時回傳 502/503/429 等錯誤而造成長時間停滯的情況。所有 download retry 都沿用同一個 request ID，不重新 submit CAMS job；每次嘗試重新取得 Results/location，預設最多 4 次，2 秒起始 backoff、12 秒上限。signed download URL 不寫入 CASE 或 journal。

新增 `ads_download_attempts`、`ads_download_retry_count`、`ads_download_url_refresh_count`、`ads_download_elapsed_seconds` 等 telemetry，以及 `CAMS_POST_SUCCESS_DOWNLOAD_RECOVERY_TELEMETRY` Integrity。R5.7.34 phased deadline 與 R5.7.37 Near-Surface Molecular Boundary Closure 均保持不變。

發行驗證：working tree **542/542 PASS**；FULL-CLEAN 解壓後 **542/542 PASS**；正式封包已完成。R5.7.38 Field Validation 仍需新 CASE。


## R5.7.37 Near-Surface Molecular Boundary Closure

R5.7.37 專門處理 Twilight Glow `Scatter→Observer` 路徑在近地層出現的 pressure-profile 下邊界缺口。既有 **10 m (`0.01 km`) molecular endpoint tolerance 完全保留，不放寬**。當 CAMS 原生 O₃ model level 137、Open-Meteo surface pressure、2 m temperature 與 2 m relative humidity 都具備真實證據時，程式建立約 10 m AGL 的 near-surface molecular anchor，與最低原生 pressure-level 形成真實垂直 bracket，供 Rayleigh 與 HITRAN gas-species 路徑內插。

任何必要證據缺失時不建立 anchor；Missing 仍為 Missing，不向下外插 pressure-level O₃、不使用固定 O₃、不以放寬 tolerance 取得假 PASS。CASE Integrity 另新增 anchor provenance、固定 10 m tolerance 與實際 bridge provenance 檢查。

發行驗證：working tree **533/533 PASS**；FULL-CLEAN 解壓後 **533/533 PASS**；封包 **506 個檔案成員、0 cache/pyc**。R5.7.37 已於 2026-09-10 sunset CASE 完成 Field Validation：Analysis Integrity **61/61 PASS**、CASE Integrity **23/23 PASS**、100 km / 3.75 km molecular coverage **156/156**。

## R5.7.36 Formation Canvas Eligibility / Low-Cloud Role Separation

R5.7.36 修正日本真實 CASE 暴露的 Formation 語義問題：低雲（雲底 <2 km）雖然應保留在 CloudScene 中作為 `ILLUMINATION_BLOCKER` / `VIEW_OBSTRUCTION`，但不應被升格成火燒雲 Formation Canvas。

本版規則：

- `0–100 km` 且 `cloud base >= 2 km`：`FORMATION_CANVAS_TARGET`。
- `0–100 km` 且 `cloud base < 2 km`：`BLOCKER_ONLY_LOW_CLOUD`，保留雲體但不建立 Canvas target。
- `>100 km`：`UPSTREAM_OR_DIAGNOSTIC_CLOUD`，可參與上游阻光/診斷，但不是 Formation Canvas。
- 2.0 km 邊界本身仍為 eligible，沒有提高門檻。
- 不刪低雲、不把低雲當 clear、不改既有 blocker 光學。

新增 Integrity：`FORMATION_CANVAS_LOW_CLOUD_ROLE_SEPARATION`。任何 `<2 km` 雲被放入 `v1_canvas_candidates` 都會 FAIL。


## R5.7.35.2 零有效 Viewing Target 的降水 Integrity 語義修正

本版修正日本真實 CASE 暴露的 Integrity 誤判：當 `v1_viewing_path_geometry` 存在，但所有列的 `photographic_target_eligible=False` 時，`v1_viewing_precipitation_evidence` 為空是合理的「不適用」，不應因 GFS 原生 `RWMR/SNMR/GRLE` 已 READY 就硬判 handoff FAIL。

新的規則是：

- `eligible Viewing target = 0`：`VIEWING_NATIVE_HYDROMETEOR_HANDOFF = NOT_APPLICABLE`。
- `eligible Viewing target > 0`：仍要求每個 target 都有 precipitation evidence；空表、漏列或 `VIEW_PRECIPITATION_VOLUME_UNRESOLVED` 仍為 FAIL。
- 不修改 Viewing 幾何、降水光學、Formation、Aerosol、Glow 或 Photography 物理。


## R5.7.35.1 Aerosol Missing-Reason Handoff Hotfix

R5.7.35 real sunset CASE field validation showed the aerosol scattering physics itself closed correctly, but 872 unresolved aerosol-proxy rows had an empty `glow_aerosol_missing_components` diagnostic field. R5.7.35.1 preserves every R5.7.35 numeric value and state while handing upstream `Sun→Scatter` / `Scatter→Observer` missing reasons into the aerosol evidence table. An Integrity guard now fails if an unresolved/partial aerosol row has no explicit reason. No SSA, asymmetry-g, HG phase, extinction, proxy, Formation, Viewing or Photography science is changed.

Working-tree regression: **514/514 PASS**.

## R5.7.35 Aerosol Scattering Physics Phase 1

Adds independent Twilight Glow aerosol single-scattering evidence using CAMS native AOD/SSA/asymmetry factor, native 3-D aerext532, bounded six-band interpolation, and a clearly labeled Henyey-Greenstein phase approximation. Multiple scattering and calibrated absolute radiance remain unresolved.


## R5.7.34 CAMS ADS Stateful Deadline / Request-ID Recovery

R5.7.34 replaces the flat 90-second CAMS ADS wait with a state-aware remote-job contract. The official ECMWF Data Stores client is used for asynchronous `submit`, durable opaque `request_id`, `get_remote(request_id)` reattachment and download after success. Local queue/running/total wait deadlines are separate; a timeout stops local waiting but does not cancel the remote ADS request. Request IDs are persisted with a deterministic request fingerprint, and the next identical role/time/request reattaches instead of blindly submitting a duplicate. Missing remains Missing; no CAMS science inputs, angles, bands or Formation/Viewing/Glow rules are changed.

Default stateful waits: queue 75 s, running 120 s, total 180 s. The external worker watchdog is a last-resort 210 s hard ceiling.



## R5.7.33.1 Native 3D Aerosol Readiness Integrity Hotfix

R5.7.33 真實 sunset CASE 首次同時觸發 R5.7.28 `REAL_ONE_SIDED_TEMPORAL_FALLBACK` 與 CAMS native 3-D aerosol timeout。舊 `TWILIGHT_GLOW_OBSERVER_AEROSOL_LONG_RANGE_COVERAGE` 以 spectral column AOD 是否可用判斷 native 3-D route readiness，導致合法的 spectral fallback 把缺失的 native `aerext532` 錯判為 provider-ready，產生假 hard FAIL。R5.7.33.1 將 guard 改為逐 `time + solar_altitude_deg` 檢查 `cams_native_aerosol_source + cams_aerext532_m1_*`；只有 native 3-D 真正 READY 的 long-range targets 才要求六波段 aerosol tau 完整。native timeout targets 保持 Missing，不由 spectral fallback 提升。Physics、Formation、Viewing、Glow extinction 與 Photography 均未改動。

Working-tree regression: **501/501 PASS**.

## R5.7.33 Twilight Glow Deep-Range Gas/Rayleigh/Cloud Closure

R5.7.32 真實 sunset CASE 將 Glow `Scatter→Observer` 收斂到最後 10/1092 個 Partial。R5.7.33 將其中六個 100 km、z=3.75 km 的 Rayleigh/Gas 個案確認為最低原生 pressure-level 的邊界 touch：第一段 midpoint 約 74.62 m，而最低真實 gas profile 約 75.07 m，只差約 0.45 m。Glow 現在沿用既有 Gas RT 已凍結的 `<=0.01 km` 最低 native profile boundary tolerance；不允許超過 tolerance 或向 profile top 外插。

另外四個 100 km、z=7.75 km CLOUD Partial 是真正的原生光學證據衝突：cloud fraction 存在，但 native condensate 為 0、COT unresolved，`target_optical_truth_state=DIRECT_EVIDENCE_CONFLICT`。R5.7.33 明確輸出 `GLOW_OBSERVER_CLOUD_DIRECT_EVIDENCE_CONFLICT_PRESERVED`，cloud tau 仍保持 Missing，不改成 clear/zero。

新增 Integrity：

- `TWILIGHT_GLOW_OBSERVER_DEEP_RANGE_MOLECULAR_COVERAGE`
- `TWILIGHT_GLOW_OBSERVER_CLOUD_CONFLICT_PRESERVATION`

R5.7.32 immutable CASE forensic replay：100 km Rayleigh 156/156、gas species 156/156 resolved；四個 cloud conflict 保留。正確預期是 **1088/1092 observer Full + 4 conflict-preserved Partial**，不是用假資料追求 1092/1092。

Field validation 尚待 R5.7.33 新 CASE。


## R5.7.32 Glow Observer-Path Aerosol Coverage Robustness

R5.7.31 真實 sunset CASE 將 Glow `Scatter→Observer` 的主要缺口定位到 CAMS native aerosol vertical geometry：CAMS GRIB `z` 的實際單位是 `m**2 s**-2`（geopotential），舊 decoder 的單位字串比對沒有涵蓋 ecCodes 這個拼法，因此曾把 geopotential 直接當 metres，將 1000/500/30 hPa 高度約放大 9.80665 倍。

R5.7.32 在 provider decode 時正式正規化：

- `m**2 s**-2` / 同義 geopotential units → 除以 `g0=9.80665 m s^-2` → geopotential height metres；
- `m` / `gpm` 類 height units → 直接使用；
- 未知 units → fail-close 為 Missing，不再保留可能錯誤的數值。

Glow observer aerosol 另外允許一個非常小、**Glow-only** 的 lowest-native-level endpoint snap：當長距離 observer ray 的 segment midpoint 只比最低 CAMS pressure surface 低 `<=0.05 km` 時，可使用最近的最低 native `aerext532`；這不會擴大 route、不會用 AOD 外插，也不改 Viewing 預設 strict contract。R5.7.31 field evidence 離線重播顯示：60/80/100 km long-range targets 從原先大量 Partial 恢復為 **468/468 aerosol resolved**，其中只有 6 個 100 km targets 使用 endpoint snap。

新增 Integrity：

- `CAMS_GEOPOTENTIAL_HEIGHT_NORMALIZATION`
- `TWILIGHT_GLOW_OBSERVER_AEROSOL_LONG_RANGE_COVERAGE`

並輸出 Glow observer aerosol required/resolved segment count、lowest-endpoint snap count 與 tolerance provenance。Formation、Viewing、Photography、13 angles、六波段、Route Invariance、R5.7.31 two-leg extinction 公式均不改動。

Working-tree regression：**492 passed / 0 failed**。R5.7.32 真實 CASE 已 field-close：Analysis Integrity 50/50 PASS、CASE Integrity 22/22 PASS、60/80/100 km aerosol 468/468 resolved。


## R5.7.31 Twilight Glow Full Six-Band Extinction Phase 1

R5.7.31 延續已 field-pass 的獨立 Twilight Glow 第三分支，只補齊 Glow 自己的兩段
六波段 extinction evidence：`Sun → Atmospheric Scatter Volume` 與
`Scatter Volume → Observer`。Formation 的 `Sun→CloudBase`、Viewing 的
`Cloud→Observer`、Photography Formation-first hard gate 均不改動。

每個 atmospheric scattering volume 現在都明列 550/575/600/650/700/750 nm 的
Rayleigh、non-O3 gas、O3、aerosol、cloud、precipitation optical depth，只有所有
component evidence 在同一 time + solar angle + glow volume identity 完整時，才建立
`tau_total` 與 `exp(-tau_total)` transmission。O3 從 HITRAN gas total 中獨立拆出，
non-O3 gas 定義為 O2+H2O，避免 575 nm Chappuis absorption 被重複計算。

新增 CASE evidence：

- `v1_twilight_glow_sun_to_scatter_extinction_550_750nm.csv`
- `v1_twilight_glow_scatter_to_observer_extinction_550_750nm.csv`
- `v1_twilight_glow_single_scattering_550_750nm.csv`

並新增 target coverage、six-band schema、Sun-path numeric closure、observer-path
numeric closure、single-scattering numeric closure Integrity。Partial/Missing component tau
可以保留為 diagnostic，但不得升格為 total transmission 或 final source proxy。

本版仍只輸出 **uncalibrated Rayleigh single-scattering spectral proxy**。Aerosol
single-scattering albedo、aerosol phase function、multiple scattering、surface coupling 與
絕對 radiometric calibration 尚未完成，因此
`calibrated_glow_radiance_available=False` 必須維持。Glow 不建立 Canvas、不修改
Formation/Viewing/Photography，也不能把「無火燒雲但有霞光」改寫成 Firecloud GO。

Working-tree regression：**486 passed / 0 failed**。正式 FULL-CLEAN 解壓回歸與 SHA256
見本版 Release Notes。


## R5.7.30.1 Integrity Regression Restore + Packaging Continuity Hotfix

R5.7.30 的 Twilight Glow 第三分支本身保留不變；本 hotfix 修正檢查時發現的
Integrity regression：R5.7.29.1 已 field-pass 的
`VIEWING_PRECIPITATION_TARGET_COVERAGE` 與
`VIEWING_NATIVE_HYDROMETEOR_HANDOFF` 曾被弱化成只要求「>0 downstream rows」。
R5.7.30.1 恢復完整 time + solar angle + canvas target coverage，並要求當
RWMR/SNMR/GRLE 全部 READY 時，不得存在
`VIEW_PRECIPITATION_VOLUME_UNRESOLVED`。

同時恢復 R5.7.29.1 的 versioned release notes 與 spool-handoff spec，避免
FULL-CLEAN 完整替換包遺失已凍結的歷史契約文件。Formation、Viewing extinction、
Twilight Glow、Photography、13 angles、六波段、route resolution 與 provider policy
均未改動。

## R5.7.30 Independent Twilight Glow Third Branch

R5.7.30 建立與 Formation、Viewing 分離的第三條物理分支：
`Sun → atmospheric scatter volume → Observer`。它使用既有 13-angle、
10–100 km、4/5/8/12 km 大氣 reference volumes，逐一保存
550/575/600/650/700/750 nm 的入射相對照度、散射體至觀測者的
gas/aerosol/cloud/precipitation extinction、Rayleigh extinction、分子散射係數、
phase-weighted source coefficient 與單次散射 source proxy。

只有 Sun path、observer path、Rayleigh path、散射幾何與局部分子狀態全部完整時，
才輸出六波段 source proxy；任一成分 Partial/Missing 時，final tau、transmission 與
source proxy 必須保持 Missing。此 proxy 沒有被宣稱為絕對天空輻亮度：目前缺少
aerosol single-scattering albedo／phase function、calibrated angular-volume
integration 與 multiple scattering，因此相關狀態全部明列為 unresolved。

新增 `v1_twilight_glow_scattering_volume_550_750nm.csv`、
`v1_twilight_glow_summary.csv` 與六項 `TWILIGHT_GLOW_*` Integrity guards。
Glow 不建立 Canvas、不輸出 decision/score、不改寫 Formation，也不成為 Photography
modifier。UI、權重、13 angles、route resolution 與 Forecast／Observation 邊界均未改動。

## R5.7.29.1 Viewing Precipitation Spool Handoff Hotfix

R5.7.29 真實部署 CASE 證明 GFS 已完整取得 RWMR/SNMR/GRLE，但
`viewing_route_snapshot` 在 final aggregation 讀取前被
`AngleFrameSpool.cleanup()` 刪除，造成 Viewing precipitation evidence 只有表頭，
所有 target 的 precipitation component 都保持 unresolved。

R5.7.29.1 將 cleanup 移到 Viewing snapshot drain 之後，並把 precipitation table
交給 Analysis Integrity。新增 target coverage 與 native hydrometeor handoff 兩項
硬檢查；當 RWMR/SNMR/GRLE 都為 READY，空 evidence table 或
`VIEW_PRECIPITATION_VOLUME_UNRESOLVED` 不再能被整體 Integrity 誤判為 PASS。

本 hotfix 不更改任何 extinction 公式、粒徑假設、Full RT 條件、Formation、Glow、
Photography gate、13 angles、六波段、route resolution 或 provider policy。

## R5.7.29 Viewing Full Six-Band RT Closure

R5.7.29 專門收斂獨立的 **Cloud→Observer Viewing** 六波段證據鏈。每個可攝影
target 現在必須在 550/575/600/650/700/750 nm 明列 Gas、CAMS aerosol、
cloud occupancy-optics 與 forecast-native precipitation optical depth；只有四個
component 在同一 time + solar angle + target identity 都完整時，才輸出 total
optical depth 與 transmission。Partial component tau 只保留為 diagnostic，絕不
升格成完整 Viewing transmission。

target cloud COT 與 Viewing precipitation 都改以 time + solar angle + object ID
綁定，防止各角度重複的 layer/canvas ID 串錯證據。GFS RWMR/SNMR/GRLE 現在
在 native merge 後才進入 Viewing snapshot；local target 亦保留明確 unresolved
row，不再從 target coverage 消失。Photography Decision 保存全部六波段 mean
transmission 與 completeness，但仍是未校準 diagnostic，不能改寫 Formation-first
hard gate。

Analysis Integrity 新增 target coverage、six-band schema、numeric closure、summary
coverage 與 Photography handoff 五項檢查；CASE 必須封存 Viewing precipitation、
spectral detail 與 spectral summary。Formation、Glow、UI、權重、13 angles、route
resolution 與 Forecast／Observation 邊界均未改動。

## R5.7.28 Red-Light Evidence Robustness

R5.7.28 根據 R5.7.27.1 真實 sunset CASE 收斂單一 CAMS
`SPECTRAL_COLUMN_AOD` 時次 timeout。當某個 CAMS 原生三小時時次缺少光譜
AOD、但同一分析已成功取得相鄰時次的真實 550/645/670/800 nm 欄位時，
只允許在 **3 小時以內**依 `point_id` 搬移這四個 provider-native 欄位。
O3、原生 3D aerosol、雲場、氣體與幾何仍綁定目標時次，不跨時次搬移。

輸出新增 `spectral_aod_temporal_evidence_state`、來源 valid time、時間偏移與
bound；六波段衍生品質明確標記
`REAL_ONE_SIDED_TEMPORAL_FALLBACK`。超過 3 小時、路徑格點不對應或相鄰
時次本身沒有至少兩個真實波段時，必須繼續保持 Missing。禁止固定
Angstrom、固定 O3、人工 AOD 或無界 endpoint extrapolation。

Red-Light reference 與 summary 現在分別輸出 cloud、aerosol、gas、
precipitation evidence；cloud `DIRECT_EVIDENCE_CONFLICT` 不再遮蔽 aerosol
temporal state。Formation、Viewing、Glow、13 angles、六波段、route
resolution、物理權重與 Forecast／Observation 分離均未改動。

## R5.7.27.1 Photography Integrity Handoff Hotfix

R5.7.27.1 修正 R5.7.27 的整合漏接：完整分析已建立 13-angle
`v1_photography_decision`，但先前未將它放入 `_pre_integrity_result`，使
Analysis Integrity 在真實 pipeline 中把 decision table 視為空表並可能誤報
angle coverage `FAIL`。本 hotfix 補上正式 handoff，並把
`v1_photography_decision.csv` 納入 CASE archive required-member 檢查。

本版不改 Formation、Viewing、Glow、13 angles、六波段、route resolution、
物理權重或任何 Forecast／Observation 分離規則。

正式來源基線：**R5.7.22.1 ACCEPTED BASELINE**。


## R5.7.27 Formation-First Photography Decision Aggregation

R5.7.27 收斂 **Formation → Viewing → Photography Decision** 的最外層聚合契約。Photography Decision 的時間軸現在由 Formation 驅動，因此 0°～−6°、每 0.5° 的 **13 個核心角度必須完整輸出 13/13 rows**；Viewing 可以因為沒有真實 target 而只有部分角度，但不得因此刪掉 Photography Decision 的其他角度。

本版加入 **Formation-first hard gate**：只要 Formation 已經是物理上明確的 NO-GO，例如 `CLEAR_RED_PATH_NO_CANVAS`、其他已解析 `NO_CANVAS_*` 狀態、或 `NOT_FORMED_EARTH_SHADOW`，最終 `photography_opportunity` 必須是 `NO_GO`。Cloud→Observer Viewing 仍保留原始診斷值，但此時其角色會標為 `DIAGNOSTIC_ONLY_FORMATION_NO_GO`，不得把 NO-GO 提升成 `FAIR / LIMITED / GOOD`。

No-Canvas 且沒有 Cloud→Observer target 時，Viewing 以 `VIEWING_NOT_APPLICABLE_NO_FORMED_TARGET` 表示 N/A；這不是 Viewing 資料缺失，也不會回寫 Formation。`NO_CANVAS_EVIDENCE` 仍不被硬判 NO-GO，因為它可能代表 Canvas evidence 尚未完整；只有 R5.7.26+ 已解析的 no-Canvas states 才能進 hard NO-GO。

Analysis Integrity 新增 `PHOTOGRAPHY_DECISION_FORMATION_ANGLE_COVERAGE` 與 `PHOTOGRAPHY_FORMATION_NO_GO_DOMINANCE`，防止日後再退回 2/13 rows 或 Viewing 覆蓋 Formation。

本版不修改 R5.7.26 Red-Light Availability、六波段 RT、Canvas Optical Truth、Viewing 物理本身或任何科學權重。


## R5.7.26 Red-Light Availability + Clear-Path-No-Canvas State

R5.7.26 將「紅光有沒有來」與「有沒有雲接住紅光」正式拆成不同物理事實。新增不代表真實雲體的 Reference Receivers，在 Primary Canvas（0–40 km）與 Extended Canvas（40–100 km）區域，以六波段 550/575/600/650/700/750 nm、有限太陽盤 `DirectSolarFraction`、Gas/O₃、CAMS aerosol、上游 CloudScene blocker 與原生 3D hydrometeor/降水證據，診斷 `RED_LIGHT_PATH_OPEN / PARTIAL / BLOCKED / CONFLICT / UNKNOWN`。Reference receiver 永遠不會被提升成 Canvas，也不會自行建立 Firecloud Formation。

若兩個 Canvas 域都沒有有效目標雲，target-specific `SPECTRAL_AEROSOL_PATH`、`SPECTRAL_CLOUD_PATH` 與 `FULL_SPECTRAL_RT` 皆為 `NOT_APPLICABLE`，而不是 Missing。若同時 Red-Light path 證據完整且通道 Open，Formation 的無雲情境會明確輸出 `CLEAR_RED_PATH_NO_CANVAS`；這代表「光路好，但沒有畫布」，不是火燒雲形成，也不是資料不足。`Unused Red-Light Potential` 僅為未校準連續診斷量，不是 Physics Score。Glow/Twilight Glow 仍是獨立第三分支，Viewing 仍是 Cloud→Observer。

只有在 Cloud Geometry completeness 完整時，「0 個 Canvas candidates」才可正式提升為 `ABSENT / NO_CANVAS`；若雲幾何本身 Partial/Missing，則輸出 `CANVAS_AVAILABILITY_UNKNOWN`，避免把資料不足誤當成晴空。

本版 regression：**456 passed / 0 failed**（正式封裝前 working tree；FULL-CLEAN 解壓驗收見本版 Release Notes）。

**凍結關係：** `Red-Light Availability != Firecloud Formation != Viewing != Glow`。真正 Formation 仍需要 Red-Light Availability × Effective Canvas Availability × Canvas Optical Response。

## R5.7.25 Formation Sun→CloudBase Cloud-Path Completeness

本版專門收斂 **Formation 的紅光照射路徑**。請注意：本版的 `Cloud Path`、`SPECTRAL_CLOUD_PATH`、`OpticalPathResult`、`FULL_SPECTRAL_RT` 都是 **Sun→CloudBase**，回答「紅橘光能不能照到目標雲底」；它們不是 Viewing。觀測者能否看見已形成的火燒雲，仍由獨立的 **Cloud→Observer Viewing** 分支判定。

R5.7.25 修正：

- V1 Canvas-specific `Sun→CloudBase OpticalPathResult` 成為 Formation Full RT completeness 的權威判定，不再讓底層 finite native slant tau 越級宣告 Full RT。
- native cloud slant tau 只有在 `upstream_path_checked=True`、`native_ray_path_completeness>=0.999` 且 path state 完整時，才可公開為 production cloud transmission；partial tau 僅保留為 lower-bound diagnostic。
- Cloud Fraction 顯示有雲但 native condensate 為 0／不支持時，明確標為 `DIRECT_EVIDENCE_CONFLICT`，不再混成一般 Missing，也不假設 Clear。
- 已解析垂直 COT 但 horizontal support 不完整時，保持 `CLOUD_HORIZONTAL_SUPPORT_UNRESOLVED / PARTIAL`，不得升級為完整 upstream cloud RT。
- Formation RT applicability 以 **CloudBase `DirectSolarFraction`** 為權威。Penumbra 中即使最近 native voxel centre 已落入陰影，只要目標 CloudBase 仍看得到部分太陽盤，Gas/Aerosol/Cloud Formation RT 仍屬 required。
- `physics_data_completeness.csv` 新增／統一 `SPECTRAL_CLOUD_PATH`，且 `FULL_SPECTRAL_RT` 必須與 V1 Sun→CloudBase OpticalPathResult 一致；Integrity 會檢查兩者是否分歧。

本版不改 Viewing、Photography Decision、Target Canvas COT truth、Tier-2 LUT 權重或任何 Forecast/Observation 分離規則。

驗收：Working tree **445 passed / 0 failed**；FULL-CLEAN ZIP 解壓後 **445 passed / 0 failed**。


## R5.7.24.3 Provider Cycle Freeze / Prefetch-Handoff Reliability

本版修正長時間分析跨越 provider availability boundary 時，prefetch 與 per-angle lookup 可能解析到不同 GFS/CAMS cycle 的問題。Analysis worker 啟動時凍結 `FIRECLOUD_PROVIDER_RESOLUTION_NOW_UTC`；父程序、per-angle resolver 與 CAMS 外部 worker 全部使用同一個 analysis-start clock。此修正不改 Forecast valid time、物理幾何、六波段、Formation / Viewing 或 Missing 語義。


## R5.7.24.2 Spectral Aerosol Formation-Path Contract

R5.7.24.1 REAL CASE 顯示 CAMS native 3-D aerosol、Spectral AOD、O₃、gas profile 與 HITRAN 都可 READY，但 0°～−5°仍被標成 `SPECTRAL_AEROSOL_PATH=MISSING`。實際原因是這些角度沒有 Canvas target；−5.5°～−6°雖有 Canvas，但 DirectSolarFraction 全為 0、全部位於 Earth Shadow。舊完整性邏輯把「沒有需要計算的 spectral target」錯當成 Missing。

R5.7.24.2 修正：

- `NO_TARGET_CLOUD_GEOMETRY` 與 `NO_DIRECT_SUNLIT_CANVAS_RT_REQUIRED` 正式標為 `NOT_APPLICABLE`，不再假 Missing。
- aerosol route spectrum 對齊六波段：**550 / 575 / 600 / 650 / 700 / 750 nm**。
- native CAMS 3-D aerosol 只有在六波段 tau、path completeness 與 route domain 都完整時才可作 production path。
- native path 有有限 tau 但不完整時，可嘗試 real multi-wavelength AOD 的 **Sun→CloudBase** exponential-profile fallback。
- 舊 Observer→Target aerosol fallback 不再用於新的 Formation production path。
- partial native tau 仍保留作診斷，但不得直接成為 public `aerosol_transmission_λ`。

本修正不改 Formation / Viewing / Glow、Earth Shadow、DirectSolarFraction、Target Optical Truth、Route Invariance 或 Tier-2 directional geometry。


## R5.7.24.1 CAMS Availability Guard

R5.7.24 現場 CASE 已驗證記憶體收斂有效，但在 2026-09-08 10:21 UTC 的 WARM_PRODUCTION 分析中，CAMS cycle resolver 過早選到當日 00Z +9/+12h。ADS 對 O₃ 與 Spectral AOD 回覆 HTTP 400 `invalid request / valid combination`，舊 adaptive planner 又把這種非空間型錯誤誤判成可由縮小 route bbox 修復，造成大量無效子區重試與 CAMS 預取約 573 秒，最終 O₃ evidence chain 仍 FAIL。

R5.7.24.1 因此採可靠性優先修正：

- CAMS 預設 availability guard 由 10.25 h 調整為 **12.25 h**，避免過早切換到剛發布但角色資料尚未完整可取的新 cycle。
- HTTP 400 `invalid request / invalid combination / valid combination` 被分類為**非空間型 ADS request failure**，不再做 adaptive spatial subdivision。
- 仍維持 Missing / fail-closed 語義；不以舊值、常數或 synthetic profile 補 O₃ / aerosol evidence。
- R5.7.24 的 Runtime Reliability、Recovery、Memory Containment 全部保留。

## R5.7.24 Runtime Reliability / Completion Guarantee + Memory Containment

本版把「程式能可靠完成分析」放在效能之前。R5.7.23.4 已有一次真正 `COLD_ISOLATED_TEST` one-shot 完成案例，但長時間執行仍曾出現 app/session 中止與約 1.0–1.1 GB RSS，因此 R5.7.24 專門收斂 worker、recovery 與記憶體生命週期。

- Streamlit 主 script 不再用長時間 `while` 監看背景分析；改為 detached analysis worker + 非阻塞自動刷新 fragment。
- live worker 在頁面 rerun/reload 後會自動重新連線監看，不會因刷新啟動第二個 worker。
- recovery journal 同時保存 master 與 per-job `job_state.json`；master 遺失/損壞時可掃描 per-job / attempt progress 重建。
- 每次 attempt 保存獨立 request / progress / stdout / stderr / result，前次錯誤不再冒充本次 worker stderr。
- 13 個完整 route snapshots 改為 worker-local `/tmp` spool，不再同時常駐 RAM。
- Viewing route snapshot、Cloud/Gas/Aerosol/Spectral 大型 per-angle evidence 也改為 spool；完整性 audit 先轉成小型 per-angle 摘要。
- `details` 僅保留 UI 垂直剖面必要的 direction/distance/low-mid-high cloud cover 欄位，不再保存完整 provider snapshot。
- 每角度邊界執行 `gc.collect + malloc_trim`（支援 glibc 時）；analysis worker 啟動時使用 `MALLOC_ARENA_MAX=2` 與 `MALLOC_TRIM_THRESHOLD_=131072` 降低 heap arena retention。
- 13-angle 完成後、aggregation 前主動釋放 GFS/CAMS/Secondary provider in-memory cache。
- 不減少 13 angles、不降低 0.5 km 垂直解析度、不刪六波段、不改 Formation / Viewing / Glow / Missing / Route Invariance / Tier-2 科學契約。

**本版不是效能優化版。** 外部 CAMS ADS / DWD 網路仍可能耗時；R5.7.24 的目標是即使慢，也盡量能跑完、能留下狀態、能安全 Resume。

正式來源基線：**R5.7.22.1 ACCEPTED BASELINE**。

## R5.7.23.3 CAMS Live-Telemetry Hotfix

- 修正 production global ADS single-flight 模式中，第一個 CAMS time bundle 實際執行時 UI 仍可能顯示「時次 1/2｜等待；時次 2/2｜等待」的 telemetry blind spot。
- role heartbeat 在 single-flight 模式下會立即刷新 UI。
- 新增「解碼快取查找」與「worker啟動」子階段，區分 cache I/O、worker spawn 與真正 ADS request。
- 第二時次在第一 time bundle 完成前維持「等待」仍屬正常 single-flight 行為。
- 不修改 CAMS 90 秒 deadline、request variables、adaptive planner、Formation / Viewing / 六波段或 Tier-2 科學契約。


## R5.7.23.2 Memory-Safe Aggregation Hotfix

- 修正 13-angle 完成後「彙整民用曙暮光時間軸與矩陣」階段的 RAM 尖峰。
- 大型 per-angle DataFrame 不再先 `.copy()` 後與原件同時留在 `details`；改為先完成 completeness audit，再逐類 drain 到最終 aggregate matrix。
- 每完成一類 aggregation 即釋放暫存 frame 並執行 GC，降低同時存在的 duplicate buffers。
- aggregation 拆成可見子階段並寫入 runtime resource telemetry，便於定位真正的記憶體瓶頸。
- 不減少 13 angles、不降低 0.5 km 垂直解析度、不刪 CASE 證據，也不修改 Formation / Viewing / Tier-2 科學邏輯。


## R5.7.23.1 Runtime Hotfix

本 hotfix 針對 Cold Test 實測中「CAMS 時次 1/2 三鏈已完成，但時次 2/2 長時間維持等待」以及 Streamlit rerun 誤把仍存活的背景分析 worker 標成未正常完成兩項問題。

- CAMS 外部 worker 完成後，新增 `DECODED_ROUTE_CACHE_WRITE` 與 `CAMS_BUNDLE_POSTPROCESS` 進度狀態，避免 UI 停在舊訊息而無法知道父程序真正所在階段。
- `COLD_ISOLATED_TEST` 不再同步寫第二份 decoded-route pickle cache；raw CAMS GRIB 仍維持 atomic/QC cache，因此不改科學資料。
- Warm/Resume decoded-route cache 仍保留，但其額外 `fsync` 改為 opt-in，避免 mounted filesystem 上的非必要同步落盤拖住 analysis worker。
- Streamlit rerun/reload 若偵測 detached analysis worker PID 仍存活，會自動重新連線監看，不再誤標為「上一次分析未正常完成」，也不會啟動第二個 analysis worker。
- 不修改 Formation、Viewing、Glow、六波段、Route Invariance 或 Tier-2 calibration 科學契約。


R5.7.23 同時完成兩條工程主線：

1. **Runtime Hardening**：Cold/Warm/Resume、cache provenance、atomic cache、CAMS ADS single-flight、stage heartbeat、resource telemetry。
2. **Genuine Liquid-Cloud Full Directional Calibration Pipeline V3**：REAL CASE domain → spherical MYSTIC jobs → external result collector/QC → production LUT package gate。

本建置環境沒有 `uvspec`，所以 genuine calibrated directional LUT **尚未生成／尚未安裝**；不得以 synthetic LUT 取代。

### Runtime Cold Test

UI 勾選 Cold Test 後，本次 job 使用隔離 provider cache namespace。CASE 會新增：

- `runtime_execution_contract.csv`
- `runtime_cache_provenance.csv`
- `runtime_stage_trace.csv`
- `runtime_resource_telemetry.csv`

### Calibration CLI

由 CASE 推導 domain：

```bash
python tools/derive_tier2_liquid_directional_domain_from_case.py --case <CASE.zip_or_dir> --output-dir <domain_dir>
```

建立 calibration bundle：

```bash
python build_tier2_liquid_directional_calibration_jobs.py --foundation-csv <foundation.csv> --readiness-csv <readiness.csv> --output-dir <bundle_dir>
```

在外部 libRadtran 環境先渲染 jobs（不執行 RT）：

```bash
python run_tier2_libradtran_mystic_calibration.py --jobs-csv <jobs.csv> --solver-recipe-json <recipe.json> --run-dir <run_dir> --data-files-path <libRadtran/data> --atmosphere-file <atm.dat> --render-only
```

真正 external MYSTIC 執行後收集結果：

```bash
python collect_tier2_libradtran_mystic_results.py --jobs-csv <jobs.csv> --run-dir <run_dir> --output-csv <results.csv> --solver-version <version>
```

最後 production build 必須同時提供 exact domain spec 與 calibration metadata：

```bash
python build_tier2_liquid_directional_lut_from_results.py --jobs-csv <jobs.csv> --results-csv <results.csv> --metadata-json <metadata.json> --domain-spec-json <domain.json> --output-dir <lut_package_dir>
```

詳見：

- `RUNTIME_HARDENING_SPEC_R5.7.23.md`
- `TIER2_LIQUID_DIRECTIONAL_CALIBRATION_PIPELINE_SPEC_R5.7.23.md`

## R5.7.23 Genuine Liquid-Cloud Full Directional Calibration Pipeline

本版以 **R5.7.22.1 ACCEPTED BASELINE** 為唯一基準，不改動 Route Invariance、Formation / Viewing / Glow 分離或六波段契約。新增 production calibration 生產線：

`REAL Tier-2-ready liquid targets → calibration domain → libRadtran/MYSTIC spherical jobs → external RT QC → calibrated directional LUT package`

- Production LUT 軸維持 `COT × r_eff × θ₀ × θᵥ × Δφ × wavelength`。
- `cloud_thickness_km` 只保留為幾何／光學證據，不是 production interpolation axis。
- 第一階段只建立 **liquid cloud** genuine calibration，不以 ICE 或 synthetic response 混入。
- 外部結果必須完整覆蓋 job tensor、solver exit=0、Monte-Carlo convergence QC、approved full-hemisphere solver 與 provenance。
- 若沒有 genuine RT 結果，production LUT 必須維持 `NOT_YET_GENERATED_EXTERNAL_RT_REQUIRED`；不可用 synthetic LUT 冒充。
- 本版提供正式 job generator、MYSTIC spherical recipe/template、external-result validator 與 production package builder。


## R5.7.22.1 Route Invariance Hotfix

本版在 R5.7.22 Full Directional Cloud Scattering Geometry Contract 上修正 provider sampling route 與 runtime 太陽角度集合耦合的問題。

正式凍結：

- GFS / CAMS / Forecast 的 Reference Route 固定以太陽高度 **−2.0°** 的太陽方位建立。
- Provider spatial sampling distance lattice 固定依完整 **0°～−6°** PhysicsCore 路徑需求建立。
- 改變 runtime angle subset、或從 9-angle 擴充到 13-angle，不得旋轉或縮短既有 sampling corridor。
- 每個太陽高度仍使用自己的事件時間、太陽高度與太陽方位計算 Sun→Cloud 與 Tier-2 directional geometry。
- CASE 新增 `route_reference_contract.csv`，保存 reference angle、reference time、reference azimuth、route domain 與 invariance provenance。

此修正關閉 R5.7.21.1 / 未修正 R5.7.22 中因核心角度中點由 −2° 變成 −3°，導致 route bearing 約偏移 0.672° 的回歸。


R5.7.22 正式把 Tier-2 雲散射方向幾何由原本只依賴 `scattering_angle`，升級為完整的 target-local directional contract：

- `θ₀ = solar_zenith_deg`
- `θᵥ = view_zenith_deg`
- `Δφ = relative_azimuth_deg`
- `scattering_angle_deg` 僅保留為衍生診斷，不再是 production interpolation axis

核心火燒雲太陽高度維持：

`0, −0.5, −1, −1.5, −2, −2.5, −3, −3.5, −4, −4.5, −5, −5.5, −6°`

共 13 個角度。

## 核心架構

PhysicsCore 持續維持三個獨立問題：

- **Formation**：Sun → CloudBase，判斷火燒雲是否形成。
- **Viewing**：Cloud → Observer，判斷已形成的火燒雲是否看得到。
- **Glow**：獨立的大氣霞光分支，不取代雲底受光 Formation。

Formation 核心輸出仍分離為 Brightness、Redness、Effective Illuminated Area，不合併成單一 Formation Score。

## Tier-2 Full Directional Scattering

R5.7.22 production LUT 的核心插值維度為：

`COT × r_eff × θ₀ × θᵥ × Δφ`

六波段各自完整保留：

`550 / 575 / 600 / 650 / 700 / 750 nm`

### 方向幾何定義

- `θ₀`：Cloud → Sun 相對雲底當地天頂的夾角，範圍 0–180°。
- `θᵥ`：Cloud → Observer 相對雲底當地天頂的夾角，範圍 0–180°。
- `Δφ`：Cloud→Sun 與 Cloud→Observer 在雲底當地水平面的最小方位差，範圍 0–180°。
- `scattering_angle_deg`：Sun→Cloud incoming photon 與 Cloud→Observer outgoing photon 的夾角，只作診斷。

太陽方向會先由觀測點 local ENU 轉為 ECEF，再投影到每個 target cloud 的 local ENU；不再把觀測點太陽角度直接當成每個雲底的 local angles。

### cloud thickness 的角色

`cloud_thickness_km` 仍保留於 target / CASE 幾何與雲體證據，但 R5.7.22 不再把它當成純雲散射 LUT 的 production interpolation axis。

## Production LUT 安全閘門

R5.7.22 不接受舊版 scattering-angle-only LUT 直接升級成 production LUT。

Production LUT 必須提供：

- full directional `θ₀ / θᵥ / Δφ` 網格
- 六波段完整覆蓋
- multiple-scattering 校準來源
- full-hemisphere 0–180° 支援聲明
- RT solver provenance
- QC PASS
- validation reference
- CSV SHA256

舊 R5.7.19/R5.7.20 LUT 只保留歷史 regression 用途，不能啟動 R5.7.22 production solver。

## 跨區域時間

延續 R5.7.21：

- 依座標自動解析 IANA timezone。
- 物理時刻另外保存 UTC。
- 同一 UTC 瞬間的太陽幾何不受顯示時區影響。
- 可用日本、沖繩或其他區域作 REAL_CANVAS regression testing。

## 執行與部署

主要 Streamlit 入口：

`app.py`

完整依賴請見：

`requirements.txt`

本版文件：

- `RELEASE_NOTES_PhysicsCore_V1.0-R5.7.22.md`
- `IMPLEMENTATION_STATUS_PhysicsCore_V1.0-R5.7.22.md`
- `TIER2_DIRECTIONAL_SCATTERING_GEOMETRY_SPEC_R5.7.22.md`

## R5.7.23 Runtime Hardening

為了區分真正的 provider/runtime stall 與重新 TEST 後的 persistent-cache 加速，本版提供三種分析執行契約：`WARM_PRODUCTION`、`COLD_ISOLATED_TEST`、`RESUME_SAME_JOB`。Cold Test 會建立 job-specific provider cache namespace；CASE 另保存 runtime stage trace、cache provenance 與 resource telemetry。CAMS production 預設採 ADS global single-flight，避免兩個 forecast time 同時送出 SPECTRAL_COLUMN_AOD 等遠端請求。

R5.7.23 的 genuine liquid-cloud calibration pipeline 已可產生與驗證外部 libRadtran/MYSTIC jobs；本封裝環境未含 `uvspec`，因此 genuine calibrated production LUT 仍維持 `NOT_YET_GENERATED_EXTERNAL_RT_REQUIRED`，不會以 synthetic LUT 取代。

## Release Gate
- Working regression：562/562 PASS
- FULL-CLEAN：CLOSED
- Extracted regression：562/562 PASS
- cache / pyc：0
- Field validation：OPEN
