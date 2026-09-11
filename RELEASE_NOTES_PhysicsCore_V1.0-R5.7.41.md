# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41

## 主題
**Canvas Optical Truth Phase 2A / Target Vertical Microphysics Overlap**

R5.7.41 延續 R5.7.40.1 正式基線，將主 GFS `pgrb2` 與 `pgrb2b` 中間 pressure-level 的 direct-native CLWMR/ICMR/HGT/TMP 合併為 target Cloud Base–Top 垂直 evidence layer。

### 新增
- Target envelope sample position：Interior / Boundary / Outside。
- strict-interior positive native condensate 與 boundary-only support 分離。
- native known/missing coverage。
- primary target bracket availability。
- expected pgrb2b intermediate level missing count。
- lower/upper vertical bracket。
- max known vertical gap。
- assumed-r_eff COT diagnostic scaffold。
- `CANVAS_VERTICAL_MICROPHYSICS_OVERLAP` Integrity guard。
- 三份新 CASE CSV。
- 無網路 Offline CASE Replay 工具。

### 科學邊界
本版 **不**：
- promotion target COT；
- promotion Formation；
- 由 RH / cloud fraction 生成 condensate/COT；
- 把 Missing 當 zero/clear；
- 修改 Formation / Viewing / Glow / Photography 門檻或權重。

所有 direct target evidence conflict 的 COT 診斷均 fail-close 為 `BLOCKED_DIRECT_EVIDENCE_CONFLICT`。

### 2026-09-11 CASE -2 離線 replay
舊 vertical-conflict evidence：988 rows / 58 unique conflict canvases。

R5.7.41 semantics replay：
- `NO_NATIVE_CONDENSATE_SUPPORT`：979
- `BOUNDARY_ONLY_NATIVE_CONDENSATE_SUPPORT`：9
- strict-interior positive support：0

舊的 9 筆 `ADJACENT_PRIMARY_NATIVE_CONDENSATE_SUPPORT_PRESENT` 全部被更精確辨識為 boundary-only，而不是 interior support。

### Regression
- R5.7.41 focused/integration：21/21 PASS。
- Working-tree full regression：571/571 PASS。
- FULL-CLEAN extracted regression：於正式封裝 gate 執行並記錄於 Current Project State。
