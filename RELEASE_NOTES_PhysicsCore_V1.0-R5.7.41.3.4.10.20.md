# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.20

## 名稱
**Ice Optics Phase 2 Step 3G — Primary Wyser Numeric Recovery Audit + Synthetic Closure Harness Readiness**

## 主要新增
- 新增 `firecloud/ice_microphysics_wyser_primary_numeric_recovery.py`。
- 新增 Step 3G evidence / gate / contract。
- 新增 dual-source numeric promotion policy。
- 新增 strictly synthetic-only `diagnostic_mass_closure()`。
- 新增 Analysis Integrity 3 個 hard gates。
- 新增 CASE Archive required-member 3 gates。
- 新增 CASE Archive content 3 gates。
- CASE export 直接由當前 release builder 重建 Step 3G static evidence。
- 不修改 Formation / Viewing / Twilight Glow / six-band Frozen Science。

## 科學結論
- Wyser primary Eq.(5)/(6) machine-readable numeric recovery **尚未完成**。
- `D=2.5L^0.6` 保留為多來源 corroborated non-primary lineage。
- corrupt Eq.(6) machine extraction 明確禁止作 numeric source。
- synthetic harness ready，但 scientific mass closure 尚未執行。
- absolute PSD / L→Dmax / Yang/Bi bulk integration / production Ice Optics 全部維持 fail-close。

## Regression
- Step 3G TDD primary：7/7 PASS
- targeted Ice Optics regression：88/88 PASS
- working-tree full regression：835/835 PASS
- 既有 pandas FutureWarning 1 個，非失敗

## Release Gate
`IMPLEMENTATION / REGRESSION PASS — FIELD VALIDATION PENDING`
