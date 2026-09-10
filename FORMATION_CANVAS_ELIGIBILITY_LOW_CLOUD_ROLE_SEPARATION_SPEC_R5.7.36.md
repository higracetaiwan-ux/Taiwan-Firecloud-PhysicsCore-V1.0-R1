# R5.7.36：Formation Canvas Eligibility / 低雲角色分離規格

## 問題來源

2026-09-10 日本 sunset CASE 中，`v1_canvas_candidates` 共 585 列，但雲底全部位於 0–0.352 km。Viewing 已正確將它們視為 `FOREGROUND_LOW_CLOUD_OBSTRUCTION_ONLY`，Formation 卻仍把它們計入 Canvas，造成 `CANVAS_PRESENT_EVALUATE_FORMATION`。

## 凍結規則

低雲是遮擋者，不是有效火燒雲 Canvas。低雲仍必須保留在 CloudScene 與 blocker/viewing 幾何中，不能刪除，也不能視為 Clear。

## R5.7.36 角色

- `FORMATION_CANVAS_TARGET`：0–100 km 且雲底 >= 2.0 km。
- `BLOCKER_ONLY_LOW_CLOUD`：0–100 km 且雲底 < 2.0 km。
- `UPSTREAM_OR_DIAGNOSTIC_CLOUD`：距離 >100 km 或不在 Formation Canvas domain。

## 執行層

`v1_cloud_layers` 保留所有雲層並新增：
- `formation_canvas_eligible`
- `formation_cloud_role`
- `formation_canvas_eligibility_reason`
- `formation_canvas_min_base_km`

`v1_canvas_candidates` 僅包含 `FORMATION_CANVAS_TARGET`。因此低雲不再建立 DirectSolar、Sun→CloudBase target optical path、Canvas radiance 或 Formation aggregation。

## Integrity

新增 `FORMATION_CANVAS_LOW_CLOUD_ROLE_SEPARATION`：任何 `<2 km` row 被升格進 `v1_canvas_candidates` 都為 FAIL。空 Canvas 在幾何完整時是合法物理結果。

## 不變項目

- 2.0 km 門檻不提高。
- 13 個太陽角、六波段、Formation/Viewing/Glow 三軌不變。
- Missing ≠ Clear ≠ Zero ≠ N/A。
- 不修改 COT、SSA、g、HG、能見度或任何分數。
