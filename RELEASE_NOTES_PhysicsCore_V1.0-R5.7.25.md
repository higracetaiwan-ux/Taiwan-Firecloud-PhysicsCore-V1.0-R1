# Taiwan Firecloud PhysicsCore V1.0-R5.7.25 發行說明

## 主題

**Formation Sun→CloudBase Cloud-Path Completeness + Penumbra RT Applicability**

本版專門修正 Formation（紅橘光照射到目標雲底）路徑的光學完整性與曙暮光半影邊界判定。它不屬於 Viewing 改版。

### 先釐清兩條不同物理路徑

- **Formation：Sun→CloudBase**：回答「太陽紅橘光能不能穿過上游大氣／雲體，真正照到目標雲底」。本版的 `Cloud Path`、`SPECTRAL_CLOUD_PATH`、`OpticalPathResult`、`FULL_SPECTRAL_RT` 都屬於這一條。
- **Viewing：Cloud→Observer**：回答「即使火燒雲已形成，觀測者能不能看得到」。這是獨立分支，本版沒有把它混入 Formation，也沒有用 Viewing 結果回寫 Formation。

## 問題一：finite native cloud τ 被誤當完整 Formation cloud path

R5.7.24.3 sunrise REAL CASE 顯示，底層 native spectral RT 可以取得有限 `slant_cloud_optical_depth_estimate`，但 V1 Canvas-specific OpticalPathResult 仍判定上游雲光學證據存在 conflict／horizontal support 不完整。舊完整度層可能仍把這些 target 宣告為 `FULL_SPECTRAL_RT=READY`，造成同一事件兩套 Formation cloud-path 判定不一致。

R5.7.25 修正：

- V1 Canvas-specific `Sun→CloudBase OpticalPathResult` 成為 Formation Full RT completeness 的權威判定。
- native cloud slant τ 只有在 `upstream_path_checked=True`、`native_ray_path_completeness>=0.999`、`upstream_path_state=UPSTREAM_PATH_CHECKED` 時，才可公開成 production `cloud_transmission_λ`。
- finite 但 incomplete 的 native τ 仍保存為 `cloud_rt_native_known_tau_lower_bound`，僅供診斷／下界，不得冒充完整傳輸。

## 問題二：Cloud Fraction 與 native condensate 衝突被混成一般 Missing

若 forecast Cloud Fraction 顯示有雲，但 native condensate 為 0／不足，這不是「已知無雲」，也不只是一般資料缺失。

R5.7.25 將此類 upstream blocker 明確分類為：

- `DIRECT_EVIDENCE_CONFLICT`
- `CF_CLOUD_CONDENSATE_ZERO` 或相關直接證據衝突原因

並使 Formation spectral path 保持：

- `DIRECT_CLOUD_EVIDENCE_CONFLICT`
- `tau_cloud = NaN`
- known lower bound 可保留，但不產生假的 Full RT。

## 問題三：已解析垂直 COT 但 horizontal support 不完整

垂直 optical evidence 有值，不代表 Sun→CloudBase 的水平路徑支持完整。

若 vertical COT 已解析但 horizontal support 仍不完整，R5.7.25 維持：

- `CLOUD_HORIZONTAL_SUPPORT_UNRESOLVED`
- `PARTIAL`

不得升級為完整 upstream cloud RT。

## 問題四：Penumbra 中 native voxel-centre shadow 錯誤否決真正受光 Canvas

R5.7.24.3 sunrise CASE 的 −2° target 顯示：

- CloudBase `DirectSolarFraction ≈ 0.08876`
- 最近 native sampling voxel centre 的 `geometric_illuminated_fraction = 0`

目標雲底仍可看到部分太陽盤，因此 Formation RT 仍然是 required；舊邏輯卻可能因 nearest native voxel centre 已落入陰影而把 Gas/Aerosol RT 標成 Not Applicable。

R5.7.25 改為：

- **CloudBase `DirectSolarFraction` 為 Formation RT applicability 的權威訊號**。
- native voxel-centre illumination 只保留為 sampling / diagnostic，不得否決 Canvas-base finite-solar-disk geometry。

因此 penumbra target 只要 `DirectSolarFraction > 0`，Gas / Aerosol / Cloud Formation path 仍需依真實證據計算；若 cloud evidence conflict，最後仍保持 Conflict，不會因 atmospheric RT 成功而越級成 Full RT。

## Completeness / Integrity

`physics_data_completeness.csv` 現在正式包含：

- `SPECTRAL_AEROSOL_PATH`
- `SPECTRAL_CLOUD_PATH`
- `FULL_SPECTRAL_RT`

其中 `SPECTRAL_CLOUD_PATH` 與 `FULL_SPECTRAL_RT` 必須跟 V1 Canvas-specific Sun→CloudBase OpticalPathResult 一致。

新增 Integrity check：

- `FULL_RT_COMPLETENESS_V1_PATH_CONSISTENCY`

若 completeness 層說 100% Full RT，但 V1 path table 仍有 conflict／partial，Analysis Integrity 會 FAIL，不再允許兩套 Formation truth 分歧。

## REAL CASE 離線 replay

以 R5.7.24.3 sunrise CASE 的真實 −2° target 重播：

- V1 CloudBase `DirectSolarFraction ≈ 0.08876`
- Gas RT applicability：required
- Gas path completeness：1.0
- Aerosol path：可由真實多波段 AOD Sun→CloudBase fallback 完整建立
- Cloud path：仍因 direct cloud evidence conflict 而阻擋 Full RT

這是預期行為：**大氣可算 ≠ 上游雲阻光證據已完整**。

## 不變的科學契約

本版不改：

- Formation / Viewing / Glow 三軌分離
- 13 個核心太陽高度角 0°～−6°、0.5°步距
- 六波段 550 / 575 / 600 / 650 / 700 / 750 nm
- Earth Shadow / finite solar disk / refraction / DirectSolarFraction
- Target Canvas Optical Truth（Exact / Bounded / Conflict / Missing）
- Tier-2 directional geometry / calibrated LUT gate
- Forecast / Observation / Nowcast 分離
- Missing ≠ Clear ≠ Zero ≠ Not Applicable

## 測試

- Working tree regression：**445 passed / 0 failed**
- FULL-CLEAN ZIP 解壓後 regression：**445 passed / 0 failed**
- ZIP integrity：PASS
