# Taiwan Firecloud PhysicsCore V1.0-R5.7.39 發行說明

## 本版主題

**Canvas Optical Truth Phase 1 — GFS pgrb2b Intermediate-Level Native Condensate Evidence Probe**。

R5.7.38 真實 CASE 顯示，Formation Canvas 的 primary GFS target optics 大量為 `CF_CLOUD_CONDENSATE_ZERO → DIRECT_EVIDENCE_CONFLICT`。R5.7.39 不直接解除這些 conflict，而是新增同一 GFS cycle 的 `pgrb2b.0p25` 中間 pressure-level 原生凝結物 probe，先確認是否存在主 pressure-level 垂直取樣過粗造成的 evidence gap。

## 主要修改

- 新增 NOAA GFS `pgrb2b.0p25` Canvas optical-truth diagnostic provider。
- 中間層：125/175/225/275/325/375/425/475/525/575/625/675/725/775/825/875/925 hPa。
- 原生變數：CLWMR / ICMR / TCDC / TMP / HGT。
- probe 只在 0–100 km Formation Canvas domain 內工作。
- 只保留落入 Canvas 固定垂直 envelope 的 native pressure-level evidence。
- 新增 CASE probe evidence、summary 與 request audit。
- 新增 `CANVAS_OPTICAL_TRUTH_PGRB2B_PROBE_CONTRACT` Integrity。
- API efficiency / runtime cache provenance 納入新 probe provider。

## 科學護欄

- 不使用 RH 生成 condensate。
- 不使用 cloud fraction 生成 COT。
- 不對 CLWMR/ICMR 做垂直外插。
- Missing 仍保持 Missing。
- `CF_CLOUD_CONDENSATE_ZERO` 不會因 probe 存在就自動變成 PASS。
- R5.7.39 不修改 target COT readiness、Formation、Viewing、Glow 或 Photography decision。
- 不把垂直位置不同的 IFS condensate 強套到 GFS Canvas。

## 驗證

Focused R5.7.39 tests：**9/9 PASS**。

Working-tree full regression：**551/551 PASS**。

正式 FULL-CLEAN 與 extracted regression 於 release gate 完成後記錄於 Current Project State。

## Field Validation

需要用 R5.7.39 新 CASE 檢查中間 pressure levels 是否在原本 conflict Canvas 中發現 positive native CLWMR/ICMR。只有取得 field evidence 後，才評估 Phase 2 target optical truth closure。
