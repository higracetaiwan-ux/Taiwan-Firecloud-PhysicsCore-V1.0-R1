# R5.7.41.3.4.3 — DWD Secondary Runtime Cache Hardening

## 目標

降低 DWD ICON Global secondary native-optics provider 在同一個分析工作中，因 13 個太陽角度重複存取相同 run/lead native fields 所造成的 I/O 與無效 HTTP 請求。

本版是 **runtime / I/O hardening only**。不得改變：

- Production COT；
- Shadow COT eligibility；
- Earth Shadow / DirectSolarFraction；
- Formation / Viewing / Twilight Glow 科學判定；
- Missing / Clear / Zero 語意；
- DWD native QC/QI/T/P 數值或垂直幾何公式。

## CASE 觸發證據

Historical CASE（2026-08-27 TWS175、2026-09-04 TWS021）中：

- DWD condensate probe 預設 54 個 model levels（55–108）；
- QC + QI = 108 個 field requests / candidate time；
- 13 個太陽角度使用相同 DWD run/lead；
- 歷史 OpenData object 已不存在時，觀察到 `108 × 13 = 1404` 筆 `HTTP_404`；
- 這些 404 不提供任何 secondary optical evidence，只增加 runtime。

## 修正 A：Runtime Decoded Native Field Cache

新增 process-local `_FIELD_VALUE_CACHE`：

- key = DWD run + lead + model level + variable + route geometry signature；
- route geometry signature 只包含 point id / lat / lon / distance / direction；
- **刻意不包含**每個候選時間會變動的 surface pressure / elevation anchor；
- cache 內容只保存 native field 解碼值（QC/QI/T/P）；
- 每個候選時間的 vertical geometry 仍使用該時間自己的 surface anchor 重新計算。

因此：

> Native field values 可重用；time-specific vertical geometry 不重用。

這不會把一個時間的 Cloud Base/Top 幾何複製到另一個時間。

Cache 有 bounded item limit（預設 512），避免長生命週期 worker 無限制增長。

## 修正 B：All-404 Run/Lead Negative Cache

新增 process-local `_NEGATIVE_RUN_LEAD_CACHE`。

只有在一次完整 QC/QI probe 同時滿足：

1. decoded condensate field count = 0；
2. 實際 FIELD_FETCH rows 數 = expected QC+QI field count；
3. **每一筆** status 都是 `HTTP_404`；

才寫入 negative cache：

`RUN_LEAD_UNAVAILABLE_ALL_QC_QI_HTTP_404`

同一 process 之後相同 run/lead/level contract 的候選角度直接回：

`RUN_LEAD_UNAVAILABLE_CACHED`

不再重送 108 個 HTTP requests。

Mixed 404/500、timeout、decode failure、partial ready 等狀況 **不得**寫入 negative cache，仍維持 unresolved / 正常重試。

## Fail-closed 保證

Negative cache 代表：

> 該 run/lead 在本次 process 中已由完整 probe 證明所有要求的 QC/QI object 都是 HTTP 404。

它不代表 Clear，也不代表 zero condensate；輸出仍是 secondary optics unavailable / Missing。

## API Efficiency Audit

DWD `network_requests` 修正為包含：

- `DOWNLOADED`；
- HTTP 4xx / 5xx request rows。

並新增統計：

- decoded native field cache hit；
- negative availability cache hit。

這只改善 operational telemetry，不參與 physics gates。
