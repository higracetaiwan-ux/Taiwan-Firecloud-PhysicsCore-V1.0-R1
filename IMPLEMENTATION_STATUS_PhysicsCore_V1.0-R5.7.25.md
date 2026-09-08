# PhysicsCore V1.0-R5.7.25 實作狀態

## 已完成

- Formation Sun→CloudBase cloud-path completeness 由 V1 Canvas-specific OpticalPathResult 統一治理。
- finite native cloud τ 不再等同 production-complete cloud transmission。
- partial native τ 保留為 lower-bound diagnostic。
- CF cloud + native condensate zero／不支持正式分類為 `DIRECT_EVIDENCE_CONFLICT`。
- resolved vertical COT + unresolved horizontal support 保持 `PARTIAL`，不得升級 Full RT。
- Penumbra RT applicability 改以 CloudBase `DirectSolarFraction` 為權威；nearest native voxel-centre shadow 不再否決真正受光 Canvas。
- `SPECTRAL_CLOUD_PATH` 正式納入 `physics_data_completeness.csv`。
- `FULL_SPECTRAL_RT` completeness 與 V1 Sun→CloudBase path 強制一致。
- 新增 `FULL_RT_COMPLETENESS_V1_PATH_CONSISTENCY` Integrity check。
- UI 與文件明確分開：
  - Formation = Sun→CloudBase（紅光照到雲）
  - Viewing = Cloud→Observer（觀測者看得到）

## 真實 CASE 驗證狀態

R5.7.24.3 sunrise CASE 已用於離線 replay：

- Provider cycle freeze / CAMS handoff / CASE Integrity 已在 R5.7.24.3 REAL CASE 驗證。
- Direct-sunlit Canvas 與六波段 Formation incident RT 已存在。
- −2° penumbra target 證明 CloudBase `DirectSolarFraction > 0` 時 atmospheric RT 必須執行，即使 nearest voxel-centre illumination 已為 0。
- replay 顯示 Gas/Aerosol path 可以完整，但 Cloud direct-evidence conflict 仍正確阻擋 Full Formation RT。

## 仍未完成／下一階段

- 需要以 R5.7.25 正式部署後的新 REAL CASE 驗證新的 `SPECTRAL_CLOUD_PATH` 與 Full RT completeness 輸出。
- Target Canvas COT conflict closure 尚未完成；不得以 RH/CF/geometry 造 COT。
- 真實 `BOUNDED_NATIVE_BRACKET` CASE 尚待 field validation。
- calibrated production Tier-2 directional LUT 尚未由外部 libRadtran/MYSTIC 產生／安裝。
- Viewing Full RT 尚未完成最終產品化驗收。
- Glow / Twilight Glow 完整產品化仍在後續分析主線。

## 測試狀態

- Working tree：445 passed / 0 failed。
- FULL-CLEAN package 解壓後：445 passed / 0 failed。
- ZIP integrity：PASS。
