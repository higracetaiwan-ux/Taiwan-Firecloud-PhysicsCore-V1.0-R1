# R5.7.24.2 Spectral Aerosol Formation-Path Contract

## 1. 目的

本規格定義 Formation 的 aerosol spectral path 如何判定「需要、完整、備援或不適用」。核心原則：

- Formation 路徑永遠是 **Sun→CloudBase**。
- Viewing 路徑 Cloud→Observer 不得代替 Formation aerosol path。
- Missing、Partial、NOT_APPLICABLE 必須分離。

## 2. 六波段

所有 production aerosol spectral path 使用：

`550 / 575 / 600 / 650 / 700 / 750 nm`

575 nm 必須保留，不可由 600 nm 代替。

## 3. NOT_APPLICABLE

### 3.1 NO_TARGET_CLOUD_GEOMETRY

若該太陽高度角沒有 Canvas target：

- Spectral Aerosol Path：NOT_APPLICABLE
- Full Spectral RT：NOT_APPLICABLE

這不是 Missing。

### 3.2 NO_DIRECT_SUNLIT_CANVAS_RT_REQUIRED

若存在 Canvas，但所有 DirectSolarFraction = 0：

- Spectral Aerosol Path：NOT_APPLICABLE
- Full Spectral RT：NOT_APPLICABLE

Earth Shadow 已經決定 Formation 無 direct solar illumination，不應再要求 aerosol/gas RT 補證據。

## 4. Native CAMS 3-D aerosol production-ready 條件

每個 direct-sunlit target 必須同時：

1. 六波段 native aerosol tau 可用；
2. `native_cams_aerosol_path_completeness >= 0.999`；
3. `native_cams_aerosol_domain_complete = True`。

有限 tau 但 path/domain incomplete 只屬 partial diagnostic。

## 5. Real-AOD fallback

當 native CAMS 3-D path 不完整時，可使用：

`REAL_MULTI_WAVELENGTH_AOD_EXPONENTIAL_SUN_TO_CANVAS`

必要條件：

- 至少兩個真實 spectral AOD source bands，可建立六波段 local spectral AOD；
- 使用 Sun→CloudBase ray geometry；
- route spectral support 不能超出真實範圍做端點延伸；
- path completeness ≥ 0.999；
- incoming ray 必須在 route domain 內到達 aerosol atmosphere top。

不符合則 fail-closed。

## 6. Production public aerosol term

`aerosol_tau_λ` / `aerosol_transmission_λ` 只允許：

- complete native CAMS 3-D path，或
- complete real-AOD Sun→CloudBase fallback。

partial native tau 僅保存在 `native_cams_aerosol_*` 診斷欄位，不得冒充 production aerosol transmission。

## 7. 追蹤欄位

R5.7.24.2 新增／使用：

- `aerosol_rt_path_complete`
- `aerosol_rt_path_source`
- `route_aerosol_path_completeness`
- `route_aerosol_domain_complete`
- `route_aerosol_quality`

## 8. 不變項目

本修正不改：

- cloud optical truth
- COT/COD resolver
- Earth Shadow / DirectSolarFraction
- gas RT
- Formation/Viewing 分離
- Tier-2 directional scattering
