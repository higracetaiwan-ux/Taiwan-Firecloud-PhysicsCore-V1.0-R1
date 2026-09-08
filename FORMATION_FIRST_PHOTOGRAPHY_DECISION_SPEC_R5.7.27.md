# R5.7.27 Formation-First Photography Decision 規格

## 目的

本規格凍結 Taiwan Firecloud PhysicsCore 最外層攝影決策的聚合順序：

1. Formation：`Sun→CloudBase`，回答火燒雲是否物理形成。
2. Viewing：`Cloud→Observer`，回答已形成／可能形成的 target 是否可被觀測者看見。
3. Photography Decision：只做最外層攝影解讀，不得回寫前兩條物理分支。

## 核心規則 A：13/13 Photography Decision

Photography Decision 的主索引由 Formation timeline 驅動：

`0, -0.5, -1, -1.5, -2, -2.5, -3, -3.5, -4, -4.5, -5, -5.5, -6°`

因此正常核心分析必須輸出 13/13 rows。Viewing 可以只有存在 target 的角度；其資料以 left-join 加入，不得反向決定 Photography Decision 是否存在該角度。

## 核心規則 B：Formation hard NO-GO 優先

以下屬於已解析的 Formation NO-GO 類型：

- `NOT_FORMED_EARTH_SHADOW`
- `CLEAR_RED_PATH_NO_CANVAS`
- `PARTIAL_RED_PATH_NO_CANVAS`
- `RED_PATH_ATTENUATED_NO_CANVAS`
- `NO_CANVAS_NO_DIRECT_RED_ACCESS`
- `NO_CANVAS_RED_PATH_CONFLICT`
- `NO_CANVAS_RED_PATH_UNKNOWN`
- 其他明確 `FORMATION_FAILED / NO_FORMATION / ILLUMINATION_BLOCKED` 類型

上述任何狀態存在時：

- `formation_gate_state = FORMATION_HARD_NO_GO`
- `photography_opportunity = NO_GO`
- Viewing 若存在，`viewing_decision_role = DIAGNOSTIC_ONLY_FORMATION_NO_GO`

Viewing 的 `GOOD / MINOR / PARTIAL / SEVERE` 仍可保存，但不得將最終 Photography Opportunity 改成 `GOOD / FAIR / LIMITED / BLOCKED` 來掩蓋「根本沒有形成」的事實。

## Missing 保護

`NO_CANVAS_EVIDENCE` 不等於已確認沒有 Canvas，因此不直接列入 hard NO-GO。只有在 R5.7.26 Canvas geometry completeness guard 已確認 no-Canvas，並提升成明確 no-Canvas context state 後，才可做物理 NO-GO。

## Viewing N/A

若 Formation 明確為 no-Canvas，根本沒有火燒雲 target 可建立 `Cloud→Observer` 路徑：

- `viewing_state = VIEWING_NOT_APPLICABLE_NO_FORMED_TARGET`
- `viewing_spectral_state = VIEW_SPECTRAL_NOT_APPLICABLE_NO_TARGET`

這是 N/A，不是 Missing。

## Integrity

新增兩個分析完整性硬檢查：

- `PHOTOGRAPHY_DECISION_FORMATION_ANGLE_COVERAGE`
- `PHOTOGRAPHY_FORMATION_NO_GO_DOMINANCE`

第一項要求 Photography Decision 與 Formation 的角度集合一致；第二項要求所有 Formation hard NO-GO row 的最終 opportunity 必須是 `NO_GO`。
