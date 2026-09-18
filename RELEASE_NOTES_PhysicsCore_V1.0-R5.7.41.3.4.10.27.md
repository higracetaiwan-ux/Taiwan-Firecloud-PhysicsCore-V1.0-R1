# Release Notes — Taiwan Firecloud PhysicsCore V1.0-R5.7.41.3.4.10.27

## Step 3N — Fu96/RRTMG Independent Bulk-band SSA + Asymmetry Qualification

### 新增
- `firecloud/ice_microphysics_fu96_rrtmg_ssa_asymmetry_qualification.py`
- Step 3N 11-row evidence、1-row gate、contract。
- Fu96 / RRTMG `ssaice3` / `asyice3` source provenance pins。
- RRTMG band 24/25 與六個 production wavelengths 的 spectral-containment mapping。
- Model / CASE / integrity handoff。

### 科學邊界
本版沒有把 RRTMG broad-band coefficient 改稱 550/575/600/650/700/750 nm 的單色 coefficient。Reference availability ≠ numerical validation pass。

### 未解鎖
independent SSA numerical validation、independent asymmetry numerical validation、exact six-band like-for-like optical validation、`tau_ice` production、Production Ice Optics、physics promotion 全部仍 false。

### FIELD baseline
最新正式 FIELD baseline 維持 `.10.26 FIELD PASS`；`.10.27` 必須完成 QA release closure 與新的 FIELD CASE 後才可升格。
