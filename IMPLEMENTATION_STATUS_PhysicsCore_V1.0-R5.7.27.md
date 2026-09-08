# PhysicsCore V1.0-R5.7.27 Implementation Status

## 已完成

### Formation → Viewing → Photography Decision 聚合

- [DONE] Photography Decision 以 Formation timeline 為主索引。
- [DONE] 0°～−6°、0.5°取樣正常輸出 13/13 rows。
- [DONE] Viewing 以 left-join 加入，不再決定 Photography Decision row 是否存在。
- [DONE] Formation hard NO-GO 優先於 Viewing。
- [DONE] Formation NO-GO 時 `photography_opportunity = NO_GO`。
- [DONE] Viewing 保留原始診斷，但標記 `DIAGNOSTIC_ONLY_FORMATION_NO_GO`。
- [DONE] No-Canvas 無 target 時 Viewing = N/A，不是假 Missing。
- [DONE] `NO_CANVAS_EVIDENCE` 保持 unresolved semantics，不被誤判成物理 No Canvas。
- [DONE] Analysis Integrity 新增 angle coverage / no-go dominance guards。

## R5.7.26 CASE replay

- [PASS] Photography Decision 由 2 rows 改為 13 rows。
- [PASS] −5.5°、−6° `NOT_FORMED_EARTH_SHADOW + VIEWING_MINOR_OBSTRUCTION` 最終為 `NO_GO`，不再 `FAIR`。
- [PASS] 0°～−5° no-Canvas context 全部有 Photography Decision row。

## 尚未完成／不屬於本版

- [PENDING FIELD VALIDATION] 真實 R5.7.27 CASE。
- [PENDING] UI 13-angle 手動診斷角度切換器與「目前角度／完整 13 角度」雙匯出模式。
- [PENDING] Red-Light Evidence Robustness（CAMS 單一時次 timeout／cloud evidence conflict 分流）。
- [PENDING] Viewing Full Six-Band RT 最終閉環。
- [PENDING] Glow / Twilight Glow 完整第三分支。
- [PENDING] Target Canvas Bounded optical truth 真實 CASE 驗證。
- [PENDING] Genuine calibrated Tier-2 directional LUT。

## Regression

- Working tree：**461 passed / 0 failed**。
- FULL-CLEAN ZIP 解壓後：**461 passed / 0 failed**。
