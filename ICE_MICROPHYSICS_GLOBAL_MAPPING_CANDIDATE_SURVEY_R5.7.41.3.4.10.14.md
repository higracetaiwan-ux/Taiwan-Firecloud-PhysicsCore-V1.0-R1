# Ice Optics Phase 2 Step 3 — Global Mapping Candidate Intake / Scheme Contract Qualification

版本：`R5.7.41.3.4.10.14`  
Evidence as of：`2026-09-16`  
Science baseline：`R5.7.41.2_SHADOW_COT_AB_FROZEN`  
模式：`GLOBAL_MAPPING_CANDIDATE_QUALIFICATION_ONLY`

## 目的

本階段把「全球可用」列為優先資格，但**不把全球覆蓋等同 mapping 合法性**。候選來源只有在 exact operational scheme revision、namelist/config、hydrometeor semantics、PSD/mass-size relation、size-variable semantics、domain/uncertainty、QA 與 independent validation 全部完成後，才可能進入下一層 mapping validation。

## 全球候選排序

### Priority 1 — NOAA GFS v16 / GFDL Cloud Microphysics

- 2026-09-16 現行 operational GFS 仍為 v16；全球覆蓋、可預報台灣，PhysicsCore 已直接 ingest GFS native ice mass (`ICMR`)。
- NOAA/CCPP 文件確認 GFS v16 使用 GFDL Cloud Microphysics；GFS v16 也包含 ice-cloud effective-radius 改良。
- 但目前只能確認 **scheme family**，不能把其他 GFDL release（特別是 MP v3 / SHiELD）參數直接當成 operational GFS v16 exact runtime contract。
- 下一個必要工作：pin exact GFS v16 operational microphysics source revision/tag/commit、operational namelist、cloud-ice PSD/mass-size parameter set、size variable 定義。
- 狀態：`BLOCKED_EXACT_RUNTIME_SCHEME_CONTRACT_NOT_PINNED`。

官方/技術來源：
- https://www.emc.ncep.noaa.gov/emc/pages/numerical_forecast_systems/gfs/documentation.php
- https://dtcenter.ucar.edu/GMTB/v7.0.0/sci_doc/_g_f_s_v16_page.html

### Priority 2 — NOAA GFS v17 / Thompson

- NOAA 2026 公告提出 2026-10 將 GFS v16 升級為 v17；截至 2026-09-16 尚未成為 operational baseline。
- GFS v17 prototype 把 GFDL Cloud Microphysics 改成 Thompson scheme。
- Thompson 官方 CCPP SciDoc 顯示 cloud ice 除 mass 外，還 prognose ice number concentration，且 code 有明確 ice distribution / effective radius logic。
- 這是未來很強的全球 mass+number candidate，但必須等 operational release、exact revision 與 public output contract 被確認。
- 狀態：`BLOCKED_NOT_CURRENT_OPERATIONAL_AND_OUTPUT_CONTRACT_UNPROVEN`。

官方/技術來源：
- https://www.weather.gov/media/notification/pdf_2026/pns26-29_Science_for_GFSv17.pdf
- https://dtcenter.ucar.edu/GMTB/v7.0.0/sci_doc/_g_f_s_v17_p8_ugwpv1_page.html
- https://dtcenter.ucar.edu/GMTB/v6.0.0/sci_doc/_t_h_o_m_p_s_o_n.html

### Priority 3 — DWD ICON global

- 全球 operational、可覆蓋台灣。
- DWD ICON tutorial 清楚區分 single-moment 與 double-moment schemes；double-moment 預報 mass + number，但文件指出較適合約 3 km 或更細 convection-permitting/resolving meshes。
- 因此不能把 double-moment `qni` 假設套到 global operational ICON；目前 global open-data survey 有 `qi`，但未建立 global qni runtime contract。
- 狀態：`BLOCKED_EXACT_OPERATIONAL_CONFIGURATION_AND_SIZE_SEMANTICS_UNPROVEN`。

官方來源：
- https://opendata.dwd.de/weather/nwp/icon/grib/
- https://dwd.de/EN/ourservices/nwp_icon_tutorial/pdf_volume/icon_tutorial2025_en.pdf?__blob=publicationFile&v=3

### Reference — GFDL SHiELD / GFDL MP v3

- 全球 forecast research/reference；不是 PhysicsCore 現行 operational provider。
- GFDL MP v3 公開論文明確定義 gamma PSD；single-moment case 中 `n0` 與 `mu` 為 scheme constants、`lambda` 可由 prognostic mass mixing ratio `q` 推導。
- 它非常適合做「scheme-native mass→PSD reconstruction methodology」參考。
- 但**不得假設 MP v3 參數等於 GFS v16 operational runtime**；且其 scheme particle diameter 與 Yang/Bi nonspherical-habit `Dmax` 的 semantic bridge 仍未證明。
- 狀態：`REFERENCE_ONLY_NOT_CURRENT_OPERATIONAL_SOURCE`。

來源：
- https://www.gfdl.noaa.gov/shield/
- https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2021MS002971

### Reference — ECMWF IFS effective dimension

- 全球 operational。
- IFS radiation 文件明確以 temperature 與 in-cloud IWC 診斷 ice effective dimension/effective radius。
- 這是 radiation-effective size，不是 Yang/Bi maximum particle dimension；因此不可直接 `De/re → Dmax`。
- 狀態：`BLOCKED_SIZE_SEMANTIC_MISMATCH`。

來源：
- https://www.ecmwf.int/en/publications/ifs-documentation

### NASA GEOS-FP

- 全球 operational forecast，有 `QI/QS` mass state。
- 現行 public forecast collections 沒有足夠的 ice number / PSD / direct size state 可以直接建立 mapping candidate。
- 狀態：`BLOCKED_INSUFFICIENT_PARTICLE_SIZE_STATE`。

來源：
- https://gmao.gsfc.nasa.gov/geos-system-news/geos-fp-upgrade-to-system-version-5430-on-feb-26-2026/
- https://gmao.gsfc.nasa.gov/publications/office_notes/

## Step 3 正式結論

`NOAA_GFS_V16_GFDL_MP_CURRENT` 是**第一調查目標**，不是已核准 mapping source。

目前仍為：
- `CURRENT_GLOBAL_DIRECT_DMAX_ELIGIBLE=false`
- `CURRENT_GLOBAL_SCHEME_PSD_RECONSTRUCTION_ELIGIBLE=false`
- `MAPPING_CANDIDATE_ELIGIBLE=false`
- `PRODUCTION_ICE_OPTICS_READY=false`
- `physics_promotion_allowed=false`

## 下一步

Step 3B 應只針對 Priority 1 做 **GFS v16 exact scheme pinning**：
1. pin operational GFS v16 microphysics source revision/tag/commit；
2. pin operational namelist/config（尤其會改變 ice PSD/effective size 的參數）；
3. 對 cloud ice / snow / graupel category 做語義隔離；
4. 擷取同一 scheme 的 PSD equation、mass-size/density relation 與所有 constants；
5. 證明 scheme diameter 與 Yang/Bi `maximum_dimension_um` 是否同義；若不同，必須建立獨立、可驗證的 semantic bridge；
6. habit/roughness 在 production 前仍需獨立證據，不准 default；
7. 先做 diagnostic replay/QA，不允許直接 production promotion。
