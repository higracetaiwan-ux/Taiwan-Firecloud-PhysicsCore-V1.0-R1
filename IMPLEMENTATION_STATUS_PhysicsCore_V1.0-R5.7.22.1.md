# PhysicsCore V1.0-R5.7.22.1 實作狀態

## 狀態

**已完成：Route Invariance Hotfix**

R5.7.22 Full Directional Cloud Scattering Geometry Contract 保留，並完成 provider sampling route 與 runtime angle set 的解耦。

## 已完成

- 固定 Reference Route 太陽高度：−2.0°。
- Reference Route 不再取 `solar_angles_deg` 中點。
- Provider route distance lattice 固定使用完整 0°～−6° 路徑需求。
- 9-angle / 13-angle runtime subset 產生相同 reference route。
- 若 −2° 不在 runtime angle set，會獨立求出 −2° crossing，不會改用其他角度。
- 新增 `route_reference_contract.csv`。
- 新增 Analysis Integrity route bearing/domain invariance 檢查。
- 新增 CASE archive member requirement。
- 保留 per-angle Sun→Cloud / Formation / Viewing / Tier-2 directional geometry。
- 版本升級為 `1.0.0-R5.7.22.1`。

## Regression Fixture

2026-09-08 Japan REAL_CANVAS R5.7.21 CASE：

- 207 route points 完整還原。
- reference azimuth 約 278.565909°。
- −5° offset bearing 約 273.565909°。
- route max 1180 km。
- 與舊 R5.7.21 route 的 lat/lon 僅剩浮點誤差。

## 測試

**386 passed / 0 failed**

## 尚待實體 CASE 驗證

需要新的 R5.7.22.1 CASE 與使用者已保存的未修正 R5.7.22 PRE-FIX CASE 做同事件 A/B，以確認：

- route drift 在真實 CASE 中歸零；
- 0°～−4° Target Optical Truth / Tier-2 readiness 回到 route-invariant 基線；
- −4.5°～−6° 僅增加 per-angle evidence，不改變 provider sampling corridor。
