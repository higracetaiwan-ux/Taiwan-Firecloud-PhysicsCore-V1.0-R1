# Implementation Status — V1.0-R5.7.41.3.4.10.12

## 狀態

**Ice Optics Phase 2 Step 1B IMPLEMENTATION / REGRESSION PASS。FIELD VALIDATION PENDING。**

最後一個 FIELD PASS 基線仍為 `V1.0-R5.7.41.3.4.10.11.2`；Science baseline 維持 `R5.7.41.2_SHADOW_COT_AB_FROZEN`。

## 程式實作

- 新增 `firecloud/ice_microphysics_capability.py`。
- `firecloud/model.py` 在既有 GFS inventory / native cloud / Ice runtime 完成後建立：
  - `v1_ice_microphysics_native_input_capability_audit`
  - `v1_ice_microphysics_phase2_mapping_eligibility`
  - `ice_microphysics_phase2_contract`
- `app.py` 將下列 evidence 納入 CASE ZIP / manifest / SHA256：
  - `ice_microphysics_native_input_capability_audit.csv`
  - `ice_microphysics_phase2_mapping_eligibility.csv`
  - `ice_microphysics_phase2_contract.json`
- GFS provenance aggregate 保留 run / forecast-hour / valid-time，供 audit 使用；不改 provider physics。

## Fail-close contract

本版明確不建立：

- `r_eff -> Dmax`
- `IWP -> Dmax`
- `T / RH / TCDC / cloud thickness -> Dmax`
- assumed PSD
- fixed/default habit
- fixed/default surface roughness

Positive IWP 若缺合法 Dmax/PSD/habit/roughness，mapping readiness 維持 false；`physics_promotion_allowed=false`。

## 驗證

- Phase 2 targeted regression：**25 passed / 0 failed**。
- Full regression：**772 passed / 0 failed / 1 existing pandas FutureWarning**。
- `.10.11.2` TWS175 FIELD CASE replay：2691 runtime rows，213 positive-IWP，Dmax/r_eff/resolved habit/resolved roughness 均 0；結果 `INSUFFICIENT_MICROPHYSICS`，符合預期。

## 科學邊界

Formation / Viewing / Twilight Glow / Production COT / 六波段 / Canvas / Corridor / REZ / Earth Shadow / Missing semantics 全部保持凍結。
