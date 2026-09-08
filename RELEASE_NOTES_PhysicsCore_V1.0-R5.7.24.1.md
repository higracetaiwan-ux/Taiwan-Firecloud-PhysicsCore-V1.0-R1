# Taiwan Firecloud PhysicsCore V1.0-R5.7.24.1 改版說明

## 版本主題

**CAMS Availability Guard + Non-Spatial HTTP 400 Fail-Fast**

本版以「程式能正常完成且資料證據鏈不因錯誤 cycle 選擇而失效」為優先，不做科學權重或解析度調整。

## 現場 CASE 發現

R5.7.24 / 2026-09-08 sunset CASE 顯示：

- `analysis_run_mode = WARM_PRODUCTION`
- 程式完整跑到 CASE，但 `analysis_integrity = FAIL`
- CAMS resolver 在約 10:21 UTC 選到 `2026-09-08 00Z`，使用 +9 / +12 h lead
- O₃ 與 Spectral AOD 大量收到 ADS HTTP 400：`invalid request / Request has not produced a valid combination of values`
- adaptive planner 對相同 cycle/lead/variable contract 做 route 子區切割，造成數十次無效請求
- `CAMS_PREFETCH_TOTAL ≈ 573.3 s`
- O₃ numeric payload = 0%，最終形成 evidence-chain hard failure

同一事件稍早的 R5.7.23.4 Cold CASE 在 09:31 UTC 使用前一個 `2026-09-07 12Z` cycle（+21/+24 h）時，O₃、AOD、532 nm aerosol 均能取得，證明問題不是事件幾何本身。

## 修正

1. CAMS 預設 availability lag：
   - 舊：10.25 h
   - 新：**12.25 h**

2. 新增非空間型 ADS request failure 分類：
   - HTTP 400
   - `invalid request`
   - `invalid combination`
   - `valid combination`

   上述錯誤不再做 spatial adaptive subdivision。

3. Missing 語義不變：
   - 仍為 fail-closed
   - 不用舊值代替新 cycle
   - 不用常數 O₃
   - 不合成 aerosol profile

## R5.7.24 記憶體成果保留

該現場 CASE 亦驗證 R5.7.24 Memory Containment 有效：

- R5.7.23.4 最大 RSS：約 1081 MB
- R5.7.24 最大 RSS：約 821 MB
- process peak：約 1135 MB → 約 887 MB
- −6° per-angle 完成 RSS：約 1000 MB → 約 639 MB

因此本版保留 R5.7.24 全部 spool、provider-cache release、GC / malloc_trim、allocator guard 與 recovery durability。

## 科學契約

未修改：

- 13 angles：0° → −6°，0.5° 間距
- 0.5 km 垂直雲柱
- 550 / 575 / 600 / 650 / 700 / 750 nm 六波段
- Formation / Viewing / Glow 分離
- DirectSolarFraction / Earth Shadow
- Missing ≠ Clear ≠ Zero
- Route Invariance
- Tier-2 Full Directional Geometry
- Genuine MYSTIC calibration pipeline

## Regression

正式封裝前完整 regression 必須全數通過，並從 FULL-CLEAN ZIP 重新解壓再驗證。
