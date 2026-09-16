# RELEASE NOTES — V1.0-R5.7.41.3.4.10.15.1

## 名稱
**Step 3B CASE Evidence Handoff Integrity Hotfix**

## 背景
`.10.15 / 2026-09-17 sunrise / TWS100 合歡山北峰` FIELD CASE 發現：model 內部的 GFS v16 scheme-pin evidence 為 8 rows、gate 為 1 row、contract 完整，Analysis Integrity 因此 PASS；但真正 CASE export 卻寫出 0-row evidence、0-row gate 與空 `{}` contract。既有 Archive Integrity 只檢查檔名存在，因此誤判 PASS。

## 修正
- CASE export 不再依賴 UI/session `result` 中的 Step 3B static evidence keys。
- CASE 產生時直接由當前 running release 的：
  - `build_gfsv16_scheme_pin_evidence()`
  - `build_gfsv16_scheme_pin_gate()`
  - `gfsv16_scheme_pin_contract_payload()`
  重建 release-static Step 3B evidence。
- `build_archive_integrity_audit()` 新增內容級 hard gate：
  - evidence CSV `row_count >= 8`
  - gate CSV `row_count >= 1`
  - contract JSON `byte_size > 2`
- 因此「檔名存在但內容為空」不再可能得到 CASE Archive overall PASS。

## 科學基線
完全不變：
`R5.7.41.2_SHADOW_COT_AB_FROZEN`

不更動：
Formation、Viewing、Twilight Glow、六波段、Canvas、Corridor、REZ、Earth Shadow、Production/Shadow COT、CLWMR/ICMR threshold、Missing≠Clear≠Zero。

Ice Optics 仍保持：
- effective radius ≠ Yang/Bi Dmax
- Dmax mapping：disabled
- PSD reconstruction：disabled
- habit default：prohibited
- roughness default：prohibited
- production promotion：disabled

## 測試
Working-tree full regression：
**800/800 PASS，0 failed，1 existing pandas FutureWarning**

FIELD validation 尚未完成；上一個正式 FIELD PASS 仍為 `.10.14`。
