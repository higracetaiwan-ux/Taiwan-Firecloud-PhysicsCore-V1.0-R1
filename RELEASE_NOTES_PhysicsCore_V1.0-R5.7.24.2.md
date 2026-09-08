# Taiwan Firecloud PhysicsCore V1.0-R5.7.24.2 改版說明

## 版本主題

**Spectral Aerosol Formation-Path Contract + NOT_APPLICABLE Semantics + Six-Band AOD Fallback**

本版針對 R5.7.24.1 REAL CASE 中出現的 `SPECTRAL_AEROSOL_PATH = MISSING` 進行科學鏈修正。目標不是把 Missing 隱藏，而是區分真正缺資料與物理上不需要計算的情況，並修正 aerosol fallback 的 Formation 幾何與六波段契約。

## 現場 CASE 發現

R5.7.24.1 / 2026-09-08 sunset CASE 顯示：

- CAMS native 3-D aerosol：READY
- CAMS spectral AOD：READY
- O₃ / gas profile / HITRAN：READY
- 但 0°～−5° 的 `SPECTRAL_AEROSOL_PATH` 與 `FULL_SPECTRAL_RT` 被標成 MISSING
- 這些角度實際上 `v1_canvas_candidates = 0`
- −5.5°、−6°雖有 Canvas candidates，但 DirectSolarFraction 全為 0，全部位於 Earth Shadow

因此 0°～−6°沒有任何需要 Formation spectral RT 的 direct-sunlit Canvas。舊邏輯因 `spectral_voxels` 為空就直接標 Missing，違反：

`Missing ≠ Not Applicable`

## 修正一：NOT_APPLICABLE 正式進入完整性契約

當：

- `canvas_count = 0` → `NO_TARGET_CLOUD_GEOMETRY`
- 有 Canvas，但 `direct_sunlit_canvas_count = 0` → `NO_DIRECT_SUNLIT_CANVAS_RT_REQUIRED`

則：

- `SPECTRAL_AEROSOL_PATH = NOT_APPLICABLE`
- `FULL_SPECTRAL_RT = NOT_APPLICABLE`
- completeness = 1.0，但 evidence state 保留為 `NOT_APPLICABLE`，不改寫成 READY/FULL。

若存在 direct-sunlit Canvas，而 spectral RT table 仍為空，仍維持 MISSING / fail-closed。

## 修正二：六波段 aerosol route AOD 契約補齊 575 nm

舊 route spectral derivation 預先衍生：

- 600 / 650 / 700 / 750 nm

但 PhysicsCore 正式契約是：

- **550 / 575 / 600 / 650 / 700 / 750 nm**

R5.7.24.2 起，real multi-wavelength AOD route 會完整提供六波段；575 nm 不再遺漏。

## 修正三：native CAMS 3-D partial tau 不再冒充完整 aerosol path

舊邏輯只要 `native_cams_aerosol_tau_650nm` 有數值，就傾向視為 native path 存在；但有限 tau 可能仍有：

- `native_cams_aerosol_path_completeness < 1`
- `native_cams_aerosol_domain_complete = False`

R5.7.24.2 起 production native aerosol path 必須同時滿足：

- 六波段 native tau 均可用
- path completeness ≥ 0.999
- domain complete = True

否則只能保留為 native partial diagnostic，不能直接餵給 Full Spectral RT。

## 修正四：fallback 改為真正 Sun→CloudBase 幾何

舊 real-AOD fallback 的歷史函式採 Observer→Target 方向，與 Formation 所需的 Sun→CloudBase 路徑不同。

R5.7.24.2 新增 Formation 專用 fallback：

`REAL_MULTI_WAVELENGTH_AOD_EXPONENTIAL_SUN_TO_CANVAS`

其特性：

- 使用 real multi-wavelength column AOD
- 以明確標示的 exponential vertical profile 做垂直重建
- 路徑幾何使用 Sun→CloudBase incoming ray
- 必須完整覆蓋路徑並在 route domain 內到達 aerosol atmosphere top 才能 production-ready
- domain / spectral support 不完整時維持 Missing/Partial，不以端點外插或常數補值

## 修正五：fallback 觸發條件改為「native path 未完整」

舊條件只在 native tau 為 NaN 時才嘗試 fallback。

新條件：

- native tau Missing，或
- native path completeness 不足，或
- native route domain 未閉合

只要 direct-sunlit target 需要 RT，就可嘗試 real-AOD Sun→CloudBase fallback。

## 科學契約未變

未修改：

- 13 angles：0° → −6°，0.5° 間距
- 0.5 km 垂直雲柱
- Formation / Viewing / Glow 分離
- DirectSolarFraction / Earth Shadow
- Missing ≠ Clear ≠ Zero
- Missing ≠ Not Applicable
- Route Invariance
- Target Optical Truth / COT conflict semantics
- Tier-2 Full Directional Geometry
- Genuine MYSTIC calibration pipeline

## Regression

Working tree 完整 regression：**434 passed / 0 failed**。

正式 FULL-CLEAN ZIP 仍需重新解壓後再跑同一套完整 regression 才可交付。
