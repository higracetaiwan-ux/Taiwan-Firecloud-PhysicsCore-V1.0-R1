# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.18

## 版本
`1.0.0-R5.7.41.3.4.10.18`

## 名稱
**Ice Optics Phase 2 Step 3E — Wyser PSD Normalization + Hex-Column Geometry / L→Dmax Coordinate Qualification**

## 新增
- `firecloud/ice_microphysics_wyser_psd_geometry_contract.py`。
- Step 3E evidence / gate / contract。
- Analysis Integrity 3 個 hard gates。
- CASE Archive required-member 3 gates。
- CASE Archive content 3 gates。
- CASE export 由當前版本 builder 重建 static Step 3E evidence。

## 科學狀態
- primary-source IWC amplitude normalization rule：PINNED。
- absolute PSD numeric reconstruction：BLOCKED。
- exact Wyser column geometry：BLOCKED。
- L→Yang/Bi Dmax：BLOCKED。
- Production Ice Optics / physics promotion：BLOCKED。

## Regression
- Step 3E primary TDD：7/7 PASS。
- targeted：64/64 PASS。
- full regression（分組）：821/821 PASS。
- 既有 pandas FutureWarning：1，非失敗。

## Release gate
`IMPLEMENTATION / REGRESSION PASS — FIELD VALIDATION PENDING`
