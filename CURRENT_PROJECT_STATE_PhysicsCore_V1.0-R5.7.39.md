# Taiwan Firecloud PhysicsCore — Current Project State
## V1.0-R5.7.39

### 現行主線

R5.7.39：**Canvas Optical Truth Phase 1 / GFS pgrb2b Native Condensate Evidence Probe**。

### 已 Field Closed / Field Pass

- R5.7.35 Aerosol Scattering Physics Phase 1：FIELD PASS。
- R5.7.35.1 Aerosol Missing-Reason Handoff：FIELD PASS。
- R5.7.37 Near-Surface Molecular Boundary Closure：FIELD CLOSED；100 km / 3.75 km molecular coverage 156/156，原 10 m tolerance 不變。
- R5.7.38 正常 download telemetry contract：FIELD PASS；2026-09-10 CASE Analysis Integrity 62/62、CASE Integrity 23/23。真正 transient 502/503/429 same-request recovery branch 仍需自然案例 FIELD CLOSE。

### R5.7.39 問題來源

R5.7.38 真實 CASE 中，432 個 Formation Canvas 的 primary GFS target optics 大量落在 `CF_CLOUD_CONDENSATE_ZERO → DIRECT_EVIDENCE_CONFLICT`，Canvas Optical Suitability 因而維持 `OPTICS_UNKNOWN`。同 CASE 的 IFS positive-condensate cloud body 垂直位置低於 GFS 高雲 Canvas，不能合法拿來覆蓋 GFS conflict。

### R5.7.39 解法

新增 GFS `pgrb2b.0p25` 的 intermediate pressure-level direct-native condensate probe：

- 125/175/225/.../925 hPa
- CLWMR / ICMR / TCDC / TMP / HGT
- 只對 0–100 km Formation Canvas
- 只接受落入 Canvas fixed vertical envelope 的 native rows
- diagnostic-only，不 promotion COT / Formation

### 核心凍結規則

- Missing ≠ Clear ≠ Zero。
- RH / cloud fraction 不得生成 condensate/COT。
- CLWMR/ICMR 不外插。
- GFS/IFS 垂直位置不同時不得硬融合。
- probe positive 只是 direct-native evidence，不等於 COT READY。

### 目前驗證

- Focused：9/9 PASS。
- Full working-tree regression：551/551 PASS。
- FULL-CLEAN release gate：進行中。
- Field Validation：OPEN。

### 下一步

1. 完成 FULL-CLEAN、SHA256、extracted regression。
2. 用 R5.7.39 跑新 CASE。
3. 統計原本 `CF_CLOUD_CONDENSATE_ZERO` Canvas 中，pgrb2b intermediate levels 的 positive native condensate 數量與高度分布。
4. 若 field evidence 證明主 pressure-level 取樣漏雲，再設計 Phase 2 target optical truth closure；若 intermediate levels 仍全零，保留 conflict。
