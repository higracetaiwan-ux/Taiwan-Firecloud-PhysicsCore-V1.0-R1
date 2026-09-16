# IMPLEMENTATION STATUS — R5.7.41.3.4.10.14

Status: **IMPLEMENTATION COMPLETE / REGRESSION PASS / FIELD VALIDATION PENDING**

完成項目：
- 新增 `firecloud/ice_microphysics_mapping_candidates.py`。
- 建立 6 個 global-first candidate/reference records。
- GFS v16 設為 Priority 1 investigation target，但 mapping eligibility 保持 false。
- GFS v17 Thompson 明確標為 future candidate；2026-09-16 不得視為 operational。
- ICON double-moment 不得假設套用 global operational grid。
- SHiELD GFDL MPv3 只作 explicit PSD mathematical reference，不得替代 GFS v16 exact scheme。
- IFS effective dimension 明確保持 `not Dmax`。
- 新增 3 個 Analysis Integrity gates 與 3 個 CASE Archive required members。
- 沒有新增 provider download，也沒有改任何 production optical property。

Regression：
- targeted：`28 passed / 0 failed`
- full working tree：`790 passed / 0 failed / 1 existing pandas FutureWarning`
- first fresh-extract：`790 passed / 0 failed / 1 existing pandas FutureWarning`

下一步：`.10.14 FIELD CASE`，驗證三個 Step 3 evidence artifacts 與六個 integrity/archive gates 真正在實跑 CASE 內生效。
