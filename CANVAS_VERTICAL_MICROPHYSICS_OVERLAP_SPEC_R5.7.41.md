# Taiwan Firecloud PhysicsCore V1.0-R5.7.41
## Canvas Optical Truth Phase 2A / Target Vertical Microphysics Overlap 規格

### 1. 目的
R5.7.41 不直接解決 COT，而是補上 R5.7.40 後仍缺少的 Target Cloud Base–Top 原生垂直微物理證據契約。主 `pgrb2` 與 `pgrb2b` intermediate pressure levels 的 CLWMR/ICMR/HGT/TMP 會被合併成同一條 direct-native vertical evidence column，再逐一投影到固定 Formation Canvas target envelope。

### 2. 永久硬規則
- Missing ≠ Zero ≠ Clear。
- RH / cloud fraction 不得生成 condensate、COD、COT。
- pgrb2b cloud fraction 不參與 target geometry 或 COT。
- Boundary support ≠ Interior support。
- `cot_promotion_allowed=False`。
- `formation_promotion_allowed=False`。
- R5.7.41 不修改 Formation / Viewing / Glow / Photography science。

### 3. Target sample position
每個 direct-native pressure-level sample 分成：
- `INTERIOR`
- `BOUNDARY_LOWER`
- `BOUNDARY_UPPER`
- `BOUNDARY_NEAR`（僅浮點 round-trip 容差）
- `BELOW_TARGET`
- `ABOVE_TARGET`
- `UNKNOWN`

Boundary tolerance 僅為 `1e-5 km` 的數值容差，不得被解讀為擴張實際雲體。

### 4. Overlap states
- `INTERIOR_NATIVE_CONDENSATE_SUPPORT`
- `BOUNDARY_ONLY_NATIVE_CONDENSATE_SUPPORT`
- `NO_NATIVE_CONDENSATE_SUPPORT`
- `MIXED_CONFLICT_WITH_INTERIOR_SUPPORT`
- `VERTICAL_EVIDENCE_INCOMPLETE`

若 pgrb2b 預期中間層缺資料，必須進入 `VERTICAL_EVIDENCE_INCOMPLETE`，不得因 sample 不存在而視為 zero。

### 5. COT 診斷骨架
現有 bulk optics 公式沿用：

`beta_ext ~= 3 Qext M / (4 rho r_eff)`

預設有效半徑仍為明示假設：
- liquid `r_eff = 10 μm`
- ice `r_eff = 30 μm`

因此即使診斷成功，也只能標記：
- `COT_ESTIMATE_ASSUMED_REFF`
- `DIAGNOSTIC_ASSUMED_REFF_NOT_NATIVE_COT`

若 target 存在 `DIRECT_EVIDENCE_CONFLICT`，則 COT 診斷必須：
- `BLOCKED_DIRECT_EVIDENCE_CONFLICT`
- estimate = Missing

### 6. 新增 CASE evidence
- `v1_canvas_vertical_microphysics_overlap.csv`
- `v1_canvas_vertical_microphysics_samples.csv`
- `v1_canvas_vertical_microphysics_overlap_summary.csv`

### 7. Integrity
新增 `CANVAS_VERTICAL_MICROPHYSICS_OVERLAP` guard，檢查：
- direct conflict canvases coverage
- allowed overlap states
- boundary/interior semantics
- Missing preservation
- no CF/RH→COT
- conflict blocks assumed-r_eff COT diagnostic
- no COT/Formation promotion

### 8. Offline Replay
附 `tools/replay_r5741_canvas_vertical_overlap.py`，可直接讀既有 R5.7.40/R5.7.40.1 CASE ZIP，不呼叫 GFS/CAMS，快速重播舊 qualification evidence 到 R5.7.41 boundary/interior semantics。此工具只作 regression，不取代 production overlap engine。
