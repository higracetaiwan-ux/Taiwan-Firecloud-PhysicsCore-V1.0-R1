# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.19

## 名稱
**Ice Optics Phase 2 Step 3F — Exact Wyser Eq.(5)/(6) Geometry + Mass-Size / PSD Mass-Closure Qualification**

## 主要新增
- 新增 `firecloud/ice_microphysics_wyser_mass_geometry_closure.py`。
- 新增 Step 3F evidence / gate / contract。
- 新增 3 個 Analysis Integrity hard gates。
- 新增 3 個 CASE Archive required-member gates。
- 新增 3 個 CASE Archive content gates。
- CASE export 由當前版本 builder 重建 Step 3F static evidence。
- `D=2.5L^0.6` 僅升格為 **CORROBORATED_SECONDARY_LINEAGE**，不宣稱 primary numeric Eq.(5) 已釘住。
- Eq.(6) machine extraction 仍拒絕作為 numeric mass-size contract。
- Formation / Viewing / Twilight Glow / 六波段 Frozen Science 不變。

## Gate
`WYSER_GEOMETRY_LINEAGE_CORROBORATED_PRIMARY_MASS_SIZE_CLOSURE_BLOCKED`

## Regression
- Step 3F primary TDD：7/7 PASS。
- Targeted regression：81/81 PASS。
- Working-tree full regression：828/828 PASS（0 failed；1 個既有 pandas FutureWarning）。
- Final packaged fresh-extract：待最終封裝後驗證。

## Release state
`IMPLEMENTATION / REGRESSION PASS — FIELD VALIDATION PENDING`
