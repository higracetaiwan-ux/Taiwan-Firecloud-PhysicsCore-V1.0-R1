# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.17

## 版本
`1.0.0-R5.7.41.3.4.10.17`

## 名稱
**Ice Optics Phase 2 Step 3D — Wyser PSD + Yang/Bi Habit Bulk-Integration Contract Qualification**

## 主要新增
- 新增 `firecloud/ice_microphysics_wyser_yang_bulk_contract.py`。
- 新增 Step 3D evidence / gate / contract。
- 新增 Analysis Integrity 3 個 hard gates。
- 新增 CASE Archive required-member 3 gates。
- 新增 CASE Archive content 3 gates。
- CASE export 直接由當前版本 builder 重建 Step 3D static evidence，避免 handoff 空檔。
- 保留六波段 550/575/600/650/700/750 nm。
- 不修改 Formation / Viewing / Twilight Glow frozen science。

## 科學結論
- Wyser PSD 核心結構已部分 pin。
- 直接 `rei→Dmax` 仍禁止。
- future path 改為 PSD-weighted Yang/Bi bulk integration。
- absolute PSD normalization、column geometry、L→Dmax、habit、roughness、independent validation 尚未完成，因此 production promotion 仍關閉。

## Regression
- Step 3D primary TDD：7/7 PASS
- targeted regression：73/73 PASS
- working-tree full regression：814/814 PASS
- 既有 pandas FutureWarning 1 個，非失敗

## Release Gate
`IMPLEMENTATION / REGRESSION PASS — FIELD VALIDATION PENDING`
