# Taiwan Firecloud PhysicsCore V1.0-R5.7.26 Release Notes

## 版本主旨

**Red-Light Availability + Clear-Path-No-Canvas State**

本版建立獨立於真實 Canvas 的紅光可達性診斷，正式處理「紅光條件很好，但 0–40 km 與 40–100 km 沒有有效雲畫布」的典型情境。

## 主要修改

- 新增 `firecloud/red_light_availability.py`。
- 新增 virtual Reference Receivers；不會成為 Canvas，也不建立假 COT。
- Reference receiver 使用六波段 550/575/600/650/700/750 nm，保留有限太陽盤、Gas/O₃、CAMS aerosol、上游 cloud blocker 與原生 3-D hydrometeor 證據。
- 新增 `v1_red_light_reference_550_750nm.csv`。
- 新增 `v1_red_light_availability_summary.csv`。
- No Canvas 時 target-specific `SPECTRAL_AEROSOL_PATH / SPECTRAL_CLOUD_PATH / FULL_SPECTRAL_RT` 全部改為 `NOT_APPLICABLE / NO_TARGET_CLOUD_GEOMETRY`。
- 新增 `CLEAR_RED_PATH_NO_CANVAS` 等 no-Canvas context states。
- 新增 Canvas geometry evidence guard：只有 cloud geometry completeness 完整時，0 candidates 才能判 `ABSENT`；否則保持 `CANVAS_AVAILABILITY_UNKNOWN`。
- 新增 `Unused Red-Light Potential`，但明確標示為未校準連續診斷，不是 Physics Score／機率。
- legacy `physics_score` 在 no-Canvas context 下改為 `legacy_physics_score_applicable=False`，不能參與 operational angle selection。
- Headline summary 可直接輸出 `CLEAR_RED_PATH_NO_CANVAS`，不再把已確定的 no-Canvas 結果寫成 `UNKNOWN / DATA INCOMPLETE`。
- Analysis Integrity 新增 no-Canvas `NOT_APPLICABLE` 與 headline propagation 檢查。

## 不變的凍結契約

- Formation = Sun→CloudBase。
- Viewing = Cloud→Observer。
- Glow 為獨立第三分支。
- Missing ≠ Clear ≠ Zero ≠ Not Applicable。
- Forecast / Observation / Nowcast 永久分離。
- 六波段不提前合併。
- Reference receiver 不得造雲、不產生 Firecloud Formation。
- 不修改 COT truth、Tier-2 calibrated LUT、Formation/Viewing 權重。

## 2026-09-08 sunset CASE 對照

R5.7.25 CASE 在 0°～−5°皆為 `NO_CANVAS_EVIDENCE`，但舊 headline 仍顯示 `UNKNOWN / DATA INCOMPLETE`，且 `SPECTRAL_CLOUD_PATH` 曾被錯列 Missing。R5.7.26 專門收斂這個語義。

此舊 CASE 的 Forecast native cloud evidence 在部分 reference ray 上仍存在 direct evidence conflict，因此不能事後硬改成 `RED_LIGHT_PATH_OPEN`。使用者提供的實拍可作後續 Observation / Ground Truth 驗證，不可回寫成 Forecast evidence。

## 驗收

- Red-Light 專項 regression：通過。
- Working tree 完整 regression：**456 passed / 0 failed**。
- FULL-CLEAN 解壓後 regression：**456 passed / 0 failed**。
- 真實 R5.7.26 field CASE：尚待部署後驗收，因此本版不得宣稱 field-validated。
