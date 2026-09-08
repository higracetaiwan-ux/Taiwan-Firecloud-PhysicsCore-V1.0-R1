# Taiwan Firecloud PhysicsCore V1.0-R5.7.27 Release Notes

## 版本主旨

**Formation-First Photography Decision Aggregation**

本版修正 R5.7.26 真實 sunset CASE 暴露的兩個最外層聚合問題：Photography Decision 只有 2/13 angles，以及 Formation 已明確不成立時仍被 Viewing 顯示成 `FAIR`。

## 主要修改

- Photography Decision 改由 Formation timeline 作主索引，正常核心分析輸出完整 13/13 angles。
- Viewing 僅 left-join 到 Formation；Viewing rows 稀疏不再刪除其他角度的 Photography Decision。
- 新增 `formation_gate_state`。
- 新增 `viewing_decision_role`。
- Formation hard NO-GO 優先於 Viewing：已確定 no-Canvas、Earth Shadow、Formation failed／illumination blocked 時，`photography_opportunity = NO_GO`。
- Viewing 原始狀態仍保留，但在 Formation NO-GO 時標為 `DIAGNOSTIC_ONLY_FORMATION_NO_GO`。
- No-Canvas 且沒有 target 時，Viewing 改為 `VIEWING_NOT_APPLICABLE_NO_FORMED_TARGET`，不是 Missing。
- `NO_CANVAS_EVIDENCE` 不被直接硬判 NO-GO，以維持 Missing ≠ No Canvas。
- Analysis Integrity 新增 13-angle coverage 與 Formation NO-GO dominance 檢查。

## R5.7.26 真實 sunset CASE 離線 replay

原始 R5.7.26 CASE：

- Photography Decision 只有 −5.5°、−6.0°兩列。
- 兩列 Formation 都是 `NOT_FORMED_EARTH_SHADOW`。
- Viewing 都是 `VIEWING_MINOR_OBSTRUCTION`。
- 舊最終結果卻為 `FAIR`。

R5.7.27 replay：

- Photography Decision = **13/13 rows**。
- 0°～−4.5°：`NO_CANVAS_RED_PATH_CONFLICT → NO_GO`。
- −5°：`NO_CANVAS_NO_DIRECT_RED_ACCESS → NO_GO`。
- −5.5°、−6°：`NOT_FORMED_EARTH_SHADOW → NO_GO`。
- −5.5°、−6°的 `VIEWING_MINOR_OBSTRUCTION` 仍保留，但只作 diagnostic。

## 不變的凍結契約

- Formation = Sun→CloudBase。
- Viewing = Cloud→Observer。
- Glow 為獨立第三分支。
- Red-Light Availability ≠ Formation。
- Missing ≠ Clear ≠ Zero ≠ Not Applicable。
- 不恢復單一 Physics Score。
- 不修改六波段、COT truth、Tier-2、Earth Shadow、Provider 或 Forecast/Observation 分離規則。

## 驗收

- 專項 Photography Decision regression：**9 passed / 0 failed**。
- Working tree 完整 regression：**461 passed / 0 failed**。
- FULL-CLEAN ZIP 解壓後完整 regression：**461 passed / 0 failed**。
- R5.7.26 真實 CASE 離線 replay：13/13 + Formation NO-GO dominance PASS。
- 真實 R5.7.27 部署 CASE：尚待 field validation。
