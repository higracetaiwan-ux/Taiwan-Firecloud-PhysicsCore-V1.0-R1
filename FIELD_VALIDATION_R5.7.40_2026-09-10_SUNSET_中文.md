# R5.7.40 / 2026-09-10 Sunset CASE 驗證

## 科學結果
- Vertical qualification rows：432。
- Unique conflict canvases：45。
- 432/432：`ISOLATED_PRIMARY_CF_SPIKE_HYDROMETEOR_UNSUPPORTED`。
- qualification confidence：FULL。
- COT promotion：0。
- Formation promotion：0。

150 hPa 主 cloud-fraction 訊號缺乏 100/200 hPa 主鄰層及 125/175 hPa intermediate native condensate 支撐，因此 target optical truth 繼續保持 `DIRECT_EVIDENCE_CONFLICT` / `OPTICS_UNKNOWN`。

## Integrity 問題
R5.7.40 CASE 的 `CANVAS_OPTICAL_VERTICAL_CONFLICT_QUALIFICATION` 誤為 `ALLOWED_EMPTY`，根因是 pre-export audit 漏傳 `v1_target_canvas_optical_evidence`。

## R5.7.40.1 離線 replay
補齊 handoff 後：Integrity = PASS；432 qualification rows；45 expected / 45 observed unique canvases。
