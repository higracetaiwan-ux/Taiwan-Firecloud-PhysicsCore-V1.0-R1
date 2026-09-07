# Taiwan Firecloud PhysicsCore V1.0-R5.7.22 實作狀態

## 已完成

- Full Directional Cloud Scattering Geometry Contract
- `θ₀ / θᵥ / Δφ` target-local geometry
- Observer ENU → ECEF → Target ENU 太陽方向轉換
- scattering angle 衍生診斷閉合
- Directional LUT schema V2
- Directional LUT runtime loader / installer
- Directional calibration package contract
- Full-hemisphere production solver gate
- 5-D multilinear interpolation：`COT × r_eff × θ₀ × θᵥ × Δφ`
- Exact target deterministic Tier-2 response
- Bounded COT response interval
- local directional cell completeness audit
- legacy scattering-angle LUT migration detection
- CASE evidence 擴充
- CLI calibration / build / install tools
- 13-angle 0°～−6° 核心分析保持不變

## 科學安全邊界

R5.7.22 **不內建任何假 calibrated LUT**。

沒有 genuine full-directional calibrated LUT 時：

- `solver_eligible = False`
- 不執行 production interpolation
- 不生成假的 Tier-2 radiance
- 不改寫 Tier-1 或 Formation

## 尚待真實 CASE 驗收

需要使用有 Canvas 的 R5.7.22 CASE 確認：

1. `θ₀ / θᵥ / Δφ` 在 0°～−6° 的實際分布。
2. 既有 567 / 999 Canvas regression 類型是否全部取得 `FULL_DIRECTIONAL_GEOMETRY_READY`。
3. 未安裝 directional LUT 時是否全數安全停在 LUT gate。
4. 未來安裝 genuine calibrated LUT 後，domain coverage 與 production interpolation 是否正確啟動。

## 測試結果

目前完整 regression：

**381 passed / 0 failed**
