# R5.7.24.1 CAMS Availability Guard 技術規格

## 問題

CAMS Global Forecast 的 nominal publication time 不等於所有 role 在 ADS 上都已立即形成可合法查詢的 variable/lead 組合。若過早切到新 cycle，ADS 可能回覆 HTTP 400 `invalid request` / `Request has not produced a valid combination of values`。

這類錯誤屬於：

**cycle / lead / variable selection availability failure**

不是 route bbox 太大。

## 規則 A：保守 cycle guard

預設：

`FIRECLOUD_CAMS_AVAILABILITY_LAG_HOURS = 12.25`

保留環境變數覆寫能力，但 production 預設採可靠性優先。

## 規則 B：HTTP 400 不做 spatial subdivision

若錯誤文字同時符合 HTTP 400 與以下任一特徵：

- `invalid request`
- `invalid combination`
- `valid combination`

則分類：

`NONSPATIAL_ADS_REQUEST_FAILURE`

該 role/segment 立即 fail-closed，不再切 ROOT.1 / ROOT.2 / deeper children。

## 規則 C：不偽造資料

此修正只改 request planning / retry policy，不改 Missing 語義：

- O₃ 缺失仍是 Missing
- AOD 缺失仍是 Missing / Partial
- 532 nm aerosol 缺失仍是 Missing
- 不使用 RH / CF 造 aerosol optical depth
- 不使用固定 O₃ 常數
- 不把 prior-cycle payload 靜默標成 current-cycle payload

## 規則 D：空間型 adaptive planner 保留

只有失敗可能與 bbox / workload / remote processing size 有關時，才允許 spatial subdivision。

## 現場回歸依據

R5.7.24 2026-09-08 sunset CASE：

- 00Z +9/+12 h 對 O₃/AOD 產生大量 HTTP 400
- CAMS prefetch 約 573 s
- O₃ payload completeness = 0
- analysis integrity FAIL

R5.7.23.4 同事件較早執行：

- previous 12Z +21/+24 h
- 三條 CAMS role 均成功

因此 availability guard 是 runtime reliability 修正，不是火燒雲物理權重調整。
