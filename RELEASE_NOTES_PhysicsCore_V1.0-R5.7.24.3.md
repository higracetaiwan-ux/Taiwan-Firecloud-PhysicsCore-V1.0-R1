# Taiwan Firecloud PhysicsCore V1.0-R5.7.24.3 Release Notes

## 版本主題

**Provider Cycle Freeze / Prefetch-Handoff Reliability**

## 修正內容

本版修正 R5.7.24.2 真實 CASE 發現的 provider cycle 漂移問題。

同一個分析開始時，CAMS 預取可能使用前一個已發布 cycle；若分析執行數分鐘後剛好跨越新的 availability boundary，舊版 per-angle lookup 會再次呼叫 resolver，並可能切換到較新的 cycle。此時前段已成功預取的 CAMS payload 仍存在，但後段 lookup 使用不同 key，因此被錯誤呈現成 O3 / aerosol Missing，連 request audit 都可能在最終 CASE 中消失。

R5.7.24.3 將 provider cycle availability clock 凍結在 analysis worker 啟動時間。GFS、CAMS parent、CAMS external worker、decoded cache 與 per-angle lookup 在同一個 job 內使用同一個 reference clock。

## 真實 R5.7.24.2 CASE 驗證

該 CASE 已確認：

- `SPECTRAL_AEROSOL_PATH` 的 R5.7.24.2 NOT_APPLICABLE 修正有效。
- 0°～−5°：`NOT_APPLICABLE / NO_TARGET_CLOUD_GEOMETRY`。
- −5.5°～−6°：`NOT_APPLICABLE / NO_DIRECT_SUNLIT_CANVAS_RT_REQUIRED`。
- 記憶體 containment 持續有效，observed RSS max 約 758 MB，process peak 約 856 MB。
- CAMS 預取本身並非全失敗：第一時次 O3/AOD/532 全部成功；第二時次 O3 與 532 成功，Spectral AOD 90 秒 TIMEOUT_DEFERRED。
- 第一個 angle 於 12:15:15 UTC 開始，正好跨過 CAMS 12.25 h availability boundary，造成 prefetch key 與 per-angle key 不一致。

## 不變的科學契約

本版不改：Formation / Viewing / Glow 分離、Sun→CloudBase、DirectSolarFraction、Earth Shadow、13 angles、六波段 550/575/600/650/700/750 nm、Target Canvas optical truth、Tier-2 directional geometry、Missing/Conflict 語義。
