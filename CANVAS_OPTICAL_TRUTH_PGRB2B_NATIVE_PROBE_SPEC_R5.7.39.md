# R5.7.39 Canvas Optical Truth Phase 1
## GFS pgrb2b Intermediate-Level Native Condensate Probe 規格

### 目的

R5.7.38 真實 CASE 中，Formation Canvas 的 primary GFS target optics 大量落在 `CF_CLOUD_CONDENSATE_ZERO → DIRECT_EVIDENCE_CONFLICT`。同時，這些高雲 Canvas 位於約 13–16 km，而既有 GFS primary pressure-level 取樣在高層主要使用 100/150/200 hPa 等主層，存在漏掉中間垂直結構的可能。

R5.7.39 只回答一個問題：

> 在同一 GFS forecast cycle、同一路徑、同一 Canvas 垂直範圍內，`pgrb2b.0p25` 的中間 pressure levels 是否存在原生 CLWMR/ICMR 凝結物證據？

本版是 **Evidence Probe**，不是 COT promotion 版本。

### 原生資料

Provider：`NOAA_GFS_0P25_PGRB2B_CANVAS_OPTICAL_PROBE`

中間 pressure levels：

`125/175/225/275/325/375/425/475/525/575/625/675/725/775/825/875/925 hPa`

變數：

- `CLWMR`：cloud liquid water mixing ratio
- `ICMR`：cloud ice mixing ratio
- `TCDC`：cloud fraction
- `TMP`：temperature
- `HGT`：geopotential height

### 空間與垂直限制

- 只對 `0–100 km` Formation Canvas domain 啟用。
- 只接受落在該 Canvas 固定 `z_base_km–z_top_km` 垂直包絡內的中間 pressure-level row。
- 不為了配對 secondary provider 而放寬垂直 overlap。
- `>100 km` 雲仍可保留其他上游/診斷角色，但不進此 Canvas target probe。

### 凍結科學規則

1. `Missing ≠ Clear ≠ Zero`。
2. 不允許 RH → condensate。
3. 不允許 cloud fraction → COT。
4. 不允許 CLWMR/ICMR 垂直外插。
5. 原生 `CLWMR + ICMR >= 1e-7 kg/kg` 才記為 `POSITIVE`。
6. condensate 為 0 且 cloud fraction >0 時保留 `CF_CLOUD_CONDENSATE_ZERO`。
7. condensate 缺失保持 `OPTICS_MISSING`。
8. R5.7.39 **不得**輸出或修改 `target_cot`、`target_optics_ready`、`formation_state`、Formation probability 或 Photography outcome。

### CASE 輸出

- `v1_canvas_optical_native_probe.csv`
- `v1_canvas_optical_native_probe_summary.csv`
- `gfs_canvas_optical_probe_request_audit.csv`

### Integrity

新增：

`CANVAS_OPTICAL_TRUTH_PGRB2B_PROBE_CONTRACT`

PASS 條件包含：

- probe source 與 contract 正確；
- 必要原生欄位存在；
- condensate numeric/state 語義一致；
- 不含任何 COT/Formation promotion 欄位。

Provider 不可用或沒有幾何重疊時為可見 `WARN`，不得把空 probe 解讀成 clear sky，也不得改寫 Formation。

### Phase 1 不處理

- 不建立新的 target COT。
- 不校正 effective radius。
- 不由 cloud fraction 建 COD/COT。
- 不跨 GFS/IFS 平均或融合 conflicting cloud bodies。
- 不修改 Formation / Viewing / Glow 權重或決策門檻。

### Field Validation 問題

下一個真實 R5.7.39 CASE 必須回答：

1. 有多少 Formation Canvas 在中間 pressure levels 取得 positive native CLWMR/ICMR？
2. 這些 positive evidence 是否出現在原本 primary `CF_CLOUD_CONDENSATE_ZERO` 的同一 Canvas 垂直包絡？
3. 若仍為全零，則 conflict 應維持，不得強制 closure。
4. 若有大量 positive，才進 Phase 2 設計：如何用更密的原生垂直 evidence 建立 target optical truth，而不是直接把 probe positive 等同 COT READY。
