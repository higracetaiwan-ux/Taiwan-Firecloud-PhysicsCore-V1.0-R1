# R5.7.41.3.2 Field Replay — 2026-09-12 TWS059 野柳岬 Sunrise

來源：R5.7.41.3.1 Online CASE，離線重播 Shadow migration handoff，不重新抓取 GFS/CAMS。

## 原版 R5.7.41.3.1
- targets：585
- eligible：585
- ineligible：0
- Target Optical Truth `CONDENSATE_CLOUD_CF_LOW_CONFLICT`：39 rows
- qualification：39/39 已正確辨識
- 問題：Vertical Overlap / Shadow migration 未同步 fail-close

## R5.7.41.3.2 replay
- targets：585
- eligible：546
- ineligible：39
- eligible fraction：93.33%
- ineligible reasons：`DIRECT_EVIDENCE_CONFLICT;VERTICAL_INTEGRATION_CONTRACT_FAILED`
- direct-conflict candidate COT finite count：0
- mean Legacy Production COT：約 0.365424
- mean eligible Shadow in-cloud COT：約 0.458557
- median Shadow/Legacy ratio：約 1.188656×
- Production switch：0
- COT promotion：0
- Formation promotion：0
- independent target-truth→eligibility handoff guard：PASS

## CASE 分類
可納入正式 Shadow cohort，分類為：High Cloud Canvas / Mostly Eligible + Low-CF Direct Conflict Control。
