# R5.7.25 Formation Sun→CloudBase Cloud-Path Completeness 規格

## 1. 適用範圍

本規格只處理 **Formation incoming path**：

`Sun → upstream atmosphere/clouds → target CloudBase`

目標是判斷紅橘光是否真的能到達目標雲底。

本規格**不處理**觀測者是否能看到該目標。Viewing 另屬：

`target Cloud → Observer`

兩條路徑不得互相覆寫。

## 2. 權威幾何

Formation RT 是否需要計算，以 target Canvas CloudBase 的有限太陽盤結果為準：

`DirectSolarFraction = F_sun`

- `F_sun > 0`：Formation atmospheric/cloud RT required。
- `F_sun = 0`：Direct-solar Formation RT 可為 Not Applicable；不得因 nearest native voxel-centre 的值反向改寫 CloudBase 幾何。

native voxel-centre `geometric_illuminated_fraction` 是取樣／診斷欄位，不是 Formation applicability authority。

## 3. Native cloud slant τ 公開條件

底層 native slant cloud optical depth 只有同時滿足以下條件才可成為 production cloud transmission：

1. finite `slant_cloud_optical_depth_estimate`
2. `upstream_path_checked = True`
3. `native_ray_path_completeness >= 0.999`
4. `upstream_path_state = UPSTREAM_PATH_CHECKED`

否則：

- production `cloud_transmission_λ = Missing`
- finite τ 可保留為 `cloud_rt_native_known_tau_lower_bound`
- provenance 必須指出 path missing/partial

## 4. Direct evidence conflict

若 Cloud Fraction／CloudScene 建立明確 cloud occupancy，但 native condensate 為 0 或與 occupancy 直接矛盾：

`DIRECT_EVIDENCE_CONFLICT`

不得解讀為：

- Clear
- Zero cloud optical depth
- 一般 Missing

也不得用 RH / CF / geometry 造出 COT。

## 5. Horizontal support

vertical COT 有值，不代表水平 Sun→CloudBase cloud prism 已完整解析。

若 horizontal optical support 不完整：

`CLOUD_HORIZONTAL_SUPPORT_UNRESOLVED / PARTIAL`

不得輸出 Full cloud path transmission。

## 6. V1 OpticalPathResult 為 Formation Full RT 權威

Formation Full RT 的 operational completeness 由 V1 Canvas-specific `OpticalPathResult` 判定，因為它同時保存：

- DirectSolarFraction
- Gas path
- Aerosol path
- Cloud blocker geometry
- Cloud optical evidence state
- Precipitation path
- Missing / Partial / Conflict provenance

底層 `spectral_rt` 的 finite number 只能作 component evidence，不可自行越級成最終 Formation Full RT truth。

## 7. Completeness 狀態

`SPECTRAL_CLOUD_PATH` 允許：

- READY
- PARTIAL
- CONFLICT
- MISSING
- NOT_APPLICABLE

`FULL_SPECTRAL_RT` 必須跟 V1 path rows 的 `critical_path_status / evidence_state / transmission` 一致。

## 8. Integrity

`FULL_RT_COMPLETENESS_V1_PATH_CONSISTENCY` 比較每個 direct-sunlit angle 的 V1 Full RT fraction 與 exported completeness。

若不一致，Analysis Integrity = FAIL。

## 9. Frozen boundary

本版不得：

- 以 Viewing path 代替 Formation path
- 以 target-cloud COT 當 upstream blocker COT
- 以 RH/CF/geometry 造 τ
- 以 finite partial τ 冒充完整 transmission
- 以 native voxel-centre shadow 否決 CloudBase finite-solar-disk illumination
