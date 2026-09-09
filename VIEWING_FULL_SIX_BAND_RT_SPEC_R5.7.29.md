# R5.7.29 Viewing Full Six-Band RT 規格

## 1. 目的與邊界

本版只完成獨立的 `Cloud→Observer` Viewing 六波段 RT 證據閉環。Formation
仍是 `Sun→CloudBase`；Glow 仍是第三條獨立分支。本版不新增攝影門檻、分數、
權重或 UI 決策，也不改 13 angles、route resolution 與 Forecast／Observation
邊界。

固定波段為 `550 / 575 / 600 / 650 / 700 / 750 nm`。

## 2. Full RT 必要條件

每一個 `photographic_target_eligible=True` 的 target，以
`time + solar_altitude_deg + canvas_id + cloud_layer_id` 作唯一識別。每一波段
必須同時具備：

- `view_tau_gas_*nm`：真實 route gas profile 的 Cloud→Observer 積分；
- `view_tau_aerosol_*nm`：CAMS 原生 3-D extinction，並具 R5.7.28 exact-time
  或 3 小時內真實相鄰時次 provenance；
- `view_tau_cloud_*nm`：前景雲 occupancy expectation 與可追溯 COT；
- `view_tau_precip_*nm`：forecast-native RWMR/SNMR/GRLE 路徑積分。

只有四個 component 都是 resolved，才可計算：

`view_tau_total = gas + aerosol + cloud + precipitation`

`view_transmission = exp(-view_tau_total)`

任一 component partial/missing 時，component diagnostic 可保留，但 total 與
transmission 必須為 Missing，狀態不得升格為 Full。

## 3. Evidence identity 與 coverage

- COT 必須以 `time + angle + layer_id` 綁定；不得把跨角度重複 layer ID 當全域鍵。
- precipitation 必須以 `time + angle + canvas_id` 綁定。
- local 或無法形成正長度 Viewing path 的 eligible target 仍須輸出明確
  `VIEW_SIX_BAND_RT_UNRESOLVED` row，不得從 coverage 消失。
- GFS Viewing snapshot 必須在 native hydrometeor merge 後建立。

## 4. Summary 與 Photography

每個 time-angle summary 輸出 target 數、Full/Partial/Unresolved 數、整體與逐波段
completeness，以及六波段 mean transmission。Mean 只能聚合 Full rows。

Photography Decision 接收全部六波段與 completeness，但其角色固定為
`DIAGNOSTIC_ONLY_UNCALIBRATED`。Formation hard NO-GO 必須先判定，Viewing RT
不得把它改成 FAIR、LIMITED 或 GOOD。

## 5. Integrity

Analysis Integrity 固定檢查：

- `VIEWING_SIX_BAND_TARGET_COVERAGE`
- `VIEWING_SIX_BAND_SCHEMA`
- `VIEWING_SIX_BAND_NUMERIC_CLOSURE`
- `VIEWING_SIX_BAND_SUMMARY_COVERAGE`
- `VIEWING_SIX_BAND_PHOTOGRAPHY_HANDOFF`

CASE archive 必須包含 `v1_viewing_precipitation_evidence.csv`、
`v1_viewing_spectral_extinction_550_750nm.csv` 與
`v1_viewing_spectral_summary.csv`。

